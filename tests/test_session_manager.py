import time
import tempfile
from pathlib import Path
import unittest

from antigravity_cua.session_manager import SessionManager

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_state.db"
        self.manager = SessionManager(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_register_and_get_session(self):
        session = self.manager.register_session(
            space_id="test-box-1",
            provider="cloud",
            image="test-image",
            lease_seconds=300
        )
        self.assertEqual(session.space_id, "test-box-1")
        self.assertEqual(session.status, "active")

        retrieved = self.manager.get_session("test-box-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.space_id, "test-box-1")
        self.assertEqual(retrieved.provider, "cloud")

    def test_renew_lease(self):
        self.manager.register_session("test-box-renew", "cloud", "img", lease_seconds=10)
        old_expiry = self.manager.get_session("test-box-renew").lease_expires_at

        time.sleep(0.05)
        new_expiry = self.manager.renew_lease("test-box-renew", extend_seconds=600)
        self.assertGreater(new_expiry, old_expiry)

    def test_list_expired_and_remove(self):
        # Register session with negative TTL (already expired)
        self.manager.register_session("expired-box", "cloud", "img", lease_seconds=-10)
        self.manager.register_session("active-box", "cloud", "img", lease_seconds=600)

        expired = self.manager.list_expired()
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0].space_id, "expired-box")

        # Test cleanup
        removed = self.manager.remove_session("expired-box")
        self.assertTrue(removed)
        self.assertEqual(len(self.manager.list_expired()), 0)

if __name__ == "__main__":
    unittest.main()
