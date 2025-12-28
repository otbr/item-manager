import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QTextEdit, QFileDialog, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

# Assumindo que você tem o otbparser na pasta ou no path
from otbparser import OtbFile

# --- FLAGS (Mantidas iguais) ---
OTB_FLAG_BLOCK_SOLID        = 1 << 0
OTB_FLAG_BLOCK_PROJECTILE   = 1 << 1
OTB_FLAG_BLOCK_PATHFIND     = 1 << 2
OTB_FLAG_HAS_HEIGHT         = 1 << 3
OTB_FLAG_USEABLE            = 1 << 4
OTB_FLAG_PICKUPABLE         = 1 << 5
OTB_FLAG_MOVEABLE           = 1 << 6
OTB_FLAG_STACKABLE          = 1 << 7
OTB_FLAG_FLOORCHANGEDOWN    = 1 << 8
OTB_FLAG_FLOORCHANGENORTH   = 1 << 9
OTB_FLAG_FLOORCHANGEEAST    = 1 << 10
OTB_FLAG_FLOORCHANGESOUTH   = 1 << 11
OTB_FLAG_FLOORCHANGEWEST    = 1 << 12
OTB_FLAG_ALWAYSONTOP        = 1 << 13
OTB_FLAG_READABLE           = 1 << 14
OTB_FLAG_ROTATABLE          = 1 << 15
OTB_FLAG_HANGABLE           = 1 << 16
OTB_FLAG_VERTICAL           = 1 << 17
OTB_FLAG_HORIZONTAL         = 1 << 18
OTB_FLAG_CANNOTDECAY        = 1 << 19
OTB_FLAG_ALLOWDISTREAD      = 1 << 20
OTB_FLAG_CORPSE             = 1 << 21
OTB_FLAG_CLIENTCHARGES      = 1 << 22
OTB_FLAG_LOOKTHROUGH        = 1 << 23
OTB_FLAG_ANIMATION          = 1 << 24
OTB_FLAG_FULLGROUND         = 1 << 25
OTB_FLAG_FORCEUSE           = 1 << 26

