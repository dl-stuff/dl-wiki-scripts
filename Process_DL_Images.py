#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import re
import copy
from PIL import Image
from shutil import copyfile, rmtree

ALPHA_TYPES = ('A', 'alpha', 'alphaA8')
YCbCr_TYPES = ('Y', 'Cb', 'Cr')
EXT = '.png'
PORTRAIT_CATEGORIES = (
    '_Full-Screen_Art',
    'Wyrmprint_Images',
    'Dragon_Images',
    'NPC_Portrait_Images',
    'Story_Art',
    'Character_Portrait_Images',
)
PORTRAIT_SUFFIX = '_portrait'
WYRMPRINT_ALPHA = 'Wyrmprint_Alpha.png'
CATEGORY_REGEX = {
    re.compile(r'background/story'): 'Background_Art',
    re.compile(r'images/icon/ability/l'): 'Ability_Icons',
    re.compile(r'images/icon/status/'): 'Affliction_Icons',
    re.compile(r'images/icon/guildemblem/m/(\d+)'): 'Alliance_Crest_Icons',
    re.compile(r'images/icon/union/m/'): 'Affinity_Bonus_Icons',
    re.compile(r'images/icon/brcharaskin/l/'): 'Alberian_Battle_Skin_Icons',
    re.compile(r'images/icon/brcharaskin/m/'): 'Small_Alberian_Battle_Skin_Icons',
    re.compile(r'images/icon/skill/ingamel'): 'Borderless_Skill_Icons',
    re.compile(r'images/story/bookpage/'): 'Book_Background_Art',
    re.compile(r'images/icon/queststorycellbg/1'): 'Campaign_Story_Banners',
    re.compile(r'images/icon/castlestorycellbg'): 'Castle_Story_Banners',
    re.compile(r'images/icon/chara/l'): 'Character_Icon_Images',
    re.compile(r'images/icon/chara/m'): 'Small_Character_Icon_Images',
    re.compile(r'images/outgame/unitdetail/chara'): 'Character_Portrait_Images',
    re.compile(r'images/icon/item/useitem/l'): 'Consumables_Images',
    re.compile(r'images/icon/crafttopcellbg'): 'Crafting_Banner_Images',
    re.compile(r'images/outgame/eventlocalized/(\d+)/questdetail_defensemap_(\d+)'): 'Defensive_Battle_Map_Images',
    re.compile(r'images/icon/item/dragongift/l'): 'Dragon_Gift_Icons',
    re.compile(r'images/icon/dragon/l'): 'Dragon_Icons',
    re.compile(r'images/icon/dragon/m'): 'Small_Dragon_Icons',
    re.compile(r'images/outgame/unitdetail/dragon'): 'Dragon_Images',
    re.compile(r'images/outgame/shop/top/dreamselect'): '_Dream_Summon_Banner_Images',
    re.compile(r'images/icon/element/m/'): 'Element_Icons',
    re.compile(r'images/icon/enemyability'): 'Enemy_Ability_Icons',
    re.compile(r'images/outgame/eventlocalized/21601'): 'Mercurial_Gauntlet_Images',
    re.compile(r'images/outgame/eventlocalized/(\d+)/eventquestmenu(list|top)', re.IGNORECASE): 'Event_Banners',
    re.compile(r'images/outgame/eventlocalized/(\d+)/event_prologue_(\d+)', re.IGNORECASE): 'Event_Guide_Images',
    re.compile(r'images/outgame/eventlocalized/(\d+)/event_(jikai|defense)_preview_(\d+)', re.IGNORECASE): 'Event_Preview_Images',
    re.compile(r'images/outgame/eventlocalized/(\d+)/event_banner_cell_(\d+)', re.IGNORECASE): 'Event_Quest_Banners',
    re.compile(r'images/outgame/eventlocalized/(\d+)/event_banner_01', re.IGNORECASE): 'Event_Treasure_Trade_Shop_Banners',
    re.compile(r'images/outgame/eventlocalized/(\d+)/event_banner_02', re.IGNORECASE): 'Event_Collection_Rewards_Banners',
    re.compile(r'images/outgame/eventlocalized/mainstory/mainstorymenulist_(\d+)', re.IGNORECASE): 'Campaign_Story_Banners',
    re.compile(r'images/icon/queststorycellbg/2'): 'Event_Story_Headers',
    re.compile(r'images/fort/tw'): 'Facility_Images',
    re.compile(r'emotion/eventcg'): '_Full-Screen_Art',
    re.compile(r'images/icon/chargegauge'): 'Gauge_Icons',
    re.compile(r'images/loading/tips/'): 'Loading_Tips_Images',
    re.compile(r'images/outgame/loginbonus'): 'Login_Bonus_Banners',
    re.compile(r'images/icon/item/(?:event|materialdata|gather)/l'): 'Material_Icons',
    re.compile(r'images/icon/item/(?:event|materialdata|gather)/m'): 'Small_Material_Icons',
    re.compile(r'images/icon/manacircle/'): 'MC_Icons',
    re.compile(r'images/story/tutorial'): 'Misc_Guide_Images',
    re.compile(r'images/icon/modechange'): 'Mode_Icons',
    re.compile(r'emotion/story/chara/120'): 'NPC_Portrait_Images',
    re.compile(r'images/icon/item/other/l'): 'Other_Icons',
    re.compile(r'images/icon/profile/l/'): 'Profile_Icons',
    re.compile(r'images/icon/questthumbnail'): 'Quest_List_Thumbnails',
    re.compile(r'images/icon/rarity/'): 'Rarity_Icons',
    re.compile(r'images/icon/item/event/s/(\d+)'): 'Resource_Icons',
    re.compile(r'images/icon/shoppack/specialshop/wide'): 'Shop_Pack_Icons',
    re.compile(r'images/icon/skill/l'): 'Skill_Icons',
    re.compile(r'images/icon/form/m/'): 'Slot_Icons',
    re.compile(r'images/icon/form/s/'): 'Small_Slot_Icons',
    re.compile(r'images/icon/skill/m'): 'Small_Skill_Icons',
    re.compile(r'images/icon/campaign/'): 'Special_Campaign_Icons',
    re.compile(r'images/icon/stamp/l/framed'): 'Sticker_Images',
    re.compile(r'emotion/story'): 'Story_Art',
    re.compile(r'images/outgame/summon/top/(\d+)/localized/Summon_(Switch|Top)_Banner'): 'Summon_Showcase_Banner_Images',
    re.compile(r'images/icon/caption/'): 'UI_Icons',
    re.compile(r'images/icon/unitenhanceicon/l/'): 'Upgrade_Icons',
    re.compile(r'images/icon/weapon/l'): 'Weapon_Icons',
    re.compile(r'images/icon/weapon/m'): 'Small_Weapon_Icons',
    re.compile(r'images/icon/amulet/l'): 'Wyrmprint Icons',
    re.compile(r'images/icon/amulet/m'): 'Small_Wyrmprint Icons',
    re.compile(r'images/icon/mapicon/'): 'Main_Campaign_Map_Icons',
    re.compile(r'images/outgame/unitdetail/amulet'): 'Wyrmprint_Images',
    re.compile(r'images/icon/amulet/artistname/'): '_Wyrmprint_Artists',

    re.compile(r'Btn_'): '__Unused/Button',
    re.compile(r'images/ingame/(?:chara|dragon)/(?:bustup|face)'): '__Unused/Closeups',
    re.compile(r'emotion/ingame/skillcutin'): '__Unused/Cutin',
    re.compile(r'images/outgame/eventlocalized/\d+'): '__Unused/Event',
    re.compile(r'emotion/event'): '__Unused/Event/Screen',
    re.compile(r'images/icon/(?:chara/wide|dragon/button)'): '__Unused/Icons',
    re.compile(r'_Mypage'): '__Unused/Mypage',
    re.compile(r'(?:/s/|/m/|/ingamem/)'): '__Unused/Small',
    re.compile(r'images/outgame/summon/top/\d+'): '__Unused/Summon',
}
CATEGORY_NAME_FORMATS = {
    'Alliance_Crest_Icons': (lambda number: 'Icon Alliance {}'.format(number)),
    'Defensive_Battle_Map_Images':
        (lambda event_id, number:
            'DefenseMap EVENT_NAME_{} {}'.format(event_id, number)),
    'Event_Banners':
        (lambda number, type:
            'Banner{} {}'.format('_Top' if type == 'top' else '', number)),
    'Event_Guide_Images':
        (lambda event_id, number:
            'EVENT_NAME_{} Prologue {}'.format(event_id, number)),
    'Event_Preview_Images':
        (lambda event_id, type, number:
            'EVENT_NAME_{} {} {}'.format(event_id, 'Jikai Preview' if type == 'jikai' else 'Additional', number)),
    'Event_Quest_Banners':
        (lambda event_id, number: 'Banner {}_{}'.format(event_id, number)),
    'Event_Treasure_Trade_Shop_Banners':
        (lambda event_id: 'EVENT_NAME_{} Banner 01'.format(event_id)),
    'Event_Collection_Rewards_Banners':
        (lambda event_id: 'EVENT_NAME_{} Banner 02'.format(event_id)),
    'Resource_Icons':
        (lambda number: 'ITEM_NAME_{} Icon'.format(number)),
    'Summon_Showcase_Banner_Images':
        (lambda number, type:
            'Banner_Summon_Showcase {}'.format(number) if type=='Switch' else
                '{} Summon_Top_Banner'.format(number)),
    'Campaign_Story_Banners':
        (lambda number: 'Banner Top Campaign Chapter ' + number),
}


