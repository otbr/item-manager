from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPen, QBrush, QWheelEvent, QPainter, QPixmap, QImage
import numpy as np

class MapPreviewWidget(QGraphicsView):

    MINIMAP_COLORS = {
        'water': QColor(65, 105, 225),       # Royal blue (azul royal)
        'sand': QColor(210, 180, 140),       # Tan (bege)
        'grass': QColor(34, 139, 34),        # Forest green (verde floresta)
        'dirt': QColor(139, 119, 101),       # Brown/tan (marrom terra)
        'stone': QColor(105, 105, 105),      # Dim gray (cinza)
        'mountain': QColor(105, 105, 105),   # Dim gray (montanha)
        'snow': QColor(255, 250, 250),       # Snow white (branco neve)
        'cave': QColor(50, 50, 50),          # Dark gray (cinza escuro)
        'river': QColor(30, 80, 180),        # Dark blue (azul escuro rio)
        'tree': QColor(0, 80, 0),            # Dark green (verde escuro árvore)
        'bush': QColor(50, 120, 50),         # Medium green (verde médio)
        'flower': QColor(255, 150, 200),     # Pink (rosa)
        'rock_soil': QColor(139, 119, 101),  # Brown/tan (terra pedregosa)
        'default': QColor(50, 50, 50)        # Cinza muito escuro
    }
    
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        

        self.setStyleSheet("background-color: #000000; border: 1px solid #333;")
        self.scene.setBackgroundBrush(QBrush(Qt.GlobalColor.black))
        
        self.current_z = 7
        self.map_width = 0
        self.map_height = 0
        

        self.minimap_data = {}
        self.minimap_pixmap_item = None
        
        self.view_rect = None
        

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.delayed_update)
        self.pending_tiles = []
        

        self.zoom_level = 1.0
    
    def initialize_map(self, width, height, z_layers):
        """Inicializa o mapa com dimensões específicas"""
        self.map_width = width
        self.map_height = height
        self.z_layers = z_layers
        self.minimap_data = {}
        
        # Inicializa as camadas configuradas
        for z in range(z_layers):
            self.minimap_data[z] = np.zeros((height, width, 3), dtype=np.uint8)
        
        # GARANTIR que a camada 7 sempre existe (térreo padrão Tibia)
        if 7 not in self.minimap_data:
            self.minimap_data[7] = np.zeros((height, width, 3), dtype=np.uint8)
        
        self.render_current_layer()

    
    def set_z_layer(self, z):
        """Muda a camada Z visualizada"""
        if z != self.current_z:
            self.current_z = z
            self.render_current_layer()
    
    def clear_map(self):
        """Limpa o preview"""
        self.scene.clear()
        self.minimap_pixmap_item = None
        self.view_rect = None
        self.pending_tiles.clear()
    
    def add_tile(self, x, y, z, terrain_type):
        """Adiciona um tile ao mapa (1 pixel = 1 tile)"""
        if z not in self.minimap_data or x >= self.map_width or y >= self.map_height:
            return
        
        color = self.MINIMAP_COLORS.get(terrain_type, self.MINIMAP_COLORS['default'])
        
        self.minimap_data[z][y, x] = [color.red(), color.green(), color.blue()]
        
        if z == self.current_z:
            self.pending_tiles.append((x, y, terrain_type))
            
            if len(self.pending_tiles) >= 1000:
                self.batch_update()
    
    def batch_update(self):

        if not self.pending_tiles:
            return
        
        if self.minimap_pixmap_item:
            self.render_current_layer()
        
        self.pending_tiles.clear()
    
    def delayed_update(self):

        self.batch_update()
    
    def render_current_layer(self):

        if self.current_z not in self.minimap_data:
            return
        

        layer_data = self.minimap_data[self.current_z]
        height, width, channel = layer_data.shape
        bytes_per_line = width * channel

        qimage = QImage(
            layer_data.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )
        
     
        pixmap = QPixmap.fromImage(qimage)
        
        
        if self.minimap_pixmap_item:
            self.minimap_pixmap_item.setPixmap(pixmap)
        else:
            self.minimap_pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.minimap_pixmap_item)
        
   
        self.scene.setSceneRect(0, 0, width, height)
        
  
        self.update_view_rect()
        
    
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.scale(self.zoom_level, self.zoom_level)
    
    def update_view_rect(self):
    
        if self.view_rect:
            self.scene.removeItem(self.view_rect)
        
        view_width = min(100, self.map_width // 4)
        view_height = min(100, self.map_height // 4)
        view_x = (self.map_width - view_width) // 2
        view_y = (self.map_height - view_height) // 2
        
        from PyQt6.QtWidgets import QGraphicsRectItem
        self.view_rect = QGraphicsRectItem(view_x, view_y, view_width, view_height)
        self.view_rect.setPen(QPen(Qt.GlobalColor.white, 1))
        self.view_rect.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.scene.addItem(self.view_rect)
    
    def wheelEvent(self, event: QWheelEvent):
        
        zoom_factor = 1.15
        
        if event.angleDelta().y() > 0:
            self.zoom_level *= zoom_factor
            self.scale(zoom_factor, zoom_factor)
        else:
            self.zoom_level /= zoom_factor
            self.scale(1 / zoom_factor, 1 / zoom_factor)
    
    def mousePressEvent(self, event):
     
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            map_x = int(scene_pos.x())
            map_y = int(scene_pos.y())
            
            if self.view_rect and 0 <= map_x < self.map_width and 0 <= map_y < self.map_height:
                view_width = self.view_rect.rect().width()
                view_height = self.view_rect.rect().height()
                
                new_x = max(0, min(map_x - view_width // 2, self.map_width - view_width))
                new_y = max(0, min(map_y - view_height // 2, self.map_height - view_height))
                
                self.view_rect.setRect(new_x, new_y, view_width, view_height)
        
        super().mousePressEvent(event)
    
    def get_minimap_color_legend(self):
  
        return self.MINIMAP_COLORS
    
    def render_map(self):

        self.render_current_layer()