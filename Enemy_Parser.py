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

    # Phraeganoth
    re.compile(r'RAID_01_0([56])_E_(\d)\d'): (lambda x, y: get_label(f'QUEST_NAME_204200{x}0{int(y)+1}')),

    # Timeworn Torment
    re.compile(r'RAID_10_01_E_0\d'): (lambda: get_label(f'QUEST_NAME_204100301')),
    re.compile(r'RAID_10_03_E_0\d'): (lambda: get_label(f'QUEST_NAME_204100302')),
    re.compile(r'RAID_10_04_E_0\d'): (lambda: get_label(f'QUEST_NAME_204100401')),
    re.compile(r'RAID_10_05_E_0\d'): (lambda: get_label(f'QUEST_NAME_204100501')),
    re.compile(r'RAID_10_06_E_0\d'): (lambda: get_label(f'QUEST_NAME_204100601')),
    re.compile(r'RAID_10_06_E_1\d'): (lambda: get_label(f'QUEST_NAME_204100602')),
    re.compile(r'RAID_10_06_E_2\d'): (lambda: get_label(f'QUEST_NAME_204100603')),
    re.compile(r'RAID_10_01_E_18'): (lambda: get_label(f'QUEST_NAME_204100201')),
    re.compile(r'RAID_10_03_E_11'): (lambda: get_label(f'QUEST_NAME_204100202')),
    re.compile(r'RAID_10_01_E_1[1-3]'): (lambda: get_label(f'QUEST_NAME_204100101')),
    re.compile(r'RAID_10_01_E_1[4-7]'): (lambda: get_label(f'QUEST_NAME_204100102')),

    # Doomsday Getaway
    re.compile(r'RAID_09_01_E_0\d'): (lambda: get_label(f'QUEST_NAME_204090301')), # Scylla Clash: Beginner
    re.compile(r'RAID_09_03_E_0\d'): (lambda: get_label(f'QUEST_NAME_204090302')), # Scylla Clash: Expert
    re.compile(r'RAID_09_04_E_0\d'): (lambda: get_label(f'QUEST_NAME_204090401')), # Scylla Clash EX
    re.compile(r'RAID_09_05_E_0\d'): (lambda: get_label(f'QUEST_NAME_204090501')), # Scylla Clash: Nightmare
    re.compile(r'RAID_09_06_E_0\d'): (lambda: get_label(f'QUEST_NAME_204090601')), # Scylla Clash: Omega (Solo)
    re.compile(r'RAID_09_06_E_1\d'): (lambda: get_label(f'QUEST_NAME_204090602')), # Scylla Clash: Omega Level 1 (Raid)
    re.compile(r'RAID_09_06_E_2\d'): (lambda: get_label(f'QUEST_NAME_204090603')), # Scylla Clash: Omega Level 2 (Raid)
    re.compile(r'RAID_09_01_E_11'): (lambda: get_label(f'QUEST_NAME_204090201')),  # Assault on Admiral Pincers: Beginner
    re.compile(r'RAID_09_03_E_11'): (lambda: get_label(f'QUEST_NAME_204090202')),  # Assault on Admiral Pincers: Expert

    # Rhythmic Resolution
    re.compile(r'BUILD_23_01_E_0\d'): (lambda: get_label(f'QUEST_NAME_208230101')),
    re.compile(r'BUILD_23_02_E_0\d'): (lambda: get_label(f'QUEST_NAME_208230102')),
    re.compile(r'BUILD_23_03_E_(\d)\d'): (lambda x: get_label(f'QUEST_NAME_20823030{int(x)+1}')),
    re.compile(r'BUILD_23_04_E_\d\d'): (lambda: get_label(f'QUEST_NAME_208230401')),
    re.compile(r'BUILD_23_05_E_[01]\d'): (lambda: get_label(f'QUEST_NAME_208230501')),
    re.compile(r'BUILD_23_05_E_[23]\d'): (lambda: get_label(f'QUEST_NAME_208230502')),
    re.compile(r'BUILD_23_05_E_[45]\d'): (lambda: get_label(f'QUEST_NAME_208230601')),

    # Nadine & Linnea (hecc)
    re.compile(r'COMBAT_01_0([1-3])_E_\d\d'): (lambda x: get_label(f'QUEST_NAME_222010{x}03')),
    re.compile(r'COMBAT_01_04_E_(\d\d)'): (lambda x: get_label(f'QUEST_NAME_22201040{3 if int(x) < 30 else 4}')),
    re.compile(r'COMBAT_01_05_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010101')),
    re.compile(r'COMBAT_01_06_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010102')),
    re.compile(r'COMBAT_01_07_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010201')),
    re.compile(r'COMBAT_01_08_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010202')),
    re.compile(r'COMBAT_01_09_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010301')),
    re.compile(r'COMBAT_01_10_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010302')),
    re.compile(r'COMBAT_01_11_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010401')),
    re.compile(r'COMBAT_01_12_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010402')),

    # Summertime Saviors
    re.compile(r'COMBAT_02_0([1-4])_E_\d\d'): (lambda x: get_label(f'QUEST_NAME_222020{x}03')+' (Summertime_Saviors)'),
    re.compile(r'COMBAT_02_05_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222020404')+' (Summertime_Saviors)'),
    re.compile(r'COMBAT_02_06_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010101')+' (Summertime Saviors)'),
    re.compile(r'COMBAT_02_07_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010102')+' (Summertime Saviors)'),
    re.compile(r'COMBAT_02_08_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010201')+' (Summertime Saviors)'),
    re.compile(r'COMBAT_02_09_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010202')+' (Summertime Saviors)'),
    re.compile(r'COMBAT_02_10_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010301')+' (Summertime Saviors)'),
    re.compile(r'COMBAT_02_11_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010302')+' (Summertime Saviors)'),
    re.compile(r'COMBAT_02_12_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010401')+' (Summertime Saviors)'),
    re.compile(r'COMBAT_02_13_E_\d\d'): (lambda: get_label(f'QUEST_NAME_222010402')+' (Summertime Saviors)'),

    # FEH collab
    re.compile(r'CLB_01_01_1([1-3])_E_\d\d'): (lambda x: get_label('QUEST_NAME_21401030{}'.format(x))),
    re.compile(r'CLB_01_03_0([1-3])_E_\d\d'): (lambda x: get_label('QUEST_NAME_21403060{}'.format(x))),
    re.compile(r'CLB_01_03_(08|09|10|23)_E_\d\d'): (lambda x: get_label(f'QUEST_NAME_21403110{int(x)-7 if x != "23" else 4}')),
    re.compile(r'CLB_01_03_(11|12|13|24)_E_\d\d'): (lambda x: get_label(f'QUEST_NAME_21403120{int(x)-10 if x != "24" else 4}')),
    re.compile(r'CLB_01_03_(14|15|16|25)_E_\d\d'): (lambda x: get_label(f'QUEST_NAME_21403130{int(x)-13 if x != "25" else 4}')),
    re.compile(r'CLB_01_03_(17|18|19|26)_E_\d\d'): (lambda x: get_label(f'QUEST_NAME_21403140{int(x)-16 if x != "26" else 4}')),
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
        data['ParamGroupName'] = ep['_ParamGroupName']
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
            name = QUEST_NAME_REGEX[pattern](*match.groups())
            return name
    return ''

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
BOOK_GROUP_PREFIXES = {
    'ENM': 'e',
    'BOS': 'b',
    'RID': 'r',
    'HBS': 'h',
    'EOJ': 'o',
}
def get_model_name(ed):
    category = ed['_Category']
    group = ed['_EnemyGroupName'].split('_', 1)[0]
    if category == '0':
        return ''
    elif category in BASE_VARIATION_PREFIXES:
        return '{}{}_{}'.format(BASE_VARIATION_PREFIXES[category],
                                ed['_BaseId'], ed['_VariationId'].zfill(2))
    elif group in BOOK_GROUP_PREFIXES:
        return BOOK_GROUP_PREFIXES[group] + ed['_BookId'][-7:]
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

