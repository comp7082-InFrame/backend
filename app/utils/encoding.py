import numpy as np


def encoding_to_bytes(encoding: np.ndarray) -> bytes:
    """Convert face encoding (128-dim float64 numpy array) to bytes for database storage."""
    return encoding.tobytes()


def bytes_to_encoding(data: bytes) -> np.ndarray:
    """Convert bytes back to face encoding numpy array."""
    return np.frombuffer(data, dtype=np.float64)
