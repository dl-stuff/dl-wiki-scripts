#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from collections import OrderedDict, defaultdict
import argparse
import csv
import os
import re

QUEST_NAME_REGEX = {
    re.compile(r'TUTORIAL_'): (lambda: 'Prologue'),
    re.compile(r'MAIN_(\d+)_(\d+)_E_'):
            (lambda x, y: 'Chapter {}: {}'.format(int(x), MAIN_DIFFICULTY.get(y, y))),
    re.compile(r'WALL_\d+_(\d+)_(\d+)_E_'):
            (lambda x, y: 'The Mercurial Gauntlet ({}): Lv. {}'.format(
                ELEMENTAL_TYPES.get(x.lstrip('0'), x), int(y))),
    re.compile(r'RARE_\d+_(\d+)_E(\d+)'):
            (lambda x, y: get_rare_enemy_quest_name(x,y)),

    # Simple TextLabel lookup.
    re.compile(r'EXP_\d+_(\d+)_E'):
            (lambda x: get_label('QUEST_NAME_2010101{}'.format(x))),
    re.compile(r'WEEKLY_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_202{}01{}'.format(x, y))),
    re.compile(r'DRAGONBATTLE_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_203{}01{}'.format(x, y))),
    re.compile(r'DRAGONBATTLE_ULT_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_210{}01{}'.format(
                    x, QUEST_DIFFICULTY_OVERRIDES['DRAGONBATTLE_ULT'].get(y, y)))),
    re.compile(r'EMPIRE_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_211{}01{}'.format(x, y))),
    re.compile(r'ASTRAL_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_217{}01{}'.format(x, y))),
    re.compile(r'AGITO_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_219{}01{}'.format(x, y))),
    re.compile(r'VOIDBATTLE_(\d+)_(\d+)_E'):
            (lambda x, y: get_label('QUEST_NAME_300{}01{}'.format(
                    QUEST_NAME_OVERRIDES['VOIDBATTLE'].get(x, x), y))),

    # QUEST_NAME_214010301 - front normal
    # CLB_01_01_11_E_01
    # QUEST_NAME_214010302 - hard
    # CLB_01_01_12_E_01
    # QUEST_NAME_214010303 - lunatic
    # CLB_01_01_13_E_01
    re.compile(r'CLB_01_01_1([1-3])_E_\d\d'): (lambda x: get_label('QUEST_NAME_21401030{}'.format(x))),
    # QUEST_NAME_214030601 - thorr normal
    # CLB_01_03_01_E_01
    # QUEST_NAME_214030602 - hard
    # CLB_01_03_02_E_01
    # QUEST_NAME_214030603 - lunatic
    # CLB_01_03_03_E_01
    re.compile(r'CLB_01_03_0([1-3])_E_\d\d'): (lambda x: get_label('QUEST_NAME_21403060{}'.format(x))),
    # CLB_01_03_08_E_01
    # CLB_01_03_09_E_01
    # CLB_01_03_10_E_01
    # CLB_01_03_23_E_01
    re.compile(r'CLB_01_03_(08|09|10|23)_E_\d\d'): (lambda x: get_label(f'QUEST_NAME_21403110{int(x)-7 if x != "23" else 4}')),
    # CLB_01_03_11_E_01
    # CLB_01_03_12_E_01
    # CLB_01_03_13_E_01
    # CLB_01_03_24_E_01
    re.compile(r'CLB_01_03_(11|12|13|24)_E_\d\d'): (lambda x: get_label(f'QUEST_NAME_21403120{int(x)-10 if x != "24" else 4}')),
    # CLB_01_03_14_E_01
    # CLB_01_03_15_E_01
    # CLB_01_03_16_E_01
    # CLB_01_03_25_E_01
    re.compile(r'CLB_01_03_(14|15|16|25)_E_\d\d'): (lambda x: get_label(f'QUEST_NAME_21403130{int(x)-13 if x != "25" else 4}')),
    # CLB_01_03_17_E_01
    # CLB_01_03_18_E_01
    # CLB_01_03_19_E_01
    # CLB_01_03_26_E_01
    re.compile(r'CLB_01_03_(17|18|19|26)_E_\d\d'): (lambda x: get_label(f'QUEST_NAME_21403140{int(x)-16 if x != "26" else 4}')),
    # CLB_01_03_20_E_01
    # CLB_01_03_21_E_01
    # CLB_01_03_22_E_01
    # CLB_01_03_27_E_01
    re.compile(r'CLB_01_03_(20|21|22|27)_E_\d\d'): (lambda x: get_label(f'QUEST_NAME_21403150{int(x)-19 if x != "27" else 4}')),
}
QUEST_NAME_OVERRIDES = {
    'VOIDBATTLE': {
        '10': '11',
        '11': '10',
    },
}
QUEST_DIFFICULTY_OVERRIDES = {
    'DRAGONBATTLE_ULT': {
        '01': '02',
        '04': '01',
        '05': '03',
        '06': '04',
    },
}
MAIN_DIFFICULTY = {
    '01': 'Normal',
    '02': 'Hard',
    '03': 'Very Hard',
}
RARE_ENEMY_QUESTS = {
    '01': 'Light Campaign / Avenue / Ruins Quests: Level ',
    '02': 'Water Campaign / Ruins Quests: Level ',
    '03': 'Wind Campaign / Ruins Quests: Level ',
    '04': 'Shadow Campaign / Avenue / Ruins Quests: Level ',
    '05': 'Flame Campaign / Ruins Quests: Level ',
}
TRIBES = {
    '0': 'None',
    '1': 'Thaumian',
    '2': 'Physian',
    '3': 'Demihuman',
    '4': 'Therion',
    '5': 'Undead',
    '6': 'Demon',
    '7': 'Human',
    '8': 'Dragon',
}
ELEMENTAL_TYPES = {
    '1': 'Flame',
    '2': 'Water',
    '3': 'Wind',
    '4': 'Light',
    '5': 'Shadow',
    '99': '', # None
}

