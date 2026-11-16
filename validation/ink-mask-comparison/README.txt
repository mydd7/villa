Comparison of #2567 and #2582 on PHerc0800

Both approaches suppress predictions where all selected CT layers are zero.
#2567 makes this the default. #2582 requires --mask-off-surface and preserves
the existing output without it. They are alternatives for the same problem.

The optional mask produces the exact same uint8 pixels as #2567 on the tested
980 x 980 surface, both with and without mirror TTA. Zero differing pixels
in each comparison. This is one surface and one checkpoint on Windows CPU;
it does not establish ink accuracy or support on other devices.

Inputs, source revisions, hashes and result hashes are in validation.json.
The earlier integration protocol records the frozen Windows native runtime
and the source changes used for the reference outputs. No new native build.
The #2582 infer.py was executed against the unchanged inference dependencies
on main 14f56f2. The prior #2567 reference also includes #2453's backend
selector, explicitly using torch. These are not unmodified PR checkouts.

Reproduction in a working project Python environment:
1. Obtain the PHerc0800 surface volume and the published ink_9um checkpoint
   identified in validation.json, or recreate our input using the render
   options in the linked integration protocol. Keep the exact same input.
2. Apply the source changes from #2567 and run:
   python -m vesuvius.ink_detection.inference.infer INPUT CHECKPOINT ours-plain.tif --device cpu --no-compile --batch-size 4 --loader-threads 4
   python -m vesuvius.ink_detection.inference.infer INPUT CHECKPOINT ours-tta.tif --device cpu --no-compile --batch-size 4 --loader-threads 4 --tta-mirror
3. In the #2582 source configuration run the same commands, adding
   --mask-off-surface and naming outputs optional-plain.tif / optional-tta.tif.
4. Run the supplied comparison helper with NumPy, tifffile and imagecodecs:
   python compare.py ours-plain.tif optional-plain.tif ours-tta.tif optional-tta.tif

OMP_NUM_THREADS=4 and MKL_NUM_THREADS=4 for both source configurations.
Each inference ran in its own process, with identical frozen native bindings.
Wall times in the record are individual validation runs, not a benchmark.

No screenshots or raw logs are included: TIFF metadata and logs can contain
machine-specific paths. The comparison uses decoded pixel arrays, not TIFF
container hashes. No source changes are proposed by this evidence branch.
