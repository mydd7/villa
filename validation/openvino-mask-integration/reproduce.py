import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from vc_reader import images
from vc_reader.reader import ZarrReader


parser = argparse.ArgumentParser()
parser.add_argument('surface_volume', type=Path)
parser.add_argument('checkpoint', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
assert hashlib.sha256(args.checkpoint.read_bytes()).hexdigest() == 'e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab'
args.output.mkdir(parents=True, exist_ok=False)
temporary = args.output / 'tmp'
temporary.mkdir()
environment = os.environ.copy()
environment.update({'OMP_NUM_THREADS': '4', 'MKL_NUM_THREADS': '4', 'TEMP': str(temporary.resolve()), 'TMP': str(temporary.resolve()), 'TMPDIR': str(temporary.resolve())})
with ZarrReader.open(args.surface_volume, level=0) as source:
    ct = source[2:19]
support = ct.any(axis=0)
report = {'selected_ct_sha256': hashlib.sha256(ct.tobytes()).hexdigest(), 'support_sha256': hashlib.sha256(support.tobytes()).hexdigest(), 'ct_supported_pixels': int(support.sum()), 'empty_ct_pixels': int((~support).sum()), 'cases': []}
for tta in [False, True]:
    maps = {}
    row = {'tta_mirror': tta, 'runs': []}
    for backend in ['torch', 'openvino']:
        label = backend + ('-tta' if tta else '-plain')
        output = args.output / (label + '.tif')
        command = [sys.executable, '-m', 'vesuvius.ink_detection.inference.infer', str(args.surface_volume), str(args.checkpoint), str(output), '--device', 'cpu', '--no-compile', '--batch-size', '4', '--loader-threads', '4', '--backend', backend]
        if tta:
            command.append('--tta-mirror')
        start = time.perf_counter()
        with (args.output / (label + '.log')).open('wb') as log:
            result = subprocess.run(command, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=240)
        assert result.returncode == 0, label
        pixels = images.read(output)
        assert pixels.dtype == np.uint8 and pixels.shape == support.shape
        maps[backend] = pixels
        row['runs'].append({'backend': backend, 'elapsed_seconds': time.perf_counter() - start, 'pixel_sha256': hashlib.sha256(pixels.tobytes()).hexdigest(), 'empty_ct_nonzero': int(np.count_nonzero(pixels[~support]))})
    delta = np.abs(maps['torch'].astype(np.int16) - maps['openvino'].astype(np.int16))
    row['max_abs_difference'] = int(delta.max())
    row['ct_supported_max_difference'] = int(delta[support].max())
    row['different_pixels'] = int(np.count_nonzero(delta))
    row['difference_gt_one'] = int(np.count_nonzero(delta > 1))
    report['cases'].append(row)
    (args.output / 'results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report))
