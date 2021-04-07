# dragalia-wiki-scripts

## Requirements
* Python 3
* Pillow (https://pypi.org/project/Pillow/)

## Example usage
```
Process_DL_Images.py -i <input_folder> -o <output_folder>
```
The input_folder is expected to have images in the same folder structure described by the game manifest, in order to properly auto-categorize and alpha-merge images.

To remove the old output folder before processing:
```
Process_DL_Images.py -i <input_folder> -o <output_folder> --delete_old
```

### Enemy Data parsing
The input_folder is expected to contain the CSV-form master Monos from the game dump.
```
Enemy_Parser.py -i <input_folder> -o <output_folder>
```
