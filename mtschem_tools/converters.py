import struct
import json
from typing import Dict, Tuple, Any
import numpy as np
from PIL import Image


class MTSConverter:
    @staticmethod
    def mts_to_json(mts_filepath: str, json_filepath: str) -> Dict[str, Any]:
        with open(mts_filepath, 'rb') as f:
            data = f.read()

        result = {
            'format': 'minetest_schematic',
            'version': None,
            'size': None,
            'nodes': [],
            'metadata': {}
        }

        if data[:4] != b'MTSM':
            raise ValueError("Invalid MTS file signature")

        result['version'] = struct.unpack('>H', data[4:6])[0]

        result['size'] = struct.unpack('>HHH', data[6:12])

        import json
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        return result

    @staticmethod
    def json_to_schematic_template(json_filepath: str, output_filepath: str) -> None:
        import json
        with open(json_filepath, 'r', encoding='utf-8') as f:
            template = json.load(f)

        print(f"Template loaded: {template}")
        # TODO

    @staticmethod
    def create_slice_images(mts_filepath: str, output_dir: str, axis: str = 'z') -> None:
        try:
            import mtschem
        except ImportError:
            print("Install 'mtschem' package first: pip install mtschem")
            return

        schem = mtschem.Schem(mts_filepath)

        palette = {
            'air': (0, 0, 0, 0),
            'default:stone': (128, 128, 128, 255),
            'default:dirt': (139, 69, 19, 255),
            'default:dirt_with_grass': (0, 128, 0, 255),
            'default:water_source': (0, 0, 255, 128),
            'default:tree': (101, 67, 33, 255),
            'default:leaves': (0, 100, 0, 255),
        }

        if axis == 'z':
            slices = schem.data.shape[2]
            width, height = schem.data.shape[0], schem.data.shape[1]
        elif axis == 'y':
            slices = schem.data.shape[1]
            width, height = schem.data.shape[0], schem.data.shape[2]
        else:  # axis == 'x'
            slices = schem.data.shape[0]
            width, height = schem.data.shape[1], schem.data.shape[2]

        for i in range(slices):
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            pixels = img.load()

            for x in range(width):
                for y in range(height):
                    if axis == 'z':
                        node_id = schem.data["node"][x, y, i]
                    elif axis == 'y':
                        node_id = schem.data["node"][x, i, y]
                    else:
                        node_id = schem.data["node"][i, x, y]

                    node_name = schem.nodes[node_id]
                    color = palette.get(node_name, (255, 0, 255, 255))
                    pixels[x, y] = color

            img.save(f'{output_dir}/slice_{axis}_{i:03d}.png')

        print(f"Created {slices} slice images in '{output_dir}'")