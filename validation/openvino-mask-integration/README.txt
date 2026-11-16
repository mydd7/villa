Independent Windows integration check for PRs #2453 and #2567

This is a validation of the existing OpenVINO proposal, not a competing backend.
Base: 14f56f2b39eec158addef00466ffe64570639dd1.
Backend source: #2453, 90ed975861cdb02e7b6a5ec254d2ac3d4eea76c0.
Mask source: #2567, 3e8d5228600fa26f5a601db0665c005c8315504b.

Only the backend changes to infer.py and inference_runtime.py were applied
first. Then only the mask change to infer.py was added. Source hashes for
both combinations, input hashes, eight run results and native runtime
provenance are in validation.json. The check uses those two proposals without additional product changes.

Environment: Windows x64, Ryzen 5 7500F, Python 3.14.7, torch 2.15.0+cpu,
NumPy 2.5.4, OpenVINO 2026.4.1. Both runtimes use four inference threads.
OpenVINO and its telemetry dependency were installed in an isolated local
packages folder. The proposal's own telemetry suppression was retained.

Data: PHerc0800 surface 20251029010146, rendered from the public
20250521135224-8.640um volume, 21 slices, scale 1, group 0,
flip-normals, voxel size 8.64 micrometers. Input shape: 21 x 980 x 980;
checkpoint-selected layers: 2..18. The full mesh prefix and CT fingerprint
are in validation.json. Checkpoint: scrollprize/ink_9um,
hybrid_3d2d-seed42/step-075000.pth, SHA256 pinned in the script/report.

Reproduction, in an isolated checkout/environment with the native reader and
OpenVINO 2026.4.1 installed:

1. Start a local branch at the base above. Fetch PR2453 and apply only its
   two inference source-file changes to that branch. Keep the existing
   main versions of the other modules. Confirm the source hashes.
2. Run:
   python reproduce.py <surface-volume.zarr> <step-075000.pth> <before-output>
3. Apply only PR2567's infer.py change. Confirm the new source hashes.
4. Repeat with the same inputs and a new <after-output> directory.

The script runs both backends, with and without mirror TTA, using batch 4,
four loader threads and eager CPU inference. Each CLI runs in its own process.
Raw logs remain in the chosen output directory; they contain local paths and
are not part of these public proofs. The JSON report omits those paths.

Results:
- Every one of the eight CLI processes exited successfully.
- In each backend and both TTA modes, all 497,600 CT-supported pixels remain
  byte-identical after adding the mask; all 462,800 empty-CT pixels become zero.
- After masking, OpenVINO and torch differ by at most one uint8 gray level.
- Without the mask, plain inference differs by two levels at nine pixels,
  all outside CT support. Mirror TTA already differs by at most one level.

This is one real surface and one checkpoint, not an accuracy evaluation or
a legibility claim. Ensembles, CUDA/MPS and other operating systems were not
run. Wall-clock values are single correctness runs including startup and
conversion, not a speed benchmark. Python 3.14 emits torch.jit FutureWarnings
during conversion; all tested processes still exit normally.
