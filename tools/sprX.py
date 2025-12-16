import sys
import os
import struct
import shutil
import subprocess
from PIL import Image
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFrame, QSlider, QCheckBox, QTextEdit, 
                             QFileDialog, QMessageBox, QGroupBox, QGridLayout, 
                             QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap

class SPRExtractorWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, spr_path, output_path, params):
        super().__init__()
        self.spr_path = spr_path
        self.output_path = output_path
        self.params = params
        self.stop_requested = False

    def run(self):
        try:
            self.extract_spr()
        except Exception as e:
            self.error_signal.emit(str(e))

    def extract_spr(self):
        self.log_signal.emit(f"🔄 Loading SPR: {os.path.basename(self.spr_path)}")
        
        with open(self.spr_path, 'rb') as f:

            header = f.read(8)
            if len(header) < 8:
                self.error_signal.emit("Invalid SPR file - header too short")
                return
                
            self.signature, self.sprite_count = struct.unpack('II', header)
            self.log_signal.emit(f"📊 Signature: 0x{self.signature:X}, Sprites: {self.sprite_count}")
            self.progress_signal.emit(0)

            if self.sprite_count == 0:
                self.finished_signal.emit("")
                return


            offsets = []
            for i in range(self.sprite_count):
                offsets.append(struct.unpack('I', f.read(4))[0])

            file_size = os.path.getsize(self.spr_path)
            total_steps = self.sprite_count + 1
            current_step = 0
            extracted_count = 0

            os.makedirs(self.output_path, exist_ok=True)

            for sprite_id in range(1, self.sprite_count + 1):
                if self.stop_requested:
                    self.log_signal.emit("⏹️ Extraction cancelled")
                    break

                try:
                    offset = offsets[sprite_id - 1]
                    self.log_signal.emit(f"📤 Extracting sprite {sprite_id}/{self.sprite_count}")
                    
                    if offset == 0:
                        current_step += 1
                        self.progress_signal.emit(int((current_step / total_steps) * 100))
                        continue

                  
                    next_offset = 0
                    for j in range(sprite_id, len(offsets)):
                        if offsets[j] != 0:
                            next_offset = offsets[j]
                            break
                    
                    if next_offset == 0:
                        size = file_size - offset
                    else:
                        size = next_offset - offset

                    f.seek(offset)
                    raw_data = f.read(size)
                    
         
                    img = self.decode_sprite(raw_data, self.params.get('transparency', False))
                    
                    if img is None:
                        self.log_signal.emit(f"⚠️ Sprite {sprite_id}: failed to decode")
                        current_step += 1
                        self.progress_signal.emit(int((current_step / total_steps) * 100))
                        continue

      
                    if self.params['transparent_enabled']:
                        img = self.make_transparent(img, self.params['transparent_threshold'])

      
                    output_file = os.path.join(self.output_path, f"{sprite_id:05d}.png")
                    img.save(output_file, optimize=self.params.get('optimize', True))
                    extracted_count += 1
                    
                except Exception as e:
                    self.log_signal.emit(f"⚠️ Sprite {sprite_id}: {str(e)}")
                
                current_step += 1
                self.progress_signal.emit(int((current_step / total_steps) * 100))

        self.log_signal.emit(f"✅ Extraction completed! {extracted_count}/{self.sprite_count} sprites extracted.")
        self.finished_signal.emit(self.output_path)


    def decode_sprite(self, raw_data, transparency):
        """EXATO do datspr.py - decode correto com header extended"""
        if not raw_data:
            return None

        start_idx = 0
        

        if (len(raw_data) >= 3 and raw_data[0] == 0xFF and 
            raw_data[1] == 0x00 and raw_data[2] == 0xFF):
            start_idx = 3  # Skip extended header
        

        if start_idx + 2 <= len(raw_data):
            start_idx += 2
        
        sprite_content = raw_data[start_idx:]
        
        if transparency:
            return self.decode_1098_rgba(sprite_content)
        else:
            return self.decode_standard(sprite_content)

    def decode_standard(self, data):

        try:
            w, h = 32, 32
            img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            pixels = img.load()
            
            p = 0
            x, y = 0, 0
            drawn = 0
            
            while p < len(data) and drawn < 1024:
                if p + 4 > len(data):
                    break
                    
                trans, colored = struct.unpack_from('<HH', data, p)
                p += 4
                drawn += trans
                
                # Skip transparent pixels
                current = y * w + x + trans
                y, x = divmod(current, w)
                
                if p + colored * 3 > len(data):
                    break
                    
                # Draw colored RGB pixels
                for _ in range(colored):
                    if y >= h:
                        break
                    pixels[x, y] = (data[p], data[p+1], data[p+2], 255)
                    p += 3
                    x += 1
                    drawn += 1
                    
                    if x >= w:
                        x = 0
                        y += 1
                        
            return img
        except:
            return None

    def decode_1098_rgba(self, data):

        try:
            w, h = 32, 32
            img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            pixels = img.load()
            
            x, y = 0, 0
            p = 0
            total_pixels = w * h
            drawn = 0
            
            while p + 4 <= len(data) and drawn < total_pixels:
                transparent, colored = struct.unpack_from('<HH', data, p)
                p += 4
                drawn += transparent
                
                # Skip transparent pixels
                for _ in range(transparent):
                    x += 1
                    if x >= w:
                        x = 0
                        y += 1
                    if y >= h:
                        break
                
                if p + colored * 4 > len(data):
                    break
                    
                # Draw colored RGBA pixels
                for _ in range(colored):
                    if y >= h:
                        break
                    if p + 4 > len(data):
                        break
                        
                    r = data[p]
                    g = data[p+1]
                    b = data[p+2]
                    a = data[p+3]
                    p += 4
                    
                    # FIX: alpha=0 mas RGB≠0 → opaque
                    if a == 0 and (r != 0 or g != 0 or b != 0):
                        a = 255
                        
                    pixels[x, y] = (r, g, b, a)
                    x += 1
                    drawn += 1
                    
                    if x >= w:
                        x = 0
                        y += 1
                        
            return img
        except Exception as e:
            self.log_signal.emit(f"Decode RGBA error: {e}")
            return None




    def make_transparent(self, img, threshold):
        """Remove pixels com alpha baixo"""
        data = img.getdata()
        new_data = []
        for item in data:
            if item[3] <= threshold:
                new_data.append((0, 0, 0, 0))
            else:
                new_data.append(item)
        img.putdata(new_data)
        return img

class SPRExtractorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPR Extractor Pro")
        self.setGeometry(100, 100, 1100, 750)
        self.output_folder = ""
        self.worker = None
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout_main = QVBoxLayout(self.central_widget)
        self.build_ui()
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #ffffff; }
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #4CAF50; 
                border-radius: 10px; 
                margin-top: 1ex; 
                background-color: #2d2d2d;
                padding-top: 10px;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 15px; 
                padding: 0 8px 0 8px; 
                color: #4CAF50; 
                background-color: #1e1e1e;
            }
            QTextEdit, QLineEdit { 
                background-color: #2d2d2d; 
                border: 2px solid #555; 
                border-radius: 6px; 
                padding: 6px; 
                color: #ffffff; 
                selection-background-color: #4CAF50;
            }
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                border-radius: 8px; 
                padding: 10px; 
                font-size: 13px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
            QPushButton:disabled { background-color: #666; }
            QLabel { color: #ffffff; }
            QProgressBar { 
                border: 2px solid #555; 
                border-radius: 6px; 
                text-align: center;
                background-color: #2d2d2d;
                color: #ffffff; 
                font-weight: bold; 
            }
            QProgressBar::chunk { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 4px;
            }
        """)

    def build_ui(self):
        # Header
        header = QLabel("SPRITE EXTRACTOR")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: #4CAF50; 
            padding: 20px; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #4CAF50, stop:0.5 #45a049, stop:1 #2e7d32); 
            border-radius: 12px;
        """)
        self.layout_main.addWidget(header)

        # SPR File
        path_frame = self.create_input_frame("📁 SPR File:")
        self.spr_entry = QLineEdit()
        self.spr_entry.setPlaceholderText("Select .spr file...")
        btn_spr = QPushButton("📂 Browse SPR")
        btn_spr.clicked.connect(self.select_spr_file)
        path_frame.layout().addWidget(self.spr_entry)
        path_frame.layout().addWidget(btn_spr)
        self.layout_main.addWidget(path_frame)

        # Output
        out_frame = self.create_input_frame("📂 Output Folder:")
        self.out_entry = QLineEdit()
        self.out_entry.setReadOnly(True)
        btn_out = QPushButton("Change Folder")
        btn_out.clicked.connect(self.select_output_folder)
        out_frame.layout().addWidget(self.out_entry)
        out_frame.layout().addWidget(btn_out)
        self.layout_main.addWidget(out_frame)

        # Options
        options_group = QGroupBox("⚙️ Advanced Options")
        options_layout = QGridLayout(options_group)
        
        self.chk_transparency = QCheckBox("Use Extended RGBA decoding")
        self.chk_transparency.setChecked(True)
        
        self.chk_alpha_clean = QCheckBox("Clean low-alpha pixels")
        self.slider_alpha = QSlider(Qt.Orientation.Horizontal)
        self.slider_alpha.setRange(0, 64)
        self.slider_alpha.setValue(8)
        self.slider_alpha_label = QLabel("Alpha threshold: 8")
        self.slider_alpha.valueChanged.connect(self.update_alpha_label)
        
        self.chk_optimize = QCheckBox("Optimize PNG output")
        self.chk_optimize.setChecked(True)
        
        options_layout.addWidget(self.chk_transparency, 0, 0, 1, 2)
        options_layout.addWidget(self.chk_alpha_clean, 1, 0)
        options_layout.addWidget(self.slider_alpha_label, 1, 1)
        options_layout.addWidget(self.slider_alpha, 1, 2)
        options_layout.addWidget(self.chk_optimize, 2, 0)
        
        self.layout_main.addWidget(options_group)


        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.layout_main.addWidget(self.progress_bar)


        btn_layout = QHBoxLayout()
        self.btn_extract = QPushButton("🚀 EXTRACT ALL SPRITES")
        self.btn_extract.setFixedHeight(55)
        self.btn_extract.clicked.connect(self.start_extraction)
        btn_layout.addWidget(self.btn_extract)

        self.btn_stop = QPushButton("⏹️ STOP")
        self.btn_stop.setFixedHeight(55)
        self.btn_stop.setVisible(False)
        self.btn_stop.clicked.connect(self.stop_extraction)
        btn_layout.addWidget(self.btn_stop)

        self.btn_open = QPushButton("📁 OPEN OUTPUT")
        self.btn_open.setFixedHeight(55)
        self.btn_open.setVisible(False)
        self.btn_open.clicked.connect(self.open_output_folder)
        btn_layout.addWidget(self.btn_open)
        
        self.layout_main.addLayout(btn_layout)


        self.create_display_area()

    def create_input_frame(self, label_text):
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.addWidget(QLabel(label_text))
        return frame

    def create_display_area(self):
        container = QFrame()
        layout = QHBoxLayout(container)
        
        # Info/Preview
        info_group = QGroupBox("📊 SPR Info")
        info_layout = QVBoxLayout(info_group)
        self.info_label = QLabel("No SPR selected")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_group)
        
        # Log
        log_group = QGroupBox("📋 Extraction Log")
        log_layout = QVBoxLayout(log_group)
        self.log_box = QTextEdit()
        self.log_box.setMaximumHeight(300)
        self.log_box.setReadOnly(True)
        log_layout.addWidget(self.log_box)
        layout.addWidget(log_group, 2)
        
        self.layout_main.addWidget(container)

    def update_alpha_label(self, value):
        self.slider_alpha_label.setText(f"Alpha threshold: {value}")

    def select_spr_file(self):
        spr_path, _ = QFileDialog.getOpenFileName(
            self, "Select SPR File", "", "SPR Files (*.spr);;All Files (*)"
        )
        if spr_path:
            self.spr_entry.setText(spr_path)
            self.update_spr_info(spr_path)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.out_entry.setText(folder)

    def update_spr_info(self, spr_path):
        try:
            with open(spr_path, 'rb') as f:
                header = f.read(8)
                if len(header) < 8:
                    raise ValueError("Invalid header")
                    
                signature, sprite_count = struct.unpack('II', header)
                
                offsets = []
                f.seek(8)
                for i in range(sprite_count):
                    offsets.append(struct.unpack('I', f.read(4))[0])
                
                valid_sprites = sum(1 for o in offsets if o != 0)
                
                info = f"""
SPR Signature: 0x{signature:X}
Total Sprites: {sprite_count}
Valid Sprites: {valid_sprites}
File Size: {os.path.getsize(spr_path):,} bytes
                """.strip()
                
                self.info_label.setText(info)
        except Exception as e:
            self.info_label.setText(f"❌ Error reading SPR: {str(e)}")

    def start_extraction(self):
        spr_path = self.spr_entry.text().strip()
        if not os.path.isfile(spr_path):
            QMessageBox.critical(self, "Error", "Please select a valid SPR file!")
            return

        if not self.output_folder:
            self.output_folder = os.path.splitext(spr_path)[0] + "_extracted"
        self.out_entry.setText(self.output_folder)

        params = {
            'transparency': self.chk_transparency.isChecked(),
            'transparent_enabled': self.chk_alpha_clean.isChecked(),
            'transparent_threshold': self.slider_alpha.value(),
            'optimize': self.chk_optimize.isChecked()
        }

        self.btn_extract.setEnabled(False)
        self.btn_stop.setVisible(True)
        self.btn_open.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_box.clear()
        self.log("🚀 Starting professional SPR extraction...")
        self.info_label.setText("⏳ Extracting sprites...")

        self.worker = SPRExtractorWorker(spr_path, self.output_folder, params)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def stop_extraction(self):
        if self.worker:
            self.worker.stop_requested = True
            self.log("⏹️ Stopping extraction...")

    def log(self, message):
        self.log_box.append(message)
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def on_finished(self, output_path):
        self.btn_extract.setEnabled(True)
        self.btn_stop.setVisible(False)
        self.progress_bar.setVisible(False)
        self.btn_open.setVisible(bool(output_path))
        
        if output_path and os.path.exists(output_path):
            self.info_label.setText(f"✅ COMPLETE!\nOutput: {os.path.basename(output_path)}")
            self.log(f"💾 Files saved to: {output_path}")
        else:
            self.info_label.setText("❌ Cancelled or empty SPR")

    def on_error(self, error):
        self.btn_extract.setEnabled(True)
        self.btn_stop.setVisible(False)
        self.progress_bar.setVisible(False)
        self.info_label.setText("❌ Extraction failed")
        QMessageBox.critical(self, "Error", f"Extraction failed:\n{error}")

    def open_output_folder(self):
        if self.output_folder and os.path.exists(self.output_folder):
            subprocess.Popen(['explorer', self.output_folder] if os.name == 'nt' else ['open', self.output_folder])

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    window = SPRExtractorWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
