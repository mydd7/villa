import argparse
import cProfile
import hashlib
import importlib.util
import json
from pathlib import Path
import pstats
import shutil
import subprocess
import tempfile
import time
import tracemalloc

import psutil
from vc_reader.reader import open_group
from vesuvius.ink_detection.preprocessing import create_label_zarrs


parser = argparse.ArgumentParser()
parser.add_argument('input', type=Path)
parser.add_argument('report', type=Path)
parser.add_argument('--repository', type=Path, default=Path.cwd())
parser.add_argument('--source-ref')
args = parser.parse_args()
source_path = 'vesuvius/src/vesuvius/ink_detection/preprocessing/create_label_zarrs.py'
with tempfile.TemporaryDirectory(prefix='label-pyramid-memory-') as directory:
    root = Path(directory)
    module = create_label_zarrs
    if args.source_ref:
        saved = root / 'baseline.py'
        saved.write_bytes(subprocess.check_output(['git', '-C', str(args.repository), 'show', f'{args.source_ref}:{source_path}']))
        spec = importlib.util.spec_from_file_location('label_pyramid_baseline', saved)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    input_path = root / 'w00_supervision_mask.png'
    shutil.copyfile(args.input, input_path)
    tracemalloc.start()
    profiler = cProfile.Profile()
    start = time.perf_counter()
    profiler.enable()
    module.convert_image(input_path, levels=3, chunk_workers=1)
    profiler.disable()
    seconds = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    memory = psutil.Process().memory_info()
    source_bytes = Path(module.__file__).read_bytes()
    committed = subprocess.check_output(['git', '-C', str(args.repository), 'show', f'{args.source_ref or "HEAD"}:{source_path}'])
    assert source_bytes.replace(b'\r\n', b'\n') == committed.replace(b'\r\n', b'\n')
    report = {
        'source_commit': subprocess.check_output(['git', '-C', str(args.repository), 'rev-parse', args.source_ref or 'HEAD'], text=True).strip(),
        'source_file_sha256': hashlib.sha256(source_bytes).hexdigest(),
        'source_normalized_sha256': hashlib.sha256(source_bytes.replace(b'\r\n', b'\n')).hexdigest(),
        'input_png_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
        'seconds': seconds,
        'numpy_python_peak_bytes': peak,
        'peak_working_set_bytes': getattr(memory, 'peak_wset', None),
        'peak_private_commit_bytes': getattr(memory, 'peak_pagefile', None),
    }
    output = input_path.with_suffix('.zarr')
    report['output_files'] = {path.relative_to(output).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in output.rglob('*') if path.is_file()}
    report['levels'] = []
    group = open_group(output)
    for level in range(3):
        with group[str(level)] as array:
            plane = array[32]
            assert not array[0].any() and not array[31].any() and not array[33].any() and not array[64].any()
            report['levels'].append({'shape': list(array.shape), 'chunks': list(array.chunks), 'plane_sha256': hashlib.sha256(plane.tobytes()).hexdigest()})
    with args.report.with_suffix('.profile.txt').open('w', encoding='utf-8') as stream:
        pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats('cumulative').print_stats(20)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in report.items() if key not in ('output_files', 'levels')}))
