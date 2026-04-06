import os
import uuid
from dataclasses import dataclass

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile

from app.api.deps import get_face_service
from app.config import get_settings
from app.models.user import User
from app.utils.encoding import encoding_to_bytes

settings = get_settings()


@dataclass
class PreparedUserPhoto:
    photo_path: str
    encoding: np.ndarray
    encoding_bytes: bytes


async def prepare_user_photo(
    photo: UploadFile,
    existing_photo_path: str | None = None,
) -> PreparedUserPhoto:
    contents = await photo.read()
    image_bytes = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    face_service = get_face_service()
    if face_service is None:
        raise HTTPException(status_code=503, detail="Face recognition service is not initialized")

    encoding = face_service.extract_face_encoding(image)
    if encoding is None:
        raise HTTPException(status_code=400, detail="No face detected in image")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    photo_filename = f"{uuid.uuid4()}.jpg"
    photo_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, photo_filename))
    if not cv2.imwrite(photo_path, image):
        raise HTTPException(status_code=500, detail="Failed to save image file")

    if existing_photo_path and os.path.exists(existing_photo_path):
        os.remove(existing_photo_path)

    return PreparedUserPhoto(
        photo_path=photo_path,
        encoding=encoding,
        encoding_bytes=encoding_to_bytes(encoding),
    )


def apply_prepared_user_photo(user: User, prepared_photo: PreparedUserPhoto):
    user.photo_path = prepared_photo.photo_path
    user.photo_encoding = prepared_photo.encoding_bytes
