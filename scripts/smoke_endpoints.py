"""
Endpoint smoke test for a running backend instance.

Usage:
    python scripts/smoke_endpoints.py
    python scripts/smoke_endpoints.py --base-url http://localhost:8000/api
"""
from __future__ import annotations

import argparse
from typing import Any

import requests

DEFAULT_BASE_URL = "http://localhost:8000/api"


def run_request(results: list[tuple[str, str, str, str]], label: str, method: str, url: str, **kwargs):
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        status = "PASS" if response.status_code < 400 else "FAIL"
        data_preview = ""
        try:
            body = response.json()
            if isinstance(body, list):
                data_preview = f"{len(body)} items"
            elif isinstance(body, dict):
                data_preview = str(list(body.keys()))[:60]
        except Exception:
            data_preview = response.text[:60]
        results.append((status, str(response.status_code), label, data_preview))
        return response
    except Exception as exc:
        results.append(("ERROR", "-", label, str(exc)[:60]))
        return None


def get_first(url: str, params: dict[str, Any] | None = None):
    """Fetch a list endpoint and return the first item, or None."""
    try:
        response = requests.get(url, params=params, timeout=10)
        body = response.json()
        if isinstance(body, list) and body:
            return body[0]
        if isinstance(body, dict):
            for value in body.values():
                if isinstance(value, list) and value:
                    return value[0]
    except Exception:
        pass
    return None


