import argparse
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont


parser = argparse.ArgumentParser()
parser.add_argument('--data', type=Path, required=True)
parser.add_argument('--villa', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.villa / 'foundation/volume-registration/pipeline'))
from volreg.cores.dense_correlation import resample_fine
here = Path(__file__).resolve().parent
rows = json.loads((here / 'measurements.json').read_text())
transform = json.loads((here / '20230206171837_to_20230205180739.json').read_text())
xyz = np.vstack([transform['transformation_matrix'], [0, 0, 0, 1]])
swap = [2, 1, 0, 3]
matrix = xyz[np.ix_(swap, swap)]
bootstrap = np.eye(4)
bootstrap[:3, 3] = [-6784, -64, -256]
windows = {}
for key in ['a', 'b']:
    histogram = np.zeros(256, dtype=np.int64)
    for row in rows:
        if row['split'] == 'fit' and row['usable']:
            values = np.load(args.data / row['files'][key])
            histogram += np.bincount(values.ravel(), minlength=256)
    cdf = np.cumsum(histogram) / histogram.sum()
    windows[key] = [int(np.searchsorted(cdf, q)) for q in [.005, .995]]
(here / 'display-windows.json').write_text(json.dumps(windows, indent=2) + '\n')
output = here / 'images'
output.mkdir(exist_ok=True)
font = ImageFont.load_default(size=18)


def grey(values, key):
    low, high = windows[key]
    return np.clip((values.astype(np.float32) - low) * 255 / (high - low), 0, 255).astype(np.uint8)


for row in rows:
    if row['split'] != 'holdout':
        continue
    a, b = [np.load(args.data / row['files'][key]) for key in ['a', 'b']]
    image = Image.new('RGB', (792, 938), '#15191e')
    draw = ImageDraw.Draw(image)
    draw.text((12, 10), row['id'] + ' | ' + ('reliable match' if row['usable'] else 'local match rejected'), font=font)
    draw.text((12, 36), 'A origin ZYX: ' + str(row['a_origin_zyx']) + ' | level 0, 7.91 um', font=font)
    for column, name in enumerate(['XY', 'XZ', 'YZ']):
        draw.text((12 + column * 260, 68), name, font=font)
    for index, mapping in enumerate([None, bootstrap, matrix]):
        name = ['A reference', 'Bootstrap overlay', 'Candidate overlay'][index]
        top = 96 + index * 280
        draw.text((12, top), name, font=font)
        if mapping is None:
            rgb = np.repeat(grey(a[32:-32, 32:-32, 32:-32], 'a')[..., None], 3, axis=3)
        else:
            local = mapping.copy()
            local[:3, 3] += mapping[:3, :3] @ row['b_origin_zyx'] - row['a_origin_zyx']
            moved = resample_fine(b, 1, local, np.array([32, 32, 32]), 64)
            assert moved is not None
            rgb = np.stack([grey(a[32:-32, 32:-32, 32:-32], 'a'), grey(moved, 'b'), grey(moved, 'b')], axis=3)
        for column, plane in enumerate([rgb[32], rgb[:, 32], rgb[:, :, 32]]):
            tile = Image.fromarray(plane).resize((256, 256), Image.Resampling.NEAREST)
            image.paste(tile, (12 + column * 260, top + 24))
    image.save(output / (row['id'] + '.png'))
