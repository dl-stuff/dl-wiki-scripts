#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
from PIL import Image
from UnityPy import AssetsManager

# Sprites URLs - grab these from the manifests under the "images/ingame/ui" / "uilocalized" like items
# Each URL should be on a new line, the pipe (|) and following label are optional.
URLS = '''
http://dragalialost.akamaized.net/dl/assetbundles/Android/Q3/Q3PYHY6AIKRFGCJXKN56RABXYTKTGWA7OSKSTBQCU5P7DJ3BP2MQ | images/uilocalized2/atlascompress/uilocalized2
http://dragalialost.akamaized.net/dl/assetbundles/Android/FH/FHY6MPJJOSZSOVL5MJRTFBVKK7HKGLFPCV642O2XREX3MYZGXO3Q | images/uilocalized2/atlascompress/uilocalized2_a
'''
TEXTURE_OUT = './sprites/'


def main():
  os.makedirs(TEXTURE_OUT, exist_ok=True)
  sprite_atlases = {}

  for line in URLS.strip().split('\n'):
    if '|' in line:
      url, _ = [x.strip() for x in line.split('|')]
    else:
      url = line.strip()

    print(url)
    response = requests.get(url, verify=False).content
    am = AssetsManager()
    am.load_file(url, data=response)

    # Extract the assets
    for asset in am.assets.values():
      # The AssetBundle object is always keyed at <1>.
      bundle_name = asset.objects[1].read().name
      print(bundle_name)
      # Map alpha texture AssetBundles to the same entry as the main texture.
      bundle_name = bundle_name.replace('_a.a', '.a')

      if bundle_name not in sprite_atlases:
        sprite_atlases[bundle_name] = {'sprites': []}

      for obj in asset.objects.values():
        if obj.type == 'Texture2D':
          data = obj.read()
          if data.name.endswith('_A'):
            sprite_atlases[bundle_name]['AlphaTex'] = obj
          else:
            sprite_atlases[bundle_name]['MainTex'] = obj

        elif obj.type == 'Sprite':
          data = obj.read()
          sprite_atlases[bundle_name]['sprites'].append(data)

  # Alpha merge and extract the Textures & Sprites
  for atlas in sprite_atlases.values():
    main_tex = atlas['MainTex'].read()
    alpha_tex = atlas['AlphaTex'].read()
    atlas_name = main_tex.name
    sprites_path = os.path.join(TEXTURE_OUT, atlas_name)
    os.makedirs(sprites_path, exist_ok=True)
    print(atlas_name)

    # Merge the main texture with the alpha and save
    r, g, b = main_tex.image.split()[:3]
    a = alpha_tex.image.split()[0]
    Image.merge("RGBA", (r,g,b,a)).save(sprites_path + '.png')

    # Extract each sprite
    for sprite in atlas['sprites']:
      sprite.m_RD.texture = atlas['MainTex']
      sprite.m_RD.alphaTexture = atlas['AlphaTex']
      img = sprite.image
      if 'Icon_Buff' in sprite.name:
        img = resize(img)
      img.save(os.path.join(sprites_path, sprite.name + '.png'))



''' Returns a copy of the image resized as a square. '''
def resize(image, size=30):
  square = Image.new('RGBA', (size, size), (0, 0, 0, 0))

  h, w = image.width, image.height

  offset = ((30 - image.width) // 2, (30 - image.height) // 2)
  square.paste(image, offset)
  return square



if __name__ == '__main__':
  main()
