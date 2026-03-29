"""
Endpoint smoke test — run while backend is running on localhost:8000.
Usage: python test_endpoints.py
"""
import requests

BASE = "http://localhost:8000/api"
results = []

def test(label, method, url, **kwargs):
    try:
        r = requests.request(method, url, timeout=10, **kwargs)
        status = "PASS" if r.status_code < 400 else "FAIL"
        data_preview = ""
        try:
            body = r.json()
            if isinstance(body, list):
                data_preview = f"{len(body)} items"
            elif isinstance(body, dict):
                data_preview = str(list(body.keys()))[:60]
        except Exception:
            data_preview = r.text[:60]
        results.append((status, r.status_code, label, data_preview))
        return r
    except Exception as e:
        results.append(("ERROR", "-", label, str(e)[:60]))
        return None

def get_first(url, params=None):
    """Fetch a list endpoint and return the first item, or None."""
    try:
        r = requests.get(url, params=params, timeout=10)
        body = r.json()
        if isinstance(body, list) and len(body) > 0:
            return body[0]
        if isinstance(body, dict):
            for v in body.values():
                if isinstance(v, list) and len(v) > 0:
                    return v[0]
    except Exception:
        pass
    return None

# ── Step 1: Fetch real IDs from DB ──────────────────────────────────────────
campus      = get_first(f"{BASE}/campuses/")
building    = get_first(f"{BASE}/buildings/")
room        = get_first(f"{BASE}/rooms/")
term        = get_first(f"{BASE}/terms/")
student     = get_first(f"{BASE}/students/")

campus_id   = campus.get("id")          if campus   else None
building_id = building.get("id")        if building else None
room_id     = room.get("id")            if room     else None
term_id     = term.get("id")            if term     else None
student_id  = student.get("id")         if student  else None

course      = get_first(f"{BASE}/courses/", params={"term_id": term_id}) if term_id else None
course_id   = course.get("id")          if course   else None

# Fetch a class_id from sessions or classes endpoints
session     = get_first(f"{BASE}/sessions/", params={"course_id": course_id}) if course_id else None
session_id  = session.get("id")         if session  else None
class_id    = session.get("class_id")   if session  else None

# Try to get a teacher_id from the session
teacher_id  = session.get("teacher_id") if session  else None

print(f"\nResolved IDs from DB:")
print(f"  campus_id   = {campus_id}")
print(f"  building_id = {building_id}")
print(f"  room_id     = {room_id}")
print(f"  term_id     = {term_id}")
print(f"  course_id   = {course_id}")
print(f"  student_id  = {student_id}")
print(f"  session_id  = {session_id}")
print(f"  class_id    = {class_id}")
print(f"  teacher_id  = {teacher_id}")

# Fallback dummy UUID for endpoints that need an ID but we don't have one
dummy = "00000000-0000-0000-0000-000000000001"

# ── Step 2: Run all GET tests ────────────────────────────────────────────────
print("\nRunning GET tests...")

# Location
test("GET /campuses/",                    "GET", f"{BASE}/campuses/")
test("GET /campuses/?campus_id=",         "GET", f"{BASE}/campuses/", params={"campus_id": campus_id})
test("GET /buildings/",                   "GET", f"{BASE}/buildings/")
test("GET /buildings/?campus_id=",        "GET", f"{BASE}/buildings/", params={"campus_id": campus_id})
test("GET /rooms/",                       "GET", f"{BASE}/rooms/")
test("GET /rooms/?building_id=",          "GET", f"{BASE}/rooms/", params={"building_id": building_id})

# Academic structure
test("GET /terms/",                       "GET", f"{BASE}/terms/")
test("GET /terms/?term_id=",              "GET", f"{BASE}/terms/", params={"term_id": term_id})
test("GET /terms/by_date/",               "GET", f"{BASE}/terms/by_date/", params={"date": "2026-03-01T00:00:00"})

if term_id:
    test("GET /courses/?term_id=",        "GET", f"{BASE}/courses/", params={"term_id": term_id})
else:
    results.append(("SKIP", "-", "GET /courses/?term_id=", "no term_id"))

if course_id:
    test("GET /sessions/?course_id=",     "GET", f"{BASE}/sessions/", params={"course_id": course_id})
else:
    results.append(("SKIP", "-", "GET /sessions/?course_id=", "no course_id"))

if session_id:
    test("GET /sessions/records/",        "GET", f"{BASE}/sessions/records/", params={"session_id": session_id})
else:
    results.append(("SKIP", "-", "GET /sessions/records/", "no session_id"))

# Users / students
test("GET /students/",                    "GET", f"{BASE}/students/")
if student_id:
    test("GET /students/{id}",            "GET", f"{BASE}/students/{student_id}")
else:
    results.append(("SKIP", "-", "GET /students/{id}", "no student_id"))

# Classes views
_tid = teacher_id or dummy
test("GET /classes/teacher_classes/",     "GET", f"{BASE}/classes/teacher_classes/",
     params={"teacher_id": _tid, "start_date": "2026-01-01", "end_date": "2026-12-31"})
test("GET /classes/teacher/term_course/", "GET", f"{BASE}/classes/teacher/term_course/",
     params={"teacher_id": _tid})
_sid = student_id or dummy
test("GET /classes/student/term_course/", "GET", f"{BASE}/classes/student/term_course/",
     params={"student_id": _sid})

# Roster
if class_id:
    test("GET /roster/?class_id=",        "GET", f"{BASE}/roster/", params={"class_id": class_id})
else:
    results.append(("SKIP", "-", "GET /roster/?class_id=", "no class_id"))

# Attendance
if session_id:
    test("GET /attendance/current",       "GET", f"{BASE}/attendance/current", params={"session_id": session_id})
    test("GET /attendance/history (session)", "GET", f"{BASE}/attendance/history", params={"session_id": session_id})
else:
    results.append(("SKIP", "-", "GET /attendance/current", "no session_id"))
    results.append(("SKIP", "-", "GET /attendance/history (session)", "no session_id"))

if student_id:
    test("GET /attendance/history (student)", "GET", f"{BASE}/attendance/history", params={"student_id": student_id})
else:
    results.append(("SKIP", "-", "GET /attendance/history (student)", "no student_id"))

if course_id:
    test("GET /attendance/history (course)", "GET", f"{BASE}/attendance/history", params={"course_id": course_id})
else:
    results.append(("SKIP", "-", "GET /attendance/history (course)", "no course_id"))

# Attendances (teacher summary view)
test("GET /attendances/teacher/",         "GET", f"{BASE}/attendances/teacher/", params={"teacher_id": _tid})

# ── Step 3: Print results ────────────────────────────────────────────────────
print(f"\n{'STATUS':<8} {'CODE':<6} {'ENDPOINT':<50} {'RESPONSE'}")
print("-" * 115)
for status, code, label, preview in results:
    marker = "✓" if status == "PASS" else ("~" if status == "SKIP" else "✗")
    print(f"{marker} {status:<6} {str(code):<6} {label:<50} {preview}")

passed  = sum(1 for r in results if r[0] == "PASS")
failed  = sum(1 for r in results if r[0] == "FAIL")
skipped = sum(1 for r in results if r[0] == "SKIP")
print(f"\n{passed}/{len(results) - skipped} passed, {failed} failed, {skipped} skipped")
