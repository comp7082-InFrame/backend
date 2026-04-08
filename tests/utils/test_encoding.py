import unittest

import numpy as np

from app.utils.encoding import bytes_to_encoding, encoding_to_bytes


class EncodingUtilsTests(unittest.TestCase):
    def test_encoding_round_trip_preserves_float32_values(self):
        original = np.array([0.25, 0.5, 0.75], dtype=np.float64)

        encoded = encoding_to_bytes(original)
        restored = bytes_to_encoding(encoded)

        self.assertEqual(restored.dtype, np.float32)
        self.assertTrue(np.allclose(restored, np.array([0.25, 0.5, 0.75], dtype=np.float32)))

    def test_bytes_to_encoding_returns_independent_array(self):
        raw = np.array([1.0, 2.0], dtype=np.float32).tobytes()

        restored = bytes_to_encoding(raw)
        restored[0] = 99.0

        self.assertEqual(np.frombuffer(raw, dtype=np.float32)[0], 1.0)
