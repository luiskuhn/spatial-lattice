# Integrated OME-Zarr export

The optional `BUILD_INTEGRATED_OMEZARR` subworkflow combines the stitched MACSima
image, one Cellpose instance mask and registered H&E in one calibrated scene.
It runs after registration and segmentation; its QC output is a dependency of MultiQC.

## Enable export

Build the development container from the repository root:

```bash
docker build -t quay.io/spatial-lattice-omezarr:dev -f modules/local/integrated_omezarr/Dockerfile .
```

This tag is local only: no image has been published to Quay.
Use a JSON parameter file so Boolean values retain their type:

```json
{
  "input": "/absolute/path/samplesheet.csv",
  "outdir": "/absolute/path/results",
  "project": false,
  "segmentation": "cellpose4",
  "stainwarpy": true,
  "fixed_img": "multiplexed",
  "final_sz": "multiplexed",
  "integrated_omezarr": true
}
```

```bash
nextflow run . -profile docker -params-file params.json -resume
```

The ROI samplesheet requires `experiment,sample,rack,well,roi,raw_images_ROI,HnE_ROI`.
Supply an H&E file and matching raw MACSima ROI. Use unique acquisition identifiers.
Registration joins use ROI metadata and reject duplicate or unmatched inputs.
This first adapter supports one acquisition per ROI; project-mode H&E and multiple
exposures per ROI need further work.

On solidfox, `./runs/solidfox/run.sh` activates the existing nf-core environment
and uses the prepared CSV and parameters. Image files remain under Caro.
Default output there is `/home/ubuntu/projects/spatial_lattice/results/solidfox`.

## Artifact and coordinates

The output is `<outdir>/integrated/<acquisition_id>.ome.zarr`, plus
`integrated_omezarr_mqc.json` for MultiQC. The store contains:

- `macsima`: full multichannel mosaic and Gaussian image pyramid.
- `macsima/labels/cellpose`: integer labels with a nearest-neighbour pyramid and source-image reference.
- `hne_registered`: registered RGB H&E and image pyramid.
- Root scene metadata: named coordinate systems and transformations.
- `spatial_lattice` attributes: source OME-XML, marker table, registration metrics,
  calibration, SHA-256 source checksums and exporter library versions.

The common spatial frame is MACSima YX in micrometres; channel axes remain
separate from spatial coordinates. Full-resolution source pixel values are preserved.
Already-registered H&E is not transformed a second time.

The Stainwarpy 0.2.4 adapter preserves its native-H&E-to-registration-grid matrix,
XY/YX permutation, integer downsampling shape and pixel-center resize mapping to
MACSima. Native H&E calibration is also recorded, but its original pixel array
is not duplicated into this store.

## Scope and validation

This is experimental NGFF 0.6/RFC-5 support using pinned ngff-zarr 0.52.0;
viewer compatibility must be checked. See [RFC-5](https://ngff.openmicroscopy.org/rfc/5/).
The adapter requires isotropic source calibration, matching reference grids,
affine/similarity registration, and exactly one Cellpose method.
Projective transforms, nonlinear registration, ASHLAR per-tile transformation
history, spatial-omics tables and SpatialData serialization are not implemented.
The exported intensity image is the ASHLAR mosaic, even when background subtraction
is enabled for segmentation.

Every export reopens the scene with NGFF schema validation and checks image grids.
The focused real-data test uses existing outputs, including the previously published
Cellpose mask; it does not launch another segmentation job:

```bash
nextflow run tests/omezarr_example.nf -profile docker --outdir results/omezarr-test
python tests/check_omezarr_example.py results/omezarr-test/integrated/SAMPLE_1_exp2.ome.zarr
```

Run the Python check in the exporter environment. The example paths are specific to
solidfox. Source-pixel patches, label source links, axis permutation and pixel-center
mapping were checked on the 7985 x 12602 example. The complete pipeline was compiled
with `--help`; a new full end-to-end processing run has not been validated.

After changing the container, rebuild it and omit `-resume` for the export test:
the mutable development tag alone does not invalidate Nextflow's cache.

## Container verification and inherited registration modules

INTEGRATED_OMEZARR is the only new executable process in BUILD_INTEGRATED_OMEZARR.
Its Dockerfile and locked Python dependencies are in modules/local/integrated_omezarr.
The subworkflow orchestrates this containerized process; it does not require another image.
The image `quay.io/spatial-lattice-omezarr:dev` is built locally on solidfox, not published to Quay.
Docker CLI smoke testing and NGFF validation of the example artifact passed.

```bash
docker run --rm -e XDG_CACHE_HOME=/tmp/ngff-cache \\
  quay.io/spatial-lattice-omezarr:dev integrate_omezarr.py --help
```

RAMI2D was inherited from commit [fafc698](https://github.com/luiskuhn/spatial-lattice/commit/fafc698dd3f1cb9ba45a756eff8ac742e63367c2)
(CaroAMN, 2026-09-21), which also added Stainwarpy.
RAMI2D_REGISTER is optional and disabled by default. RAMI2D_TRANSFORM is imported but
not invoked by the main workflow. Both already declare a Seqera container.
Neither is part of the tested OME-Zarr integration path; the grey branch in the diagram
indicates inherited functionality, not a newly implemented or validated registration route.
