# Prototype validation

Run from the repository root. Use the existing `nf-core` conda environment for Nextflow/Java and Docker for image processing. Build the two local images documented in [prototype_subworkflows.md](../../docs/prototype_subworkflows.md) first.

## Unit and complete workflow wiring checks

```bash
python -m unittest discover -s tests/prototype -p 'test_*.py' -v
python tests/prototype/run_stub.py "$(command -v nextflow)"
```

The stub runner creates two ROI rows belonging to the same experiment/sample and exercises both backends with masks/background subtraction on and off, checking two distinct stores and MultiQC. It creates private version-command shims and empty image files under ignored `testing/`. These files are wiring tests, never valid scientific output. No real image processing is performed by this runner.

## Actual RAMI2D and exporter on deterministic synthetic images

```bash
docker run --rm -v "$PWD:/workspace" -w /workspace spatial-lattice/omezarr:prototype-subworkflows \
  python tests/prototype/make_fixture.py
nextflow -C tests/prototype/rami2d.config run tests/prototype/rami2d.nf \
  --fixture "$PWD/testing/prototype-images" -work-dir testing/prototype-real-work
```

This tests image registration, a moving label mask, absence of moving labels, native transform archiving and validated OME-Zarr output. It uses synthetic image patterns and reference labels, not Cellpose. The fixture is intentionally small. Default output: `testing/prototype-rami2d/`.

## Tissue-derived toy pair

Mount the source OME-Zarr and a new destination directory into the exporter container. For example, with both under the repository's ignored `testing/` directory:

```bash
docker run --rm -v "$PWD:/workspace" -w /workspace spatial-lattice/omezarr:prototype-subworkflows \
  python tests/prototype/make_tissue_fixture.py testing/source.ome.zarr testing/tissue-inputs
nextflow -C tests/prototype/tissue.config run tests/prototype/tissue.nf \
  --fixture "$PWD/testing/tissue-inputs" --outdir testing/tissue-stainwarpy \
  -work-dir testing/tissue-stain-work
nextflow -C tests/prototype/tissue.config run tests/prototype/tissue.nf \
  --fixture "$PWD/testing/tissue-inputs" --outdir testing/tissue-rami2d \
  --registration_backend rami2d -work-dir testing/tissue-rami-work
```

The generator refuses an existing destination. It extracts a 1024×1024 crop with overlapping tissue signal, resets its origin to local zero and records the source offset/calibration in `fixture.json`. The input MACSima channel order must match the previous four-channel example; the tissue test config explicitly selects DAPI at index 2. Adapt this selection for other sources.

The moving H&E is the previously registered image displaced down 24 and right 32 pixels. A similarly displaced copy of the Cellpose labels serves as a synthetic moving annotation. Neither is new native data or independently segmented H&E. No raw MACSima staging, ASHLAR stitching, or full-size Cellpose run occurs in this test. Baseline alignment errors remain in the crop; success here is not proof of biological registration accuracy.

Inspect `macsima`, `hne_registered` and their labels subgroups in napari. Keep the unshifted `baseline_hne.ome.tif` available to compare recovered geometry. Both resulting artifacts must have the same calibrated image/mask grid, integer labels and native transform provenance. Failure or poor matching should remain visible; no automatic fallback changes the registration scheme.

Use an explicit run name with `-resume <name>` when several test sessions exist, so Nextflow resumes the intended test.
