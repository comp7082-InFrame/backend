import numpy as np


def encoding_to_bytes(encoding: np.ndarray) -> bytes:
    """Convert face encoding (512-dim float32 numpy array) to bytes for database storage."""
    return encoding.astype(np.float32).tobytes()


def bytes_to_encoding(data: bytes) -> np.ndarray:
    """Convert bytes back to face encoding numpy array."""
    return np.frombuffer(data, dtype=np.float32).copy()
