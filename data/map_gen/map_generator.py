import random
from noise import snoise2
from otbm_generator import OTBMWriter
from borders import BorderSystem

class MapGenerator:
    DEFAULT_TERRAIN_IDS = {
        'water': 4608,
        'grass': 4526,
        'dirt': 103,
        'sand': 231,
        'mountain': 919,
    }

    TREE_IDS = [2700]
    BUSH_IDS = [2767]
    FLOWER_IDS = [2740]
    ROCK_IDS = [1285]

    def __init__(self, params, progress_callback=None, tile_callback=None):
        self.width = params['width']
        self.height = params['height']
        self.z_layers = params['z_layers']
        self.seed = params['seed'] or random.randint(1, 24000)
        self.noise_scale = params['noise_scale']
        self.octaves = params['octaves']
        self.output_path = params['output_path']
        self.progress_callback = progress_callback
        self.tile_callback = tile_callback
        self.live_preview = params.get('live_preview', True)

        # IDs customizáveis
        custom_ids = params.get('custom_terrain_ids', {})
        self.terrain_ids = self.DEFAULT_TERRAIN_IDS.copy()
        if custom_ids:
            self.terrain_ids.update(custom_ids)

        # Sistema de bordas
        self.border_system = BorderSystem()

    def generate(self):
        try:
            writer = OTBMWriter(self.output_path, version=1098)
            writer.start()
            writer.write_root_header(self.width, self.height)
            writer.write_map_data(f"Generated with OTMapGen Python - Seed {self.seed}")

            print("Fase 1: Gerando terrenos com Perlin noise...")
            terrain_map = []
            ground_ids = []
            z = 7

            for y in range(self.height):
                terrain_row = []
                ground_row = []
                for x in range(self.width):
                    noise_value = snoise2(
                        x / self.noise_scale,
                        y / self.noise_scale,
                        octaves=self.octaves,
                        base=self.seed + z
                    )
                    terrain_type, base_terrain_id = self.get_terrain_from_noise(noise_value, z)
                    terrain_row.append(terrain_type)
                    ground_row.append(base_terrain_id)
                
                terrain_map.append(terrain_row)
                ground_ids.append(ground_row)

            print("Fase 2: Aplicando bordas automÃ¡ticas...")
            # Agora retorna uma matriz de border items
            border_items = self.border_system.apply_borders(terrain_map, ground_ids, self.terrain_ids)

            print("Fase 3: Escrevendo OTBM...")
            total_tiles = self.width * self.height
            processed = 0

            for y in range(self.height):
                for x in range(self.width):
                    terrain_type = terrain_map[y][x]
                    ground_id = ground_ids[y][x]
                    
                    # Escreve o terreno base (SEMPRE mantÃ©m o terreno original)
                    writer.write_tile(x, y, z, ground_id)
                    
                    # Se existe borda, adiciona como ITEM decorativo
                    if border_items[y][x] is not None:
                        writer.write_item(x, y, z, border_items[y][x])
                    
                    # DecoraÃ§Ãµes normais (Ã¡rvores, flores, etc)
                    decoration = self.get_decoration(terrain_type, x, y)
                    if decoration:
                        writer.write_item(x, y, z, decoration)

                    # Live preview
                    if self.live_preview and self.tile_callback:
                        self.tile_callback(x, y, z, terrain_type)

                    processed += 1
                    if self.progress_callback and processed % 500 == 0:
                        progress = int((processed / total_tiles) * 100)
                        self.progress_callback(progress)

            writer.finalize()
            
            if self.progress_callback:
                self.progress_callback(100)
            
            return f"Mapa gerado com sucesso: {self.output_path} (seed: {self.seed})"
        
        except Exception as e:
            import traceback
            return f"Erro ao gerar mapa: {str(e)}\n{traceback.format_exc()}"

    def get_decoration(self, terrain_type, x, y):

        random.seed(self.seed + x * 1000 + y)

        if terrain_type == 'grass':
            if random.random() < 0.02:
                return random.choice(self.TREE_IDS)
            elif random.random() < 0.02:
                return random.choice(self.BUSH_IDS)
            elif random.random() < 0.05:
                return random.choice(self.FLOWER_IDS)
            elif random.random() < 0.01:
                return random.choice(self.ROCK_IDS)

        return None

    def get_terrain_from_noise(self, noise, z):

        if z == 7:
            if noise < -0.3:
                return 'water', self.terrain_ids['water']
            elif noise < -0.1:
                return 'sand', self.terrain_ids['sand']
            elif noise < 0.3:
                return 'grass', self.terrain_ids['grass']
            elif noise < 0:
                return 'dirt', self.terrain_ids['dirt']
            else:
                return 'mountain', self.terrain_ids['mountain']

        return 'grass', self.terrain_ids['grass']