image_name_pattern_alpha = re.compile(r'(.*?)(_(A|alpha|alphaA8))?$')
image_name_pattern_YCbCr = re.compile(r'(.*?)_(Y|Cb|Cr)$')
def split_image_name(file_name):
    # format basename_channel(YCbCr)
    matches = image_name_pattern_YCbCr.match(file_name)
    if matches:
        base_name, _ = matches.groups()
        return base_name, 'YCbCr'
    # format basename_channel(Alpha)
    matches = image_name_pattern_alpha.match(file_name)
    if matches:
        base_name, _, channel = matches.groups()
        channel = 'base' if channel is None else channel
        return base_name, channel
    else:
        return file_name, 'base'

def merge_image_name(base_name, channel):
    image_name = base_name
    if channel != 'base':
        image_name += '_' + channel
    image_name += EXT
    return image_name

def build_image_dict(files):
    images = {}
    for f in files:
        file_name, file_ext = os.path.splitext(f)
        if file_ext != EXT or 'parts' in file_name:
            continue
        base_name, channel = split_image_name(file_name)
        if base_name not in images:
            images[base_name] = {}
        images[base_name][channel] = True
    return images

def filter_image_dict(images):
    no_merge = {}
    
    ref = copy.deepcopy(images)
    for base_name in ref:
        if len(ref[base_name]) == 1:
            no_merge[base_name] = images[base_name]
            del images[base_name]
    return images, no_merge