class Enemy:
    def __init__(self, enemy_param, enemy_data, enemy_list, weapon_data):
        ep = enemy_param
        ed = enemy_data[ep['_DataId']]
        el = enemy_list[ed['_BookId']]

        data = OrderedDict()
        data['Id'] = ep['_Id']
        data['DataId'] = ep['_DataId']
        data['Name'] = get_label(el['_Name'])
        data['ModelId'] = get_model_name(ed)
        data['RareStayTime'] = ep['_RareStayTime']
        data['HP'] = ep['_HP']
        data['Atk'] = ep['_Atk']
        data['Def'] = ep['_Def']
        data['Overwhelm'] = ep['_Overwhelm']
        data['BaseOD'] = ep['_BaseOD']
        data['BaseBreak'] = ep['_BaseBreak']
        data['CounterRate'] = ep['_CounterRate']
        data['BarrierRate'] = ep['_BarrierRate']
        data['GetupActionRate'] = ep['_GetupActionRate']
        data['Poison'] = ep['_RegistAbnormalRate01']
        data['Burn'] = ep['_RegistAbnormalRate02']
        data['Freeze'] = ep['_RegistAbnormalRate03']
        data['Paralysis'] = ep['_RegistAbnormalRate04']
        data['Blind'] = ep['_RegistAbnormalRate05']
        data['Stun'] = ep['_RegistAbnormalRate06']
        data['Bog'] = ep['_RegistAbnormalRate07']
        data['Sleep'] = ep['_RegistAbnormalRate08']
        data['Curse'] = ep['_RegistAbnormalRate09']
        data['Frostbite'] = ep['_RegistAbnormalRate10']
        data['PartsA'] = ep['_PartsA']
        data['PartsB'] = ep['_PartsB']
        data['PartsC'] = ep['_PartsC']
        data['PartsD'] = ep['_PartsD']
        data['PartsNode'] = ep['_PartsNode']
        # data['CrashedHPRate'] = ep['_CrashedHPRate'] # Currently unused
        data['MissionType'] = get_enemy_quest_name(ep['_ParamGroupName'])
        data['MissionDifficulty'] = ''    # Currently unused
        data['Tribe'] = TRIBES.get(el['_TribeType'], el['_TribeType'])
        data['Weapon'] = get_label(weapon_data.get(ed['_WeaponId'], ''))
        data['ElementalType'] = ELEMENTAL_TYPES.get(ed['_ElementalType'])
        data['BreakDuration'] = ed['_BreakDuration']
        data['MoveSpeed'] = ed['_MoveSpeed']
        data['TurnSpeed'] = ed['_TurnSpeed']
        data['SuperArmor'] = ed['_SuperArmor']
        data['BreakAtkRate'] = ed['_BreakAtkRate']
        data['BreakDefRate'] = ed['_BreakDefRate']
        data['ODAtkRate'] = ed['_ObAtkRate']
        data['ODDefRate'] = ed['_ObDefRate']
        data['Ability01'] = ep['_Ability01']
        data['Ability02'] = ep['_Ability02']
        data['Ability03'] = ep['_Ability03']
        data['Ability04'] = ep['_Ability04']
        self.data = data

    def summary(self):
        return ''.join([
                'Id: ', self.data['Id'],
                ', DataId: ', self.data['DataId'],
                ', ModelId: ', self.data['ModelId'],
                '\n\tName: ', self.data['Name'],
                '\n\tQuest: ', self.data['MissionType'],
                '\n\tTribe: ', self.data['Tribe'],
                '\n\tElement: ', self.data['ElementalType'],
                '\n\tHP: ', self.data['HP'], ', ATK: ', self.data['Atk'],
            ])

    def __repr__(self):
        for item in self.data.items():
            for i in item:
                if isinstance(i, dict):
                    print(i)

        return ''.join([
                '{{EnemyData|',
                '|'.join('='.join(item) for item in self.data.items()),
                '}}',
            ])

