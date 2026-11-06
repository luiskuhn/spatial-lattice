"""Geometry regression tests for the minimal Stainwarpy resize correction."""

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from skimage.transform import resize

path = (
    Path(__file__).resolve().parents[1]
    / "modules/local/stainwarpy/register/fix_stainwarpy_resize.py"
)
spec = importlib.util.spec_from_file_location("resize_fix", path)
fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix)


class ResizeCoordinates(unittest.TestCase):
    def test_matches_actual_resize_sampling(self):
        # Coordinate ramps provide an independent measurement of resize's map.
        shape = (253, 401)
        smaller = (63, 100)
        points = np.array([[2, 3], [10, 20], [30, 40], [50, 80]])
        expected = np.column_stack(
            [
                resize(r, smaller, order=1, preserve_range=True, anti_aliasing=False)[
                    tuple(points.T)
                ]
                for r in np.indices(shape, dtype=float)
            ]
        )
        np.testing.assert_allclose(fix.lift_points(points, shape, smaller), expected)
        self.assertGreater(np.max(np.abs(points * 4 - expected)), 1)

    def test_same_size_is_identity(self):
        points = np.array([[1, 2], [15, 20]])
        np.testing.assert_array_equal(
            fix.lift_points(points, (100, 200), (100, 200)), points
        )

    def test_only_coordinate_lifting_changes_in_feature_path(self):
        fixed = np.zeros((253, 401))
        moving = np.zeros((300, 500))
        points = np.array([[2, 3], [10, 20], [30, 40], [50, 80]])
        descriptors = np.zeros((4, 128), dtype=np.uint8)

        class Detector:
            def detect_and_extract(self, image):
                self.keypoints = points.copy()
                self.descriptors = descriptors.copy()

        with (
            patch.object(fix, "SIFT", return_value=Detector()) as sift,
            patch.object(
                fix,
                "match_descriptors",
                return_value=np.column_stack((np.arange(4), np.arange(4))),
            ) as match,
            patch.object(
                fix, "ransac", return_value=(None, np.ones(4, dtype=bool))
            ) as robust,
        ):
            src, dst = fix.features_with_SIFT(fixed, moving)
        sift.assert_called_once_with(n_octaves=3, n_scales=5)
        self.assertEqual(
            match.call_args.kwargs, {"max_ratio": 0.6, "cross_check": True}
        )
        self.assertEqual(
            robust.call_args.kwargs,
            {"min_samples": 4, "residual_threshold": 2, "max_trials": 1000},
        )
        np.testing.assert_allclose(
            src, fix.lift_points(points, moving.shape, (75, 125))[:, ::-1]
        )
        np.testing.assert_allclose(
            dst, fix.lift_points(points, fixed.shape, (63, 100))[:, ::-1]
        )


if __name__ == "__main__":
    unittest.main()
