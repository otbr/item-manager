import struct

# Constantes OTB
NODE_START = 0xFE
NODE_END   = 0xFF
ESCAPE     = 0xFD

# Tipos de Atributos (Baseado no TFS)
ATTR_SERVERID    = 0x10 # As vezes muda dependendo da versão, mas o padrão OTB usa mapeamento
ATTR_CLIENTID    = 0x11
ATTR_NAME        = 0x12
ATTR_DESCR       = 0x13
ATTR_SPEED       = 0x14
ATTR_SLOT        = 0x15
ATTR_MAXITEMS    = 0x16
ATTR_WEIGHT      = 0x17
ATTR_WEAPON      = 0x18
ATTR_AMMU        = 0x19
ATTR_ARMOR       = 0x1A
ATTR_MAGLEVEL    = 0x1B
ATTR_MAGFIELD    = 0x1C
ATTR_WRITEABLE   = 0x1D
ATTR_ROTATABLE   = 0x1E
ATTR_CAPACITY    = 0x1F
ATTR_DECAY       = 0x20
ATTR_SPRITEHASH  = 0x21
ATTR_MINIMAPCOLOR= 0x22
ATTR_07          = 0x23
ATTR_08          = 0x24
ATTR_LIGHT       = 0x25

# Tipos usados no seu código original (mapeamento direto por byte lido)
class OtbItem:
    def __init__(self):
        self.type_id = 0
        self.server_id = 0
        self.client_id = 0
        self.flags = 0
        self.speed = 0
        self.light_level = 0
        self.light_color = 0
        self.attribs = b""  
        self.children = []

class OtbFile:
    def __init__(self):
        self.root_children = []
        self.version_data = b""

    def load(self, path):
        with open(path, "rb") as f:
            data = f.read()

        if len(data) < 4:
            raise ValueError("Arquivo muito pequeno para ser um OTB.")

        self.version_data = data[:4]
        pos = 4
        
        self.root_children = []

        while pos < len(data) and data[pos] != NODE_START:
            pos += 1
        
        if pos >= len(data):
            raise ValueError("Nenhum nó raiz (0xFE) encontrado no OTB.")

        # Parse recursivo a partir da Raiz
        self.root_children, _ = self._parse_node_contents(data, pos)

    def _parse_node_contents(self, data, pos):
        """
        Lê um nó a partir do byte NODE_START (0xFE) atual.
        Retorna (lista_de_filhos, nova_posicao).
        Para a raiz, retorna os grupos/itens.
        """
        # Validação inicial
        if pos >= len(data) or data[pos] != NODE_START:
            return [], pos

        pos += 1 # Consome 0xFE
        
        if pos >= len(data): return [], pos

        # Tipo do Nó (1 byte)
        node_type = data[pos]
        pos += 1

        current_node = OtbItem()
        current_node.type_id = node_type

        children = []

        while pos < len(data):
            val = data[pos]

            if val == NODE_END: # 0xFF
                pos += 1

                current_node.children = children
                return [current_node], pos

            elif val == NODE_START: # 0xFE (Filho)
                sub_children, new_pos = self._parse_node_contents(data, pos)

                children.extend(sub_children)
                pos = new_pos
            
            else:

                attr_type = val
                pos += 1
                

                if pos + 2 > len(data):

                    break
                
                size = struct.unpack("<H", data[pos:pos+2])[0]
                pos += 2
                
                if pos + size > len(data):
                    # Fim inesperado no meio dos dados
                    break
                
                payload = data[pos:pos+size]
                pos += size
                
                self._parse_single_attribute(current_node, attr_type, payload)

        return [current_node], pos

    def _parse_single_attribute(self, item, attr_type, payload):
        """Decodifica payload de atributos conhecidos ou salva no blob."""
        try:
            # Mapeamento baseado na ordem comum do OTB (TFS)
            # Server ID (TypeID) = 16 (0x10)
            if attr_type == 0x10 and len(payload) >= 2:
                item.server_id = struct.unpack("<H", payload)[0]
                
            # Client ID (SpriteID) = 17 (0x11)
            elif attr_type == 0x11 and len(payload) >= 2:
                item.client_id = struct.unpack("<H", payload)[0]
            
            # Speed = 20 (0x14)
            elif attr_type == 0x14 and len(payload) >= 2:
                item.speed = struct.unpack("<H", payload)[0]
            
            # Light = 37 (0x25)
            elif attr_type == 0x25 and len(payload) >= 4:
                 item.light_level = payload[0]
                 item.light_color = payload[1]
                 
            item.attribs += bytes([attr_type]) + struct.pack("<H", len(payload)) + payload
            
        except Exception:
            pass

    def get_all_items(self):
        """Retorna lista plana de todos os itens encontrados na árvore recursiva."""
        items = []
        
        def traverse(nodes):
            for node in nodes:
                if node.server_id > 0 or node.client_id > 0:
                    items.append(node)
                traverse(node.children)
        
        traverse(self.root_children)
        return items

    def save(self, path):
        output = self.version_data
        
        def write_node(node):
            res = b""
            res += b"\xFE" # Start
            res += bytes([node.type_id]) # Type
            
            
            current_attribs = node.attribs
            p = 0
            final_attribs = b""
            
            updated_types = set()
            
            while p < len(current_attribs):
                atype = current_attribs[p]
                p += 1
                asize = struct.unpack("<H", current_attribs[p:p+2])[0]
                p += 2
                adata = current_attribs[p:p+asize]
                p += asize
                
                # Substituição
                if atype == 0x11: # Client ID (Update)
                    final_attribs += bytes([atype]) + struct.pack("<H", 2) + struct.pack("<H", node.client_id)
                    updated_types.add(atype)
                elif atype == 0x14: # Speed
                    final_attribs += bytes([atype]) + struct.pack("<H", 2) + struct.pack("<H", node.speed)
                    updated_types.add(atype)
                elif atype == 0x25: # Light
                    final_attribs += bytes([atype]) + struct.pack("<H", 4) + struct.pack("<H", node.light_level) + struct.pack("<H", node.light_color)
                    updated_types.add(atype)
                else:
                    # Mantém original
                    final_attribs += bytes([atype]) + struct.pack("<H", asize) + adata
           
            
            res += final_attribs
            
            # Escreve Filhos
            for child in node.children:
                res += write_node(child)
                
            res += b"\xFF" # End
            return res

        for root in self.root_children:
            output += write_node(root)

        with open(path, "wb") as f:
            f.write(output)