def get_label(label, default=''):
    return TEXT_LABEL.get(label, default) or default

def get_enemy_quest_name(group_name):
    for pattern in QUEST_NAME_REGEX:
        match = pattern.match(group_name)
        if match:
            return QUEST_NAME_REGEX[pattern](*match.groups())
    return MANUAL_QUEST_MAP.get(group_name, '')

def get_rare_enemy_quest_name(x, y):
    x = int(x)
    if x == 0:
        return 'Campaign / Avenue / Ruins Quests'
    else:
        return RARE_ENEMY_QUESTS[y] + str(x)

# Categories whose 3D model resource IDs depend on their Base and Variation IDs
BASE_VARIATION_PREFIXES = {
    '3': 'd',
    '5': 'c',
}
# Categories whose 3D model resource IDs depend on their BookIds
BOOK_PREFIXES = {
    '1': 'e',
    '2': 'b',
    '4': 'r',
    '7': 'h',
    '9': 'o',
}
def get_model_name(ed):
    category = ed['_Category']
    if category in BOOK_PREFIXES:
        return BOOK_PREFIXES[category] + ed['_BookId'][-7:]
    elif category in BASE_VARIATION_PREFIXES:
        return '{}{}_{}'.format(BASE_VARIATION_PREFIXES[category],
                                ed['_BaseId'], ed['_VariationId'].zfill(2))
    else:
        return ''


def csv_to_dict(path, index=None, value_key=None, tabs=False):
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
            value_key = keys[-1] # get second key
        if value_key:
            return {row[index]: row[value_key] for row in reader if row[index] != '0'}
        else:
            # load >2 column files as a dict[string] = OrderedDict
            return {row[index]: row for row in reader if row[index] != '0'}

def parse(input_dir, output_dir='EnemyData',
          manual_map_file_path='./ManualMapRelations.txt', text_label_dict=None):
    global MANUAL_QUEST_MAP, TEXT_LABEL 
    enemy_param = csv_to_dict(os.path.join(input_dir, 'EnemyParam.txt'), index='_Id')
    enemy_data = csv_to_dict(os.path.join(input_dir, 'EnemyData.txt'), index='_Id')
    enemy_list = csv_to_dict(os.path.join(input_dir, 'EnemyList.txt'), index='_Id')
    weapon_data = csv_to_dict(os.path.join(input_dir, 'WeaponData.txt'), index='_Id', value_key='_Name')
    MANUAL_QUEST_MAP = csv_to_dict(manual_map_file_path, tabs=True)
    if text_label_dict:
        TEXT_LABEL = text_label_dict
    else:
        TEXT_LABEL = csv_to_dict(os.path.join(input_dir, 'TextLabel.txt'), index='_Id', value_key='_Text', tabs=True)

    enemies_set = set()
    tribes = defaultdict(list)
    enemies_count = 0
    questless = []
    for enemy_param in enemy_param.values():
        enemy = Enemy(enemy_param, enemy_data, enemy_list, weapon_data)

        if not enemy.data['MissionType']:
            questless.append('{}: {}'.format(enemy_param['_ParamGroupName'], enemy.summary()))
        else:
            try:
                enemies_set.add(enemy.data['Name'])
            except Exception as e:
                print(e)
                print(enemy.data['Name'])
            tribes[enemy.data['Tribe']].append(enemy)
            enemies_count += 1

    os.makedirs(output_dir, exist_ok=True)

    for tribe, enemies in tribes.items():
        output_path = os.path.join(output_dir, tribe + '.txt')
        print(output_path)
        # Sort the enemies alphabetically by name
        enemies.sort(key=lambda x: x.data.get('Name', ''))
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write('\n'.join((str(e) for e in enemies)))

    if questless:
        with open(os.path.join(output_dir, '_MISSING_NAMES.txt'), 'w', encoding='utf-8') as outfile:
            if questless:
                outfile.write('Missing Quest Name Mapping\n')
                outfile.write('==========================\n')
                outfile.write('\n'.join((e for e in questless)))

    # Lastly, print the summary
    with open(os.path.join(output_dir, '_Summary.txt'), 'w', encoding='utf-8') as outfile:
        outfile.write('Total Enemy Entries: ' + str(enemies_count))
        outfile.write('\nUnique Enemy Names: ' + str(len(enemies_set)))
        outfile.write('\nEnemy Names\n')
        outfile.write('===========\n')
        outfile.write('\n'.join(sorted(enemies_set)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Enemy CSV data into Wikitext.')
    parser.add_argument('-i', type=str, help='directory of input text files  (default: ./)', default='./')
    parser.add_argument('-o', type=str, help='directory of output text files  (default: ./EnemyData)', default='./EnemyData')
    parser.add_argument('-map', type=str, help='path to ManualMapRelations.txt  (default: ./)', default='./')

    args = parser.parse_args()
    input_dir = args.i
    output_dir = args.o
    map_file = os.path.join(args.map, 'ManualMapRelations.txt')
    parse(input_dir, output_dir, map_file)