def parse(input_dir, output_dir='EnemyData', text_label_dict=None):
    global TEXT_LABEL 
    enemy_param = csv_to_dict(os.path.join(input_dir, 'EnemyParam.txt'), index='_Id')
    enemy_data = csv_to_dict(os.path.join(input_dir, 'EnemyData.txt'), index='_Id')
    enemy_list = csv_to_dict(os.path.join(input_dir, 'EnemyList.txt'), index='_Id')
    weapon_data = csv_to_dict(os.path.join(input_dir, 'WeaponData.txt'), index='_Id', value_key='_Name')
    if text_label_dict:
        TEXT_LABEL = text_label_dict
    else:
        TEXT_LABEL = csv_to_dict(os.path.join(input_dir, 'TextLabel.txt'), index='_Id', value_key='_Text', tabs=True)

    enemies_set = set()
    tribes = defaultdict(list)
    enemies_count = 0
    for enemy_param in enemy_param.values():
        enemy = Enemy(enemy_param, enemy_data, enemy_list, weapon_data)

        if enemy_param['_ParamGroupName'].startswith('DEBUG'):
            # We think these were left in by accident, hide them from the output
            continue

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

    args = parser.parse_args()
    input_dir = args.i
    output_dir = args.o
    parse(input_dir, output_dir, map_file)
