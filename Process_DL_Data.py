#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import csv
import glob
import json
import os
import re
import sqlite3
import string
import traceback

from collections import OrderedDict, defaultdict
from datetime import datetime
from shutil import copyfile, rmtree

import pdb

EXT = '.txt'
DEFAULT_TEXT_LABEL = ''
ENTRY_LINE_BREAK = '\n=============================\n'
EDIT_THIS = '<EDIT_THIS>'

ROW_INDEX = '_Id'
EMBLEM_N = 'EMBLEM_NAME_'
EMBLEM_P = 'EMBLEM_PHONETIC_'

TEXT_LABEL = 'TextLabel'
TEXT_LABEL_JP = 'TextLabelJP'
TEXT_LABEL_TC = 'TextLabelTC'
TEXT_LABEL_SC = 'TextLabelSC'
TEXT_LABEL_DICT = {}

CHAIN_COAB_SET = set()
EPITHET_DATA_NAME = 'EmblemData'
EPITHET_DATA_NAMES = None
ITEM_NAMES = {
    'AstralItem': {},
    'BuildEventItem': {},
    'CollectEventItem': {},
    'CombatEventItem': {},
    'Clb01EventItem': {},
    'ExHunterEventItem': {},
    'ExRushEventItem': {},
    'GatherItem': {},
    'RaidEventItem': {},
    'SimpleEventItem': {},
}
SKILL_DATA_NAME = 'SkillData'
SKILL_DATA_NAMES = None

ORDERING_DATA = {}

