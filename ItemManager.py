import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTabWidget, QLabel, QSplashScreen)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPalette, QColor

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

data_path = os.path.join(base_path, "data")
if data_path not in sys.path:
    sys.path.append(data_path)

from ImageUpscale import ImageUpscaleTab 
from otbReload import OtbReloadTab
from datspr import DatSprTab

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Item Manager")
        self.resize(900, 1000)

        icon_path = os.path.join(base_path, "ItemManagerIco.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.build_main_interface()

    def build_main_interface(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        self.tab_view = QTabWidget()
        layout.addWidget(self.tab_view)

        # tab 2
        self.tab_manager = QWidget()
        self.tab_view.addTab(self.tab_manager, "Sprite Editor")
        manager_layout = QVBoxLayout(self.tab_manager)
        self.upscale_module = ImageUpscaleTab(self.tab_manager, base_path)
        manager_layout.addWidget(self.upscale_module)
        
        # tab 2
        self.datspr_module = DatSprTab()
        self.tab_view.addTab(self.datspr_module, "Spr/Dat Editor")

        # tab 3
        self.tab_otbreload = QWidget()
        self.tab_view.addTab(self.tab_otbreload, "Otb Reload")
        
        otb_layout = QVBoxLayout(self.tab_otbreload)
        self.otb_module = OtbReloadTab()
        otb_layout.addWidget(self.otb_module)

def set_dark_theme(app):
    """Configura um tema escuro estilo Fusion"""
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplica o tema escuro
    set_dark_theme(app)

    # Lógica da Splash Screen
    splash_path = os.path.join(base_path, "ItemManagersplash.png")
    splash_pixmap = QPixmap(splash_path)

    if not splash_pixmap.isNull():
        splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
        splash.show()
        
        # Função para iniciar a janela principal após o delay
        def show_main_window():
            # Precisamos declarar main_window como global para o Garbage Collector não limpar
            global main_window
            main_window = App()
            main_window.showMaximized() # Equivalente ao state('zoomed')
            splash.finish(main_window) # Fecha o splash quando a main window abrir

        # Configura timer de 3 segundos (3000ms)
        QTimer.singleShot(3000, show_main_window)
    else:
        print("Erro ao carregar imagem de splash. Iniciando diretamente.")
        main_window = App()
        main_window.showMaximized()

    sys.exit(app.exec())