def print_image_dict(images, paths=True):
    for d in images:
        print(d)
        for i in images[d]:
            if paths:
                for c in images[d][i]:
                    print('\t', merge_image_name(i, c))
            else:
                print(i, '\n\t', images[d][i])

def merge_alpha(directory, base_name, alpha_type):
    base_img = Image.open('{}/{}'.format(directory, merge_image_name(base_name, 'base')))
    alph_img = Image.open('{}/{}'.format(directory, merge_image_name(base_name, alpha_type)))

    if base_img.size != alph_img.size:
        return
    try:
        r, g, b, _ = base_img.split()
    except:
        r, g, b = base_img.split()
    if alpha_type == 'alphaA8':
        _, _, _, a = alph_img.split()
    else:
        a = alph_img.convert('L')

    return Image.merge("RGBA", (r,g,b,a))

def merge_YCbCr(directory, base_name, unique_alpha=False):
    Y_img = Image.open('{}/{}'.format(directory, merge_image_name(base_name, 'Y')))
    _, _, _, Y = Y_img.convert('RGBA').split()
    Cb = Image.open('{}/{}'.format(directory, merge_image_name(base_name, 'Cb'))).convert('L').resize(Y_img.size, Image.ANTIALIAS)
    Cr = Image.open('{}/{}'.format(directory, merge_image_name(base_name, 'Cr'))).convert('L').resize(Y_img.size, Image.ANTIALIAS)
    if unique_alpha:
        a = Image.open('{}/{}'.format(directory, merge_image_name(base_name, 'alpha'))).convert('L')
    elif 'unitdetail/amulet' in directory:
        a = Image.open(WYRMPRINT_ALPHA).convert('L')
    else:
        a = None
    if a is not None:
        r, g, b = Image.merge("YCbCr", (Y, Cb, Cr)).convert('RGB').split()
        return Image.merge("RGBA", (r, g, b, a))
    else:
        return Image.merge("YCbCr", (Y, Cb, Cr)).convert('RGB')    

def merge_all_images(current_dir, images):
    merged_images = {}

    for i in images:
        m = {}
        if 'base' in images[i]:
            for alpha in ALPHA_TYPES:
                if alpha in images[i]:
                    m['alpha'] = merge_alpha(current_dir, i, alpha)
                    break
        elif 'YCbCr' in images[i]:
            try:
              m['YCbCr'] = merge_YCbCr(current_dir, i, unique_alpha=('alpha' in images[i]))
            except Exception as e:
              print(e)
        if len(m) > 0:
            merged_images[i] = m

    return merged_images