class OtbReloadTab(QWidget):
    def __init__(self, parent_ignored=None):
        super().__init__()

        self.otb = None
        self.otb_path = None
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(15)

        # Title
        lbl_title = QLabel("OTB Reload Attributes")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        # Description
        lbl_desc = QLabel("This tool will update the items.otb using the attributes from the Tibia.dat loaded in the other tab.")
        lbl_desc.setStyleSheet("color: gray;")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        # Button Load OTB
        self.btn_search = QPushButton("1. Load items.otb")
        self.btn_search.setMinimumHeight(40)
        self.btn_search.clicked.connect(self.load_otb)
        layout.addWidget(self.btn_search)

        # Path Label
        self.path_label = QLabel("No OTB loaded")
        self.path_label.setStyleSheet("color: gray; font-style: italic;")
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.path_label)

        # Button Apply
        self.btn_apply = QPushButton("2. Update OTB from DAT")
        self.btn_apply.setMinimumHeight(40)
        self.btn_apply.setStyleSheet("""
            QPushButton { background-color: #2E7D32; color: white; font-weight: bold; }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:disabled { background-color: #555; color: #888; }
        """)
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self.apply_reload)
        layout.addWidget(self.btn_apply)

        # Log Box
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Log messages will appear here...")
        layout.addWidget(self.log_box)
        
        # Beta Label
        lbl_beta = QLabel("Beta")
        lbl_beta.setStyleSheet("color: #ff5555; font-size: 30px; font-weight: bold;")
        lbl_beta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_beta)

    def load_otb(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select items.otb", "", "OTB Files (*.otb)")
        if not path:
            return

        try:
            self.otb = OtbFile()
            self.otb.load(path)
            self.otb_path = path
            
            self.path_label.setText(os.path.basename(path))
            self.path_label.setStyleSheet("color: #4FC3F7; font-weight: bold;")
            self.btn_apply.setEnabled(True)
            
            self.log(f"OTB loaded: {path}")
            self.log(f"Total items read: {len(self.otb.get_all_items())}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read OTB: {str(e)}")

    def log(self, text):
        self.log_box.append(text)

    def get_dat_editor(self):
        # Acessa a janela principal (App)
        main_window = self.window()
        
        # Verifica se o App tem o atributo 'datspr_module' (que seria a aba do editor)
        if hasattr(main_window, 'datspr_module'):
            # Verifica se essa aba tem o objeto 'editor' carregado
            if hasattr(main_window.datspr_module, 'editor') and main_window.datspr_module.editor:
                return main_window.datspr_module.editor
        
        return None

    def apply_reload(self):
        dat_editor = self.get_dat_editor()
        
        if not dat_editor:
            QMessageBox.warning(self, "Warning", 
                "The Tibia.dat file is not loaded in the ‘Spr/Dat Editor’ tab.\nPlease load the .dat first.")
            return
            
        if not self.otb:
            return

        updated_count = 0
        items_list = self.otb.get_all_items()
        
        self.log("Starting update...")
        # Força atualização visual da UI antes do loop pesado
        QApplication.processEvents()

        try:
            for item in items_list:
                cid = item.client_id
                
                # Ignora ID 0 ou inválidos
                if cid == 0: continue
                    
                # dat_editor.things é um dict {category: {id: object}}
                # 'items' é a categoria de itens
                if 'items' not in dat_editor.things: continue
                
                dat_thing = dat_editor.things['items'].get(cid)
                if not dat_thing: continue
                    
                props = dat_thing.get('props', {})
                
                new_flags = 0
                
                # Mapeamento de Flags
                if 'Unpassable' in props:      new_flags |= OTB_FLAG_BLOCK_SOLID
                if 'BlockMissile' in props:    new_flags |= OTB_FLAG_BLOCK_PROJECTILE
                if 'BlockPathfind' in props:   new_flags |= OTB_FLAG_BLOCK_PATHFIND
                if 'HasElevation' in props:    new_flags |= OTB_FLAG_HAS_HEIGHT
                if 'Usable' in props:          new_flags |= OTB_FLAG_USEABLE
                if 'Pickupable' in props:      new_flags |= OTB_FLAG_PICKUPABLE
                if 'Stackable' in props:       new_flags |= OTB_FLAG_STACKABLE
                if 'OnTop' in props:           new_flags |= OTB_FLAG_ALWAYSONTOP
                if 'Rotatable' in props:       new_flags |= OTB_FLAG_ROTATABLE
                if 'Hangable' in props:        new_flags |= OTB_FLAG_HANGABLE
                if 'HookVertical' in props:    new_flags |= OTB_FLAG_VERTICAL
                if 'HookHorizontal' in props:  new_flags |= OTB_FLAG_HORIZONTAL
                if 'AnimateAlways' in props:   new_flags |= OTB_FLAG_ANIMATION
                if 'FullGround' in props:      new_flags |= OTB_FLAG_FULLGROUND
                if 'ForceUse' in props:        new_flags |= OTB_FLAG_FORCEUSE
                
                # Exemplo de flag que não existe diretamente no DAT, mas é inferida
                if 'ShowOnMinimap' in props:   new_flags |= OTB_FLAG_LOOKTHROUGH # Ajuste conforme sua lógica

                # Lógica Inversa
                if 'Unmoveable' not in props:
                    new_flags |= OTB_FLAG_MOVEABLE
                    
                if 'Writable' in props or 'WritableOnce' in props:
                    new_flags |= OTB_FLAG_READABLE

                # Atualiza flags
                if item.flags != new_flags:
                    item.flags = new_flags

                # Attributes (Speed)
                if 'Ground' in props and 'Ground_data' in props:
                    try:
                        speed_val = int(props['Ground_data'][0])
                        item.speed = speed_val
                    except: pass
                else:
                    item.speed = 0

                # Attributes (Light)
                if 'HasLight' in props and 'HasLight_data' in props:
                    try:
                        l_level, l_color = props['HasLight_data']
                        item.light_level = int(l_level)
                        item.light_color = int(l_color)
                    except: pass
                else:
                    item.light_level = 0
                    item.light_color = 0

                updated_count += 1

            # Save
            base_dir = os.path.dirname(self.otb_path)
            filename = os.path.basename(self.otb_path)
            new_path = os.path.join(base_dir, filename.replace(".otb", "_updated.otb"))
            
            self.otb.save(new_path)
            
            self.log("--------------------------------")
            self.log(f"SUCCESS! File saved at:\n{new_path}")
            self.log(f"Items processed: {updated_count}")
            
            QMessageBox.information(self, "Completed", f"OTB Updated!\nSaved as: {os.path.basename(new_path)}")

        except Exception as e:
            self.log(f"Error during update: {str(e)}")
            QMessageBox.critical(self, "Save Error", str(e))
