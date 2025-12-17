# monster_generator.py
import xml.etree.ElementTree as ET
from xml.dom import minidom
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QSpinBox, QPushButton, QTextEdit, QWidget, QGridLayout,
    QComboBox, QCheckBox, QLineEdit, QTabWidget, QScrollArea,
    QMessageBox, QFileDialog, QListWidget, QFormLayout  
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PIL import Image
import struct
import os
import glob


def prettify_xml(elem):
    rough_string = ET.tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="\t")
    lines = pretty_xml.split('\n')
    lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    lines = [line for line in lines if line.strip()]
    return '\n'.join(lines)

class MonsterLoader:
    @staticmethod
    def load_monsters_from_xml(xml_path):
        monsters = []
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            for monster in root.findall('monster'):
                name = monster.get('name', '')
                file_path = monster.get('file', '')
                if name and file_path:
                    monsters.append({'name': name, 'file': file_path})
            print(f"✓ Loaded {len(monsters)} monsters from {xml_path}")
            return monsters
        except Exception as e:
            print(f"⚠ Error loading {xml_path}: {e}")
            return []

    @staticmethod
    def load_monsters_from_folder(folder_path):
        monsters = []
        try:
            xml_files = glob.glob(os.path.join(folder_path, '*.xml'))
            for xml_file in sorted(xml_files):
                filename = os.path.basename(xml_file)
                name = filename.replace('.xml', '').replace('_', ' ').title()
                monsters.append({'name': name, 'file': xml_file})
            print(f"✓ Loaded {len(monsters)} monsters from folder {folder_path}")
            return monsters
        except Exception as e:
            print(f"⚠ Error loading from folder {folder_path}: {e}")
            return []
            
            
            
