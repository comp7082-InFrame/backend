import unittest


class RouteImportTests(unittest.TestCase):
    def test_api_router_imports(self):
        from app.api.routes import api_router

        self.assertIsNotNone(api_router)
        self.assertGreater(len(api_router.routes), 0)
