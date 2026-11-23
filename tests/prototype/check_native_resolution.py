#!/usr/bin/env python3
"""Verify that OME-Zarr retains the native moving-image pixels and calibration.

Usage:
  python tests/prototype/check_native_resolution.py OUTPUT.ome.zarr SOURCE_HNE.ome.tif
"""
import sys
from contextlib import ExitStack
from pathlib import Path

import numpy as np
import ngff_zarr as ng
import zarr

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bin"))
from integrate_omezarr import read, spacing


store = Path(sys.argv[1])
source_path = Path(sys.argv[2])
scene = ng.NgffScene.from_ome_zarr(str(store))
native_layer = scene.images["hne_native"].images[0].data

with ExitStack() as stack:
    source, axes, pixels, _ = read(stack, source_path)
    assert tuple(source.shape) == tuple(native_layer.shape), (
        f"Native shape changed: source={source.shape}, output={native_layer.shape}"
    )
    assert source.dtype == native_layer.dtype, (
        f"Native dtype changed: source={source.dtype}, output={native_layer.dtype}"
    )
    source_scale = spacing(pixels)
    root = zarr.open_group(str(store), mode="r")
    provenance = root.attrs["spatial_lattice"]
    np.testing.assert_allclose(provenance["native_hne_spacing_um"], source_scale)
    assert provenance["native_hne_pixels_preserved"] is True

    # Compare every pixel in bounded tiles, avoiding a second full-image allocation.
    tile = 512
    for y in range(0, source.shape[-2], tile):
        for x in range(0, source.shape[-1], tile):
            selection = (slice(None),) * (source.ndim - 2) + (
                slice(y, min(y + tile, source.shape[-2])),
                slice(x, min(x + tile, source.shape[-1])),
            )
            expected = source[selection].compute()
            actual = native_layer[selection].compute()
            np.testing.assert_array_equal(actual, expected)

edges = scene.coordinateTransformations
assert any(
    edge.input.path == "hne_native" and edge.output.name == "hne_native_physical"
    for edge in edges
), "Native image is not connected to its calibrated physical scene transform"
print("Native H&E pixels, dtype, calibration, and RFC-5 scene edge verified")
