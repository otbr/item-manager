# otbm_writer.py - Baseado no TibiaOTBMGenerator (funcional)
import struct
from typing import List

# OTBM Control Characters
NODE_START = 0xFE
NODE_END = 0xFF
ESCAPE = 0xFD

# OTBM Node Types
OTBM_ROOTV1 = 1
OTBM_MAP_DATA = 2
OTBM_TILE_AREA = 4
OTBM_TILE = 5
OTBM_ITEM = 6
OTBM_TOWNS = 12
OTBM_WAYPOINTS = 15

# OTBM Attributes
OTBM_ATTR_DESCRIPTION = 1
OTBM_ATTR_ITEM = 9

class OTBMWriter:
    def __init__(self, filename: str, version: int = 1098):
        self.filename = filename
        self.version = version
        self.buffer = bytearray()
        self.tile_data = {}  # Dicionário: {(x,y,z): ground_id}
        self.tile_items = {}  # Dicionário: {(x,y,z): [item_ids]}
        
        self.otbm_version = 2
        self.otb_major_version = 3
        self.otb_minor_version = 57
        self.width = 0
        self.height = 0
        self.description = ""
    
    def start(self):
        self.buffer = bytearray()
    
    def write_root_header(self, width: int, height: int):
        self.width = width
        self.height = height
    
    def write_map_data(self, description: str = ""):
        self.description = description
    
    def write_tile(self, x: int, y: int, z: int, ground_id: int):
        """Adiciona ou atualiza um tile - O(1)"""
        tile_key = (x, y, z)
        self.tile_data[tile_key] = ground_id
    
    def write_item(self, x: int, y: int, z: int, item_id: int):
        """Adiciona item decorativo - O(1)"""
        tile_key = (x, y, z)
        if tile_key not in self.tile_items:
            self.tile_items[tile_key] = []
        self.tile_items[tile_key].append(item_id)
    
    def finalize(self):
        self.buffer = bytearray()
        self.buffer.extend(b'OTBM')
        
        self._start_node(OTBM_ROOTV1)
        self._write_root_header()
        self._write_map_data()
        self._end_node()
        
        with open(self.filename, 'wb') as f:
            f.write(self.buffer)
    
    def _write_byte(self, value: int):
        self.buffer.append(value & 0xFF)
    
    def _write_escaped_byte(self, value: int):
        value = value & 0xFF
        if value in (NODE_START, NODE_END, ESCAPE):
            self.buffer.append(ESCAPE)
        self.buffer.append(value)
    
    def _write_escaped_bytes(self, data: bytes):
        for b in data:
            self._write_escaped_byte(b)
    
    def _write_u16(self, value: int):
        self._write_escaped_bytes(struct.pack('<H', value))
    
    def _write_u32(self, value: int):
        self._write_escaped_bytes(struct.pack('<I', value))
    
    def _write_string(self, text: str):
        encoded = text.encode('latin1')
        self._write_u16(len(encoded))
        self._write_escaped_bytes(encoded)
    
    def _start_node(self, node_type: int):
        self._write_byte(NODE_START)
        self._write_escaped_byte(node_type)
    
    def _end_node(self):
        self._write_byte(NODE_END)
    
    def _write_root_header(self):
        self._write_u32(self.otbm_version)
        self._write_u16(self.width)
        self._write_u16(self.height)
        self._write_u32(self.otb_major_version)
        self._write_u32(self.otb_minor_version)
    
    def _write_map_data(self):
        self._start_node(OTBM_MAP_DATA)
        
        if self.description:
            self._write_escaped_byte(OTBM_ATTR_DESCRIPTION)
            self._write_string(self.description)
        

        areas = {}
        for (x, y, z), ground_id in self.tile_data.items():
            base_x = (x // 256) * 256
            base_y = (y // 256) * 256
            area_key = (base_x, base_y, z)
            
            if area_key not in areas:
                areas[area_key] = []
            areas[area_key].append((x, y, z, ground_id))
        

        for (base_x, base_y, z), tiles in areas.items():
            self._write_tile_area(base_x, base_y, z, tiles)
        

        if self.otbm_version >= 2:
            self._start_node(OTBM_TOWNS)
            self._end_node()
        
        if self.otbm_version >= 2:
            self._start_node(OTBM_WAYPOINTS)
            self._end_node()
        
        self._end_node()
    
    def _write_tile_area(self, base_x: int, base_y: int, z: int, tiles: List):
        self._start_node(OTBM_TILE_AREA)
        self._write_u16(base_x)
        self._write_u16(base_y)
        self._write_escaped_byte(z)
        
        for tile_x, tile_y, tile_z, ground_id in tiles:
            self._write_tile(tile_x, tile_y, ground_id, base_x, base_y, tile_z)
        
        self._end_node()
    
    def _write_tile(self, x: int, y: int, ground_id: int, base_x: int, base_y: int, z: int):
        self._start_node(OTBM_TILE)
        
        x_offset = x - base_x
        y_offset = y - base_y
        self._write_escaped_byte(x_offset)
        self._write_escaped_byte(y_offset)
        
        # Ground item
        self._write_byte(OTBM_ATTR_ITEM)
        self._write_u16(ground_id)
        
        # Items decorativos
        tile_key = (x, y, z)
        if tile_key in self.tile_items:
            for item_id in self.tile_items[tile_key]:
                self._start_node(OTBM_ITEM)
                self._write_u16(item_id)
                self._end_node()
        
        self._end_node()
