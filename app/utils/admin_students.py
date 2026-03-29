import json
import uuid


def parse_course_ids(raw_value: str | None) -> list[uuid.UUID]:
    if raw_value is None or raw_value == "":
        return []

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError("course_ids must be valid JSON") from exc

    if not isinstance(parsed, list):
        raise ValueError("course_ids must be a JSON array")

    unique_ids: list[uuid.UUID] = []
    seen: set[uuid.UUID] = set()

    for value in parsed:
        try:
            course_id = uuid.UUID(str(value))
        except ValueError as exc:
            raise ValueError(f"invalid course id: {value}") from exc

        if course_id not in seen:
            unique_ids.append(course_id)
            seen.add(course_id)

    return unique_ids


def is_currently_seen(status: str | None) -> bool:
    return status is not None and status != "absent"