def match_category(directory, file_name):
    file_path = os.path.join(directory, file_name)
    for pattern, category in CATEGORY_REGEX.items():
        res = pattern.search(file_path)
        if res:
            if len(res.groups()) > 0:
                return category, CATEGORY_NAME_FORMATS[category](*res.groups())
            return category, None
    return '', None

def create_output_dir(out_dir, make_categories=False):
    os.makedirs(out_dir, exist_ok=True)
    if make_categories:
        for category in CATEGORY_REGEX.values():
            os.makedirs(out_dir + '/' + category, exist_ok=True)

def delete_empty_subdirectories(directory):
    for root, _, files in os.walk(directory, topdown=False):
        if not files:
            try:
                os.rmdir(root)
            except:
                pass

def save_merged_images(merged_images, current_dir, out_dir):
    for i in merged_images:
        for t in merged_images[i]:
            img = merged_images[i][t]
            category, name = match_category(current_dir, i)
            img_name = i
            if name is not None:
                img_name = name

            if category:
                if category in PORTRAIT_CATEGORIES:
                    img_name += PORTRAIT_SUFFIX
                save_path = '{}/{}/{}'.format(out_dir, category, img_name)
            else:
                save_path = os.path.join(out_dir, '_uncategorized', current_dir, img_name)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

            while os.path.exists(save_path):
                save_path += '#'
            img.save(save_path + EXT, optimize=True)


def copy_not_merged_images(not_merged, current_dir, input_dir, out_dir):
    relative_dir = current_dir.replace(input_dir, '')
    if os.path.isabs(relative_dir):
        relative_dir = relative_dir[1:]
    for i in not_merged:
        for c in not_merged[i]:
            category, name = match_category(current_dir, i)
            if name is not None:
                img_name = name + EXT
            else:
                img_name = merge_image_name(i, c)

            if category:
                if category in PORTRAIT_CATEGORIES:
                    img_name = img_name.replace(EXT, PORTRAIT_SUFFIX + EXT)
                elif 'Borderless' in category:
                    img_name = img_name.replace(EXT, ' Borderless' + EXT)
                target_path = os.path.join(out_dir, category, img_name)
            else:
                target_path = os.path.join(out_dir, '_uncategorized', relative_dir, img_name)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

            while os.path.exists(target_path):
                target_path = '{}#{}'.format(target_path.replace(EXT, ''), EXT)
            copyfile(os.path.join(current_dir, merge_image_name(i, c)), target_path)


def process(input_dir='./', output_dir='./output-img', wyrmprint_alpha_path='Wyrmprint_Alpha.png', delete_old=False):
    global WYRMPRINT_ALPHA
    if delete_old:
        if os.path.exists(output_dir):
            try:
                rmtree(output_dir)
                print('Deleted old {}\n'.format(output_dir))
            except Exception:
                print('Could not delete old {}\n'.format(output_dir))

    create_output_dir(output_dir, make_categories=True)
    WYRMPRINT_ALPHA = wyrmprint_alpha_path
    overall_not_merged = {}

    for root, unused_subdirs, files, in os.walk(input_dir):
      if not len(files):
        continue
      images = build_image_dict(files)
      images, not_merged = filter_image_dict(images)

      merged = merge_all_images(root, images)

      current_dir = root.replace(input_dir, '')
      if os.path.isabs(current_dir):
        current_dir = current_dir[1:]
      save_merged_images(merged, current_dir, output_dir)
      copy_not_merged_images(not_merged, root, input_dir, output_dir)
      overall_not_merged[root] = not_merged

    delete_empty_subdirectories(output_dir)
    print('\nThe following images were copied to {} without merging:'.format(output_dir))
    print_image_dict(overall_not_merged)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge alpha and YCbCr images.')
    parser.add_argument('-i', type=str, help='directory of input images', default='./')
    parser.add_argument('-o', type=str, help='directory of output images  (default: ./output-img)', default='./output-img')
    parser.add_argument('--delete_old', help='delete older output files', dest='delete_old', action='store_true')
    parser.add_argument('-wpa', type=str, help='path to Wyrmprint_Alpha.png.', default='Wyrmprint_Alpha.png')

    args = parser.parse_args()
    process(input_dir=args.i, output_dir=args.o, wyrmprint_alpha_path=args.wpa, delete_old=args.delete_old)
