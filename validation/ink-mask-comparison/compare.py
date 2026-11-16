import argparse
import hashlib
import json
import numpy as np
import tifffile

parser = argparse.ArgumentParser()
parser.add_argument('ours_plain')
parser.add_argument('optional_plain')
parser.add_argument('ours_tta')
parser.add_argument('optional_tta')
args = parser.parse_args()
results = []
for tta, left, right in [(False, args.ours_plain, args.optional_plain), (True, args.ours_tta, args.optional_tta)]:
    expected = tifffile.imread(left)
    actual = tifffile.imread(right)
    if expected.dtype != np.uint8 or actual.dtype != np.uint8 or expected.shape != actual.shape:
        raise ValueError('Expected matching uint8 TIFF dimensions')
    results.append({'tta_mirror': tta, 'shape': list(actual.shape), 'different_pixels': int(np.count_nonzero(actual != expected)), 'max_abs_difference': int(np.max(np.abs(actual.astype(np.int16) - expected.astype(np.int16)))), 'pixel_sha256': hashlib.sha256(actual.tobytes()).hexdigest()})
print(json.dumps(results, indent=2))
if any(row['different_pixels'] for row in results):
    raise SystemExit(1)
