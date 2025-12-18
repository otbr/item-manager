class BorderSystem:

    BASE_TERRAIN_IDS = {
        'water': 4608,
        'sand': 231,
        'grass': 4526,
        'dirt': 103,
        'mountain': 919,
    }

    BORDER_OFFSETS = {
        # mountain_grass borders
        4469: {'x': 0, 'y': -1},   # n - move 1 sqm pra cima
        4471: {'x': 0, 'y': 1},    # s - move 1 sqm pra baixo
        4468: {'x': -1, 'y': 0},   # w - move 1 sqm pra esquerda
        4477: {'x': 1, 'y': 0},    # ne - move 1 sqm pra direita
        4478: {'x': 0, 'y': 1},    # sw - move 1 sqm pra baixo
        4472: {'x': 1, 'y': 0},     # sw - move 1 sqm pra direita
        4479: {'x': -1, 'y': 0},     # sw - move 1 sqm pra direita
        100: {'x': -3, 'y': 3},     # sw - move 1 sqm pra direita

    }

    BORDER_MAPPING = {
        'sand_water': {
            'full': 231,
            'n': 4632,
            's': 4634,
            'w': 4633,
            'e': 4635,
            'nw': 4639,
            'ne': 4638,
            'sw': 4637,
            'se': 4636,
            'cnw': 4643,
            'cne': 4642,
            'csw': 4641,
            'cse': 4640
        },
        'sand_grass': {
            'full': 231,
            'n': 4542,
            's': 4544,
            'w': 4545,
            'e': 4543,
            'nw': 4550,
            'ne': 4551,
            'sw': 4552,
            'se': 4553,
            'cnw': 4546,
            'cne': 4547,
            'csw': 4548,
            'cse': 4549,
        },
        
        'mountain_grass': {
            'full': 919,
            'n': 874,   #ok
            'n': 4469,   #ok
            's': 4471,   #ok
            'w': 4468,   #ok
            'e': 4472,   #ok
            'nw': 4479,  #ok          
            'ne': 4477,   #ok
            'sw': 4478,   #ok
            'se': 877,    #ok
            # 'cnw': 100,
            # 'cne': 100,
            # 'csw': 100,            
            # 'cse': 100


       
            
        },
    }

    @staticmethod
    def get_neighbors(terrain_map, x, y):
        """Retorna os vizinhos de um tile (4 direções + 4 diagonais)"""
        height = len(terrain_map)
        width = len(terrain_map[0])
        neighbors = {}

        neighbors['n'] = terrain_map[y-1][x] if y > 0 else None
        neighbors['s'] = terrain_map[y+1][x] if y < height-1 else None
        neighbors['w'] = terrain_map[y][x-1] if x > 0 else None
        neighbors['e'] = terrain_map[y][x+1] if x < width-1 else None

        neighbors['nw'] = terrain_map[y-1][x-1] if (y > 0 and x > 0) else None
        neighbors['ne'] = terrain_map[y-1][x+1] if (y > 0 and x < width-1) else None
        neighbors['sw'] = terrain_map[y+1][x-1] if (y < height-1 and x > 0) else None
        neighbors['se'] = terrain_map[y+1][x+1] if (y < height-1 and x < width-1) else None

        return neighbors

    @staticmethod
    def get_border_mask(current_terrain, neighbors, target_terrain):
        mask_parts = []

        for direction in ['n', 's', 'w', 'e']:
            neighbor = neighbors.get(direction)
            if neighbor == target_terrain:
                mask_parts.append(direction)

        if mask_parts:
            joined = '_'.join(sorted(mask_parts, key=lambda d: ['n', 's', 'e', 'w'].index(d)))
            if joined == 'n_w':
                return 'nw'
            elif joined == 'n_e':
                return 'ne'
            elif joined == 's_w':
                return 'sw'
            elif joined == 's_e':
                return 'se'
            else:
                return joined

        if (neighbors.get('n') == current_terrain and
            neighbors.get('w') == current_terrain and
            neighbors.get('nw') == target_terrain):
            return 'cnw'

        if (neighbors.get('n') == current_terrain and
            neighbors.get('e') == current_terrain and
            neighbors.get('ne') == target_terrain):
            return 'cne'

        if (neighbors.get('s') == current_terrain and
            neighbors.get('w') == current_terrain and
            neighbors.get('sw') == target_terrain):
            return 'csw'

        if (neighbors.get('s') == current_terrain and
            neighbors.get('e') == current_terrain and
            neighbors.get('se') == target_terrain):
            return 'cse'

        for direction in ['nw', 'ne', 'sw', 'se']:
            neighbor = neighbors.get(direction)
            if neighbor == target_terrain:
                return direction

        return 'full'

    @classmethod
    def apply_borders(cls, terrain_map, ground_ids, default_terrain_ids):
        height = len(terrain_map)
        width = len(terrain_map[0])
        border_items = [[None for _ in range(width)] for _ in range(height)]

        TERRAIN_PRIORITY = {
            'water': 1,
            'sand': 2,
            'grass': 3,
            'dirt': 4,
            'mountain': 5
        }

        for y in range(height):
            for x in range(width):
                current_terrain = terrain_map[y][x]
                neighbors = cls.get_neighbors(terrain_map, x, y)

                if ground_ids[y][x] is None or ground_ids[y][x] == 0:
                    ground_ids[y][x] = default_terrain_ids.get(
                        current_terrain,
                        cls.BASE_TERRAIN_IDS.get(current_terrain, 0)
                    )

                neighbor_terrains = set(n for n in neighbors.values() if n and n != current_terrain)
                sorted_neighbors = sorted(
                    neighbor_terrains,
                    key=lambda t: TERRAIN_PRIORITY.get(t, 999)
                )

                for target_terrain in sorted_neighbors:
                    border_key = f"{current_terrain}_{target_terrain}"
                    if border_key not in cls.BORDER_MAPPING:
                        continue

                    mask = cls.get_border_mask(current_terrain, neighbors, target_terrain)
                    border_map = cls.BORDER_MAPPING[border_key]
                    border_id = border_map.get(mask)

                    if border_id and border_id != cls.BASE_TERRAIN_IDS.get(current_terrain):
                        # Aplica offset se existir para este border_id
                        offset = cls.BORDER_OFFSETS.get(border_id, {'x': 0, 'y': 0})
                        target_x = x + offset['x']
                        target_y = y + offset['y']

                        # Verifica se a posição alvo está dentro dos limites
                        if 0 <= target_x < width and 0 <= target_y < height:
                            border_items[target_y][target_x] = border_id

                        break

        return border_items

    @classmethod
    def add_custom_border(cls, from_terrain, to_terrain, border_ids):
        border_key = f"{from_terrain}_{to_terrain}"
        cls.BORDER_MAPPING[border_key] = border_ids

    @classmethod
    def add_border_offset(cls, border_id, x_offset, y_offset):
        """Adiciona ou atualiza o offset de um border ID específico"""
        cls.BORDER_OFFSETS[border_id] = {'x': x_offset, 'y': y_offset}
