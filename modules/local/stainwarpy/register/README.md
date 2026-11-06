# Resize-coordinate correction

The module uses the existing Stainwarpy 0.2.4 container and command-line options.
`fix_stainwarpy_resize.py` replaces only its feature-coordinate lifting. Upstream
multiplies keypoints by the nominal downsampling factor; the correction uses
`(point + 0.5) * original_shape / resized_shape - 0.5` for each image and axis.
This accounts for pixel centers and rounded resize dimensions.

The helper is embedded in the task script, so no new inputs, channels, processes,
containers or parameters are needed. Nextflow hashes its content with the task.
Feature resolution, integer keypoints, descriptor matching, RANSAC settings,
random sampling, reference channel and transform model retain upstream behavior.
The output metrics record that the correction was applied; the OME-Zarr exporter
already preserves those metrics.

This is a geometric bug fix, not a registration-accuracy guarantee. The audit
found that the existing OME-Zarr preserves the source images exactly and that
residual tissue misalignment is already present in the registered TIFF. Local
deformation or feature-fit error may remain after this correction. Existing
artifacts are not rewritten.

Run regression tests inside the existing container:

```bash
docker run --rm -v "$PWD:/pipeline" -w /pipeline \
  community.wave.seqera.io/library/stainwarpy:0.2.4--c8bf19657f01e47a \
  python -m unittest discover -s tests -p 'test_stainwarpy_resize.py'
```

On solidfox, an isolated real-data module check uses the original extracted
reference channel and H&E:

```bash
nextflow run tests/stainwarpy_resize_example.nf -profile docker \
  --outdir results/stainwarpy-resize-fix-check
```

Review/remove this narrowly version-guarded shim when upgrading Stainwarpy.