ROMAN_NUMERALS = [None, 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
ELEMENT_TYPE = {
    '0': None,
    '1': 'Flame',
    '2': 'Water',
    '3': 'Wind',
    '4': 'Light',
    '5': 'Shadow',
    '99': 'None'
}
CLASS_TYPE = [None, 'Attack', 'Defense', 'Support', 'Healing']
WEAPON_TYPE = [None, 'Sword', 'Blade', 'Dagger', 'Axe', 'Lance', 'Bow', 'Wand', 'Staff', 'Manacaster']
QUEST_TYPE_DICT = {
    'Campaign': re.compile(r'MAIN_|PROLOGUE_'),
    'Event': re.compile(r'AGITO_|ASTRAL_|DRAGONBATTLE_|WEEKLY_|EXP_|EMPIRE_|VOIDBATTLE_'),
    'Facility': re.compile(r'BUILD_'),
    'Raid': re.compile(r'RAID_'),
    'Onslaught': re.compile(r'COMBAT_'),
    'Defensive': re.compile(r'CLB_DEF_'),
    'Collab': re.compile(r'CLB_\d|EX_'),
    'Battle Royale': re.compile(r'BR_'),
    'Simple': re.compile(r'SIMPLE_'),
}

GROUP_TYPE_DICT = {
    '1' : 'Campaign',
    '2' : 'Event',
}
QUEST_MODE_PLAY_TYPE_DICT = {
    '1' : '',
    '2' : ' (Solo)',
    '3' : ' (Co-op)',
}
WEAPON_SERIES = {
    '1' : 'Core',
    '2' : 'Void',
    '3' : 'High Dragon',
    '4' : 'Agito',
    '5' : 'Chimeratech',
    '6' : 'Other',
}

FACILITY_EFFECT_TYPE_DICT = {
    '1': 'Adventurer', # weapon
    '2': 'Adventurer', # elemental
    '4': 'Dragon', # dracolith
    '6': 'Dragon' # fafnir
}

# (icon+text, text only, category)
ENTITY_TYPE_DICT = {
    '2': (lambda id: '{{' + get_label('USE_ITEM_NAME_' + id) + '-}}',
          lambda id: get_label('USE_ITEM_NAME_' + id),
          'Consumable'),
    '3': (lambda id: '{{Icon|Weapon|' + get_label('WEAPON_NAME_' + id) + '|size=24px|text=1}}',
          lambda id: get_label('WEAPON_NAME_' + id),
          'Weapon'),
    '4': (lambda _: '{{Rupies-}}',
          lambda _: 'Rupies',
          'Resource'),
    '7': (lambda id: '{{Icon|Dragon|' + get_label('DRAGON_NAME_' + id) + '|size=24px|text=1}}',
          lambda id: get_label('DRAGON_NAME_' + id),
          'Dragon'),
    '8': (lambda id: '{{' + get_label('MATERIAL_NAME_' + id) + '-}}',
          lambda id: get_label('MATERIAL_NAME_' + id),
          'Material'),
    '9': (lambda id: '{{Icon|Facility|' + get_label('FORT_PLANT_NAME_' + id) + '|size=24px|text=1}}',
          lambda id: get_label('FORT_PLANT_NAME_' + id),
          'Facility'),
    '10': (lambda id: '[[File:Icon Profile 0' + EPITHET_RANKS.get(id, '') + ' Frame.png|19px|Epithet|link=Epithets]] ' + get_label('EMBLEM_NAME_' + id),
           lambda id: get_label('EMBLEM_NAME_' + id),
           'Epithet'),
    '11': (lambda id: '[[File:' + id + ' en.png|24px|Sticker|link=Stickers]] ' + get_label('STAMP_NAME_' + id),
           lambda id: get_label('STAMP_NAME_' + id),
           'Sticker'),
    '12': (lambda id: '{{Icon|Wyrmprint|' + get_label('AMULET_NAME_' + id) + '|size=24px|text=1}}',
           lambda id: get_label('AMULET_NAME_' + id),
           'Wyrmprint'),
    '14': (lambda _: '{{Eldwater-}}',
           lambda _: 'Eldwater',
           'Resource'),
    '15': (lambda id: '{{' + get_label('DRAGON_GIFT_NAME_' + id) + '-}}',
           lambda id: get_label('DRAGON_GIFT_NAME_' + id),
           'Gift'),
    '16': (lambda _: '{{Skip Ticket-}}',
           lambda _: 'Skip Ticket',
           'Consumable'),
    '17': (lambda id: '{{' + get_label('SUMMON_TICKET_NAME_' + id) + '-}}',
           lambda id: get_label('SUMMON_TICKET_NAME_' + id),
           'Consumable'),
    '18': (lambda _: '{{Mana-}}',
           lambda _: 'Mana',
           'Resource'),
    '20': (lambda id: '{{' + get_item_label('RaidEventItem', id) + '-}}',
           lambda id: get_item_label('RaidEventItem', id),
           'Material'),
    '22': (lambda id: '{{' + get_item_label('BuildEventItem', id) + '-}}',
           lambda id: get_item_label('BuildEventItem', id),
           'Material'),
    '23': (lambda _: '{{Wyrmite-}}',
           lambda _: 'Wyrmite',
           'Currency'),
    '24': (lambda id: '{{' + get_item_label('CollectEventItem', id) + '-}}',
           lambda id: get_item_label('CollectEventItem', id),
           'Material'),
    '25': (lambda id: '{{' + get_item_label('Clb01EventItem', id) + '-}}',
           lambda id: get_item_label('Clb01EventItem', id),
           'Material'),
    '26': (lambda id: '{{' + get_item_label('AstralItem', id) + '-}}',
           lambda id: get_item_label('AstralItem', id),
           'Consumable'),
    '28': (lambda _: '{{Hustle Hammer-}}',
           lambda _: 'Hustle Hammer',
           'Consumable'),
    '29': (lambda id: '{{' + get_item_label('ExRushEventItem', id) + '-}}',
           lambda id: get_item_label('ExRushEventItem', id),
           'Material'),
    '30': (lambda id: '{{' + get_item_label('SimpleEventItem', id) + '-}}',
           lambda id: get_item_label('SimpleEventItem', id),
           'Material'),
    '31': (lambda id: '{{' + get_label('LOTTERY_TICKET_NAME_' + id) + '-}}',
           lambda id: get_label('LOTTERY_TICKET_NAME_' + id),
           'Consumable'),
    '32': (lambda id: '{{' + get_item_label('ExHunterEventItem', id) + '-}}',
           lambda id: get_item_label('ExHunterEventItem', id),
           'Material'),
    '33': (lambda id: '{{' + get_item_label('GatherItem', id) + '-}}',
           lambda id: get_item_label('GatherItem', id),
           'Material'),
    '34': (lambda id: '{{' + get_item_label('CombatEventItem', id) + '-}}',
           lambda id: get_item_label('CombatEventItem', id),
           'Material'),
    '37': (lambda id: '{{Icon|WeaponSkin|' + str(id) + '|size=24px|text=1}}',
           lambda id: get_label('WEAPON_SKIN_NAME_' + id),
           'WeaponSkin'),
    '38': (lambda id: '{{Icon|Weapon|' + get_label('WEAPON_NAME_' + id) + '|size=24px|text=1}}',
           lambda id: get_label('WEAPON_NAME_' + id),
           'Weapon'),
    '39': (lambda id: '{{Icon|Wyrmprint|' + get_label('AMULET_NAME_' + id) + '|size=24px|text=1}}',
           lambda id: get_label('AMULET_NAME_' + id),
           'Wyrmprint'),
}
MISSION_ENTITY_OVERRIDES_DICT = {
    '3' : lambda x: ["Override={}".format(get_entity_item('3', x, format=0))],
    '7' : lambda x: ["Override={}".format(get_entity_item('7', x, format=0))],
    '10': lambda x: ["Epithet: {}".format(get_label(EMBLEM_N + x)), "Rank=" + EPITHET_RANKS.get(x, '')],
    '11' : lambda x: ["Override={}".format(get_entity_item('11', x, format=0))],
    '12' : lambda x: ["Override={}".format(get_entity_item('12', x, format=0))],
}
EVENT_TYPES = {
    '1': 'Raid',
    '4': 'Facility',
    '5': 'Story',
    '6': 'Collab', # CLB01 / Fire Emblem
    '7': 'Collab', # EX_RUSH / Mega Man
    '8': 'Collab', # EX_HUNTER / MonHun
    '9': 'Simple',
    '10': 'Onslaught',
    '11': 'Alberian Battle Royale',
}

MATERIAL_NAME_LABEL = 'MATERIAL_NAME_'
PERCENTAGE_REGEX = re.compile(r' (\d+)%')

class DataParser:
    def __init__(self, _data_name, _template, _formatter, _process_info):
        self.data_name = _data_name
        self.template = _template
        self.formatter = _formatter
        self.process_info = _process_info
        self.row_data = []
        self.extra_data = {}

    def process_csv(self, file_name, func):
        with open(in_dir+file_name+EXT, 'r', newline='', encoding='utf-8') as in_file:
            reader = csv.DictReader(in_file)
            for row in reader:
                if row[ROW_INDEX] == '0':
                    continue
                try:
                    func(row, self.row_data)
                except TypeError:
                    func(row, self.row_data, self.extra_data)
                # except Exception as e:
                #     print('Error processing {}: {}'.format(file_name, str(e)))

    def process(self):
        try: # process_info is an iteratable of (file_name, process_function)
            for file_name, func in self.process_info:
                self.process_csv(file_name, func)
        except TypeError: # process_info is the process_function
            self.process_csv(self.data_name, self.process_info)

    def emit(self, out_dir):
        with open(out_dir+self.data_name+EXT, 'w', newline='', encoding='utf-8') as out_file:
            for display_name, row in self.row_data:
                out_file.write(self.formatter(row, self.template, display_name))

class CustomDataParser:
    def __init__(self, _data_name, _processor_params):
        self.data_name = _data_name
        self.process_func = _processor_params[0]
        self.extra_files = _processor_params[1:]

    def process(self, in_dir, out_dir):
        with open(in_dir+self.data_name+EXT, 'r', newline='', encoding='utf-8') as in_file:
            reader = csv.DictReader(in_file)
            with open(out_dir+self.data_name+EXT, 'w', newline='', encoding='utf-8') as out_file:
                self.process_func(reader, out_file, *[in_dir+f+EXT for f in self.extra_files])

class DatabaseBasedParser:
    def __init__(self, _data_name, _processor_params):
        self.data_name = _data_name
        self.process_func = _processor_params[0]

    def process(self, out_dir):
        with open(out_dir+self.data_name+EXT, 'w', newline='', encoding='utf-8') as out_file:
            self.process_func(out_file)

def csv_as_index(path, index=None, value_key=None, tabs=False):
    with open(path, 'r', newline='', encoding='utf-8') as csvfile:
        if tabs:
            reader = csv.DictReader(csvfile, dialect='excel-tab')
        else:
            reader = csv.DictReader(csvfile)

        keys = reader.fieldnames

        if not index:
            index = keys[0] # get first key as index
        if not value_key and len(keys) == 2:
            # If not otherwise specified, load 2 column files as dict[string] = string
            value_key = keys[1] # get second key
        if value_key:
            return {row[index]: row[value_key] for row in reader if row[index] != '0'}
        else:
            # load >2 column files as a dict[string] = OrderedDict
            return {row[index]: row for row in reader if row[index] != '0'}

def get_label(key, lang='en'):
    try:
        txt_label = TEXT_LABEL_DICT[lang]
    except KeyError:
        txt_label = TEXT_LABEL_DICT['en']
    return (txt_label.get(key, DEFAULT_TEXT_LABEL) or DEFAULT_TEXT_LABEL).replace('\\n', ' ')

def get_item_label(type, key):
    try:
        label_key = ITEM_NAMES[type][key]
        return get_label(label_key)
    except KeyError:
        return key

def get_epithet(emblem_id, lang='en'):
    return get_label(EMBLEM_N + emblem_id, lang=lang)

def get_jp_epithet(emblem_id):
    if 'jp' in TEXT_LABEL_DICT:
        return '{{' + 'Ruby|{}|{}'.format(
            get_label(EMBLEM_N + emblem_id, lang='jp'),
            get_label(EMBLEM_P + emblem_id, lang='jp')) + '}}'
    return ''

def get_epithet_rarity(emblem_id):
    return db_query_one(f"SELECT _Rarity FROM EmblemData WHERE _Id='{emblem_id}'")['_Rarity']

# Formats= 0: icon + text, 1: text only, 2: category
def get_entity_item(item_type, item_id, format=1):
    try:
        if item_type == '0':
            return ''
        if format == 2:
            return ENTITY_TYPE_DICT[item_type][format]
        else:
            return ENTITY_TYPE_DICT[item_type][format](item_id)
    except KeyError:
        return 'Entity type {}: {}'.format(item_type, item_id)

# All process_* functions take in 1 parameter (OrderedDict row) and return 3 values (OrderedDict new_row, str template_name, str display_name)
# Make sure the keys are added to the OrderedDict in the desired output order
def process_AbilityLimitedGroup(row, existing_data):
    new_row = OrderedDict()
    copy_without_entriesKey(new_row, row)
    new_row['AbilityLimitedText'] = get_label(row['_AbilityLimitedText']).format(ability_limit0=row['_MaxLimitedValue'])
    existing_data.append((None, new_row))

def process_AbilityShiftGroup(row, existing_data, ability_shift_groups):
    ability_shift_groups[row[ROW_INDEX]] = row

def process_AbilityData(row, existing_data, ability_shift_groups):
    if row[ROW_INDEX] in CHAIN_COAB_SET:
        # Process abilities known to be chain coabilities (from being
        # referenced in CharaData), separately.
        return
    new_row = OrderedDict()

    new_row['Id'] = row[ROW_INDEX]
    new_row['PartyPowerWeight'] = row['_PartyPowerWeight']

    shift_value = 0
    try:
        shift_group = ability_shift_groups[row['_ShiftGroupId']]
        for i in range(1, int(shift_group['_AmuletEffectMaxLevel']) + 1):
            if shift_group['_Level{}'.format(i)] == row[ROW_INDEX]:
                shift_value = i
                break
    except KeyError:
        shift_value = int(row['_ShiftGroupId'])

    # TODO: figure out what actually goes to {ability_val0}
    ability_value = EDIT_THIS if row['_AbilityType1UpValue'] == '0' else row['_AbilityType1UpValue']
    name = get_label(row['_Name']).format(
        ability_shift0  =   ROMAN_NUMERALS[shift_value], # heck
        ability_val0    =   ability_value)
    # guess the generic name by chopping off the last word, which is usually +n% or V
    new_row['GenericName'] = name[:name.rfind(' ')].replace('%', '')
    new_row['Name'] = name

    # _ElementalType seems unreliable, use (element) in _Name for now
    detail_label = get_label(row['_Details'])
    if '{element_owner}' in detail_label and ')' in new_row['Name']:
        element = new_row['Name'][1:new_row['Name'].index(')')]
    else:
        element = ELEMENT_TYPE[row['_ElementalType']]
        if element == 'None':
            element = 'EDIT_THIS'
    new_row['Details'] = detail_label.format(
        ability_cond0   =   row['_ConditionValue'],
        ability_val0    =   ability_value,
        element_owner   =   element)
    new_row['Details'] = PERCENTAGE_REGEX.sub(r" '''\1%'''", new_row['Details'])

    new_row['AbilityIconName'] = row['_AbilityIconName']
    new_row['AbilityGroup'] = row['_ViewAbilityGroupId1']
    new_row['AbilityLimitedGroupId1'] = row['_AbilityLimitedGroupId1']
    new_row['AbilityLimitedGroupId2'] = row['_AbilityLimitedGroupId2']
    new_row['AbilityLimitedGroupId3'] = row['_AbilityLimitedGroupId3']
    existing_data.append((new_row['Name'], new_row))

def process_ChainCoAbility(row, existing_data):
    if not row[ROW_INDEX] in CHAIN_COAB_SET:
        return
    new_row = OrderedDict()
    new_row['Id'] = row[ROW_INDEX]

    ability_value = (EDIT_THIS if row['_AbilityType1UpValue'] == '0'
                               else row['_AbilityType1UpValue'])
    new_row['Name'] = get_label(row['_Name']).format(
        ability_val0 = ability_value)
    # guess the generic name by chopping off the last word, which is usually +n% or V
    new_row['GenericName'] = new_row['Name'][:new_row['Name'].rfind(' ')].replace('%', '')

    # _ElementalType seems unreliable, use (element) in _Name for now
    detail_label = get_label(row['_Details'])
    if '{element_owner}' in detail_label and ')' in new_row['Name']:
        element = new_row['Name'][1:new_row['Name'].index(')')]
    else:
        element = ELEMENT_TYPE[row['_ElementalType']]
    new_row['Details'] = detail_label.format(
        ability_cond0   =   row['_ConditionValue'],
        ability_val0    =   ability_value,
        element_owner   =   element).replace('  ', ' ')
    new_row['Details'] = PERCENTAGE_REGEX.sub(r" '''\1%'''", new_row['Details'])
    new_row['AbilityIconName'] = row['_AbilityIconName']

    existing_data.append((new_row['Name'], new_row))

def process_AbilityCrest(row, existing_data):
    new_row = OrderedDict()

    new_row['Id'] = row['_Id']
    new_row['BaseId'] = row['_BaseId']
    new_row['Name'] = get_label(row['_Name'])
    new_row['NameJP'] = get_label(row['_Name'], lang='jp')
    new_row['NameSC'] = get_label(row['_Name'], lang='sc')
    new_row['NameTC'] = get_label(row['_Name'], lang='tc')
    new_row['IsHideChangeImage'] = row['_IsHideChangeImage']
    new_row['Rarity'] = row['_Rarity']
    new_row['AmuletType'] = row['_AbilityCrestType']
    new_row['CrestSlotType'] = row['_CrestSlotType']
    new_row['UnitType'] = row['_UnitType']
    new_row['MinHp'] = row['_BaseHp']
    new_row['MaxHp'] = row['_MaxHp']
    new_row['MinAtk'] = row['_BaseAtk']
    new_row['MaxAtk'] = row['_MaxAtk']
    new_row['VariationId'] = row['_VariationId']
    new_row['Abilities11'] = row['_Abilities11']
    new_row['Abilities12'] = row['_Abilities12']
    new_row['Abilities13'] = row['_Abilities13']
    new_row['Abilities21'] = row['_Abilities21']
    new_row['Abilities22'] = row['_Abilities22']
    new_row['Abilities23'] = row['_Abilities23']
    new_row['UnionAbilityGroupId'] = row['_UnionAbilityGroupId']
    for i in range(1, 6):
        new_row[f'FlavorText{i}'] = get_label(row[f'_Text{i}'])
    new_row['IsPlayable'] = row['_IsPlayable']
    new_row['DuplicateEntity'] = get_entity_item(row['_DuplicateEntityType'], row['_DuplicateEntityId'])
    new_row['DuplicateEntityQuantity'] = row['_DuplicateEntityQuantity']
    new_row['AbilityCrestBuildupGroupId'] = row['_AbilityCrestBuildupGroupId']

    # Trade/obtain info
    trade = db_query_one('SELECT * FROM AbilityCrestTrade '
                        f'WHERE _AbilityCrestId="{row["_Id"]}"')

    if trade:
        new_row['NeedDewPoint'] = trade['_NeedDewPoint']
        new_row['Obtain'] = '[[Shop/Wyrmprints|Wyrmprints Shop]]'
        new_row['ReleaseDate'] = trade['_CommenceDate']
        if trade['_MemoryPickupEventId'] != '0':
            new_row['Availability'] = 'Compendium'
        elif trade['_CompleteDate']:
            new_row['Availability'] = 'Limited'
        else:
            new_row['Availability'] = 'Permanent'

    else:
        new_row['NeedDewPoint'] = 0
        new_row['Obtain'] = ''
        new_row['ReleaseDate'] = ''
        new_row['Availability'] = ''

    new_row['ArtistCV'] = row['_CvInfo']
    new_row['FeaturedCharacters'] = ''
    new_row['Notes'] = ''

    existing_data.append((new_row['Name'], new_row))

def process_Consumable(row, existing_data):
    new_row = OrderedDict()

    new_row['Id'] = row[ROW_INDEX]
    new_row['Name'] = get_label(row['_Name'])
    new_row['Description'] = get_label(row['_Description'])
    new_row['SortId'] = row[ROW_INDEX]
    new_row['Obtain'] = '\n*'

    existing_data.append((new_row['Name'], new_row))

def process_Material(row, existing_data):
    new_row = OrderedDict()

    new_row['Id'] = row[ROW_INDEX]
    new_row['Name'] = get_label(row['_Name'])
    new_row['Description'] = get_label(row['_Detail'])
    try:
        new_row['Rarity'] = row['_MaterialRarity']
    except KeyError:
        new_row['Rarity'] = '' # EDIT_THIS
    if '_EventId' in row:
        new_row['QuestEventId'] = row['_EventId']
        new_row['SortId'] = row[ROW_INDEX]

        if 'EV_BATTLE_ROYAL' in row['_Name']:
            new_row['Category'] = 'Battle Royale'

    elif '_RaidEventId' in row:
        new_row['QuestEventId'] = row['_RaidEventId']
        new_row['Category'] = 'Raid'
        new_row['SortId'] = row[ROW_INDEX]
    elif '_QuestEventId' in row:
        new_row['QuestEventId'] = row['_QuestEventId']
        new_row['Category'] = row['_Category']
        new_row['SortId'] = row['_SortId']
    new_row['Obtain'] = '\n*' + get_label(row['_Description'])
    new_row['Usage'] = '' # EDIT_THIS
    new_row['MoveQuest1'] = row['_MoveQuest1']
    new_row['MoveQuest2'] = row['_MoveQuest2']
    new_row['MoveQuest3'] = row['_MoveQuest3']
    new_row['MoveQuest4'] = row['_MoveQuest4']
    new_row['MoveQuest5'] = row['_MoveQuest5']
    new_row['PouchRarity'] = row['_PouchRarity']

    try:
        new_row['Exp'] = row['_Exp']
        # new_row['Plus'] = row['_Plus'] # augments
    except KeyError:
        pass

    existing_data.append((new_row['Name'], new_row))

def process_CharaModeData(row, existing_data, chara_mode_data):
    chara_mode_data[row[ROW_INDEX]] = row

def process_CharaData(row, existing_data, chara_mode_data):
    new_row = OrderedDict()

    new_row['IdLong'] = row[ROW_INDEX]
    new_row['Id'] = row['_BaseId']
    new_row['Name'] = get_label(row['_Name'])
    new_row['FullName'] = get_label(row['_SecondName']) or new_row['Name']
    new_row['NameJP'] = get_label(row['_Name'], lang='jp')
    new_row['NameSC'] = get_label(row['_Name'], lang='sc')
    new_row['NameTC'] = get_label(row['_Name'], lang='tc')
    new_row['Title'] = get_epithet(row['_EmblemId'])
    new_row['TitleJP'] = get_jp_epithet(row['_EmblemId'])
    new_row['TitleSC'] = get_epithet(row['_EmblemId'], lang='sc')
    new_row['TitleTC'] = get_epithet(row['_EmblemId'], lang='tc')
    new_row['Obtain'] = '' # EDIT_THIS
    new_row['ReleaseDate'] = '' # EDIT_THIS
    new_row['Availability'] = '' # EDIT_THIS
    new_row['WeaponType'] = WEAPON_TYPE[int(row['_WeaponType'])]
    new_row['Rarity'] = row['_Rarity']
    new_row['Gender'] = '' # EDIT_THIS
    new_row['Race'] = '' # EDIT_THIS
    new_row['ElementalType'] = ELEMENT_TYPE[row['_ElementalType']]
    new_row['CharaType'] = CLASS_TYPE[int(row['_CharaType'])]
    new_row['VariationId'] = row['_VariationId']
    for stat in ('Hp', 'Atk'):
        for i in range(3, 6):
            min_k = 'Min{}{}'.format(stat, i)
            new_row[min_k] = row['_' + min_k]
        max_k = 'Max{}'.format(stat)
        new_row[max_k] = row['_' + max_k]
        add_k = 'AddMax{}1'.format(stat)
        new_row[add_k] = row['_' + add_k]
        for i in range(0, 6):
            plus_k = 'Plus{}{}'.format(stat, i)
            new_row[plus_k] = row['_' + plus_k]
        mfb_k = 'McFullBonus{}5'.format(stat)
        new_row[mfb_k] = row['_' + mfb_k]
    new_row['MinDef'] = row['_MinDef']
    new_row['DefCoef'] = row['_DefCoef']
    try:
        new_row['Skill1ID'] = row['_Skill1']
        new_row['Skill2ID'] = row['_Skill2']
        new_row['Skill1Name'] = get_label(SKILL_DATA_NAMES[row['_Skill1']])
        new_row['Skill2Name'] = get_label(SKILL_DATA_NAMES[row['_Skill2']])
    except KeyError:
        new_row['Skill1ID'] = ''
        new_row['Skill2ID'] = ''
        new_row['Skill1Name'] = ''
        new_row['Skill2Name'] = ''

    new_row['HoldEditSkillCost'] = row['_HoldEditSkillCost']
    new_row['EditSkillId'] = row['_EditSkillId']

    if (row['_EditSkillId'] != row['_Skill1'] and
        row['_EditSkillId'] != row['_Skill2'] and
        row['_EditSkillId'] != '0'):
        new_row['EditSkillId'] += ' // Shared skill differs from actual skill. Double check shared skill entry!'

    new_row['EditSkillLevelNum'] = row['_EditSkillLevelNum']
    new_row['EditSkillCost'] = row['_EditSkillCost']
    new_row['EditSkillRelationId'] = row['_EditSkillRelationId']
    new_row['EditReleaseEntityType1'] = row['_EditReleaseEntityType1']
    new_row['EditReleaseEntityId1'] = row['_EditReleaseEntityId1']
    new_row['EditReleaseEntityQuantity1'] = row['_EditReleaseEntityQuantity1']

    for i in range(1, 4):
        for j in range(1, 5):
            ab_k = 'Abilities{}{}'.format(i, j)
            new_row[ab_k] = row['_' + ab_k]
    for i in range(1, 6):
        ex_k = 'ExAbilityData{}'.format(i)
        new_row[ex_k] = row['_' + ex_k]
    for i in range(1, 6):
        ex_k = 'ExAbility2Data{}'.format(i)
        new_row[ex_k] = row['_' + ex_k]
        CHAIN_COAB_SET.add(new_row[ex_k])
    new_row['ManaCircleName'] = row['_ManaCircleName']

    # new_row['EffNameCriticalHit'] = row['_EffNameCriticalHit']

    new_row['JapaneseCV'] = get_label(row['_CvInfo'])
    new_row['EnglishCV'] = get_label(row['_CvInfoEn'])
    new_row['Description'] = get_label(row['_ProfileText'])
    new_row['IsPlayable'] = row['_IsPlayable']
    new_row['MaxFriendshipPoint'] = row['_MaxFriendshipPoint']

    new_row['MaxLimitBreakCount'] = row['_MaxLimitBreakCount']

    gunmodes = set()
    for m in range(1, 5):
        mode = row['_ModeId{}'.format(m)]
        if mode in chara_mode_data and int(chara_mode_data[mode]['_GunMode']):
            gunmodes.add(chara_mode_data[mode]['_GunMode'])
    if gunmodes:
        new_row['GunModes'] = ','.join(sorted(gunmodes))

    existing_data.append((new_row['Name'] + ' - ' + new_row['FullName'], new_row))

def process_SkillDataNames(row, existing_data):
    for idx, (name, chara) in enumerate(existing_data):
        for i in (1, 2):
            sn_k = 'Skill{}Name'.format(i)
            if chara[sn_k] == row[ROW_INDEX]:
                chara[sn_k] = get_label(row['_Name'])
                existing_data[idx] = (name, chara)

def process_Dragon(row, existing_data):
    new_row = OrderedDict()

    new_row['Id'] = row[ROW_INDEX]
    new_row['BaseId'] = row['_BaseId']
    new_row['Name'] = get_label(row['_Name'])
    new_row['FullName'] = get_label(row['_SecondName']) or new_row['Name']
    new_row['NameJP'] = get_label(row['_Name'], lang='jp')
    new_row['NameSC'] = get_label(row['_Name'], lang='sc')
    new_row['NameTC'] = get_label(row['_Name'], lang='tc')
    new_row['Title'] = get_epithet(row['_EmblemId'])
    new_row['TitleJP'] = get_jp_epithet(row['_EmblemId'])
    new_row['TitleSC'] = get_epithet(row['_EmblemId'], lang='sc')
    new_row['TitleTC'] = get_epithet(row['_EmblemId'], lang='tc')
    new_row['Obtain'] = '' # EDIT_THIS
    new_row['ReleaseDate'] = '' # EDIT_THIS
    new_row['Availability'] = '' # EDIT_THIS
    new_row['Rarity'] = row['_Rarity']
    new_row['Gender'] = '' # EDIT_THIS
    new_row['ElementalType'] = ELEMENT_TYPE[row['_ElementalType']]
    new_row['VariationId'] = row['_VariationId']
    new_row['IsPlayable'] = row['_IsPlayable']
    new_row['MinHp'] = row['_MinHp']
    new_row['MaxHp'] = row['_MaxHp']
    new_row['MinAtk'] = row['_MinAtk']
    new_row['MaxAtk'] = row['_MaxAtk']
    try:
        new_row['SkillID'] = row['_Skill1']
        new_row['SkillName'] = get_label(SKILL_DATA_NAMES[row['_Skill1']])
        new_row['Skill2ID'] = row['_Skill2']
        new_row['Skill2Name'] = get_label(SKILL_DATA_NAMES[row['_Skill2']])
    except KeyError:
        pass
    for i in (1, 2):
        for j in range(1, 6):
            ab_k = 'Abilities{}{}'.format(i, j)
            new_row[ab_k] = row['_' + ab_k]
    new_row['ProfileText'] = get_label(row['_Profile'])
    new_row['LimitBreakMaterialId'] = row['_LimitBreakMaterialId']
    new_row['FavoriteType'] = row['_FavoriteType']
    new_row['JapaneseCV'] = get_label(row['_CvInfo'])
    new_row['EnglishCV'] = get_label(row['_CvInfoEn'])
    new_row['SellCoin'] = row['_SellCoin']
    new_row['SellDewPoint'] = row['_SellDewPoint']
    new_row['MoveSpeed'] = row['_MoveSpeed']
    new_row['DashSpeedRatio'] = row['_DashSpeedRatio']
    new_row['TurnSpeed'] = row['_TurnSpeed']
    new_row['IsTurnToDamageDir'] = row['_IsTurnToDamageDir']
    new_row['MoveType'] = row['_MoveType']
    new_row['IsLongRange'] = row['_IsLongLange']
    new_row['AttackModifiers'] = '\n{{DragonAttackModifierRow|Combo 1|<EDIT_THIS>%|<EDIT_THIS>}}\n{{DragonAttackModifierRow|Combo 2|<EDIT_THIS>%|<EDIT_THIS>}}\n{{DragonAttackModifierRow|Combo 3|<EDIT_THIS>%|<EDIT_THIS>}}'
    existing_data.append((new_row['Name'], new_row))

def process_ExAbilityData(row, existing_data):
    new_row = OrderedDict()

    new_row['Id'] = row[ROW_INDEX]
    new_row['Name'] = get_label(row['_Name'])
    # guess the generic name by chopping off the last word, which is usually +n% or V
    new_row['GenericName'] = new_row['Name'][0:new_row['Name'].rfind(' ')]
    new_row['Details'] = get_label(row['_Details']).format(
        value1=row['_AbilityType1UpValue0']
    )
    new_row['Details'] = PERCENTAGE_REGEX.sub(r" '''\1%'''", new_row['Details'])
    new_row['AbilityIconName'] = row['_AbilityIconName']
    new_row['Category'] = row['_Category']
    new_row['PartyPowerWeight'] = row['_PartyPowerWeight']

    existing_data.append((new_row['Name'], new_row))

event_emblem_pattern = re.compile(r'^A reward from the ([A-Z].*?) event.$')
def process_EmblemData(row, existing_data):
    new_row = OrderedDict()

    new_row['Title'] = get_label(row['_Title'])
    new_row['TitleJP'] = get_jp_epithet(row['_Id'])
    new_row['TitleSC'] = get_label(row['_Title'], lang='sc')
    new_row['TitleTC'] = get_label(row['_Title'], lang='tc')
    new_row['Icon'] = 'data-sort-value ="{0}" | [[File:Icon_Profile_0{0}_Frame.png|28px|center]]'.format(row['_Rarity'])
    new_row['Text'] = get_label(row['_Gettext'])
    res = event_emblem_pattern.match(new_row['Text'])
    if res:
        new_row['Text'] = 'A reward from the [[{}]] event.'.format(res.group(1))

    existing_data.append((new_row['Title'], new_row))

def process_FortPlantDetail(row, existing_data, fort_plant_detail):
    try:
        fort_plant_detail[row['_AssetGroup']].append(row)
    except KeyError:
        fort_plant_detail[row['_AssetGroup']] = [row]

def process_FortPlantData(row, existing_data, fort_plant_detail):
    new_row = OrderedDict()

    new_row['Id'] = row[ROW_INDEX]
    new_row['Name'] = get_label(row['_Name'])
    new_row['Description'] = get_label(row['_Description'])
    new_row['Type'] = ''
    new_row['Size'] = '{w}x{w}'.format(w=row['_PlantSize'])
    new_row['Available'] = '1'
    new_row['Obtain'] = '' # EDIT_THIS
    new_row['ReleaseDate'] = '' # EDIT_THIS
    new_row['ShortSummary'] = '' # EDIT_THIS

    images = []
    upgrades = []
    upgrade_totals = {'Cost': 0, 'Build Time': 0, 'Materials': {}}
    for detail in fort_plant_detail[row[ROW_INDEX]]:
        if len(images) == 0 or images[-1][1] != detail['_ImageUiName']:
            images.append((detail['_Level'], detail['_ImageUiName']))
        if detail['_Level'] == '0':
            continue
        upgrade_row = OrderedDict()
        upgrade_row['Level'] = detail['_Level']
        # EffectId 1 for dojo, 2 for altars
        if detail['_EffectId'] != '0':
            # stat fac
            try:
                new_row['Type'] = FACILITY_EFFECT_TYPE_DICT[detail['_EffectId']]
            except KeyError:
                print(new_row['Name'])
            if detail['_EffectId'] == '4':
                upgrade_row['Bonus Dmg'] = detail['_EffArgs1']
            else:
                upgrade_row['HP +%'] = detail['_EffArgs1']
                upgrade_row['Str +%'] = detail['_EffArgs2']
        if detail['_EventEffectType'] != '0':
            # event fac
            upgrade_row['Damage +% {{Tooltip|(Event)|This Damage boost will only be active during its associated event and will disappear after the event ends.}}'] = detail['_EventEffectArgs']
        if detail['_MaterialMaxTime'] != '0':
            # dragontree
            upgrade_row['Prod Time'] = detail['_MaterialMaxTime']
            upgrade_row['Limit'] = detail['_MaterialMax']
            upgrade_row['Output Lv.'] = detail['_Odds'].replace('FortFruitOdds_', '')
        if detail['_CostMaxTime'] != '0':
            # rupee mine
            upgrade_row['Prod Time'] = detail['_CostMaxTime']
            upgrade_row['Limit'] = detail['_CostMax']
        upgrade_row['{{Rupies}}Cost'] = '{:,}'.format(int(detail['_Cost']))
        upgrade_totals['Cost'] += int(detail['_Cost'])
        mats = {}
        for i in range(1, 6):
            if detail['_MaterialsId' + str(i)] != '0':
                material_name = get_label(MATERIAL_NAME_LABEL + detail['_MaterialsId' + str(i)])
                mats[material_name] = int(detail['_MaterialsNum' + str(i)])
                try:
                    upgrade_totals['Materials'][material_name] += mats[material_name]
                except:
                    upgrade_totals['Materials'][material_name] = mats[material_name]
        upgrade_row['Materials Needed'] = mats
        if int(detail['_NeedLevel']) > 1:
            upgrade_row['Player Lv. Needed'] = detail['_NeedLevel']
        upgrade_row['Total Materials Left to Max Level'] = None
        upgrade_row['Build Time'] = '{{BuildTime|' + detail['_Time'] + '}}'
        upgrade_totals['Build Time'] += int(detail['_Time'])

        upgrades.append(upgrade_row)
    
    if len(images) > 1:
        new_row['Images'] = '{{#tag:tabber|\nLv' + \
            '\n{{!}}-{{!}}\n'.join(
            ['{}=\n[[File:{}.png|256px]]'.format(lvl, name) for lvl, name in images]) + \
            '}}'
    elif len(images) == 1:
        new_row['Images'] = '[[File:{}.png|256px]]'.format(images[0][1])
    else:
        new_row['Images'] = ''

    if len(upgrades) > 0:
        remaining = upgrade_totals['Materials'].copy()
        mat_delim = ', '
        for u in upgrades:
            if len(remaining) == 1:
                remaing_mats = []
                for k in remaining:
                    try:
                        remaining[k] -= u['Materials Needed'][k]
                    except KeyError:
                        pass
                    if remaining[k] > 0:
                        remaing_mats.append('{{{{{}-}}}} x{:,}'.format(k, remaining[k]))
                u['Total Materials Left to Max Level'] = 'style{{=}}"text-align:left" | ' + mat_delim.join(remaing_mats) if len(remaing_mats) > 0 else '—'
            else:
                del u['Total Materials Left to Max Level']

            current_mats = []
            for k, v in u['Materials Needed'].items():
                current_mats.append('{{{{{}-}}}} x{:,}'.format(k, v))
            u['Materials Needed'] = 'style{{=}}"text-align:left" | ' + mat_delim.join(current_mats) if len(current_mats) > 0 else '—'

        colspan = list(upgrades[0].keys()).index('{{Rupies}}Cost')
        total_mats = []
        for k, v in upgrade_totals['Materials'].items():
            total_mats.append('{{{{{}-}}}} x{:,}'.format(k, v))

        totals_row = ('|-\n| style{{=}}"text-align:center" colspan{{=}}"' + str(colspan) + '" | Total || '
                + '{:,}'.format(upgrade_totals['Cost']) + ' || style{{=}}"text-align:left" | ' + mat_delim.join(total_mats)
                + (' || style{{=}}"text-align:left" | —' if len(remaining) == 1 else '')
                + ' || {{BuildTime|' + str(upgrade_totals['Build Time']) + '}}\n')

        new_row['UpgradeTable'] = ('\n{{Wikitable|class="wikitable right" style="width:100%"\n! ' + ' !! '.join(upgrades[0].keys())
                + '\n' + ''.join(map((lambda r: row_as_wikitable(r)), upgrades)) + totals_row + '}}')
    else:
        new_row['UpgradeTable'] = ''
    existing_data.append((new_row['Name'], new_row))

def process_SkillData(row, existing_data):
    new_row = OrderedDict()
    max_skill_lv = 4

    new_row['SkillId']= row[ROW_INDEX]
    new_row['Name']= get_label(row['_Name'])
    new_row['SkillType']= row['_SkillType']
    for i in range(1, max_skill_lv + 1):
        si_k = 'SkillLv{}IconName'.format(i)
        new_row[si_k]= row['_'+si_k]
    for i in range(1, max_skill_lv + 1):
        des_k = 'Description{}'.format(i)
        new_row[des_k]= get_label(row['_'+des_k])
        new_row[des_k] = PERCENTAGE_REGEX.sub(r" '''\1%'''", new_row[des_k])
    new_row['MaxSkillLevel']= '' # EDIT_THIS

    # For Sp, SpLv2, SpLv3, SpEdit, SpDragon, etc fields
    for suffix in ('', 'Edit', 'Dragon'):
        for prefix in ['Sp'] + ['SpLv'+str(i) for i in range(2, max_skill_lv + 1)]:
            sp_key = prefix + suffix
            new_row[sp_key]= row['_' + sp_key]

    new_row['SpRegen']= '' # EDIT_THIS
    new_row['IsAffectedByTension']= row['_IsAffectedByTension']
    new_row['ZoominTime']= '{:.1f}'.format(float(row['_ZoominTime']))
    new_row['Zoom2Time']= '{:.1f}'.format(float(row['_Zoom2Time']))
    new_row['ZoomWaitTime']= '{:.1f}'.format(float(row['_ZoomWaitTime']))

    existing_data.append((new_row['Name'], new_row))

def process_MissionData(row, existing_data):
    new_row = [get_label(row['_Text'])]
    try:
        entity_type = MISSION_ENTITY_OVERRIDES_DICT[row['_EntityType']](row['_EntityId'])
        new_row.extend(entity_type + [row['_EntityQuantity']])
    except KeyError:
        entity_type = get_entity_item(row['_EntityType'], row['_EntityId'])
        new_row.extend([entity_type, row['_EntityQuantity']])
        pass

    existing_data.append((new_row[0], new_row))

def process_QuestData(row, existing_data):
    new_row = {}
    for quest_type, quest_type_pattern in QUEST_TYPE_DICT.items():
        if quest_type_pattern.match(row['_AreaName01']):
            new_row['QuestType'] = quest_type
            break
    new_row['Id'] = row[ROW_INDEX]
    # new_row['_Gid'] = row['_Gid']
    new_row['QuestGroupName'] = get_label(row['_QuestViewName']).partition(':')
    if not new_row['QuestGroupName'][1]:
        new_row['QuestGroupName'] = ''
    else:
        new_row['QuestGroupName'] = new_row['QuestGroupName'][0]
    try:
        new_row['GroupType'] = GROUP_TYPE_DICT[row['_GroupType']]
    except KeyError:
        pass
    new_row['EventName'] = get_label('EVENT_NAME_{}'.format(row['_Gid']))
    new_row['SectionName'] = get_label(row['_SectionName'])
    new_row['QuestViewName'] = get_label(row['_QuestViewName'])
    new_row['Elemental'] = ELEMENT_TYPE[row['_Elemental']]
    # new_row['ElementalId'] = int(row['_Elemental'])
    # process_QuestMight
    if row['_DifficultyLimit'] == '0':
        new_row['SuggestedMight'] = row['_Difficulty']
    else:
        new_row['MightRequirement'] = row['_DifficultyLimit']

    # process_QuestSkip
    if row['_SkipTicketCount'] == '1':
        new_row['SkipTicket'] = 'Yes'
    elif row['_SkipTicketCount'] == '-1':
        new_row['SkipTicket'] = ''

    new_row['NormalStaminaCost'] = row['_PayStaminaSingle']
    new_row['CampaignStaminaCost'] = row['_CampaignStaminaSingle']
    new_row['GetherwingCost'] = row['_PayStaminaMulti']
    new_row['CampaignGetherwingCost'] = row['_CampaignStaminaMulti']

    if row['_PayEntityType'] != '0':
        new_row['OtherCostType'] = get_entity_item(row['_PayEntityType'], row['_PayEntityId'])
        new_row['OtherCostQuantity'] = row['_PayEntityQuantity']

    new_row['ClearTermsType'] = get_label('QUEST_CLEAR_CONDITION_{}'.format(row['_ClearTermsType']))

    row_failed_terms_type = row['_FailedTermsType']
    row_failed_terms_type = "0" if row_failed_terms_type == "6" else row_failed_terms_type
    new_row['FailedTermsType'] = get_label('QUEST_FAILURE_CONDITON_{}'.format(row_failed_terms_type))
    if row['_FailedTermsTimeElapsed'] != '0':
        new_row['TimeLimit'] = row['_FailedTermsTimeElapsed']

    new_row['ContinueLimit'] = row['_ContinueLimit']
    new_row['RebornLimit'] = row['_RebornLimit']
    new_row['ThumbnailImage'] = row['_ThumbnailImage']
    new_row['DropRewards'] = ''
    new_row['WeaponRewards'] = ''
    new_row['WyrmprintRewards'] = ''
    new_row['ShowEnemies'] = 1
    new_row['AutoPlayType'] = row['_AutoPlayType']

    page_name = new_row['QuestViewName']
    if new_row.get('GroupType', '') == 'Campaign':
        if row['_VariationType'] == '1':
            page_name += '/Normal'
        elif row['_VariationType'] == '2':
            page_name += '/Hard'
        elif row['_VariationType'] == '3':
            page_name += '/Very Hard'
    elif new_row.get('GroupType', '') == 'Event':
        if new_row.get('QuestType', '') == 'Onslaught':
            quest_mode_suffix = f" ({new_row['EventName']})"
        else:
            quest_mode_suffix = QUEST_MODE_PLAY_TYPE_DICT.get(row['_QuestPlayModeType'], '')
        page_name += quest_mode_suffix
        new_row['QuestViewName'] += quest_mode_suffix

    existing_data.append((page_name, new_row))

def process_QuestRewardData(row, existing_data):
    QUEST_FIRST_CLEAR_COUNT = 5
    QUEST_COMPLETE_COUNT = 3
    reward_template = '\n{{{{DropReward|droptype=First|itemtype={}|item={}|exact={}}}}}'

    found = False
    for index,existing_row in enumerate(existing_data):
        if existing_row[1]['Id'] == row[ROW_INDEX]:
            found = True
            break
    assert(found)

    curr_row = existing_row[1]
    complete_type_dict = {
        '1' : (lambda x: 'Don\'t allow any of your team to fall in battle' if x == '0' else 'Allow no more than {} of your team to fall in battle'.format(x)),
        '15': (lambda x: 'Don\'t use any continues'),
        '18': (lambda x: 'Finish in {} seconds or less'.format(x)),
        '32': (lambda x: 'Don\'t use any revives'),
    }

    curr_row['FirstClearRewards'] = ''
    for i in range(1,QUEST_FIRST_CLEAR_COUNT+1):
        entity_type = row['_FirstClearSetEntityType{}'.format(i)]
        entity_id = row['_FirstClearSetEntityId{}'.format(i)]
        if entity_type != '0':
            curr_row['FirstClearRewards'] += reward_template.format(
                get_entity_item(entity_type, entity_id, format=2),
                get_entity_item(entity_type, entity_id),
                row['_FirstClearSetEntityQuantity{}'.format(i)])

    for i in range(1,QUEST_COMPLETE_COUNT+1):
        complete_type = row['_MissionCompleteType{}'.format(i)]
        complete_value = row['_MissionCompleteValues{}'.format(i)]
        clear_reward_type = row['_MissionsClearSetEntityType{}'.format(i)]

        entity_type = row['_MissionsClearSetEntityType{}'.format(i)]
        if entity_type != '0':
            curr_row['MissionCompleteType{}'.format(i)] = complete_type_dict[complete_type](complete_value)
            curr_row['MissionsClearSetEntityType{}'.format(i)] = get_entity_item(clear_reward_type, entity_type)
            curr_row['MissionsClearSetEntityQuantity{}'.format(i)] = row['_MissionsClearSetEntityQuantity{}'.format(i)]

    first_clear1_type = row['_FirstClearSetEntityType1']
    if first_clear1_type != '0':
        curr_row['MissionCompleteEntityType'] = get_entity_item(first_clear1_type, row['_MissionCompleteEntityType'])
        curr_row['MissionCompleteEntityQuantity'] = row['_MissionCompleteEntityQuantity']

    limit_break_material_id = row['_DropLimitBreakMaterialId']
    if limit_break_material_id != '0':
        curr_row['DropLimitBreakMaterial'] = get_entity_item('8', limit_break_material_id)
        curr_row['DropLimitBreakMaterialQuantity'] = row['_DropLimitBreakMaterialQuantity']
        curr_row['LimitBreakMaterialDailyDrop'] = row['_LimitBreakMaterialDailyDrop']

    existing_data[index] = (existing_row[0], curr_row)

def process_QuestBonusData(row, existing_data):

    found = False
    for index, existing_row in enumerate(existing_data):
        if '_Gid' not in existing_row[1]:
            found = False
            break
        if existing_row[1]['_Gid'] == row['_Id']:
            found = True
            break
    if not found:
        return

    curr_row = existing_row[1]
    if row['_QuestBonusType'] == '1':
        curr_row['DailyDropQuantity'] = row['_QuestBonusCount']
        curr_row['DailyDropReward'] = ''
    elif row['_QuestBonusType'] == '2':
        curr_row['WeeklyDropQuantity'] = row['_QuestBonusCount']
        curr_row['WeeklyDropReward'] = ''

    existing_data[index] = (existing_row[0], curr_row)

def process_UnionAbility(row, existing_data):
    new_row = OrderedDict()
    new_row['Id'] = row['_Id']
    new_row['Name'] = get_label(row['_Name'])
    new_row['IconEffect'] = row['_IconEffect']
    for i in range(1, 6):
        new_row[f'CrestGroup1Count{i}'] = row[f'_CrestGroup1Count{i}']
        new_row[f'AbilityId{i}'] = row[f'_AbilityId{i}']

    existing_data.append((None, new_row))

def process_WeaponBody(row):
    new_row = OrderedDict()

    new_row['Id'] = row['_Id']
    new_row['Name'] = get_label(row['_Name'])
    new_row['NameJP'] = get_label(row['_Name'], lang='jp')
    new_row['NameSC'] = get_label(row['_Name'], lang='sc')
    new_row['NameTC'] = get_label(row['_Name'], lang='tc')
    new_row['WeaponSeriesId'] = row['_WeaponSeriesId']
    new_row['WeaponSkinId'] = row['_WeaponSkinId']
    new_row['WeaponType'] = row['_WeaponType']
    new_row['Rarity'] = row['_Rarity']
    new_row['ElementalType'] = row['_ElementalType']
    new_row['Obtain'] = 'Crafting' if row['_CreateCoin'] != '0' else '' # EDIT_THIS
    new_row['MaxLimitOverCount'] = row['_MaxLimitOverCount']
    new_row['BaseHp'] = row['_BaseHp']
    new_row['MaxHp1'] = row['_MaxHp1']
    new_row['MaxHp2'] = row['_MaxHp2']
    new_row['MaxHp3'] = row['_MaxHp3']
    new_row['BaseAtk'] = row['_BaseAtk']
    new_row['MaxAtk1'] = row['_MaxAtk1']
    new_row['MaxAtk2'] = row['_MaxAtk2']
    new_row['MaxAtk3'] = row['_MaxAtk3']
    new_row['LimitOverCountPartyPower1'] = row['_LimitOverCountPartyPower1']
    new_row['LimitOverCountPartyPower2'] = row['_LimitOverCountPartyPower2']
    new_row['CrestSlotType1BaseCount'] = row['_CrestSlotType1BaseCount']
    new_row['CrestSlotType1MaxCount'] = row['_CrestSlotType1MaxCount']
    new_row['CrestSlotType2BaseCount'] = row['_CrestSlotType2BaseCount']
    new_row['CrestSlotType2MaxCount'] = row['_CrestSlotType2MaxCount']
    new_row['ChangeSkillId1'] = row['_ChangeSkillId1']
    new_row['ChangeSkillId2'] = row['_ChangeSkillId2']
    new_row['ChangeSkillId3'] = row['_ChangeSkillId3']
    new_row['Abilities11'] = row['_Abilities11']
    new_row['Abilities12'] = row['_Abilities12']
    new_row['Abilities13'] = row['_Abilities13']
    new_row['Abilities21'] = row['_Abilities21']
    new_row['Abilities22'] = row['_Abilities22']
    new_row['Abilities23'] = row['_Abilities23']
    new_row['IsPlayable'] = row['_IsPlayable']
    new_row['Text'] = get_label(row['_Text'])
    new_row['CreateStartDate'] = row['_CreateStartDate']
    new_row['NeedFortCraftLevel'] = row['_NeedFortCraftLevel']
    new_row['NeedCreateWeaponBodyId1'] = row['_NeedCreateWeaponBodyId1']
    new_row['NeedCreateWeaponBodyId2'] = row['_NeedCreateWeaponBodyId2']
    new_row['NeedAllUnlockWeaponBodyId1'] = row['_NeedAllUnlockWeaponBodyId1']
    new_row['CreateCoin'] = row['_CreateCoin']
    for i in range(1, 6):
        new_row[f'CreateEntity{i}'] = get_entity_item(row[f'_CreateEntityType{i}'], row[f'_CreateEntityId{i}'])
        new_row[f'CreateEntityQuantity{i}'] = row[f'_CreateEntityQuantity{i}']
    new_row['DuplicateEntity'] = get_entity_item(row['_DuplicateEntityType'], row['_DuplicateEntityId'])
    new_row['DuplicateEntityQuantity'] = row['_DuplicateEntityQuantity']
    new_row['WeaponPassiveAbilityGroupId'] = row['_WeaponPassiveAbilityGroupId']
    new_row['WeaponBodyBuildupGroupId'] = row['_WeaponBodyBuildupGroupId']
    new_row['MaxWeaponPassiveCharaCount'] = row['_MaxWeaponPassiveCharaCount']
    new_row['WeaponPassiveEffHp'] = row['_WeaponPassiveEffHp']
    new_row['WeaponPassiveEffAtk'] = row['_WeaponPassiveEffAtk']
    for i in range(1, 6):
        new_row[f'RewardWeaponSkinId{i}'] = row[f'_RewardWeaponSkinId{i}']

    return new_row

def process_WeaponSkin(row):
    new_row = OrderedDict()
    # set some initial ordering
    for x in ('Id', 'Name', 'NameJP', 'NameSC', 'NameTC', 'Text'):
        new_row[x] = ''
    copy_without_entriesKey(new_row, row)
    del new_row['DuplicateEntityType']
    del new_row['DuplicateEntityId']
    new_row['Name'] = get_label(row['_Name'])
    new_row['NameJP'] = get_label(row['_Name'], lang='jp')
    new_row['NameSC'] = get_label(row['_Name'], lang='sc')
    new_row['NameTC'] = get_label(row['_Name'], lang='tc')
    new_row['Text'] = get_label(row['_Text'])
    new_row['Obtain'] = ''
    new_row['Availability'] = ''
    new_row['ReleaseDate'] = ''
    new_row['DuplicateEntity'] = get_entity_item(row['_DuplicateEntityType'], row['_DuplicateEntityId'])
    return new_row

def process_Weapons(out_file):
    weapon_skins = db_query_all("SELECT * FROM WeaponSkin WHERE _Id!='0'")
    for skin in weapon_skins:
        skin_row = process_WeaponSkin(skin)
        skin_id = skin_row['Id']
        weapon = db_query_one(f"SELECT * FROM WeaponBody WHERE _WeaponSkinId='{skin_id}'")
        if weapon:
            weapon_row = process_WeaponBody(weapon)
            skin_row['HideDisplay'] = 1
            skin_row['Obtain'] = weapon_row['Obtain']
            skin_row['Availability'] = WEAPON_SERIES.get(weapon_row['WeaponSeriesId'], '')
            skin_row['ReleaseDate'] = weapon_row['CreateStartDate']

            out_file.write(weapon_row['Name'])
            out_file.write(ENTRY_LINE_BREAK)
            out_file.write(build_wikitext_row('Weapon', weapon_row, delim='\n|'))
        else:
            out_file.write(skin_row['Name'].replace(' (Skin)', ''))
            out_file.write(ENTRY_LINE_BREAK)

        out_file.write(build_wikitext_row('WeaponSkin', skin_row, delim='\n|'))
        out_file.write(ENTRY_LINE_BREAK)
 
def prcoess_QuestWallMonthlyReward(row, existing_data, reward_sum):
    new_row = OrderedDict()
    reward_entity_dict = {
        ('18', '0'): 'Mana',
        ('4', '0') : 'Rupies',
        ('14', '0'): 'Eldwater',
        ('8', '202004004') : 'Twinkling Sand',
    }
    reward_fmt = (lambda key, amount: '{{' + reward_entity_dict[key] + '-}}' + ' x {:,}'.format(amount))

    lvl = int(row['_TotalWallLevel'])
    try:
        reward_sum[lvl] = reward_sum[lvl - 1].copy()
    except:
        reward_sum[1] = {k: 0 for k in reward_entity_dict}
    reward_key = (row['_RewardEntityType'], row['_RewardEntityId'])
    reward_amount = int(row['_RewardEntityQuantity'])
    reward_sum[lvl][reward_key] += reward_amount
    new_row['Combined'] = row['_TotalWallLevel']
    new_row['Reward'] = 'data-sort-value="{}" | '.format(reward_key[0]) + reward_fmt(reward_key, reward_amount)
    new_row['Total Reward'] = ' '.join(
        [reward_fmt(k, v) for k, v in reward_sum[lvl].items() if v > 0]
    )

    existing_data.append((lvl, new_row))

def process_BuildEventReward(reader, outfile):
    table_header = ('|CollectionRewards=<div style="max-height:500px;overflow:auto;width:100%">\n'
                    '{{Wikitable|class="wikitable darkpurple sortable right" style="width:100%"\n'
                    '|-\n'
                    '! Item !! Qty !! {} Req.')
    row_divider = '\n|-\n| style{{=}}"text-align:left" | '
    events = defaultdict(list)

    for row in reader:
        if row['_Id'] == '0':
            continue
        event_item_qty = int(row['_EventItemQuantity'])
        reward_item = get_entity_item(row['_RewardEntityType'], row['_RewardEntityId'], format=0)
        events[row['_EntriesKey']].append({
            'evt_item_qty': event_item_qty,
            'row': ' || '.join((
                reward_item,
                f'{int(row["_RewardEntityQuantity"]):,}',
                f'{event_item_qty:,}',
                ))
        })

    for event_id in events:
        reward_list = sorted(events[event_id], key = lambda x: x['evt_item_qty'])

        outfile.write('{} - {}'.format(get_label('EVENT_NAME_' + event_id), event_id))
        outfile.write(ENTRY_LINE_BREAK)
        outfile.write(table_header)
        outfile.write(row_divider)
        outfile.write(row_divider.join((x['row'] for x in reward_list)))
        outfile.write('\n}}\n</div>')
        outfile.write(ENTRY_LINE_BREAK)

def process_RaidEventReward(reader, outfile):
    table_header = ('|-| {emblem_type}=\n'
                    '<div style="max-height:500px;overflow:auto;">\n'
                    '{{{{Wikitable|class="wikitable darkred sortable right" style="width:100%"\n'
                    '|-\n'
                    '! Item !! Qty !! Emblems Req.')
    row_divider = '\n|-\n| style{{=}}"text-align:left" | '
    events = defaultdict(lambda: defaultdict(list))

    for row in reader:
        if row['_Id'] == '0':
            continue
        event_item_qty = int(row['_RaidEventItemQuantity'])
        event_item_type = get_item_label('RaidEventItem', row['_RaidEventItemId']).replace(' Emblem', '')
        reward_item = get_entity_item(row['_RewardEntityType'], row['_RewardEntityId'], format=0)
        events[row['_EntriesKey']][event_item_type].append({
            'evt_item_qty': event_item_qty,
            'row': ' || '.join((
                reward_item,
                f'{int(row["_RewardEntityQuantity"]):,}',
                f'{event_item_qty:,}',
                ))
        })

    for event_id in events:
        outfile.write('{} - {}'.format(get_label('EVENT_NAME_' + event_id), event_id))
        outfile.write(ENTRY_LINE_BREAK)
        outfile.write('|CollectionRewards=<div style="width:100%">\n'
                      '<tabber>\n')

        for emblem_type in ('Bronze', 'Silver', 'Gold'):
            reward_list = sorted(events[event_id][emblem_type], key = lambda x: x['evt_item_qty'])
            outfile.write(table_header.format(emblem_type=emblem_type))
            outfile.write(row_divider)
            outfile.write(row_divider.join((x['row'] for x in reward_list)))
            outfile.write('\n}}\n</div>\n')

        outfile.write('</tabber>\n</div>')
        outfile.write(ENTRY_LINE_BREAK)

def process_CombatEventLocation(reader, outfile, reward_filename):
    events = defaultdict(dict)

    for row in reader:
        if row['_Id'] == '0':
            continue
        events[row['_EventId']][row['_LocationRewardId']] = {
            'Name': get_label(row['_LocationName']),
            'Rewards': [],
        }

    with open(reward_filename, 'r', newline='', encoding='utf-8') as in_file:
        rewards_reader = csv.DictReader(in_file)
        for row in rewards_reader:
            if row['_Id'] == '0':
                continue
            events[row['_EventId']][row['_LocationRewardId']]['Rewards'].append(
                '* {{{{{}-}}}} x{:,}'.format(get_entity_item(row['_EntityType'], row['_EntityId']), int(row['_EntityQuantity']))
            )

    for event_id, locations in events.items():
        outfile.write('{} - {}'.format(get_label('EVENT_NAME_' + event_id), event_id))
        outfile.write(ENTRY_LINE_BREAK)

        for location in locations.values():
            outfile.write('{}:\n'.format(location['Name']))
            outfile.write('\n'.join(location['Rewards']))
            outfile.write('\n')

        outfile.write(ENTRY_LINE_BREAK)

def process_LoginBonusData(out_file):
    bonuses = db_query_all(
        "SELECT _Id,_LoginBonusName,_StartTime,_EndTime,_EachDayEntityType,_EachDayEntityQuantity "
        "FROM LoginBonusData WHERE _Id != '0' ORDER BY _EndTime DESC")

    for bonus in bonuses:
        bonus_id = bonus['_Id']
        name = get_label(bonus['_LoginBonusName'])
        # Output format: September 27, 2019 06:00:00 UTC
        start_date = datetime.strptime(bonus['_StartTime'] + ' UTC', '%Y/%m/%d %H:%M:%S %Z').strftime('%B %d, %Y %X %Z').strip()
        end_date = datetime.strptime(bonus['_EndTime'] + ' UTC', '%Y/%m/%d %H:%M:%S %Z').strftime('%B %d, %Y %X %Z').strip()

        rewards = db_query_all(
            "SELECT _Id,_Gid,_Day,_EntityType,_EntityId,_EntityQuantity "
            f"FROM LoginBonusReward WHERE _Gid='{bonus_id}'")
        rewards = '\n'.join(login_bonus_reward_string(r) for r in rewards)

        out_file.write('===' + name + '===\n')
        out_file.write('[[File:Banner ' + name + '.png|300px|right]]\n')
        out_file.write('This login bonus was active from ' + start_date +  ' to ' + end_date + '.\n')
        out_file.write('{| class="wikitable"\n')
        out_file.write('! Day || Bonus\n')
        out_file.write(rewards)
        out_file.write('\n|}\n\n')

def login_bonus_reward_string(reward):
    return ''.join([
        '|-\n| Day ', reward['_Day'],
        ' || ', get_entity_item(reward['_EntityType'], reward['_EntityId'], format=0),
         ' x', reward['_EntityQuantity'],
      ])

def process_EndeavorSets(out_file):
    campaigns = db_query_all(
        "SELECT _Id,_CampaignName,_CampaignType,_StartDate,_EndDate "
        "FROM CampaignData WHERE _CampaignType='9' AND _Id != '0' ORDER BY _StartDate")

    for c in campaigns:
        campaign_id = c['_Id']
        start_date = c['_StartDate'] + ' UTC'
        end_date = c['_EndDate'] + ' UTC'
        month = datetime.strptime(start_date, '%Y/%m/%d %H:%M:%S %Z').strftime(' (%b %Y)')
        name = get_label(c['_CampaignName']) + month

        daily_endeavors = db_query_all(
            "SELECT _Id,_Text,_SortId,_EntityType,_EntityId,_EntityQuantity "
            f"FROM MissionDailyData WHERE _CampaignId='{campaign_id}' ORDER BY _SortId")
        limited_endeavors = db_query_all(
            "SELECT _Id,_Text,_SortId,_EntityType,_EntityId,_EntityQuantity "
            f"FROM MissionPeriodData WHERE _CampaignId='{campaign_id}' ORDER BY _SortId")

        if len(daily_endeavors):
            daily_set = {
                'Name': name,
                'Type': 'Daily',
                'Description': '',
                'StartDate': start_date,
                'EndDate': end_date,
                'Endeavors': '\n' + '\n'.join(endeavor_string(e, '(Daily) ') for e in daily_endeavors),
            }
            out_file.write(build_wikitext_row('EndeavorSet', daily_set, delim='\n|'))
            out_file.write('\n')
        if len(limited_endeavors):
            limited_set = {
                'Name': name,
                'Type': 'Limited',
                'Description': '',
                'StartDate': start_date,
                'EndDate': end_date,
                'Endeavors': '\n' + '\n'.join(endeavor_string(e) for e in limited_endeavors),
            }
            out_file.write(build_wikitext_row('EndeavorSet', limited_set, delim='\n|'))
        out_file.write('\n\n')

def process_EndeavorSetsEvents(out_file):
    events = db_query_all(
        "SELECT _Id,_Name,_StartDate,_EndDate FROM EventData "
        "WHERE _Id != '0' ORDER BY _StartDate")

    for e in events:
        event_id = e['_Id']
        start_date = e['_StartDate'] + ' UTC'
        end_date = e['_EndDate'] + ' UTC'
        month = datetime.strptime(start_date, '%Y/%m/%d %H:%M:%S %Z').strftime('%B %Y')
        name = get_label(e['_Name'])

        daily_endeavors = db_query_all(
            "SELECT _Id,_Text,_SortId,_EntityType,_EntityId,_EntityQuantity "
            f"FROM MissionDailyData WHERE _QuestGroupId='{event_id}' ORDER BY _SortId")
        limited_endeavors = db_query_all(
            "SELECT _Id,_Text,_SortId,_EntityType,_EntityId,_EntityQuantity "
            f"FROM MissionPeriodData WHERE _QuestGroupId='{event_id}' ORDER BY _SortId")
        memory_endeavors = db_query_all(
            "SELECT _Id,_Text,_SortId,_EntityType,_EntityId,_EntityQuantity "
            f"FROM MissionMemoryEventData WHERE _EventId='{event_id}' ORDER BY _SortId")

        if len(daily_endeavors):
            daily_set = {
                'Name': f'{name} ({month}) Daily Endeavors',
                'Event': f'{name}/{month}',
                'Type': 'EventDaily',
                'Description': '',
                'StartDate': start_date,
                'EndDate': end_date,
                'Endeavors': '\n' + '\n'.join(endeavor_string(e) for e in daily_endeavors),
            }
            out_file.write(build_wikitext_row('EndeavorSet', daily_set, delim='\n|'))
            out_file.write('\n')
        if len(limited_endeavors):
            limited_set = {
                'Name': f'{name} ({month}) Limited Endeavors',
                'Event': f'{name}/{month}',
                'Type': 'Event',
                'Description': '',
                'StartDate': start_date,
                'EndDate': end_date,
                'Endeavors': '\n' + '\n'.join(endeavor_string(e) for e in limited_endeavors),
            }
            out_file.write(build_wikitext_row('EndeavorSet', limited_set, delim='\n|'))
            out_file.write('\n')
        if len(memory_endeavors):
            limited_set = {
                'Name': f'{name} Compendium Endeavors',
                'Event': f'{name}/Event Compendium',
                'Type': 'Event',
                'Description': '',
                'StartDate': start_date,
                'Endeavors': '\n' + '\n'.join(endeavor_string(e) for e in memory_endeavors),
            }
            out_file.write(build_wikitext_row('EndeavorSet', limited_set, delim='\n|'))
        out_file.write('\n\n')

def endeavor_string(e, prefix=''):
    desc = get_label(e['_Text']).strip()
    quantity = e['_EntityQuantity']
    item_type = get_entity_item(e['_EntityType'], e['_EntityId'], format=2)
    item = get_entity_item(e['_EntityType'], e['_EntityId'], format=1)
    extras = ''

    if item_type == 'Epithet':
        rarity = get_epithet_rarity(e['_EntityId'])
        item_type += 'Rank' + rarity
    elif item_type == 'Sticker':
        extras = '|StickerID=' + e['_EntityId'] + '_en'

    return '|'.join([
        '{{EndeavorSetRow',
        prefix + desc,
        item_type,
        item,
        quantity + extras + '}}',
      ])

def process_GenericTemplateWithEntriesKey(row, existing_data):
    new_row = OrderedDict({k[1:]: v for k, v in row.items()})
    if 'EntriesKey1' in new_row:
        del new_row['EntriesKey1']
    existing_data.append((None, new_row))

def process_GenericTemplate(row, existing_data):
    new_row = OrderedDict()
    copy_without_entriesKey(new_row, row)
    existing_data.append((None, new_row))

def process_KeyValues(row, existing_data):
    new_row = OrderedDict()
    for k, v in row.items():
        if k == ROW_INDEX:
            new_row['Id'] = v
        elif 'Text' in k:
            label = get_label(v)
            if label != '':
                new_row[k[1:]] = v
                new_row[k[1:]+'Label'] = get_label(v)
        elif v != '0' and v != '':
            new_row[k[1:]] = v
    existing_data.append((None, new_row))

def build_wikitext_row(template_name, row, delim='|'):
    row_str = '{{' + template_name + delim
    if template_name in ORDERING_DATA:
        key_source = ORDERING_DATA[template_name]
    else:
        key_source = row.keys()
    row_str += delim.join(['{}={}'.format(k, row[k]) for k in key_source if k in row])
    if delim[0] == '\n':
        row_str += '\n'
    row_str += '}}'
    return row_str

def row_as_wikitext(row, template_name, display_name = None):
    text = ""
    if display_name is not None:
        text += display_name
        text += ENTRY_LINE_BREAK
        text += build_wikitext_row(template_name, row, delim='\n|')
        text += ENTRY_LINE_BREAK
    else:
        text += build_wikitext_row(template_name, row)
        text += '\n'
    return text

def row_as_wikitable(row, template_name=None, display_name=None, delim='|'):
    return '{0}-\n{0} {1}\n'.format(delim, ' {} '.format(delim*2).join([v for v in row.values()]))

def row_as_wikirow(row, template_name=None, display_name=None, delim='|'):
    return '{{' + template_name + '|' + delim.join(row) + '}}\n'

def row_as_kv_pairs(row, template_name=None, display_name=None, delim=': '):
    return '\n\t'.join([str(k)+delim+str(v) for k, v in row.items()]) + '\n'

def copy_without_entriesKey(new_row, row):
    for k, v in row.items():
        if 'EntriesKey' in k:
            continue
        new_row[k[1:]] = v

def db_query_one(query):
    db.execute(query)
    return db.fetchone()

def db_query_all(query):
    db.execute(query)
    return db.fetchall()

def row_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

DATA_PARSER_PROCESSING = {
    'AbilityLimitedGroup': ('AbilityLimitedGroup', row_as_wikitext, process_AbilityLimitedGroup),
    'CharaData': ('Adventurer', row_as_wikitext,
        [('CharaModeData', process_CharaModeData),
         ('CharaData', process_CharaData)]),
    # Must come after CharaData processing
    'AbilityData': ('Ability', row_as_wikitext,
        [('AbilityShiftGroup', process_AbilityShiftGroup),
         ('AbilityData', process_AbilityData)]),
    'AbilityCrest': ('Wyrmprint', row_as_wikitext, process_AbilityCrest),
    'AbilityCrestBuildupGroup': ('WyrmprintBuildupGroup', row_as_wikitext, process_GenericTemplate),
    'AbilityCrestBuildupLevel': ('WyrmprintBuildupLevel', row_as_wikitext, process_GenericTemplate),
    'AbilityCrestRarity': ('WyrmprintRarity', row_as_wikitext, process_GenericTemplate),
    'BattleRoyalEventItem': ('Material', row_as_wikitext, process_Material),
    'BuildEventItem': ('Material', row_as_wikitext, process_Material),
    'ChainCoAbility': ('ChainCoAbility', row_as_wikitext, [('AbilityData', process_ChainCoAbility)]),
    'Clb01EventItem': ('Material', row_as_wikitext, process_Material),
    'CollectEventItem': ('Material', row_as_wikitext, process_Material),
    'CombatEventItem': ('Material', row_as_wikitext, process_Material),
    'SkillData': ('Skill', row_as_wikitext, process_SkillData),
    'DragonData': ('Dragon', row_as_wikitext, process_Dragon),
    'ExAbilityData': ('CoAbility', row_as_wikitext, process_ExAbilityData),
    'EmblemData': ('Epithet', row_as_wikitable, process_EmblemData),
    'FortPlantData': ('Facility', row_as_wikitext,
        [('FortPlantDetail', process_FortPlantDetail),
         ('FortPlantData', process_FortPlantData)]),
    'MaterialData': ('Material', row_as_wikitext, process_Material),
    'RaidEventItem': ('Material', row_as_wikitext, process_Material),
    'SimpleEventItem': ('Material', row_as_wikitext, process_Material),
    'MissionDailyData': ('EndeavorRow', row_as_wikirow, process_MissionData),
    'MissionPeriodData': ('EndeavorRow', row_as_wikirow, process_MissionData),
    'MissionMainStoryData': ('EndeavorRow', row_as_wikirow, process_MissionData),
    'MissionMemoryEventData': ('EndeavorRow', row_as_wikirow, process_MissionData),
    'MissionNormalData': ('EndeavorRow', row_as_wikirow, process_MissionData),
    'QuestData': ('QuestDisplay', row_as_wikitext,
        [('QuestData', process_QuestData),
            ('QuestRewardData', process_QuestRewardData),
            ('QuestEvent', process_QuestBonusData),
        ]),
    'QuestWallMonthlyReward': ('Mercurial', row_as_wikitable, prcoess_QuestWallMonthlyReward),
    'ManaMaterial': ('MCMaterial', row_as_wikitext, process_GenericTemplate),
    'CharaLimitBreak': ('CharaLimitBreak', row_as_wikitext, process_GenericTemplate),
    'MC': ('MC', row_as_wikitext, process_GenericTemplateWithEntriesKey),
    'ManaPieceElement': ('ManaPieceElement', row_as_wikitext, process_GenericTemplate),
    'UnionAbility': ('AffinityBonus', row_as_wikitext, process_UnionAbility),
    'UseItem': ('Consumable', row_as_wikitext, process_Consumable),
    'WeaponBodyBuildupGroup': ('WeaponBodyBuildupGroup', row_as_wikitext, process_GenericTemplate),
    'WeaponBodyBuildupLevel': ('WeaponBodyBuildupLevel', row_as_wikitext, process_GenericTemplate),
    'WeaponBodyRarity': ('WeaponBodyRarity', row_as_wikitext, process_GenericTemplate),
    'WeaponPassiveAbility': ('WeaponPassiveAbility', row_as_wikitext, process_GenericTemplate),
}

# Data that cannot be structured into a simple row->template relationship, and
# will be parsed into a custom output format determined by each specific function.
NON_TEMPLATE_PROCESSING = {
    'BuildEventReward': (process_BuildEventReward,),
    'CombatEventLocation': (process_CombatEventLocation, 'CombatEventLocationReward'),
    'RaidEventReward': (process_RaidEventReward,),
}

# Data that cannot be structured into a simple row->template relationship, and
# will be parsed into a custom output format determined by each specific function.
DATABASE_BASED_PROCESSING = {
    'Weapons': (process_Weapons,),
    'LoginBonus': (process_LoginBonusData,),
    'Endeavor_Sets': (process_EndeavorSets,),
    'Endeavor_Sets-Events': (process_EndeavorSetsEvents,),
}

KV_PROCESSING = {
    'AbilityData': ('AbilityData', row_as_kv_pairs, process_KeyValues),
    'ActionCondition': ('ActionCondition', row_as_kv_pairs, process_KeyValues),
    'CampaignData': ('CampaignData', row_as_kv_pairs, process_KeyValues),
    'CharaModeData': ('CharaModeData', row_as_kv_pairs, process_KeyValues),
    'CharaUniqueCombo': ('CharaUniqueCombo', row_as_kv_pairs, process_KeyValues),
    'CommonActionHitAttribute': ('CommonActionHitAttribute', row_as_kv_pairs, process_KeyValues),
    'EnemyAbility': ('EnemyAbility', row_as_kv_pairs, process_KeyValues),
    'EnemyActionHitAttribute': ('EnemyActionHitAttribute', row_as_kv_pairs, process_KeyValues),
    'EnemyParam': ('EnemyParam', row_as_kv_pairs, process_KeyValues),
    'EventData': ('EventData', row_as_kv_pairs, process_KeyValues),
    'EventPassive': ('EventPassive', row_as_kv_pairs, process_KeyValues),
    'LoginBonusReward': ('LoginBonusReward', row_as_kv_pairs, process_KeyValues),
    'PlayerAction': ('PlayerAction', row_as_kv_pairs, process_KeyValues),
    'PlayerActionHitAttribute': ('PlayerActionHitAttribute', row_as_kv_pairs, process_KeyValues),
    'QuestData': ('QuestData', row_as_kv_pairs, process_KeyValues),
}

def process(input_dir='./', output_dir='./output-data', ordering_data_path=None, delete_old=False):
    global db, in_dir, ORDERING_DATA, SKILL_DATA_NAMES, EPITHET_RANKS
    if delete_old:
        if os.path.exists(output_dir):
            try:
                rmtree(output_dir)
                print('Deleted old {}'.format(output_dir))
            except Exception:
                print('Could not delete old {}'.format(output_dir))
    if ordering_data_path:
        with open(ordering_data_path, 'r') as json_ordering_fp:
            ORDERING_DATA = json.load(json_ordering_fp)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    in_dir = input_dir if input_dir[-1] == '/' else input_dir+'/'
    out_dir = output_dir if output_dir[-1] == '/' else output_dir+'/'

    # Set up in-memory sql database for all monos
    con = sqlite3.connect(':memory:')
    con.row_factory = row_factory
    db = con.cursor()

    for mono in glob.glob(f'{in_dir}*{EXT}'):
        with open(mono, encoding='utf-8', newline='') as file:
            table_name = os.path.basename(mono).replace(EXT, '')
            dialect = 'excel-tab' if 'TextLabel' in table_name else 'excel'
            reader = csv.reader(file, dialect=dialect)
            columns = next(reader)
            rows = [tuple(row) for row in reader]
            placeholder = ','.join(["?" for i in columns])

            db.execute(f'CREATE TABLE {table_name} ({",".join(columns)})')
            try:
                db.executemany(f'INSERT INTO {table_name} VALUES ({placeholder})', rows)
            except:
                print('Error in input csv: {}'.format(table_name))
                traceback.print_exc()
    con.commit()

    TEXT_LABEL_DICT['en'] = csv_as_index(in_dir+TEXT_LABEL+EXT, index='_Id', value_key='_Text', tabs=True)
    try:
        TEXT_LABEL_DICT['jp'] = csv_as_index(in_dir+TEXT_LABEL_JP+EXT, index='_Id', value_key='_Text', tabs=True)
        TEXT_LABEL_DICT['sc'] = csv_as_index(in_dir+TEXT_LABEL_SC+EXT, index='_Id', value_key='_Text', tabs=True)
        TEXT_LABEL_DICT['tc'] = csv_as_index(in_dir+TEXT_LABEL_TC+EXT, index='_Id', value_key='_Text', tabs=True)
    except:
        pass
    SKILL_DATA_NAMES = csv_as_index(in_dir+SKILL_DATA_NAME+EXT, index='_Id', value_key='_Name')
    EPITHET_RANKS = csv_as_index(in_dir+EPITHET_DATA_NAME+EXT, index='_Id', value_key='_Rarity')
    for item_type in ITEM_NAMES:
        ITEM_NAMES[item_type] = csv_as_index(in_dir+item_type+EXT, index='_Id', value_key='_Name')
    # find_fmt_params(in_dir, out_dir)

    for data_name, process_params in DATA_PARSER_PROCESSING.items():
        template, formatter, process_info = process_params
        parser = DataParser(data_name, template, formatter, process_info)
        parser.process()
        parser.emit(out_dir)
        print('Saved {}{}'.format(data_name, EXT))

    for data_name, process_params in DATABASE_BASED_PROCESSING.items():
        parser = DatabaseBasedParser(data_name, process_params)
        parser.process(out_dir)
        print('Saved {}{}'.format(data_name, EXT))

    for data_name, process_params in NON_TEMPLATE_PROCESSING.items():
        parser = CustomDataParser(data_name, process_params)
        parser.process(in_dir, out_dir)
        print('Saved {}{}'.format(data_name, EXT))

    kv_out = out_dir+'/kv/'
    if not os.path.exists(kv_out):
        os.makedirs(kv_out)
    for data_name, process_params in KV_PROCESSING.items():
        template, formatter, process_info = process_params
        parser = DataParser(data_name, template, formatter, process_info)
        parser.process()
        parser.emit(kv_out)
        print('Saved kv/{}{}'.format(data_name, EXT))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process CSV data into Wikitext.')
    parser.add_argument('-i', type=str, help='directory of input text files', default='./')
    parser.add_argument('-o', type=str, help='directory of output text files  (default: ./output-data)', default='./output-data')
    parser.add_argument('-j', type=str, help='path to json file with ordering', default='')
    parser.add_argument('--delete_old', help='delete older output files', dest='delete_old', action='store_true')

    args = parser.parse_args()
    process(input_dir=args.i, output_dir=args.o, ordering_data_path=args.j, delete_old=args.delete_old)
