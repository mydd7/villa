import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--villa', type=Path, required=True)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--capture', action='store_true')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    plan = json.loads((here / 'input-plan.json').read_text(encoding='utf-8'))
    urls = {key: 'https://data.aws.ash2txt.org/samples/PHercParis4/volumes/' + vid + '-7.910um-54keV-masked.zarr'
            for key, vid in [('a', '20230205180739'), ('b', '20230206171837')]}
    if args.capture:
        from vc_reader.reader import ZarrReader

        args.data.mkdir(parents=True, exist_ok=True)
        for key, url in urls.items():
            with ZarrReader.open(url, level=0, auth=None, cache_writes=False, threads=4, connections=4) as source:
                for row in plan:
                    path = args.data / row['files'][key]
                    if not path.exists():
                        origin = row[key + '_origin_zyx']
                        np.save(path, source[tuple(slice(v, v + 128) for v in origin)])
                    assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'][key], path.name
        return

    sys.path.insert(0, str(args.villa / 'foundation/volume-registration/pipeline'))
    from volreg.cores.dense_correlation import aligned_match, block_rejection, correlate, peak_check, signal_centre, resample_fine
    from volreg.cores.transform_fit import select_transform_from_points, selection_to_json

    rows = []
    for row in plan:
        blocks = []
        for key in ['a', 'b']:
            path = args.data / row['files'][key]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'][key], path.name
            block = np.load(path, allow_pickle=False)
            assert block.shape == (128, 128, 128) and block.dtype == np.uint8
            blocks.append(block)
        a, b = blocks
        shift, _ = correlate(a, b)
        peak = peak_check(a, b, shift)
        centre = signal_centre(a, np.zeros(3))
        rejection = block_rejection(a) or block_rejection(b)
        match = aligned_match(a, b, shift)
        usable = bool(rejection is None and match > .85 and peak['offset'] < .5
                      and min(peak['sharpness']) > .0001 and np.linalg.norm(shift) < 8)
        rows.append(dict(row, shift_zyx=shift.tolist(), peak=peak, match=match,
                         rejection=rejection, usable=usable,
                         fixed_zyx=(np.array(row['a_origin_zyx']) + centre).tolist(),
                         moving_zyx=(np.array(row['b_origin_zyx']) + centre - peak['peak_zyx']).tolist()))
    fit = [row for row in rows if row['split'] == 'fit' and row['usable']]
    selection = select_transform_from_points([row['fixed_zyx'] for row in fit],
                                            [row['moving_zyx'] for row in fit],
                                            nominal_scale=1, expect_reflected=False)
    assert selection is not None and selection.ok
    matrix = selection.matrix
    bootstrap = np.eye(4)
    bootstrap[:3, 3] = [-6784, -64, -256]

    inner = (slice(32, -32),) * 3
    for row in rows:
        a, b = [np.load(args.data / row['files'][key], allow_pickle=False) for key in ['a', 'b']]
        predicted = matrix[:3, :3] @ row['moving_zyx'] + matrix[:3, 3]
        row['residual_voxels'] = float(np.linalg.norm(predicted - row['fixed_zyx']))
        for name, mapping, moving in [('bootstrap', bootstrap, b), ('candidate', matrix, b), ('mirrored_control', matrix, b[::-1])]:
            local = mapping.copy()
            local[:3, 3] += mapping[:3, :3] @ row['b_origin_zyx'] - row['a_origin_zyx']
            sampled = resample_fine(moving, 1, local, np.array([32, 32, 32]), 64)
            assert sampled is not None, row['id']
            row[name + '_ncc'] = aligned_match(a[inner], sampled, np.zeros(3))

    holdout = [row for row in rows if row['split'] == 'holdout']
    reliable = [row for row in holdout if row['usable']]
    xyz = [2, 1, 0]
    transform = {'schema_version': '1.0.0', 'fixed_volume': urls['a'],
                 'transformation_matrix': np.column_stack([matrix[:3, :3][np.ix_(xyz, xyz)], matrix[xyz, 3]]).tolist(),
                 'fixed_landmarks': [[row['fixed_zyx'][i] for i in xyz] for row in fit],
                 'moving_landmarks': [[row['moving_zyx'][i] for i in xyz] for row in fit]}
    import jsonschema

    jsonschema.validate(transform, json.loads((args.villa / 'foundation/volume-registration/transform_schema.json').read_text()))
    check = np.array(transform['transformation_matrix'])
    np.testing.assert_allclose(np.array(transform['moving_landmarks']) @ check[:, :3].T + check[:, 3],
                               [((matrix[:3, :3] @ row['moving_zyx'] + matrix[:3, 3])[xyz]).tolist() for row in fit], atol=1e-9)
    summary = {'status': 'candidate; human review pending; no validation outside sampled overlap',
               'direction': '20230206171837 -> 20230205180739', 'coordinates': 'XYZ level-0 voxel indices; 7.91 um both sides',
               'fit_points': len(fit), 'holdout_total': len(holdout), 'holdout_reliable': len(reliable),
               'holdout_rejected': [row['id'] for row in holdout if not row['usable']],
               'holdout_residual_median_voxels': float(np.median([row['residual_voxels'] for row in reliable])),
               'holdout_residual_max_voxels': max(row['residual_voxels'] for row in reliable),
               'holdout_all_candidate_ncc': [row['candidate_ncc'] for row in holdout],
               'holdout_all_bootstrap_ncc': [row['bootstrap_ncc'] for row in holdout],
               'holdout_all_mirrored_ncc': [row['mirrored_control_ncc'] for row in holdout],
               'model_selection': selection_to_json(selection)}
    for name, value in [('measurements.json', rows), ('summary.json', summary),
                        ('20230206171837_to_20230205180739.json', transform)]:
        save(here / name, value)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
