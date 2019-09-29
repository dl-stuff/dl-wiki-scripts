import csv
import os
import string
from shutil import copyfile, rmtree
from collections import OrderedDict
import argparse

EXT = '.txt'
DEFAULT_TEXT_LABEL = ''
ENTRY_LINE_BREAK = '\n==============================\n'

ROW_INDEX = '_Id'

TEXT_LABEL_FILE = 'TextLabel'
TEXT_LABELS = None

ROMAN_NUMERALS = [None, 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
ELEMENTS = [None, 'Flame', 'Water', 'Wind', 'Light', 'Shadow']

def get_label(key):
    return TEXT_LABELS[key] if key in TEXT_LABELS else DEFAULT_TEXT_LABEL

# All process_* functions take in 1 parameters (row) and return 3 parameters (new_row, template_name, display_name)
def process_AbilityLimitedGroup(row):
    row['_AbilityLimitedText'] = get_label(row['_AbilityLimitedText']).format(ability_limit0=row['_MaxLimitedValue'])
    return row, None, None

def process_AbilityData(row):
    new_row = OrderedDict()
    for k in ('PartyPowerWeight','AbilityIconName', 'AbilityLimitedGroupId1', 'AbilityLimitedGroupId2', 'AbilityLimitedGroupId3'):
        new_row[k] = row['_' + k]
    new_row['Name'] = get_label(row['_Name']).format(
        ability_shift0  =   ROMAN_NUMERALS[int(row['_ShiftGroupId'])],
        ability_val0    =   row['_AbilityType1UpValue'])
    new_row['Details'] = get_label(row['_Details']).format(
        ability_cond0   =   row['_ConditionValue'],
        ability_val0    =   row['_AbilityType1UpValue'],
        element_owner   =   ELEMENTS[int(row['_ElementalType'])])
    new_row['GenericName'] = ''
    new_row['AbilityGroup'] = row['_ViewAbilityGroupId1']
    return new_row, 'Ability', new_row['Name']

DATA_FILE_PROCESSING = {
    'AbilityLimitedGroup': process_AbilityLimitedGroup,
    'AbilityData': process_AbilityData,
    'AmuletData': None,
    'BuildEventItem': None,
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

def build_wikitext_row(template_name, row, delim='|'):
    row_str = '{{' + template_name + delim
    row_str += delim.join(['{}={}'.format(k.strip('_'), row[k]) for k in row])
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
            if template_name is None:
                template_name = data_name
            if display_name:
                out_file.write(display_name)
                out_file.write(ENTRY_LINE_BREAK)
                out_file.write(build_wikitext_row(template_name, row, delim='|\n'))
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
    parser.set_defaults(delete_old=False)

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

    TEXT_LABELS = csv_as_index(in_dir+TEXT_LABEL_FILE+EXT, tabs=True)

    # find_fmt_params(in_dir, out_dir)
    for data_name in DATA_FILE_PROCESSING:
        if DATA_FILE_PROCESSING[data_name] is not None:
            csv_as_wikitext(in_dir, out_dir, data_name)