class EditAttackDialog(QDialog):

    def __init__(self, attack_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Attack")
        self.setModal(True)
        self.resize(500, 450)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_combo = QComboBox()
        attack_types = ['melee', 'physical', 'fire', 'energy', 'earth', 'ice', 
                       'holy', 'death', 'lifedrain', 'manadrain', 'speed', 
                       'firefield', 'poisonfield', 'energyfield', 'custom']
        self.name_combo.addItems(attack_types)
        self.name_combo.setEditable(True)
        form.addRow("Attack Name:", self.name_combo)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(0, 999999)
        self.interval_spin.setValue(2000)
        self.interval_spin.setSuffix(" ms")
        form.addRow("Interval:", self.interval_spin)

        self.chance_spin = QSpinBox()
        self.chance_spin.setRange(0, 100)
        self.chance_spin.setValue(10)
        self.chance_spin.setSuffix(" %")
        form.addRow("Chance:", self.chance_spin)

        self.min_spin = QSpinBox()
        self.min_spin.setRange(-999999, 999999)
        self.min_spin.setValue(-100)
        form.addRow("Min Damage:", self.min_spin)

        self.max_spin = QSpinBox()
        self.max_spin.setRange(-999999, 999999)
        self.max_spin.setValue(-250)
        form.addRow("Max Damage:", self.max_spin)

        self.range_spin = QSpinBox()
        self.range_spin.setRange(0, 10)
        self.range_spin.setValue(7)
        form.addRow("Range:", self.range_spin)

        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(0, 10)
        self.radius_spin.setValue(0)
        form.addRow("Radius (0=none):", self.radius_spin)

        self.target_spin = QSpinBox()
        self.target_spin.setRange(0, 10)
        self.target_spin.setValue(0)
        form.addRow("Target (0=none):", self.target_spin)

        layout.addLayout(form)

        attr_layout = QFormLayout()
        self.shoot_effect = QLineEdit()
        self.shoot_effect.setPlaceholderText("e.g. fire, energy")
        attr_layout.addRow("Shoot Effect:", self.shoot_effect)

        self.area_effect = QLineEdit()
        self.area_effect.setPlaceholderText("e.g. firearea, energyarea")
        attr_layout.addRow("Area Effect:", self.area_effect)

        layout.addLayout(attr_layout)

        if attack_data:
            self.load_data(attack_data)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def load_data(self, data):
        self.name_combo.setCurrentText(data.get('name', 'melee'))
        self.interval_spin.setValue(data.get('interval', 2000))
        self.chance_spin.setValue(data.get('chance', 10))
        self.min_spin.setValue(data.get('min', -100))
        self.max_spin.setValue(data.get('max', -250))
        self.range_spin.setValue(data.get('range', 7))
        self.radius_spin.setValue(data.get('radius', 0))
        self.target_spin.setValue(data.get('target', 0))

        attrs = data.get('attributes', {})
        self.shoot_effect.setText(attrs.get('shootEffect', ''))
        self.area_effect.setText(attrs.get('areaEffect', ''))

    def get_data(self):
        data = {
            'name': self.name_combo.currentText(),
            'interval': self.interval_spin.value(),
            'chance': self.chance_spin.value(),
            'min': self.min_spin.value(),
            'max': self.max_spin.value(),
            'range': self.range_spin.value(),
            'attributes': {}
        }

        if self.radius_spin.value() > 0:
            data['radius'] = self.radius_spin.value()
        if self.target_spin.value() > 0:
            data['target'] = self.target_spin.value()

        if self.shoot_effect.text():
            data['attributes']['shootEffect'] = self.shoot_effect.text()
        if self.area_effect.text():
            data['attributes']['areaEffect'] = self.area_effect.text()

        return data


class EditDefenseDialog(QDialog):

    def __init__(self, defense_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Defense")
        self.setModal(True)
        self.resize(450, 350)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_combo = QComboBox()
        defense_types = ['healing', 'speed', 'invisible', 'outfit', 'custom']
        self.name_combo.addItems(defense_types)
        self.name_combo.setEditable(True)
        form.addRow("Defense Name:", self.name_combo)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(0, 999999)
        self.interval_spin.setValue(2000)
        self.interval_spin.setSuffix(" ms")
        form.addRow("Interval:", self.interval_spin)

        self.chance_spin = QSpinBox()
        self.chance_spin.setRange(0, 100)
        self.chance_spin.setValue(15)
        self.chance_spin.setSuffix(" %")
        form.addRow("Chance:", self.chance_spin)

        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 999999)
        self.min_spin.setValue(80)
        form.addRow("Min (healing):", self.min_spin)

        self.max_spin = QSpinBox()
        self.max_spin.setRange(0, 999999)
        self.max_spin.setValue(250)
        form.addRow("Max (healing):", self.max_spin)

        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(-1000, 1000)
        self.speed_spin.setValue(0)
        form.addRow("Speed Change:", self.speed_spin)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(0, 999999)
        self.duration_spin.setValue(5000)
        self.duration_spin.setSuffix(" ms")
        form.addRow("Duration:", self.duration_spin)

        layout.addLayout(form)

        attr_layout = QFormLayout()
        self.area_effect = QLineEdit()
        self.area_effect.setPlaceholderText("e.g. blueshimmer, redshimmer")
        attr_layout.addRow("Area Effect:", self.area_effect)
        layout.addLayout(attr_layout)

        if defense_data:
            self.load_data(defense_data)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def load_data(self, data):
        self.name_combo.setCurrentText(data.get('name', 'healing'))
        self.interval_spin.setValue(data.get('interval', 2000))
        self.chance_spin.setValue(data.get('chance', 15))
        self.min_spin.setValue(data.get('min', 80))
        self.max_spin.setValue(data.get('max', 250))
        self.speed_spin.setValue(data.get('speedchange', 0))
        self.duration_spin.setValue(data.get('duration', 5000))

        attrs = data.get('attributes', {})
        self.area_effect.setText(attrs.get('areaEffect', ''))

    def get_data(self):
        data = {
            'name': self.name_combo.currentText(),
            'interval': self.interval_spin.value(),
            'chance': self.chance_spin.value(),
            'attributes': {}
        }

        if self.min_spin.value() > 0:
            data['min'] = self.min_spin.value()
        if self.max_spin.value() > 0:
            data['max'] = self.max_spin.value()
        if self.speed_spin.value() != 0:
            data['speedchange'] = self.speed_spin.value()
        if self.duration_spin.value() > 0:
            data['duration'] = self.duration_spin.value()

        if self.area_effect.text():
            data['attributes']['areaEffect'] = self.area_effect.text()

        return data


class EditSummonDialog(QDialog):

    def __init__(self, summon_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Summon")
        self.setModal(True)
        self.resize(400, 200)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Monster name")
        form.addRow("Name:", self.name_edit)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(0, 999999)
        self.interval_spin.setValue(2000)
        self.interval_spin.setSuffix(" ms")
        form.addRow("Interval:", self.interval_spin)

        self.chance_spin = QSpinBox()
        self.chance_spin.setRange(0, 100)
        self.chance_spin.setValue(10)
        self.chance_spin.setSuffix(" %")
        form.addRow("Chance:", self.chance_spin)

        layout.addLayout(form)

        if summon_data:
            self.load_data(summon_data)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def load_data(self, data):
        self.name_edit.setText(data.get('name', ''))
        self.interval_spin.setValue(data.get('interval', 2000))
        self.chance_spin.setValue(data.get('chance', 10))

    def get_data(self):
        return {
            'name': self.name_edit.text(),
            'interval': self.interval_spin.value(),
            'chance': self.chance_spin.value()
        }


class EditLootDialog(QDialog):

    def __init__(self, loot_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Loot")
        self.setModal(True)
        self.resize(400, 250)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.use_id = QCheckBox("Use Item ID instead of Name")
        layout.addWidget(self.use_id)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Item name")
        form.addRow("Name:", self.name_edit)

        self.id_spin = QSpinBox()
        self.id_spin.setRange(0, 99999)
        self.id_spin.setValue(0)
        self.id_spin.setEnabled(False)
        form.addRow("ID:", self.id_spin)

        self.use_id.stateChanged.connect(lambda: self.toggle_id_name())

        self.chance_spin = QSpinBox()
        self.chance_spin.setRange(0, 100000)
        self.chance_spin.setValue(10000)
        form.addRow("Chance (0-100000):", self.chance_spin)

        self.countmax_spin = QSpinBox()
        self.countmax_spin.setRange(1, 100)
        self.countmax_spin.setValue(1)
        form.addRow("Count Max:", self.countmax_spin)

        layout.addLayout(form)

        if loot_data:
            self.load_data(loot_data)

        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def toggle_id_name(self):
        use_id = self.use_id.isChecked()
        self.id_spin.setEnabled(use_id)
        self.name_edit.setEnabled(not use_id)

    def load_data(self, data):
        if 'id' in data:
            self.use_id.setChecked(True)
            self.id_spin.setValue(data['id'])
        else:
            self.name_edit.setText(data.get('name', ''))
        self.chance_spin.setValue(data.get('chance', 10000))
        self.countmax_spin.setValue(data.get('countmax', 1))

    def get_data(self):
        data = {
            'chance': self.chance_spin.value(),
            'countmax': self.countmax_spin.value()
        }

        if self.use_id.isChecked():
            data['id'] = self.id_spin.value()
        else:
            data['name'] = self.name_edit.text()

        return data            
            
class MonsterGeneratorWindow(QDialog):


    def __init__(self, spr_editor=None, dat_editor=None, parent=None):
        super().__init__(parent)
        self.spr_editor = spr_editor
        self.dat_editor = dat_editor
        self.current_direction = 2

        self.setWindowTitle("Monster Generator")
        self.setModal(False)
        self.resize(850, 750)


        self.monsters_list = []
        self.current_monster_file = None


        self.monster_data = {
            'name': 'Demon',
            'namedescription': 'a demon',
            'race': 'blood',
            'experience': 6000,
            'speed': 280,
            'manacost': 300,
            'skull': 'none',

            # Health
            'health_now': 8200,
            'health_max': 8200,

            # Look
            'looktype': 35,
            'head': 0,
            'body': 0,
            'legs': 0,
            'feet': 0,
            'addons': 0,
            'mount': 0,
            'corpse': 6068,

            # Target
            'targetchange_interval': 4000,
            'targetchange_chance': 10,

            # Combat
            'armor': 55,
            'defense': 55,

            # Flags
            'summonable': False,
            'attackable': True,
            'hostile': True,
            'illusionable': False,
            'convinceable': False,
            'pushable': False,
            'canpushitems': True,
            'canpushcreatures': True,
            'targetdistance': 1,
            'staticattack': 90,
            'hidehealth': False,
            'runonhealth': 300,

            # Light
            'lightcolor': 0,
            'lightlevel': 0,

            # Elements
            'physical': 30,
            'holy': 30,
            'death': -10,
            'fire': 50,
            'energy': 20,
            'ice': 20,
            'earth': 40,
            'lifedrain': 0,
            'drown': 100,

            # Immunities
            'immune_physical': False,
            'immune_holy': False,
            'immune_death': False,
            'immune_fire': False,
            'immune_energy': False,
            'immune_ice': False,
            'immune_earth': False,
            'immune_lifedrain': False,
            'immune_drown': False,
            'immune_paralyze': False,
            'immune_drunk': False,
            'immune_invisible': True,
            'immune_outfit': False,
        }
        
        self.attacks_list = []
        self.defenses_list = []
        self.summons_list = []
        self.voices_list = []
        self.loot_list = []        

        self.setup_ui()
        self.auto_load_monsters()
        self.update_xml()
        
    def edit_attack(self):

        row = self.attacks_listwidget.currentRow()
        if row >= 0 and row < len(self.attacks_list):
            attack_data = self.attacks_list[row]
            dialog = EditAttackDialog(attack_data=attack_data, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.attacks_list[row] = dialog.get_data()
                self.update_attacks_list()
                self.update_xml()

    def edit_defense(self):

        row = self.defenses_listwidget.currentRow()
        if row >= 0 and row < len(self.defenses_list):
            defense_data = self.defenses_list[row]
            dialog = EditDefenseDialog(defense_data=defense_data, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.defenses_list[row] = dialog.get_data()
                self.update_defenses_list()
                self.update_xml()

    def edit_summon(self):

        row = self.summons_listwidget.currentRow()
        if row >= 0 and row < len(self.summons_list):
            summon_data = self.summons_list[row]
            dialog = EditSummonDialog(summon_data=summon_data, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.summons_list[row] = dialog.get_data()
                self.update_summons_list()
                self.update_xml()

    def edit_loot(self):
       
        row = self.loot_listwidget.currentRow()
        if row >= 0 and row < len(self.loot_list):
            loot_data = self.loot_list[row]
            dialog = EditLootDialog(loot_data=loot_data, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.loot_list[row] = dialog.get_data()
                self.update_loot_list()
                self.update_xml()        

    def auto_load_monsters(self):

        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(current_dir)
        assets_dir = os.path.join(base_dir, 'assets', 'xml')  
        
       
        monsters_xml_path = os.path.join(assets_dir, 'monsters.xml')
        if os.path.exists(monsters_xml_path):
            self.monsters_list = MonsterLoader.load_monsters_from_xml(monsters_xml_path)
            self.monster_xml_label.setText(f"✓ monsters.xml ({len(self.monsters_list)} monsters)")
            self.monster_xml_label.setStyleSheet("color: green;")
        else:
     
            monsters_folder = os.path.join(assets_dir, 'monster')
            if os.path.exists(monsters_folder):
                self.monsters_list = MonsterLoader.load_monsters_from_folder(monsters_folder)
                self.monster_xml_label.setText(f"✓ From folder ({len(self.monsters_list)} monsters)")
                self.monster_xml_label.setStyleSheet("color: orange;")
            else:
                self.monster_xml_label.setText("⚠ No monsters found")
                self.monster_xml_label.setStyleSheet("color: red;")
                return
        
 
        if self.monsters_list and hasattr(self, 'monster_combo'):  
            self.monster_combo.blockSignals(True)  
            self.monster_combo.clear()
            self.monster_combo.addItem("(Create New Monster)", None)
            
            print(f"📋 Adding {len(self.monsters_list)} monsters to combobox...")  
            
            for monster in self.monsters_list:
                self.monster_combo.addItem(monster['name'], monster['file'])
            
            self.monster_combo.blockSignals(False)  
            print(f"✓ ComboBox has {self.monster_combo.count()} items")  

    def setup_ui(self):
        main_layout = QVBoxLayout(self)


        load_group = QGroupBox("Load Monster")
        load_layout = QVBoxLayout()


        status_layout = QHBoxLayout()
        self.monster_xml_label = QLabel("Loading monsters...")
        self.monster_xml_label.setStyleSheet("color: gray;")
        status_layout.addWidget(self.monster_xml_label)

        reload_btn = QPushButton("Reload")
        reload_btn.setMaximumWidth(80)
        reload_btn.clicked.connect(self.auto_load_monsters)
        status_layout.addWidget(reload_btn)

        load_layout.addLayout(status_layout)


        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("Select Monster:"))

        self.monster_combo = QComboBox()
        self.monster_combo.setMinimumWidth(300)
        self.monster_combo.currentIndexChanged.connect(self.on_monster_selected)
        combo_layout.addWidget(self.monster_combo)

        load_monster_btn = QPushButton("Load Selected")
        load_monster_btn.clicked.connect(self.load_selected_monster)
        combo_layout.addWidget(load_monster_btn)

        combo_layout.addStretch()
        load_layout.addLayout(combo_layout)

        load_group.setLayout(load_layout)
        main_layout.addWidget(load_group)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Monster Info
        self.setup_monster_tab()

        # Tab 2: Flags
        self.setup_flags_tab()

        # Tab 3: Combat (Defense/Armor/Elements)
        self.setup_combat_tab()

        # Tab 4: Immunities
        self.setup_immunities_tab()
        
        self.setup_attacks_defenses_tab()
        self.setup_extras_tab()        

        # XML Output
        xml_group = QGroupBox("XML Output")
        xml_layout = QVBoxLayout()

        self.xml_display = QTextEdit()
        self.xml_display.setReadOnly(True)
        self.xml_display.setMinimumHeight(150)
        self.xml_display.setStyleSheet(
            "background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace;"
        )
        xml_layout.addWidget(self.xml_display)
        xml_group.setLayout(xml_layout)
        main_layout.addWidget(xml_group)

   
        button_layout = QHBoxLayout()

        self.copy_btn = QPushButton("Copy XML")
        self.copy_btn.clicked.connect(self.copy_xml)
        button_layout.addWidget(self.copy_btn)

        self.paste_btn = QPushButton("Paste XML")
        self.paste_btn.clicked.connect(self.paste_xml)
        button_layout.addWidget(self.paste_btn)

        self.save_btn = QPushButton("Save XML File")
        self.save_btn.clicked.connect(self.save_xml_file)
        button_layout.addWidget(self.save_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        main_layout.addLayout(button_layout)
        
        
    def add_attack_dialog(self):
   
        from PyQt6.QtWidgets import QInputDialog

        attack_types = ['melee', 'fire', 'energy', 'earth', 'physical', 'lifedrain', 'manadrain']
        name, ok = QInputDialog.getItem(self, "Attack Name", "Select attack type:", attack_types, 0, False)
        if not ok:
            return

        attack = {
            'name': name,
            'interval': 2000,
            'chance': 10 if name != 'melee' else None,
            'min': -100,
            'max': -200,
            'range': 7 if name != 'melee' else None,
            'attributes': {}
        }


        if name in ['fire', 'energy']:
            attack['attributes']['shootEffect'] = name
            attack['attributes']['areaEffect'] = name + 'area'

        self.attacks_list.append(attack)
        self.update_attacks_list()
        self.update_xml()

    def remove_attack(self):
        current = self.attacks_listwidget.currentRow()
        if current >= 0:
            self.attacks_list.pop(current)
            self.update_attacks_list()
            self.update_xml()

    def update_attacks_list(self):
        self.attacks_listwidget.clear()
        for attack in self.attacks_list:
            label = f"{attack['name']} (interval={attack['interval']})"
            if attack.get('chance'):
                label += f", chance={attack['chance']}"
            self.attacks_listwidget.addItem(label)

  
        if self.attacks_list:
            attacks = ET.SubElement(monster, 'attacks')
            for attack in self.attacks_list:
                attack_elem = ET.SubElement(attacks, 'attack')
                attack_elem.set('name', attack['name'])
                attack_elem.set('interval', str(attack['interval']))

                if attack.get('chance') is not None:
                    attack_elem.set('chance', str(attack['chance']))
                if attack.get('min') is not None:
                    attack_elem.set('min', str(attack['min']))
                if attack.get('max') is not None:
                    attack_elem.set('max', str(attack['max']))
                if attack.get('range') is not None:
                    attack_elem.set('range', str(attack['range']))
                if attack.get('radius') is not None:
                    attack_elem.set('radius', str(attack['radius']))
                if attack.get('target') is not None:
                    attack_elem.set('target', str(attack['target']))
                if attack.get('length') is not None:
                    attack_elem.set('length', str(attack['length']))
                if attack.get('spread') is not None:
                    attack_elem.set('spread', str(attack['spread']))
                if attack.get('speedchange') is not None:
                    attack_elem.set('speedchange', str(attack['speedchange']))
                if attack.get('duration') is not None:
                    attack_elem.set('duration', str(attack['duration']))

        
                for key, value in attack.get('attributes', {}).items():
                    attr = ET.SubElement(attack_elem, 'attribute')
                    attr.set('key', key)
                    attr.set('value', value)


        defenses = ET.SubElement(monster, 'defenses')
        defenses.set('armor', str(self.monster_data['armor']))
        defenses.set('defense', str(self.monster_data['defense']))

        for defense in self.defenses_list:
            defense_elem = ET.SubElement(defenses, 'defense')
            defense_elem.set('name', defense['name'])
            defense_elem.set('interval', str(defense['interval']))
            defense_elem.set('chance', str(defense['chance']))

            if defense.get('min') is not None:
                defense_elem.set('min', str(defense['min']))
            if defense.get('max') is not None:
                defense_elem.set('max', str(defense['max']))
            if defense.get('speedchange') is not None:
                defense_elem.set('speedchange', str(defense['speedchange']))
            if defense.get('duration') is not None:
                defense_elem.set('duration', str(defense['duration']))


            for key, value in defense.get('attributes', {}).items():
                attr = ET.SubElement(defense_elem, 'attribute')
                attr.set('key', key)
                attr.set('value', value)


        if self.summons_list:
            summons = ET.SubElement(monster, 'summons')
 
            summons.set('maxSummons', '1')

            for summon in self.summons_list:
                summon_elem = ET.SubElement(summons, 'summon')
                summon_elem.set('name', summon['name'])
                summon_elem.set('interval', str(summon['interval']))
                summon_elem.set('chance', str(summon['chance']))


        if self.voices_list:
            voices = ET.SubElement(monster, 'voices')
            voices.set('interval', '5000')
            voices.set('chance', '10')

            for voice in self.voices_list:
                voice_elem = ET.SubElement(voices, 'voice')
                voice_elem.set('sentence', voice['sentence'])
                if voice.get('yell'):
                    voice_elem.set('yell', '1')


        if self.loot_list:
            loot = ET.SubElement(monster, 'loot')

            for item in self.loot_list:
                item_elem = ET.SubElement(loot, 'item')
                if item.get('id'):
                    item_elem.set('id', str(item['id']))
                else:
                    item_elem.set('name', item['name'])

                if item.get('countmax') and item['countmax'] > 1:
                    item_elem.set('countmax', str(item['countmax']))

                item_elem.set('chance', str(item['chance']))        
        

    def on_monster_selected(self, index):

        if index < 0:
            return

        monster_file = self.monster_combo.currentData()
        if monster_file:
            self.current_monster_file = monster_file

    def load_selected_monster(self):

        if not self.current_monster_file:
            QMessageBox.information(self, "Info", "Select a monster first.")
            return
        

        if not os.path.isabs(self.current_monster_file):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(current_dir)
            assets_dir = os.path.join(base_dir, 'assets', 'xml') 
            full_path = os.path.join(assets_dir, self.current_monster_file)
        else:
            full_path = self.current_monster_file
        
        if not os.path.exists(full_path):
            QMessageBox.warning(self, "Error", f"Monster file not found:\n{full_path}")
            return
        
        try:
            self.load_monster_from_file(full_path)
            QMessageBox.information(self, "Success", f"Monster loaded from:\n{os.path.basename(full_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load monster:\n{e}")

    def load_monster_from_file(self, filepath):

        tree = ET.parse(filepath)
        root = tree.getroot()

        if root.tag != 'monster':
            raise ValueError("Invalid monster XML file")
            
            
            
              # Attacks
        self.attacks_list = []
        attacks = root.find('attacks')
        if attacks is not None:
            for attack in attacks.findall('attack'):
                attack_data = {
                    'name': attack.get('name', ''),
                    'interval': int(attack.get('interval', 2000)),
                    'attributes': {}
                }
                

                for attr in ['chance', 'min', 'max', 'range', 'radius', 'target', 
                            'length', 'spread', 'speedchange', 'duration', 'monster']:
                    if attack.get(attr):
                        attack_data[attr] = int(attack.get(attr)) if attr != 'monster' else attack.get(attr)
                
   
                for attr_elem in attack.findall('attribute'):
                    key = attr_elem.get('key')
                    value = attr_elem.get('value')
                    if key and value:
                        attack_data['attributes'][key] = value
                
                self.attacks_list.append(attack_data)
            
            self.update_attacks_list()
        

        self.defenses_list = []
        defenses = root.find('defenses')
        if defenses is not None:
            for defense in defenses.findall('defense'):
                defense_data = {
                    'name': defense.get('name', ''),
                    'interval': int(defense.get('interval', 2000)),
                    'chance': int(defense.get('chance', 10)),
                    'attributes': {}
                }
                
                for attr in ['min', 'max', 'speedchange', 'duration']:
                    if defense.get(attr):
                        defense_data[attr] = int(defense.get(attr))
                
                for attr_elem in defense.findall('attribute'):
                    key = attr_elem.get('key')
                    value = attr_elem.get('value')
                    if key and value:
                        defense_data['attributes'][key] = value
                
                self.defenses_list.append(defense_data)
            
            self.update_defenses_list()
        

        self.voices_list = []
        voices = root.find('voices')
        if voices is not None:
            for voice in voices.findall('voice'):
                voice_data = {
                    'sentence': voice.get('sentence', ''),
                    'yell': voice.get('yell') == '1'
                }
                self.voices_list.append(voice_data)
            
            self.update_voices_list()

        self.loot_list = []
        loot = root.find('loot')
        if loot is not None:
            for item in loot.findall('item'):
                item_data = {
                    'chance': int(item.get('chance', 10000)),
                    'countmax': int(item.get('countmax', 1)) if item.get('countmax') else 1
                }
                
                if item.get('id'):
                    item_data['id'] = int(item.get('id'))
                if item.get('name'):
                    item_data['name'] = item.get('name')
                
                self.loot_list.append(item_data)
            
            self.update_loot_list()
        

        self.update_xml()


        self.widgets['name'].setText(root.get('name', 'Monster'))
        self.widgets['namedescription'].setText(root.get('nameDescription', 'a monster'))

        race_text = root.get('race', 'blood')
        if self.widgets['race'].findText(race_text) >= 0:
            self.widgets['race'].setCurrentText(race_text)

        self.widgets['experience'].setValue(int(root.get('experience', 100)))
        self.widgets['speed'].setValue(int(root.get('speed', 200)))
        self.widgets['manacost'].setValue(int(root.get('manacost', 0)))

        skull_text = root.get('skull', 'none')
        if self.widgets['skull'].findText(skull_text) >= 0:
            self.widgets['skull'].setCurrentText(skull_text)


        health = root.find('health')
        if health is not None:
            self.widgets['health_now'].setValue(int(health.get('now', 100)))
            self.widgets['health_max'].setValue(int(health.get('max', 100)))


        look = root.find('look')
        if look is not None:
            self.widgets['looktype'].setValue(int(look.get('type', 0)))
            self.widgets['head'].setValue(int(look.get('head', 0)))
            self.widgets['body'].setValue(int(look.get('body', 0)))
            self.widgets['legs'].setValue(int(look.get('legs', 0)))
            self.widgets['feet'].setValue(int(look.get('feet', 0)))
            self.widgets['addons'].setValue(int(look.get('addons', 0)))
            self.widgets['mount'].setValue(int(look.get('mount', 0)))
            self.widgets['corpse'].setValue(int(look.get('corpse', 0)))


        targetchange = root.find('targetchange')
        if targetchange is not None:
            self.widgets['targetchange_interval'].setValue(int(targetchange.get('interval', 4000)))
            self.widgets['targetchange_chance'].setValue(int(targetchange.get('chance', 10)))


 
        flags = root.find('flags')
        if flags is not None:
            for flag in flags.findall('flag'):
                for key, value in flag.attrib.items():
                    if key in self.widgets:
                        if isinstance(self.widgets[key], QCheckBox):
                            self.widgets[key].setChecked(value == '1')
                        elif isinstance(self.widgets[key], QSpinBox):
                            self.widgets[key].setValue(int(value))


        defenses = root.find('defenses')
        if defenses is not None:
            self.widgets['armor'].setValue(int(defenses.get('armor', 0)))
            self.widgets['defense'].setValue(int(defenses.get('defense', 0)))

        elements = root.find('elements')
        if elements is not None:
            for element in elements.findall('element'):
                for key, value in element.attrib.items():
              
                    elem_key = key.replace('Percent', '')
                    if elem_key in self.widgets:
                        self.widgets[elem_key].setValue(int(value))


        immunities = root.find('immunities')
        if immunities is not None:
            for immunity in immunities.findall('immunity'):
                for key, value in immunity.attrib.items():
                    immune_key = f'immune_{key}'
                    if immune_key in self.widgets:
                        self.widgets[immune_key].setChecked(value == '1')

        self.update_xml()

    def setup_monster_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)

        layout = QVBoxLayout(scroll_widget)


        basic_group = QGroupBox("Basic Information")
        basic_layout = QGridLayout()
        row = 0

        self.widgets = {}

        basic_layout.addWidget(QLabel("Name:"), row, 0)
        self.widgets['name'] = QLineEdit('Demon')
        self.widgets['name'].textChanged.connect(self.update_xml)
        basic_layout.addWidget(self.widgets['name'], row, 1)
        row += 1


        basic_layout.addWidget(QLabel("Description:"), row, 0)
        self.widgets['namedescription'] = QLineEdit('a demon')
        self.widgets['namedescription'].textChanged.connect(self.update_xml)
        basic_layout.addWidget(self.widgets['namedescription'], row, 1)
        row += 1


        basic_layout.addWidget(QLabel("Race:"), row, 0)
        self.widgets['race'] = QComboBox()
        races = ['blood', 'venom', 'undead', 'fire', 'energy']
        self.widgets['race'].addItems(races)
        self.widgets['race'].currentTextChanged.connect(self.update_xml)
        basic_layout.addWidget(self.widgets['race'], row, 1)
        row += 1


        basic_layout.addWidget(QLabel("Experience:"), row, 0)
        self.widgets['experience'] = QSpinBox()
        self.widgets['experience'].setRange(0, 999999999)
        self.widgets['experience'].setValue(6000)
        self.widgets['experience'].valueChanged.connect(self.update_xml)
        basic_layout.addWidget(self.widgets['experience'], row, 1)
        row += 1


        basic_layout.addWidget(QLabel("Speed:"), row, 0)
        self.widgets['speed'] = QSpinBox()
        self.widgets['speed'].setRange(0, 9999)
        self.widgets['speed'].setValue(280)
        self.widgets['speed'].valueChanged.connect(self.update_xml)
        basic_layout.addWidget(self.widgets['speed'], row, 1)
        row += 1


        basic_layout.addWidget(QLabel("Mana Cost:"), row, 0)
        self.widgets['manacost'] = QSpinBox()
        self.widgets['manacost'].setRange(0, 99999)
        self.widgets['manacost'].setValue(0)
        self.widgets['manacost'].valueChanged.connect(self.update_xml)
        basic_layout.addWidget(self.widgets['manacost'], row, 1)
        row += 1


        basic_layout.addWidget(QLabel("Skull:"), row, 0)
        self.widgets['skull'] = QComboBox()
        skulls = ['none', 'yellow', 'green', 'white', 'red', 'black', 'orange']
        self.widgets['skull'].addItems(skulls)
        self.widgets['skull'].currentTextChanged.connect(self.update_xml)
        basic_layout.addWidget(self.widgets['skull'], row, 1)
        row += 1

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

    
        health_group = QGroupBox("Health")
        health_layout = QGridLayout()

        health_layout.addWidget(QLabel("Health Now:"), 0, 0)
        self.widgets['health_now'] = QSpinBox()
        self.widgets['health_now'].setRange(1, 999999999)
        self.widgets['health_now'].setValue(8200)
        self.widgets['health_now'].valueChanged.connect(self.update_xml)
        health_layout.addWidget(self.widgets['health_now'], 0, 1)

        health_layout.addWidget(QLabel("Health Max:"), 0, 2)
        self.widgets['health_max'] = QSpinBox()
        self.widgets['health_max'].setRange(1, 999999999)
        self.widgets['health_max'].setValue(8200)
        self.widgets['health_max'].valueChanged.connect(self.update_xml)
        health_layout.addWidget(self.widgets['health_max'], 0, 3)

        health_group.setLayout(health_layout)
        layout.addWidget(health_group)


        look_group = QGroupBox("Look")
        look_layout = QGridLayout()
        row = 0

        look_layout.addWidget(QLabel("LookType:"), row, 0)
        self.widgets['looktype'] = QSpinBox()
        self.widgets['looktype'].setRange(0, 9999)
        self.widgets['looktype'].setValue(35)
        self.widgets['looktype'].valueChanged.connect(self.update_xml)
        look_layout.addWidget(self.widgets['looktype'], row, 1)

        look_layout.addWidget(QLabel("Corpse:"), row, 2)
        self.widgets['corpse'] = QSpinBox()
        self.widgets['corpse'].setRange(0, 99999)
        self.widgets['corpse'].setValue(6068)
        self.widgets['corpse'].valueChanged.connect(self.update_xml)
        look_layout.addWidget(self.widgets['corpse'], row, 3)
        row += 1

        # Colors
        for i, color in enumerate(['head', 'body', 'legs', 'feet']):
            col = i * 2
            look_layout.addWidget(QLabel(f"{color.capitalize()}:"), row, col)
            self.widgets[color] = QSpinBox()
            self.widgets[color].setRange(0, 132)
            self.widgets[color].setValue(0)
            self.widgets[color].valueChanged.connect(self.update_xml)
            look_layout.addWidget(self.widgets[color], row, col + 1)
        row += 1

        look_layout.addWidget(QLabel("Addons:"), row, 0)
        self.widgets['addons'] = QSpinBox()
        self.widgets['addons'].setRange(0, 3)
        self.widgets['addons'].setValue(0)
        self.widgets['addons'].valueChanged.connect(self.update_xml)
        look_layout.addWidget(self.widgets['addons'], row, 1)

        look_layout.addWidget(QLabel("Mount:"), row, 2)
        self.widgets['mount'] = QSpinBox()
        self.widgets['mount'].setRange(0, 9999)
        self.widgets['mount'].setValue(0)
        self.widgets['mount'].valueChanged.connect(self.update_xml)
        look_layout.addWidget(self.widgets['mount'], row, 3)

        look_group.setLayout(look_layout)
        layout.addWidget(look_group)


        target_group = QGroupBox("Target Change")
        target_layout = QGridLayout()

        target_layout.addWidget(QLabel("Interval (ms):"), 0, 0)
        self.widgets['targetchange_interval'] = QSpinBox()
        self.widgets['targetchange_interval'].setRange(0, 999999)
        self.widgets['targetchange_interval'].setValue(4000)
        self.widgets['targetchange_interval'].valueChanged.connect(self.update_xml)
        target_layout.addWidget(self.widgets['targetchange_interval'], 0, 1)

        target_layout.addWidget(QLabel("Chance (%):"), 0, 2)
        self.widgets['targetchange_chance'] = QSpinBox()
        self.widgets['targetchange_chance'].setRange(0, 100)
        self.widgets['targetchange_chance'].setValue(10)
        self.widgets['targetchange_chance'].valueChanged.connect(self.update_xml)
        target_layout.addWidget(self.widgets['targetchange_chance'], 0, 3)

        target_group.setLayout(target_layout)
        layout.addWidget(target_group)


        layout.addStretch()
        self.tabs.addTab(scroll, "Monster")

    def setup_flags_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)

        layout = QVBoxLayout(scroll_widget)

        # Flags
        flags_group = QGroupBox("Flags")
        flags_layout = QGridLayout()

        bool_flags = [
            ('summonable', 'Summonable'),
            ('attackable', 'Attackable'),
            ('hostile', 'Hostile'),
            ('illusionable', 'Illusionable'),
            ('convinceable', 'Convinceable'),
            ('pushable', 'Pushable'),
            ('canpushitems', 'Can Push Items'),
            ('canpushcreatures', 'Can Push Creatures'),
            ('hidehealth', 'Hide Health'),
        ]

        row = 0
        col = 0
        for key, label in bool_flags:
            self.widgets[key] = QCheckBox(label)
            if key in ['attackable', 'hostile', 'canpushitems', 'canpushcreatures']:
                self.widgets[key].setChecked(True)
            self.widgets[key].stateChanged.connect(self.update_xml)
            flags_layout.addWidget(self.widgets[key], row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        flags_group.setLayout(flags_layout)
        layout.addWidget(flags_group)

        # Flags
        numeric_group = QGroupBox("Numeric Values")
        numeric_layout = QGridLayout()

        numeric_layout.addWidget(QLabel("Target Distance:"), 0, 0)
        self.widgets['targetdistance'] = QSpinBox()
        self.widgets['targetdistance'].setRange(0, 10)
        self.widgets['targetdistance'].setValue(1)
        self.widgets['targetdistance'].valueChanged.connect(self.update_xml)
        numeric_layout.addWidget(self.widgets['targetdistance'], 0, 1)

        numeric_layout.addWidget(QLabel("Static Attack (%):"), 0, 2)
        self.widgets['staticattack'] = QSpinBox()
        self.widgets['staticattack'].setRange(0, 100)
        self.widgets['staticattack'].setValue(90)
        self.widgets['staticattack'].valueChanged.connect(self.update_xml)
        numeric_layout.addWidget(self.widgets['staticattack'], 0, 3)

        numeric_layout.addWidget(QLabel("Run On Health:"), 1, 0)
        self.widgets['runonhealth'] = QSpinBox()
        self.widgets['runonhealth'].setRange(0, 999999)
        self.widgets['runonhealth'].setValue(300)
        self.widgets['runonhealth'].valueChanged.connect(self.update_xml)
        numeric_layout.addWidget(self.widgets['runonhealth'], 1, 1)

        numeric_layout.addWidget(QLabel("Light Color:"), 1, 2)
        self.widgets['lightcolor'] = QSpinBox()
        self.widgets['lightcolor'].setRange(0, 255)
        self.widgets['lightcolor'].setValue(0)
        self.widgets['lightcolor'].valueChanged.connect(self.update_xml)
        numeric_layout.addWidget(self.widgets['lightcolor'], 1, 3)

        numeric_layout.addWidget(QLabel("Light Level:"), 2, 0)
        self.widgets['lightlevel'] = QSpinBox()
        self.widgets['lightlevel'].setRange(0, 255)
        self.widgets['lightlevel'].setValue(0)
        self.widgets['lightlevel'].valueChanged.connect(self.update_xml)
        numeric_layout.addWidget(self.widgets['lightlevel'], 2, 1)

        numeric_group.setLayout(numeric_layout)
        layout.addWidget(numeric_group)

        layout.addStretch()
        self.tabs.addTab(scroll, "Flags")

    def setup_combat_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)

        layout = QVBoxLayout(scroll_widget)


        defense_group = QGroupBox("Defense")
        defense_layout = QGridLayout()

        defense_layout.addWidget(QLabel("Armor:"), 0, 0)
        self.widgets['armor'] = QSpinBox()
        self.widgets['armor'].setRange(0, 999)
        self.widgets['armor'].setValue(55)
        self.widgets['armor'].valueChanged.connect(self.update_xml)
        defense_layout.addWidget(self.widgets['armor'], 0, 1)

        defense_layout.addWidget(QLabel("Defense:"), 0, 2)
        self.widgets['defense'] = QSpinBox()
        self.widgets['defense'].setRange(0, 999)
        self.widgets['defense'].setValue(55)
        self.widgets['defense'].valueChanged.connect(self.update_xml)
        defense_layout.addWidget(self.widgets['defense'], 0, 3)

        defense_group.setLayout(defense_layout)
        layout.addWidget(defense_group)


        elements_group = QGroupBox("Elements")
        elements_layout = QGridLayout()

        elements = [
            ('physical', 'Physical', 30),
            ('holy', 'Holy', 30),
            ('death', 'Death', -10),
            ('fire', 'Fire', 50),
            ('energy', 'Energy', 20),
            ('ice', 'Ice', 20),
            ('earth', 'Earth', 40),
            ('lifedrain', 'Life Drain', 0),
            ('drown', 'Drown', 100),
        ]

        row = 0
        col = 0
        for key, label, default in elements:
            elements_layout.addWidget(QLabel(f"{label}:"), row, col)
            self.widgets[key] = QSpinBox()
            self.widgets[key].setRange(-100, 100)
            self.widgets[key].setValue(default)
            self.widgets[key].valueChanged.connect(self.update_xml)
            elements_layout.addWidget(self.widgets[key], row, col + 1)

            col += 2
            if col > 4:
                col = 0
                row += 1

        elements_group.setLayout(elements_layout)
        layout.addWidget(elements_group)

        layout.addStretch()
        self.tabs.addTab(scroll, "Combat")

    def setup_immunities_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)

        layout = QVBoxLayout(scroll_widget)

        immunities_group = QGroupBox("Immunities")
        immunities_layout = QGridLayout()

        immunities = [
            ('immune_physical', 'Physical'),
            ('immune_holy', 'Holy'),
            ('immune_death', 'Death'),
            ('immune_fire', 'Fire'),
            ('immune_energy', 'Energy'),
            ('immune_ice', 'Ice'),
            ('immune_earth', 'Earth'),
            ('immune_lifedrain', 'Life Drain'),
            ('immune_drown', 'Drown'),
            ('immune_paralyze', 'Paralyze'),
            ('immune_drunk', 'Drunk'),
            ('immune_invisible', 'Invisible'),
            ('immune_outfit', 'Outfit'),
        ]

        row = 0
        col = 0
        for key, label in immunities:
            self.widgets[key] = QCheckBox(label)
            if key == 'immune_invisible':
                self.widgets[key].setChecked(True)
            self.widgets[key].stateChanged.connect(self.update_xml)
            immunities_layout.addWidget(self.widgets[key], row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

        immunities_group.setLayout(immunities_layout)
        layout.addWidget(immunities_group)

        layout.addStretch()
        self.tabs.addTab(scroll, "Immunities")
        
    def setup_attacks_defenses_tab(self):

        from PyQt6.QtWidgets import QListWidget

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)
        layout = QVBoxLayout(scroll_widget)

        # ATTACKS
        attacks_group = QGroupBox("Attacks")
        attacks_layout = QVBoxLayout()

        self.attacks_listwidget = QListWidget()
        self.attacks_listwidget.setMaximumHeight(150)
        self.attacks_listwidget.itemDoubleClicked.connect(lambda: self.edit_attack())
        attacks_layout.addWidget(self.attacks_listwidget)

        attacks_buttons = QHBoxLayout()
        add_btn = QPushButton("Add Attack")
        add_btn.clicked.connect(self.add_attack_quick)
        attacks_buttons.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_attack)
        attacks_buttons.addWidget(edit_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_attack)
        attacks_buttons.addWidget(remove_btn)
        attacks_buttons.addStretch()

        attacks_layout.addLayout(attacks_buttons)
        attacks_group.setLayout(attacks_layout)
        layout.addWidget(attacks_group)

        # DEFENSES
        defenses_group = QGroupBox("Defense Spells (dentro de <defenses>)")
        defenses_layout = QVBoxLayout()

        self.defenses_listwidget = QListWidget()
        self.defenses_listwidget.setMaximumHeight(150)
        self.defenses_listwidget.itemDoubleClicked.connect(lambda: self.edit_defense())
        defenses_layout.addWidget(self.defenses_listwidget)

        defenses_buttons = QHBoxLayout()
        add_def_btn = QPushButton("Add Defense")
        add_def_btn.clicked.connect(self.add_defense_quick)
        defenses_buttons.addWidget(add_def_btn)

        edit_def_btn = QPushButton("Edit")
        edit_def_btn.clicked.connect(self.edit_defense)
        defenses_buttons.addWidget(edit_def_btn)

        remove_def_btn = QPushButton("Remove")
        remove_def_btn.clicked.connect(self.remove_defense)
        defenses_buttons.addWidget(remove_def_btn)
        defenses_buttons.addStretch()

        defenses_layout.addLayout(defenses_buttons)
        defenses_group.setLayout(defenses_layout)
        layout.addWidget(defenses_group)

        layout.addStretch()
        self.tabs.addTab(scroll, "Attacks/Defenses")


    def setup_extras_tab(self):
        """Tab para Summons, Voices e Loot com botões Edit"""
        from PyQt6.QtWidgets import QListWidget

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)
        layout = QVBoxLayout(scroll_widget)


        summons_group = QGroupBox("Summons")
        summons_layout = QVBoxLayout()

        self.summons_listwidget = QListWidget()
        self.summons_listwidget.setMaximumHeight(100)
        self.summons_listwidget.itemDoubleClicked.connect(lambda: self.edit_summon())
        summons_layout.addWidget(self.summons_listwidget)

        summons_buttons = QHBoxLayout()
        add_summon_btn = QPushButton("Add")
        add_summon_btn.clicked.connect(self.add_summon_quick)
        summons_buttons.addWidget(add_summon_btn)

        edit_summon_btn = QPushButton("Edit")
        edit_summon_btn.clicked.connect(self.edit_summon)
        summons_buttons.addWidget(edit_summon_btn)

        remove_summon_btn = QPushButton("Remove")
        remove_summon_btn.clicked.connect(self.remove_summon)
        summons_buttons.addWidget(remove_summon_btn)
        summons_buttons.addStretch()

        summons_layout.addLayout(summons_buttons)
        summons_group.setLayout(summons_layout)
        layout.addWidget(summons_group)

        voices_group = QGroupBox("Voices")
        voices_layout = QVBoxLayout()

        self.voices_listwidget = QListWidget()
        self.voices_listwidget.setMaximumHeight(100)
        voices_layout.addWidget(self.voices_listwidget)

        voices_buttons = QHBoxLayout()
        add_voice = QPushButton("Add Voice")
        add_voice.clicked.connect(self.add_voice_quick)
        voices_buttons.addWidget(add_voice)

        remove_voice = QPushButton("Remove")
        remove_voice.clicked.connect(self.remove_voice)
        voices_buttons.addWidget(remove_voice)
        voices_buttons.addStretch()

        voices_layout.addLayout(voices_buttons)
        voices_group.setLayout(voices_layout)
        layout.addWidget(voices_group)

        loot_group = QGroupBox("Loot")
        loot_layout = QVBoxLayout()

        self.loot_listwidget = QListWidget()
        self.loot_listwidget.setMaximumHeight(150)
        self.loot_listwidget.itemDoubleClicked.connect(lambda: self.edit_loot())
        loot_layout.addWidget(self.loot_listwidget)

        loot_buttons = QHBoxLayout()
        add_loot = QPushButton("Add Loot")
        add_loot.clicked.connect(self.add_loot_quick)
        loot_buttons.addWidget(add_loot)

        edit_loot_btn = QPushButton("Edit")
        edit_loot_btn.clicked.connect(self.edit_loot)
        loot_buttons.addWidget(edit_loot_btn)

        remove_loot = QPushButton("Remove")
        remove_loot.clicked.connect(self.remove_loot)
        loot_buttons.addWidget(remove_loot)
        loot_buttons.addStretch()

        loot_layout.addLayout(loot_buttons)
        loot_group.setLayout(loot_layout)
        layout.addWidget(loot_group)

        layout.addStretch()
        self.tabs.addTab(scroll, "Extras")
        
        
        
    def add_attack_quick(self):

        dialog = EditAttackDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            attack_data = dialog.get_data()
            self.attacks_list.append(attack_data)
            self.update_attacks_list()
            self.update_xml()


    def add_defense_quick(self):

        dialog = EditDefenseDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            defense_data = dialog.get_data()
            self.defenses_list.append(defense_data)
            self.update_defenses_list()
            self.update_xml()


    def add_summon_quick(self):

        dialog = EditSummonDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            summon_data = dialog.get_data()
            self.summons_list.append(summon_data)
            self.update_summons_list()
            self.update_xml()


    def add_loot_quick(self):
        """Adiciona loot com todos os campos editáveis"""
        dialog = EditLootDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            loot_data = dialog.get_data()
            self.loot_list.append(loot_data)
            self.update_loot_list()
            self.update_xml()        



    def remove_attack(self):
        row = self.attacks_listwidget.currentRow()
        if row >= 0:
            self.attacks_list.pop(row)
            self.update_attacks_list()
            self.update_xml()

    def update_attacks_list(self):
        self.attacks_listwidget.clear()
        for atk in self.attacks_list:
            label = f"{atk['name']} (interval={atk['interval']}"
            if atk.get('chance'):
                label += f", chance={atk['chance']}"
            label += ")"
            self.attacks_listwidget.addItem(label)


    def remove_defense(self):
        row = self.defenses_listwidget.currentRow()
        if row >= 0:
            self.defenses_list.pop(row)
            self.update_defenses_list()
            self.update_xml()

    def update_defenses_list(self):
        self.defenses_listwidget.clear()
        for defense in self.defenses_list:
            self.defenses_listwidget.addItem(f"{defense['name']} ({defense['interval']}ms)")

    def remove_summon(self):
        row = self.summons_listwidget.currentRow()
        if row >= 0:
            self.summons_list.pop(row)
            self.update_summons_list()
            self.update_xml()

    def update_summons_list(self):
        self.summons_listwidget.clear()
        for s in self.summons_list:
            self.summons_listwidget.addItem(s['name'])

    def add_voice_quick(self):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Voice", "Sentence:")
        if ok and text:
            self.voices_list.append({'sentence': text, 'yell': False})
            self.update_voices_list()
            self.update_xml()

    def remove_voice(self):
        row = self.voices_listwidget.currentRow()
        if row >= 0:
            self.voices_list.pop(row)
            self.update_voices_list()
            self.update_xml()

    def update_voices_list(self):
        self.voices_listwidget.clear()
        for v in self.voices_list:
            self.voices_listwidget.addItem(v['sentence'][:50])


    def remove_loot(self):
        row = self.loot_listwidget.currentRow()
        if row >= 0:
            self.loot_list.pop(row)
            self.update_loot_list()
            self.update_xml()

    def update_loot_list(self):
        self.loot_listwidget.clear()
        for item in self.loot_list:
            name = item.get('name', f"ID {item.get('id')}")
            self.loot_listwidget.addItem(f"{name} (chance={item['chance']})")        
        

    def update_xml(self):

        # Atualiza monster_data com valores dos widgets
        for key, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                self.monster_data[key] = widget.text()
            elif isinstance(widget, QSpinBox):
                self.monster_data[key] = widget.value()
            elif isinstance(widget, QComboBox):
                self.monster_data[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                self.monster_data[key] = widget.isChecked()


        monster = ET.Element('monster')
        monster.set('name', self.monster_data['name'])
        monster.set('nameDescription', self.monster_data['namedescription'])
        monster.set('race', self.monster_data['race'])
        monster.set('experience', str(self.monster_data['experience']))
        monster.set('speed', str(self.monster_data['speed']))

        if self.monster_data['manacost'] > 0:
            monster.set('manacost', str(self.monster_data['manacost']))

        if self.monster_data['skull'] != 'none':
            monster.set('skull', self.monster_data['skull'])

        # Health
        health = ET.SubElement(monster, 'health')
        health.set('now', str(self.monster_data['health_now']))
        health.set('max', str(self.monster_data['health_max']))

        # Look
        look = ET.SubElement(monster, 'look')
        look.set('type', str(self.monster_data['looktype']))

        if self.monster_data['head'] > 0:
            look.set('head', str(self.monster_data['head']))
        if self.monster_data['body'] > 0:
            look.set('body', str(self.monster_data['body']))
        if self.monster_data['legs'] > 0:
            look.set('legs', str(self.monster_data['legs']))
        if self.monster_data['feet'] > 0:
            look.set('feet', str(self.monster_data['feet']))
        if self.monster_data['addons'] > 0:
            look.set('addons', str(self.monster_data['addons']))
        if self.monster_data['mount'] > 0:
            look.set('mount', str(self.monster_data['mount']))

        look.set('corpse', str(self.monster_data['corpse']))

        # Target Change
        targetchange = ET.SubElement(monster, 'targetchange')
        targetchange.set('interval', str(self.monster_data['targetchange_interval']))
        targetchange.set('chance', str(self.monster_data['targetchange_chance']))

        # ===== FLAGS =====
        flags = ET.SubElement(monster, 'flags')

        flag_map = {
            'summonable': self.monster_data['summonable'],
            'attackable': self.monster_data['attackable'],
            'hostile': self.monster_data['hostile'],
            'illusionable': self.monster_data['illusionable'],
            'convinceable': self.monster_data['convinceable'],
            'pushable': self.monster_data['pushable'],
            'canpushitems': self.monster_data['canpushitems'],
            'canpushcreatures': self.monster_data['canpushcreatures']
        }

        for flag_name, flag_value in flag_map.items():
            flag_elem = ET.SubElement(flags, 'flag')
            flag_elem.set(flag_name, '1' if flag_value else '0')

        flag_elem = ET.SubElement(flags, 'flag')
        flag_elem.set('targetdistance', str(self.monster_data['targetdistance']))

        flag_elem = ET.SubElement(flags, 'flag')
        flag_elem.set('staticattack', str(self.monster_data['staticattack']))

        if self.monster_data['runonhealth'] > 0:
            flag_elem = ET.SubElement(flags, 'flag')
            flag_elem.set('runonhealth', str(self.monster_data['runonhealth']))

        if self.monster_data['hidehealth']:
            flag_elem = ET.SubElement(flags, 'flag')
            flag_elem.set('hidehealth', '1')

        if self.monster_data['lightlevel'] > 0:
            flag_elem = ET.SubElement(flags, 'flag')
            flag_elem.set('lightcolor', str(self.monster_data['lightcolor']))
            flag_elem.set('lightlevel', str(self.monster_data['lightlevel']))


        if self.attacks_list:
            attacks = ET.SubElement(monster, 'attacks')
            for attack in self.attacks_list:
                attack_elem = ET.SubElement(attacks, 'attack')
                attack_elem.set('name', attack['name'])
                attack_elem.set('interval', str(attack['interval']))

   
                for attr_name in ['chance', 'min', 'max', 'range', 'radius', 'target', 
                                 'length', 'spread', 'speedchange', 'duration', 'poison']:
                    if attack.get(attr_name) is not None:
                        attack_elem.set(attr_name, str(attack[attr_name]))

                for key, value in attack.get('attributes', {}).items():
                    attr = ET.SubElement(attack_elem, 'attribute')
                    attr.set('key', key)
                    attr.set('value', value)


        defenses = ET.SubElement(monster, 'defenses')
        defenses.set('armor', str(self.monster_data['armor']))
        defenses.set('defense', str(self.monster_data['defense']))


        for defense in self.defenses_list:
            defense_elem = ET.SubElement(defenses, 'defense')
            defense_elem.set('name', defense['name'])
            defense_elem.set('interval', str(defense['interval']))
            defense_elem.set('chance', str(defense['chance']))


            for attr_name in ['min', 'max', 'speedchange', 'duration']:
                if defense.get(attr_name) is not None:
                    defense_elem.set(attr_name, str(defense[attr_name]))


            for key, value in defense.get('attributes', {}).items():
                attr = ET.SubElement(defense_elem, 'attribute')
                attr.set('key', key)
                attr.set('value', value)


        elements = ET.SubElement(monster, 'elements')
        element_map = {
            'physicalPercent': self.monster_data['physical'],
            'deathPercent': self.monster_data['death'],
            'energyPercent': self.monster_data['energy'],
            'earthPercent': self.monster_data['earth'],
            'icePercent': self.monster_data['ice'],
            'holyPercent': self.monster_data['holy'],
            'firePercent': self.monster_data['fire'],
        }

        for elem_name, elem_value in element_map.items():
            if elem_value != 0:
                elem = ET.SubElement(elements, 'element')
                elem.set(elem_name, str(elem_value))

        if self.monster_data['lifedrain'] != 0:
            elem = ET.SubElement(elements, 'element')
            elem.set('lifedrainPercent', str(self.monster_data['lifedrain']))

        if self.monster_data['drown'] != 0:
            elem = ET.SubElement(elements, 'element')
            elem.set('drownPercent', str(self.monster_data['drown']))

        # ===== IMMUNITIES =====
        has_immunities = False
        immunities = ET.SubElement(monster, 'immunities')

        immunity_map = {
            'physical': self.monster_data.get('immune_physical', False),
            'holy': self.monster_data.get('immune_holy', False),
            'death': self.monster_data.get('immune_death', False),
            'fire': self.monster_data.get('immune_fire', False),
            'energy': self.monster_data.get('immune_energy', False),
            'ice': self.monster_data.get('immune_ice', False),
            'earth': self.monster_data.get('immune_earth', False),
            'lifedrain': self.monster_data.get('immune_lifedrain', False),
            'drown': self.monster_data.get('immune_drown', False),
            'paralyze': self.monster_data.get('immune_paralyze', False),
            'drunk': self.monster_data.get('immune_drunk', False),
            'invisible': self.monster_data.get('immune_invisible', False),
            'outfit': self.monster_data.get('immune_outfit', False),
        }

        for immunity_name, immunity_value in immunity_map.items():
            if immunity_value:
                immunity_elem = ET.SubElement(immunities, 'immunity')
                immunity_elem.set(immunity_name, '1')
                has_immunities = True

        if not has_immunities:
            monster.remove(immunities)


        if self.summons_list:
            summons = ET.SubElement(monster, 'summons')
            summons.set('maxSummons', '1')  

            for summon in self.summons_list:
                summon_elem = ET.SubElement(summons, 'summon')
                summon_elem.set('name', summon['name'])
                summon_elem.set('interval', str(summon['interval']))
                summon_elem.set('chance', str(summon['chance']))


        if self.voices_list:
            voices = ET.SubElement(monster, 'voices')
            voices.set('interval', '5000')
            voices.set('chance', '10')

            for voice in self.voices_list:
                voice_elem = ET.SubElement(voices, 'voice')
                voice_elem.set('sentence', voice['sentence'])
                if voice.get('yell'):
                    voice_elem.set('yell', '1')


        if self.loot_list:
            loot = ET.SubElement(monster, 'loot')

            for item in self.loot_list:
                item_elem = ET.SubElement(loot, 'item')

      
                if item.get('id'):
                    item_elem.set('id', str(item['id']))
                else:
                    item_elem.set('name', item['name'])


                if item.get('countmax') and item['countmax'] > 1:
                    item_elem.set('countmax', str(item['countmax']))

         
                item_elem.set('chance', str(item['chance']))


        xml_string = prettify_xml(monster)
        self.xml_display.setPlainText(xml_string)

    def copy_xml(self):

        from PyQt6.QtWidgets import QApplication
        xml_text = self.xml_display.toPlainText()
        if xml_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(xml_text)

    def paste_xml(self):

        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        xml_text = clipboard.text()

        if not xml_text:
            return

        try:
            root = ET.fromstring(xml_text)
            if root.tag == 'monster':
                self.load_monster_from_file_content(root)
        except Exception as e:
            QMessageBox.warning(self, "Paste Error", f"Failed to parse XML:\n{e}")

    def load_monster_from_file_content(self, root):

        self.widgets['name'].setText(root.get('name', 'Monster'))
        self.widgets['namedescription'].setText(root.get('nameDescription', 'a monster'))

        race_text = root.get('race', 'blood')
        if self.widgets['race'].findText(race_text) >= 0:
            self.widgets['race'].setCurrentText(race_text)

        self.widgets['experience'].setValue(int(root.get('experience', 100)))
        self.widgets['speed'].setValue(int(root.get('speed', 200)))
        self.widgets['manacost'].setValue(int(root.get('manacost', 0)))

        skull_text = root.get('skull', 'none')
        if self.widgets['skull'].findText(skull_text) >= 0:
            self.widgets['skull'].setCurrentText(skull_text)


        health = root.find('health')
        if health is not None:
            self.widgets['health_now'].setValue(int(health.get('now', 100)))
            self.widgets['health_max'].setValue(int(health.get('max', 100)))

        look = root.find('look')
        if look is not None:
            self.widgets['looktype'].setValue(int(look.get('type', 0)))
            self.widgets['head'].setValue(int(look.get('head', 0)))
            self.widgets['body'].setValue(int(look.get('body', 0)))
            self.widgets['legs'].setValue(int(look.get('legs', 0)))
            self.widgets['feet'].setValue(int(look.get('feet', 0)))
            self.widgets['addons'].setValue(int(look.get('addons', 0)))
            self.widgets['mount'].setValue(int(look.get('mount', 0)))
            self.widgets['corpse'].setValue(int(look.get('corpse', 0)))

        self.update_xml()

    def save_xml_file(self):

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Monster XML",
            f"{self.monster_data['name'].lower().replace(' ', '_')}.xml",
            "XML Files (*.xml);;All Files (*.*)"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.xml_display.toPlainText())
                QMessageBox.information(self, "Success", f"Monster saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")
