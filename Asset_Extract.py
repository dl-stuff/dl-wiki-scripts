import os
import argparse
import errno
from UnityPy import AssetsManager

def check_target_path(target):
    if not os.path.exists(os.path.dirname(target)):
        try:
            os.makedirs(os.path.dirname(target))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

# 
# def dump(obj) -> str:
#     obj.reader.reset()
#     if getattr(obj.serialized_type, 'nodes', None):
#         sb = []
#         TypeTreeHelper(obj.reader).read_type_string(sb, obj.serialized_type.nodes)
#         return ''.join(sb)
#     return ''

def unpack_Texture2D(data, dest):
    print('Texture2D', dest, flush=True)
    dest, _ = os.path.splitext(dest)
    dest = dest + '.png'
    check_target_path(dest)

    img = data.image
    img.save(dest)

def unpack_MonoBehaviour(data, dest):
    print('MonoBehaviour', dest, flush=True)
    dest, _ = os.path.splitext(dest)
    dest = dest + '.mono'
    check_target_path(dest)

    with open(dest, 'w', encoding='utf8', newline='') as f:
        f.write(data.dump())

def unpack_GameObject(data, destination_folder):
    print('GameObject', destination_folder, flush=True)
    for idx, obj in enumerate(data.components):
        obj_type_str = str(obj.type)
        if obj_type_str in unpack_dict:
            subdata = obj.read()

            dest, _ = os.path.splitext(data.name)
            dest = os.path.join(destination_folder, dest, '{:02d}'.format(idx))

            if data.name or obj_type_str == 'GameObject':
                unpack_dict[obj_type_str](subdata, dest)

unpack_dict = {
    'Texture2D': unpack_Texture2D, 
    'MonoBehaviour': unpack_MonoBehaviour,
    'GameObject': unpack_GameObject
}

def unpack_asset(file_path, destination_folder, root=None, source_folder=None):
    # load that file via AssetsManager
    am = AssetsManager(file_path)

    # iterate over all assets and named objects
    for asset in am.assets.values():
        for obj in asset.objects.values():
            # only process specific object types
            # print(obj.type, obj.container)
            obj_type_str = str(obj.type)
            if obj_type_str in unpack_dict:
                # parse the object data
                data = obj.read()

                # create destination path
                if root and source_folder:
                    intermediate = root.replace(source_folder, '')
                else:
                    intermediate = ''

                if obj_type_str == 'GameObject':
                    dest = os.path.join(destination_folder, intermediate)
                    unpack_dict[obj_type_str](data, dest)
                elif data.name:
                    dest = os.path.join(destination_folder, intermediate, data.name)
                    unpack_dict[obj_type_str](data, dest)
                

def unpack_all_assets(source_folder, destination_folder):
    # iterate over all files in source folder
    for root, _, files in os.walk(source_folder):
        for file_name in files:
            # generate file_path
            file_path = os.path.join(root, file_name)
            unpack_asset(file_path, destination_folder, root=root, source_folder=source_folder)
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract asset files.')
    parser.add_argument('-i', type=str, help='input dir', default='./download')
    parser.add_argument('-o', type=str, help='output dir', default='./extract')
    args = parser.parse_args()
    if os.path.isdir(args.i):
        unpack_all_assets(args.i, args.o)
    else:
        unpack_asset(args.i, args.o)