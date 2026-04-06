import unittest
import importlib.util


class RouteImportTests(unittest.TestCase):
    def test_api_router_imports(self):
        if importlib.util.find_spec("pydantic_settings") is None:
            self.skipTest("backend dependencies are not installed in this environment")

        from app.api.routes import api_router

        self.assertIsNotNone(api_router)
        self.assertGreater(len(api_router.routes), 0)


if __name__ == "__main__":
    unittest.main()
