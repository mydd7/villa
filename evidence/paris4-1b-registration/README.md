# Paris4 legacy 1B to 1A: registration candidate

Candidate registration for the two legacy Paris4 CT scans discussed in [villa #2312](https://github.com/ScrollPrize/villa/issues/2312): `20230206171837` (1B) to `20230205180739` (1A), using the existing registration cores. Human review is pending.

The result could supply the missing first step for transferring legacy 1B surfaces. Its usefulness for the specific candidate OBJ, or for the current 2.4 um scan, has not been established. Neither was used as ground truth.

## Result

46 disjoint pairs of real, level-0 CT blocks were measured. Of 31 fit blocks, 14 passed the correspondence checks and were used. The project's leave-one-out model selection chose `scaled-rigid9`; the affine model did not predict better. No held-out block entered that selection.

15 blocks were held out. Eight supplied sufficiently reliable local correspondences to measure geometric agreement: median **0.521 voxels**, maximum **1.365 voxels**, at 7.91 um per voxel. These are disagreements against automatic correspondences, not accuracy against independent manual landmarks. Seven ambiguous local measurements were rejected and remain in `measurements.json` and the review images.

The candidate's windowed intensity correlation on **all 15** held-out blocks is 0.871 to 0.977, median 0.948. For the same central 64-cubed regions, the coarse bootstrap has median -0.045; a deliberately Z-mirrored moving-block control has median 0.198. The bootstrap is only an initialization, not an existing published registration. Scores use the original uint8 intensities and the project's `aligned_match`, without display normalization.

## Coordinates and coverage

- Moving: `20230206171837-7.910um-54keV-masked.zarr`, actual level-0 shape ZYX `(10529, 7812, 8316)`.
- Fixed: `20230205180739-7.910um-54keV-masked.zarr`, actual level-0 shape ZYX `(14258, 7888, 8096)`.
- The transform JSON follows the existing `transform_schema.json`: `p_A_XYZ = M @ [p_B_XYZ, 1]`. Both sides use zero-based level-0 array indices, with integer coordinates at voxel sample centers. Both voxel pitches are 7.91 um. No additional crop offset or axis flip is applied.
- The approximate B-to-A translation in XYZ is `(-253, -68, -6812)` voxels, with a small rotation and axis scaling. Use the matrix, not that rounded translation.
- Fine-resolution evidence is confined to sampled blocks around fixed A Z 768 to 3072, Y 2048 to 4608, X 2048 to 6144. This is not validation of every point inside those bounds, nor of the rest of 1B.
- The shape in the current catalog differs from the fixed Zarr header. `provenance.json` records the actual headers. The legacy TIFF/OBJ coordinate frame has not been independently checked against these Zarrs. Do not silently apply this candidate to an OBJ or compose it into a registration to the modern scan.

## Reproduce

Use a villa checkout at commit `2986ceb37befd31a1ac4572ff1f095cc671c7b89`. The numerical-core hashes and versions used are in `provenance.json`. The versions below differ from the pipeline's pinned requirements.

The numerical run used Python 3.12.10, NumPy 2.5.4, SciPy 1.18.1, scikit-image 0.26.0, jsonschema 4.25.0 and Pillow 13.0.0. Capture used the existing Python 3.14 native `vc_reader`; its extension hashes are recorded. Capture and numerical analysis may run in separate environments.

From this directory, with the relevant dependencies already available:

```sh
python reproduce.py --villa /path/to/villa --data ./inputs --capture
python reproduce.py --villa /path/to/villa --data ./inputs
python render_review.py --villa /path/to/villa --data ./inputs
```

Capture reads bounded blocks directly from the two public Zarrs with disk cache writes disabled. SHA-256 checks cover every captured NPY. The 92 input blocks occupy about 184 MiB before filesystem compression. Network traffic is larger because reads touch whole chunks. The input arrays are not included here.

The frozen plans reproduce the fine-resolution measurements and fit. Discovery began with masked phase correlation at effective level 6, followed by existing dense correlation at level 3. The frozen level-0 plans use only the fit points of that coarse stage as their seed. Whole-volume coarse initialization saw the overlap, so the held-out checks are independent of the final fine fit, not an independent discovery dataset. Coarse phase-correlation coordinates were checked using a known crop of the actual CT; unequal input dimensions required subtracting the centering term. The bootstrap B-to-A ZYX translation was `(-6784, -64, -256)` level-0 voxels.

Fine correspondence acceptance is fixed at: both blocks pass the core's texture/mask checks, aligned NCC > 0.85, local peak correction < 0.5 voxel, weakest peak sharpness > 0.0001, and phase shift norm < 8 voxels. All accepted fit points enter the final model selection; final-fit residuals do not filter hold-outs. `resample_fine`, `correlate`, `peak_check`, `signal_centre` and model selection are imported from the project's existing cores. The exported transform is checked against the repository schema and against XYZ/ZYX conversion.

## Review

Open the 15 PNGs under `images/`. They include every held-out block, including rejected local measurements. Each contains three central orthogonal planes: fixed reference, bootstrap overlay, and candidate overlay. Fixed CT is red, moving CT is cyan; agreement appears gray. These show the same central 64-by-64 area scored numerically, enlarged four times with nearest-neighbor display. The 0.5/99.5 percent display windows are estimated once per scan from accepted fit blocks only and recorded in `display-windows.json`.

Before using this for labels, review matching layers in all three planes, obtain additional independent landmarks, check the legacy OBJ/TIFF frame, and test the modern scan directly. Do not treat the unmeasured part of 1B as registered merely by extrapolating this matrix.

CT data: ScrollPrize/Vesuvius Challenge, PHercParis4 public volumes, CC BY-NC 4.0 as declared in the catalog. Public input URLs and exact source identifiers are recorded in `provenance.json`.
