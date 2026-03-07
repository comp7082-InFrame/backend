import cv2
import numpy as np

ARCFACE_DST = np.array([
    [38.2946, 51.6963],  # right eye
    [73.5318, 51.5014],  # left eye
    [56.0252, 71.7366],  # nose tip
    [41.5493, 92.3655],  # right mouth corner
    [70.7299, 92.2041],  # left mouth corner
], dtype=np.float32)

ALIGNED_SIZE = (112, 112)


def align_face(image: np.ndarray, landmarks_5pt: np.ndarray) -> np.ndarray:
    """
    Align a face to the ArcFace 112x112 canonical pose.

    Args:
        image: BGR image (any size)
        landmarks_5pt: (5, 2) float32 array [re, le, nose, rm, lm]

    Returns:
        112x112 BGR aligned face image
    """
    src = landmarks_5pt.astype(np.float32)
    transform, _ = cv2.estimateAffinePartial2D(src, ARCFACE_DST, method=cv2.LMEDS)
    if transform is None:
        # Fallback: return a plain resize crop if transform fails
        return cv2.resize(image, ALIGNED_SIZE)
    aligned = cv2.warpAffine(
        image,
        transform,
        ALIGNED_SIZE,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    return aligned