def run_smoke_tests(base_url: str = DEFAULT_BASE_URL) -> list[tuple[str, str, str, str]]:
    results: list[tuple[str, str, str, str]] = []

    campus = get_first(f"{base_url}/campuses/")
    building = get_first(f"{base_url}/buildings/")
    room = get_first(f"{base_url}/rooms/")
    term = get_first(f"{base_url}/terms/")
    student = get_first(f"{base_url}/students/")

    campus_id = campus.get("id") if campus else None
    building_id = building.get("id") if building else None
    room_id = room.get("id") if room else None
    term_id = term.get("id") if term else None
    student_id = student.get("id") if student else None

    course = get_first(f"{base_url}/courses/", params={"term_id": term_id}) if term_id else None
    course_id = course.get("id") if course else None

    session = get_first(f"{base_url}/sessions/", params={"course_id": course_id}) if course_id else None
    session_id = session.get("id") if session else None
    class_id = session.get("class_id") if session else None
    teacher_id = session.get("teacher_id") if session else None

    print("\nResolved IDs from DB:")
    print(f"  campus_id   = {campus_id}")
    print(f"  building_id = {building_id}")
    print(f"  room_id     = {room_id}")
    print(f"  term_id     = {term_id}")
    print(f"  course_id   = {course_id}")
    print(f"  student_id  = {student_id}")
    print(f"  session_id  = {session_id}")
    print(f"  class_id    = {class_id}")
    print(f"  teacher_id  = {teacher_id}")

    dummy = "00000000-0000-0000-0000-000000000001"

    print("\nRunning GET tests...")

    run_request(results, "GET /campuses/", "GET", f"{base_url}/campuses/")
    run_request(results, "GET /campuses/?campus_id=", "GET", f"{base_url}/campuses/", params={"campus_id": campus_id})
    run_request(results, "GET /buildings/", "GET", f"{base_url}/buildings/")
    run_request(results, "GET /buildings/?campus_id=", "GET", f"{base_url}/buildings/", params={"campus_id": campus_id})
    run_request(results, "GET /rooms/", "GET", f"{base_url}/rooms/")
    run_request(results, "GET /rooms/?building_id=", "GET", f"{base_url}/rooms/", params={"building_id": building_id})

    run_request(results, "GET /terms/", "GET", f"{base_url}/terms/")
    run_request(results, "GET /terms/?term_id=", "GET", f"{base_url}/terms/", params={"term_id": term_id})
    run_request(results, "GET /terms/by_date/", "GET", f"{base_url}/terms/by_date/", params={"date": "2026-03-01T00:00:00"})

    if term_id:
        run_request(results, "GET /courses/?term_id=", "GET", f"{base_url}/courses/", params={"term_id": term_id})
    else:
        results.append(("SKIP", "-", "GET /courses/?term_id=", "no term_id"))

    if course_id:
        run_request(results, "GET /sessions/?course_id=", "GET", f"{base_url}/sessions/", params={"course_id": course_id})
    else:
        results.append(("SKIP", "-", "GET /sessions/?course_id=", "no course_id"))

    if session_id:
        run_request(results, "GET /sessions/records/", "GET", f"{base_url}/sessions/records/", params={"session_id": session_id})
    else:
        results.append(("SKIP", "-", "GET /sessions/records/", "no session_id"))

    run_request(results, "GET /students/", "GET", f"{base_url}/students/")
    if student_id:
        run_request(results, "GET /students/{id}", "GET", f"{base_url}/students/{student_id}")
    else:
        results.append(("SKIP", "-", "GET /students/{id}", "no student_id"))

    teacher_lookup_id = teacher_id or dummy
    run_request(
        results,
        "GET /classes/teacher_classes/",
        "GET",
        f"{base_url}/classes/teacher_classes/",
        params={"teacher_id": teacher_lookup_id, "start_date": "2026-01-01", "end_date": "2026-12-31"},
    )
    run_request(
        results,
        "GET /classes/teacher/term_course/",
        "GET",
        f"{base_url}/classes/teacher/term_course/",
        params={"teacher_id": teacher_lookup_id},
    )

    student_lookup_id = student_id or dummy
    run_request(
        results,
        "GET /classes/student/term_course/",
        "GET",
        f"{base_url}/classes/student/term_course/",
        params={"student_id": student_lookup_id},
    )

    if class_id:
        run_request(results, "GET /roster/?class_id=", "GET", f"{base_url}/roster/", params={"class_id": class_id})
    else:
        results.append(("SKIP", "-", "GET /roster/?class_id=", "no class_id"))

    if session_id:
        run_request(results, "GET /attendance/current", "GET", f"{base_url}/attendance/current", params={"session_id": session_id})
        run_request(results, "GET /attendance/history (session)", "GET", f"{base_url}/attendance/history", params={"session_id": session_id})
    else:
        results.append(("SKIP", "-", "GET /attendance/current", "no session_id"))
        results.append(("SKIP", "-", "GET /attendance/history (session)", "no session_id"))

    if student_id:
        run_request(results, "GET /attendance/history (student)", "GET", f"{base_url}/attendance/history", params={"student_id": student_id})
    else:
        results.append(("SKIP", "-", "GET /attendance/history (student)", "no student_id"))

    if course_id:
        run_request(results, "GET /attendance/history (course)", "GET", f"{base_url}/attendance/history", params={"course_id": course_id})
    else:
        results.append(("SKIP", "-", "GET /attendance/history (course)", "no course_id"))

    run_request(results, "GET /attendances/teacher/", "GET", f"{base_url}/attendances/teacher/", params={"teacher_id": teacher_lookup_id})
    return results


def print_results(results: list[tuple[str, str, str, str]]) -> int:
    print(f"\n{'STATUS':<8} {'CODE':<6} {'ENDPOINT':<50} RESPONSE")
    print("-" * 115)
    for status, code, label, preview in results:
        marker = "PASS" if status == "PASS" else ("SKIP" if status == "SKIP" else "FAIL")
        print(f"{marker:<8} {code:<6} {label:<50} {preview}")

    passed = sum(1 for result in results if result[0] == "PASS")
    failed = sum(1 for result in results if result[0] in {"FAIL", "ERROR"})
    skipped = sum(1 for result in results if result[0] == "SKIP")
    print(f"\n{passed}/{len(results) - skipped} passed, {failed} failed, {skipped} skipped")
    return 0 if failed == 0 else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run smoke tests against a running backend")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL, default: %(default)s")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run_smoke_tests(base_url=args.base_url)
    return print_results(results)


if __name__ == "__main__":
    raise SystemExit(main())
