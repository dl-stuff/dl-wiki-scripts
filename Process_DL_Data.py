import csv
import os
import string
from shutil import copyfile, rmtree
from collections import OrderedDict
import argparse

EXT = '.txt'
DEFAULT_TEXT_LABEL = ''
ENTRY_LINE_BREAK = '\n=============================\n'
EDIT_THIS = '<EDIT_THIS>'

ROW_INDEX = '_Id'

TEXT_LABEL_NAME = 'TextLabel'
TEXT_LABELS = None
ABILITY_SHIFT_GROUP_NAME = 'AbilityShiftGroup'
ABILITY_SHIFT_GROUPS = None

ROMAN_NUMERALS = [None, 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
ELEMENTS = [None, 'Flame', 'Water', 'Wind', 'Light', 'Shadow']
AMULET_TYPE = [None, 'Attack', 'Defense', 'Support', 'Healing']

def csv_as_index(path, index=None, tabs=False):
    with open(path, newline='') as csvfile:
        if tabs:
            reader = csv.DictReader(csvfile, dialect='excel-tab')
        else:
            reader = csv.DictReader(csvfile)
        first_row = next(reader)
        key_iter = iter(first_row.keys())
        csvfile.seek(0)
        if not index:
            index = next(key_iter) # get first key as index
        if len(first_row) == 2:
            # load 2 column files as dict[string] = string
            value_key = next(key_iter) # get second key
            return {row[index]: row[value_key] for row in reader if row[index] != '0'}
        else:
            # load >2 column files as a dict[string] = OrderedDict
            return {row[index]: row for row in reader if row[index] != '0'}

def get_label(key):
    return TEXT_LABELS[key].replace('\\n', ' ') if key in TEXT_LABELS else DEFAULT_TEXT_LABEL

# All process_* functions take in 1 parameter (OrderedDict row) and return 3 values (OrderedDict new_row, str template_name, str display_name)
# Make sure the keys are added to the OrderedDict in the desired output order
# It's alright to modify row instead of makeing new dict, but only do so when you want to print all the keys already present in row
def process_AbilityLimitedGroup(row):
    row['_AbilityLimitedText'] = get_label(row['_AbilityLimitedText']).format(ability_limit0=row['_MaxLimitedValue'])
    return row, None, None

def process_AbilityData(row):
    new_row = OrderedDict()

    new_row['Id'] = row['_Id']
    new_row['PartyPowerWeight'] = row['_PartyPowerWeight']
    new_row['GenericName'] = '' # EDIT_THIS

    shift_value = ROMAN_NUMERALS[int(row['_ShiftGroupId'])]
    if row['_ShiftGroupId'] in ABILITY_SHIFT_GROUPS:
        shift_group_row = ABILITY_SHIFT_GROUPS[row['_ShiftGroupId']]
        for k, v in shift_group_row.items():
            if k.startswith('_Level') and v == row['_Id']:
                shift_value = ROMAN_NUMERALS[int(k.replace('_Level', ''))]
    # TODO: figure out what actually goes here
    ability_value = EDIT_THIS if row['_AbilityType1UpValue'] == '0' else row['_AbilityType1UpValue']
    new_row['Name'] = get_label(row['_Name']).format(
        ability_shift0  =   shift_value,
        ability_val0    =   ability_value)

    # _ElementalType seems unreliable, use (element) in _Name for now
    detail_label = get_label(row['_Details'])
    if '{element_owner}' in detail_label and ')' in new_row['Name']:
        element = new_row['Name'][1:new_row['Name'].index(')')]
    else:
        element = ELEMENTS[int(row['_ElementalType'])]
    new_row['Details'] = detail_label.format(
        ability_cond0   =   row['_ConditionValue'],
        ability_val0    =   ability_value,
        element_owner   =   element)

    new_row['AbilityIconName'] = row['_AbilityIconName']
    new_row['AbilityGroup'] = row['_ViewAbilityGroupId1']
    new_row['AbilityLimitedGroupId1'] = row['_AbilityLimitedGroupId1']
    new_row['AbilityLimitedGroupId2'] = row['_AbilityLimitedGroupId2']
    new_row['AbilityLimitedGroupId3'] = row['_AbilityLimitedGroupId3']
    return new_row, 'Ability', new_row['Name']

def process_AmuletData(row):
    new_row = OrderedDict()

    new_row['Id'] = row['_Id']
    new_row['BaseId'] = row['_BaseId']
    new_row['Name'] = get_label(row['_Name'])
    new_row['NameJP'] = '' # EDIT_THIS
    new_row['FeaturedCharacters'] = '' # EDIT_THIS
    new_row['Obtain'] = '' # EDIT_THIS
    new_row['ReleaseDate'] = '' # EDIT_THIS
    new_row['Availability'] = '' # EDIT_THIS
    new_row['Rarity'] = row['_Rarity']
    new_row['AmuletType'] = AMULET_TYPE[int(row['_AmuletType'])]
    new_row['MinHp'] = row['_MinHp']
    new_row['MaxHp'] = row['_MaxHp']
    new_row['MinAtk'] = row['_MinAtk']
    new_row['MaxAtk'] = row['_MaxAtk']
    new_row['VariationId'] = row['_VariationId']
    for i in range(1, 4):
        for j in range(1, 4):
            ab = 'Abilities{}{}'.format(i, j)
            new_row[ab] = row['_' + ab]
    new_row['Ability1Event'] = 0
    new_row['Ability2Event'] = 0
    new_row['Ability3Event'] = 0
    new_row['ArtistCV'] = '' # EDIT_THIS
    for i in range(1, 6):
        new_row['FlavorText{}'.format(i)] = get_label(row['_Text{}'.format(i)])
    new_row['IsPlayable'] = row['_IsPlayable']
    new_row['SellCoin'] = row['_SellCoin']
    new_row['SellDewPoint'] = row['_SellDewPoint']

    return new_row, 'Wyrmprint', new_row['Name']

def process_BuildEventItem(row):
    new_row = OrderedDict()

    new_row['Id'] = row['_Id']
    new_row['Name'] = get_label(row['_Name'])
    new_row['Description'] = get_label(row['_Detail'])
    new_row['Rarity'] = '' # EDIT_THIS
    new_row['QuestEventId'] = row['_EventId']
    new_row['SortId'] = row['_Id']
    new_row['Obtain'] = '\n*' + get_label(row['_Description'])
    new_row['Usage'] = '' # EDIT_THIS
    new_row['MoveQuest1'] = row['_MoveQuest1']
    new_row['MoveQuest2'] = row['_MoveQuest2']
    new_row['MoveQuest3'] = row['_MoveQuest3']
    new_row['MoveQuest4'] = row['_MoveQuest4']
    new_row['MoveQuest5'] = row['_MoveQuest5']
    new_row['PouchRarity'] = row['_PouchRarity']

    return new_row, 'Material', new_row['Name']

DATA_FILE_PROCESSING = {
    'AbilityLimitedGroup': process_AbilityLimitedGroup,
    'AbilityData': process_AbilityData,
    'AmuletData': process_AmuletData, # AKA Wyrmprint
    'BuildEventItem': process_BuildEventItem,
    'CharaData': None,
    'ExAbilityData': None,
    'CollectEventItem': None,
    'MissionDailyData': None,
    'DragonData': None,
    'EmblemData': None,
    'EnemyData': None,
    'EventData': None,
    'FortPlantData': None,
    'MaterialData': None,
    'MissionNormalData': None,
    'MissionPeriodData': None,
    'QuestClearType': None,
    'QuestData': None,
    'QuestEvent': None,
    'QuestEventGroup': None,
    'QuestFailedType': None,
    'QuestRewardData': None,
    'RaidEventItem': None,
    'SkillData': None,
    'WeaponData': None,
    'WeaponCraftData': None,
    'WeaponCraftTree': None,
}

def build_wikitext_row(template_name, row, delim='|'):
    row_str = '{{' + template_name + delim
    row_str += delim.join(['{}={}'.format(k.strip('_'), row[k]) for k in row])
    if delim[0] == '\n':
        row_str += '\n'
    row_str += '}}'
    return row_str

def csv_as_wikitext(in_dir, out_dir, data_name):
    with open(in_dir+data_name+EXT, 'r') as in_file, open(out_dir+data_name+EXT, 'w') as out_file:
        reader = csv.DictReader(in_file)
        for row in reader:
            if row[ROW_INDEX] == '0':
                continue
            template_name, display_name = None, None
            if DATA_FILE_PROCESSING[data_name] is not None:
                row, template_name, display_name = DATA_FILE_PROCESSING[data_name](row)
            template_name = data_name if template_name is None else template_name
            if display_name is not None:
                out_file.write(display_name)
                out_file.write(ENTRY_LINE_BREAK)
                out_file.write(build_wikitext_row(template_name, row, delim='\n|'))
                out_file.write(ENTRY_LINE_BREAK)
            else:
                out_file.write(build_wikitext_row(template_name, row))
                out_file.write('\n')

def find_fmt_params(in_dir, out_dir):
    with open('fmt_params.csv', 'w') as out_file:
        out_file.write('file,column,fmt_param,context\n')
        for data_name in DATA_FILE_PROCESSING:
            seen = {}
            with open(in_dir+data_name+EXT, 'r') as in_file:
                reader = csv.DictReader(in_file)
                for row in reader:
                    for k, v in row.items():
                        if k not in seen:
                            seen[k] = []
                        if v in TEXT_LABELS:
                            fmt_params = {s[1]: None for s in string.Formatter().parse(TEXT_LABELS[v]) if s[1] is not None}
                            for p in fmt_params:
                                if p not in seen[k]:
                                    out_file.write(','.join((data_name, k, p)) + '\n')
                                    seen[k].append(p)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process CSV data into Wikitext.')
    parser.add_argument('-i', type=str, help='directory of input text files', required=True)
    parser.add_argument('-o', type=str, help='directory of output text files  (default: ./output)', default='./output')
    parser.add_argument('--delete_old', help='delete older output files', dest='delete_old', action='store_true')

    args = parser.parse_args()
    if args.delete_old:
        if os.path.exists(args.o):
            try:
                rmtree(args.o)
                print('Deleted old {}\n'.format(args.o))
            except Exception:
                print('Could not delete old {}\n'.format(args.o))
    if not os.path.exists(args.o):
        os.makedirs(args.o)

    in_dir = args.i if args.i[-1] == '/' else args.i+'/'
    out_dir = args.o if args.o[-1] == '/' else args.o+'/'

    TEXT_LABELS = csv_as_index(in_dir+TEXT_LABEL_NAME+EXT, tabs=True)
    ABILITY_SHIFT_GROUPS = csv_as_index(in_dir+ABILITY_SHIFT_GROUP_NAME+EXT)

    # find_fmt_params(in_dir, out_dir)
    for data_name in DATA_FILE_PROCESSING:
        if DATA_FILE_PROCESSING[data_name] is not None:
            print('Saved {}{}'.format(data_name, EXT))
            csv_as_wikitext(in_dir, out_dir, data_name)
