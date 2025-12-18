import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QLabel, QSpinBox, 
                              QLineEdit, QProgressBar, QGroupBox, QFileDialog,
                              QSplitter, QSlider, QCheckBox, QGridLayout, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import qdarktheme
from map_generator import MapGenerator
from map_preview import MapPreviewWidget

class GeneratorThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    tile_generated = pyqtSignal(int, int, int, str)
    
    def __init__(self, params):
        super().__init__()
        self.params = params
    
    def run(self):
        generator = MapGenerator(
            self.params,
            progress_callback=self.progress.emit,
            tile_callback=self.tile_generated.emit
        )
        result = generator.generate()
        self.finished.emit(result)

class OTMapGenUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OTBM Generator")
        self.setGeometry(100, 100, 1600, 900)
        

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
    
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
  
        left_panel = QWidget()
        left_scroll = QScrollArea()
        left_scroll.setWidget(left_panel)
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        left_layout = QVBoxLayout(left_panel)
        

        map_group = QGroupBox("Configurações do Mapa")
        map_layout = QVBoxLayout()
        
        # Tamanho do mapa
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Tamanho (tiles):"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(50, 2048)
        self.width_spin.setValue(120)
        size_layout.addWidget(QLabel("Largura:"))
        size_layout.addWidget(self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(50, 2048)
        self.height_spin.setValue(120)
        size_layout.addWidget(QLabel("Altura:"))
        size_layout.addWidget(self.height_spin)
        map_layout.addLayout(size_layout)
        
  
        seed_layout = QHBoxLayout()
        seed_layout.addWidget(QLabel("Seed:"))
        self.seed_input = QLineEdit()
        self.seed_input.setPlaceholderText("Exemplo: 24543")

        seed_layout.addWidget(self.seed_input)
        map_layout.addLayout(seed_layout)
        
       
        z_layout = QHBoxLayout()
        
     
        self.z_layers = QSpinBox()
        self.z_layers.setRange(1, 16)
        self.z_layers.setValue(7)
        self.z_layers.setVisible(False)
        
        z_layout.addWidget(self.z_layers)
        map_layout.addLayout(z_layout)
        
        map_group.setLayout(map_layout)
        left_layout.addWidget(map_group)
        
        terrain_group = QGroupBox("Configurações de Terreno")
        terrain_layout = QVBoxLayout()
        
        noise_layout = QHBoxLayout()
        noise_layout.addWidget(QLabel("Escala de Noise:"))
        self.noise_scale = QSpinBox()
        self.noise_scale.setRange(10, 500)
        self.noise_scale.setValue(150)
        noise_layout.addWidget(self.noise_scale)
        terrain_layout.addLayout(noise_layout)
        
        octave_layout = QHBoxLayout()
        octave_layout.addWidget(QLabel("Octaves:"))
        self.octaves = QSpinBox()
        self.octaves.setRange(1, 10)
        self.octaves.setValue(3)
        octave_layout.addWidget(self.octaves)
        terrain_layout.addLayout(octave_layout)
        
        terrain_group.setLayout(terrain_layout)
        left_layout.addWidget(terrain_group)
        

        ids_group = QGroupBox("IDs dos Terrenos (deixe vazio para usar padrão)")
        ids_layout = QGridLayout()
        

        self.terrain_id_inputs = {}

        terrain_defaults = [
            ('water', 4608, 'Água'),
            ('grass', 4526, 'Grama'),
            ('dirt', 103, 'Terra'),
            ('sand', 4548, 'Areia'),
            ('mountain', 5798, 'Montanha'),
        ]
        
        row = 0
        for terrain_key, default_id, label_text in terrain_defaults:
            # Label
            label = QLabel(f"{label_text}:")
            ids_layout.addWidget(label, row, 0)
            
       
            id_input = QLineEdit()
            id_input.setPlaceholderText(f"Padrão: {default_id}")
            id_input.setMaximumWidth(100)
            ids_layout.addWidget(id_input, row, 1)
            
         
            self.terrain_id_inputs[terrain_key] = id_input
            
            row += 1
        
 
        reset_btn = QPushButton("Resetar para IDs Padrão")
        reset_btn.clicked.connect(self.reset_terrain_ids)
        ids_layout.addWidget(reset_btn, row, 0, 1, 2)
        
        ids_group.setLayout(ids_layout)
        left_layout.addWidget(ids_group)
        

        preview_group = QGroupBox("Opções de Preview")
        preview_layout = QVBoxLayout()
        
        self.live_preview_check = QCheckBox("Preview em Tempo Real")
        self.live_preview_check.setChecked(True)
        preview_layout.addWidget(self.live_preview_check)
        
        preview_group.setLayout(preview_layout)
        left_layout.addWidget(preview_group)

        output_group = QGroupBox("Arquivo de Saída")
        output_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setText("generated_map.otbm")
        output_layout.addWidget(self.output_path)
        browse_btn = QPushButton("Procurar...")
        browse_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(browse_btn)
        output_group.setLayout(output_layout)
        left_layout.addWidget(output_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Pronto para gerar")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.status_label)
        

        self.generate_btn = QPushButton("Gerar Mapa OTBM")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.clicked.connect(self.generate_map)
        left_layout.addWidget(self.generate_btn)
        
        left_layout.addStretch()
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
  
        preview_label = QLabel("Preview do Mapa (Minimap)")
        preview_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(preview_label)
        

        self.map_preview = MapPreviewWidget()
        right_layout.addWidget(self.map_preview)

        z_control_layout = QHBoxLayout()
        # z_control_layout.addWidget(QLabel("Camada Z:"))
        
        self.z_slider = QSlider(Qt.Orientation.Horizontal)
        self.z_slider.setRange(0, 15)
        self.z_slider.setValue(7)
        self.z_slider.valueChanged.connect(self.on_z_changed)
        # z_control_layout.addWidget(self.z_slider)
        
        self.z_value_label = QLabel("7")
        z_control_layout.addWidget(self.z_value_label)
        # right_layout.addLayout(z_control_layout)
        

        legend_layout = self.create_color_legend()
        right_layout.addLayout(legend_layout)
        

        splitter.addWidget(left_scroll)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)  
        splitter.setStretchFactor(1, 2) 
    
    def reset_terrain_ids(self):
        """Limpa todos os campos de IDs personalizados"""
        for input_field in self.terrain_id_inputs.values():
            input_field.clear()
        self.status_label.setText("IDs resetados para padrão")
    
    def get_custom_terrain_ids(self):
        """Retorna dicionário com IDs personalizados (ou None se vazio)"""
        custom_ids = {}
        
        for terrain_key, input_field in self.terrain_id_inputs.items():
            text = input_field.text().strip()
            if text: 
                try:
                    custom_ids[terrain_key] = int(text)
                except ValueError:
                    pass 
        
        return custom_ids if custom_ids else None
    
    def create_color_legend(self):
        """Cria legenda de cores dos terrenos (estilo minimap)"""
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Minimap:"))
        
        colors = self.map_preview.get_minimap_color_legend()
        displayed_terrains = ['water', 'sand', 'grass', 'dirt', 'stone', 'mountain']
        
        for terrain in displayed_terrains:
            if terrain not in colors:
                continue
            
            color = colors[terrain]
            color_box = QLabel()
            color_box.setFixedSize(12, 12)
            color_box.setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); "
                f"border: 1px solid #333;"
            )
            layout.addWidget(color_box)
            
            terrain_label = QLabel(terrain.capitalize())
            terrain_label.setStyleSheet("font-size: 9pt;")
            layout.addWidget(terrain_label)
        
        layout.addStretch()
        return layout
    
    def on_z_changed(self, value):

        self.z_value_label.setText(str(value))
        self.map_preview.set_z_layer(value)
    
    def browse_output(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar Mapa", "", "OTBM Files (*.otbm)"
        )
        if filename:
            self.output_path.setText(filename)
    
    def generate_map(self):
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Gerando mapa...")
        self.map_preview.clear_map()
        
        custom_ids = self.get_custom_terrain_ids()
        
        params = {
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'z_layers': self.z_layers.value(),
            'seed': self.seed_input.text() or None,
            'noise_scale': self.noise_scale.value(),
            'octaves': self.octaves.value(),
            'output_path': self.output_path.text(),
            'live_preview': self.live_preview_check.isChecked(),
            'custom_terrain_ids': custom_ids  # NOVO: IDs personalizados
        }
        
        self.map_preview.initialize_map(params['width'], params['height'], params['z_layers'])
        
        self.thread = GeneratorThread(params)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.generation_finished)
        
        if params['live_preview']:
            self.thread.tile_generated.connect(self.on_tile_generated)
        
        self.thread.start()
    
    def on_tile_generated(self, x, y, z, terrain_type):
        """Callback quando um tile é gerado"""
        self.map_preview.add_tile(x, y, z, terrain_type)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def generation_finished(self, result):
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(result)

        if "sucesso" in result.lower():
            self.map_preview.render_map()

def main():
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    
    window = OTMapGenUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
