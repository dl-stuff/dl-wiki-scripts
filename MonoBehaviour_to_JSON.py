
import os
import errno
import re
import json
import argparse

idx_pattern = re.compile(r'\[(\d+)\]')
val_pattern = re.compile(r'(int|UInt8|string|float) (_[A-Za-z0-9]+) = (.+)')
arr_pattern = re.compile(r'vector (_[A-Za-z0-9]+)')
arr_ele_pattern = re.compile(r'(int|UInt8|string|float) (size|data) = (.+)')
dtype_dict = {
    'int': int,
    'UInt8': int,
    'string': lambda x: str(x.replace('\"', '')),
    'float': float
}

def check_target_path(target):
    if not os.path.exists(os.path.dirname(target)):
        try:
            os.makedirs(os.path.dirname(target))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

def walk_output(json_output, c_key):
    sorted_keys = sorted(list(c_key.keys()))
    c_dict = json_output
    for k in sorted_keys:
        v = c_key[k]
        try:
            c_dict = c_dict[v]
        except:
            c_dict[v] = {}
            c_dict = c_dict[v]
    return c_dict

def parse_file(file_name, output_file_path, text_label_data=None):
    if text_label_data is None:
        dtype_dict['string'] = lambda x: str(x.replace('\"', ''))
    else:
        def get_label(x):
            x = str(x.replace('\"', ''))
            try:
                return text_label_data[x]
            except:
                return x
        dtype_dict['string'] = get_label

    check_target_path(output_file_path)
    json_output = {}
    c_vec = None
    c_vec_size = None
    c_key = {}
    c_depth = 0
    with open(file_name, 'r', encoding='utf8') as mono:
        for l in mono:
            line = l.strip()

            res = arr_pattern.match(line)
            if res:
                c_vec = res.group(1)
                continue

            res = idx_pattern.match(line)
            if res and c_vec is None:
                depth = l.count('\t')
                v = int(res.group(1))
                if depth >= c_depth:
                    c_depth = depth
                    c_key[depth] = v
                else:
                    c_key = {depth: v}
                continue
            
            res = val_pattern.match(line)
            if res:
                c_vec, c_vec_size = None, None
                dtype, name, value = res.groups()
                v = dtype_dict[dtype](value)
                if v or dtype == 'UInt8':
                    out = walk_output(json_output, c_key)
                    try:
                        out[name] = v
                    except:
                        out = {name: v}
                    continue

            res = arr_ele_pattern.match(line)
            if res and c_vec is not None:
                dtype, name, value = res.groups()
                v = dtype_dict[dtype](value)
                if name == 'size':
                    c_vec_size = v
                    continue
                elif name == 'data':
                    if len(c_key) > 0:
                        out = walk_output(json_output, c_key)
                        try:
                            out[c_vec].append(v)
                        except:
                            try:
                                out[c_vec] = [v]
                            except:
                                out = {c_vec: [v]}
                    # else:
                    #     try:
                    #         json_output[c_vec].append(v)
                    #     except:
                    #         json_output[c_vec] = [v]
                    
                    c_vec_size -= 1
                    if c_vec_size == 0:
                        c_vec, c_vec_size = None, None
                    continue

    with open(output_file_path, 'w', encoding='utf8') as out:
        json.dump(json_output, out, indent=2, ensure_ascii=False)

def parse_keyval_pair(file_name, output_file_path, text_label_data=None):
    if text_label_data is None:
        dtype_dict['string'] = lambda x: str(x.replace('\"', ''))
    else:
        def get_label(x):
            x = str(x.replace('\"', ''))
            try:
                return text_label_data[x]
            except:
                return x
        dtype_dict['string'] = get_label

    check_target_path(output_file_path)
    json_output = {}
    c_label = None
    with open(file_name, 'r', encoding='utf8') as mono:
        for line in mono:
            line = line.strip()
            res = val_pattern.match(line)
            if res:
                dtype, key, value = res.groups()
                value = dtype_dict[dtype](value)
                if key == '_Id':
                    c_label = value
                elif value:
                    json_output[c_label] = value


    with open(output_file_path, 'w', encoding='utf8') as out:
        json.dump(json_output, out, indent=2, ensure_ascii=False)

    return json_output


kv_pair_files = [
    # 'TextLabel',
    'AbilityGroup', 
    'AchievementGameCenter',
    'AchievementGooglePlay'
]
def parse_all_files(source_folder, destination_folder):
    for root, _, files in os.walk(source_folder):
        text_label_data = None
        for file_name in files:
            if 'TextLabel' in file_name:
                print(file_name, flush=True)
                file_path = os.path.join(root, file_name)
                out_path = os.path.join(destination_folder, os.path.basename(file_path.replace('.mono', '.json')))
                text_label_data = parse_keyval_pair(file_path, out_path)
        for file_name in files:
            if file_name.endswith('.mono') and not 'TextLabel' in file_name:
                print(file_name, flush=True)
                file_path = os.path.join(root, file_name)
                out_path = os.path.join(destination_folder, os.path.basename(file_path.replace('.mono', '.json')))
                if any([kv in file_name for kv in kv_pair_files]):
                    parse_keyval_pair(file_path, out_path, text_label_data)
                else:
                    parse_file(file_path, out_path, text_label_data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse MonoBehaviour.')
    parser.add_argument('-i', type=str, help='input dir', default='./extract')
    parser.add_argument('-o', type=str, help='output dir', default='./mono')
    args = parser.parse_args()
    if os.path.isdir(args.i):
        parse_all_files(args.i, args.o)
    else:
        parse_file(args.i, os.path.join(args.o, os.path.basename(args.i.replace('.mono', '.json'))))