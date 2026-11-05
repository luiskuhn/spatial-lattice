# Integrated OME-Zarr

This module exports one MACSima acquisition, one Cellpose instance mask and
the registered H&E into an NGFF 0.6 scene, using ngff-zarr 0.52.0.
It is an experimental RFC-5 implementation; scene viewer compatibility varies.
SpatialData serialization is deliberately deferred.

## Build on solidfox

From the repository root:

```bash
docker build -t quay.io/spatial-lattice-omezarr:dev -f modules/local/integrated_omezarr/Dockerfile .
source /home/ubuntu/miniconda3/etc/profile.d/conda.sh
conda activate nf-core
nextflow run tests/omezarr_example.nf -profile docker --outdir results/omezarr-test -resume
```

The quay.io tag is LOCAL ONLY, built above; no image has been published.
requirements.txt pins the complete Python environment.

For the full pipeline, runs/solidfox/params.json enables integrated_omezarr.
It requires stainwarpy=true, fixed_img=final_sz=multiplexed and exactly one
Cellpose segmentation method. MultiQC waits for the exporter QC output.
The example test uses the existing full-resolution mask in Caro/spl-out;
it does not wait for or replace the still-running Caro Cellpose job.

## Coordinates

Image arrays are CYX; labels are YX. Physical spatial axes use micrometres.
A scene affine projects channel coordinates away into the shared spatial frame.
Registered H&E is already resampled: registration is NOT applied again.

The adapter is specific to Stainwarpy 0.2.4 affine/similarity registration.
The saved matrix maps native H&E XY pixels to a reduced MACSima registration
grid. Axis permutation converts XY to YX. The grid-to-reference mapping
includes integer shape rounding and skimage.resize pixel-center offsets.
Source H&E physical calibration is represented separately.
Unsupported projective transforms and anisotropic calibration are rejected.

Full-resolution pixels are preserved. Image pyramids use Gaussian downsampling;
label pyramids use nearest neighbour. Source OME-XML, marker names, registration
metrics, source checksums and exporter versions are retained in a namespaced
spatial_lattice provenance attribute. Source OME-XML is provenance, not a claim
that the original acquisition geometry still describes resampled H&E.

Export reads back the scene and checks grid consistency before publishing.
tests/check_omezarr_example.py adds sample pixel/label and coordinate checks.
The scene contains no native H&E pixel array, only its coordinate relationship.
Stitching/per-cycle ASHLAR transformations are not exported by this module;
only the final mosaic calibration and Stainwarpy registration are represented.
