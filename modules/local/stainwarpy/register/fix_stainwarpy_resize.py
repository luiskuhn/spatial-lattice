"""Stainwarpy 0.2.4 CLI with only feature resize-coordinate lifting corrected.

Feature detection/matching follows stainwarpy.reg.features_with_SIFT (MIT,
https://github.com/tckumarasekara/stainwarpy). Keep its defaults and random
sampling unchanged. This shim can be removed when the upstream fix is adopted.
"""

import json
import sys
from importlib.metadata import version
from pathlib import Path

import numpy as np
from skimage.feature import SIFT, match_descriptors
from skimage.measure import ransac
from skimage.transform import AffineTransform, resize


def lift_points(points, original_shape, resized_shape):
    """Inverse of resize's pixel-center mapping, in row/column order."""
    return (points + 0.5) * (np.asarray(original_shape) / resized_shape) - 0.5


def features_with_SIFT(fixed, moving, max_ratio=0.6, n_octaves=3, n_scales=5):
    factor = 4
    if max(fixed.shape) > 2000:
        factor = max(d // 2000 for d in fixed.shape) * 4
    elif max(fixed.shape) < 250:
        factor = 1

    fixed_scaled = resize(
        fixed, tuple(d // factor for d in fixed.shape), anti_aliasing=True
    )
    moving_scaled = resize(
        moving, tuple(d // factor for d in moving.shape), anti_aliasing=True
    )
    detector = SIFT(n_octaves=n_octaves, n_scales=n_scales)
    detector.detect_and_extract(moving_scaled)
    keypoints1, descriptors1 = detector.keypoints, detector.descriptors
    detector.detect_and_extract(fixed_scaled)
    keypoints2, descriptors2 = detector.keypoints, detector.descriptors
    matches = match_descriptors(
        descriptors1, descriptors2, max_ratio=max_ratio, cross_check=True
    )
    if len(matches) < 3:
        raise ValueError(
            "Not enough matching points found between images for reliable registration."
        )

    # The upstream code multiplies both sets by `factor`, losing pixel-center
    # offsets and the axis-specific ratios caused by integer shape rounding.
    src = lift_points(keypoints1[matches[:, 0]], moving.shape, moving_scaled.shape)
    dst = lift_points(keypoints2[matches[:, 1]], fixed.shape, fixed_scaled.shape)
    _, inliers = ransac(
        (dst, src),
        AffineTransform,
        min_samples=4,
        residual_threshold=2,
        max_trials=1000,
    )
    return [src[inliers][:, [1, 0]].copy(), dst[inliers][:, [1, 0]].copy()]


def main():
    from stainwarpy import reg
    from stainwarpy.reg_cli import app

    if version("stainwarpy") != "0.2.4":
        raise RuntimeError(
            "Review this resize-coordinate shim before changing Stainwarpy version"
        )
    reg.features_with_SIFT = features_with_SIFT
    app(standalone_mode=False)
    if len(sys.argv) > 4 and sys.argv[1] == "register":
        path = Path(sys.argv[4]) / "registration_metrics_tform_map.json"
        metrics = json.loads(path.read_text())
        metrics["spatial_lattice_coordinate_fix"] = (
            "stainwarpy-0.2.4-resize-pixel-centers-v1"
        )
        path.write_text(json.dumps(metrics, indent=2) + "\n")


if __name__ == "__main__":
    main()
