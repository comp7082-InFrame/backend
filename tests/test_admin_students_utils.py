import unittest
import uuid

from app.utils.admin_students import is_currently_seen, parse_course_ids


class AdminStudentUtilsTests(unittest.TestCase):
    def test_parse_course_ids_deduplicates_valid_values(self):
        course_id = uuid.uuid4()

        parsed = parse_course_ids(f'["{course_id}", "{course_id}"]')

        self.assertEqual(parsed, [course_id])

    def test_parse_course_ids_rejects_non_array_json(self):
        with self.assertRaises(ValueError):
            parse_course_ids('{"course_id": "bad"}')

    def test_is_currently_seen_only_for_non_absent_status(self):
        self.assertTrue(is_currently_seen("entering"))
        self.assertTrue(is_currently_seen("present"))
        self.assertFalse(is_currently_seen("absent"))
        self.assertFalse(is_currently_seen(None))


if __name__ == "__main__":
    unittest.main()
