import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import os
import shutil
import tempfile

from antigravity_cua.engine import SandboxEngine
from antigravity_cua.config import CuaConfig
from antigravity_cua.session_manager import SessionManager
from antigravity_cua.exceptions import SandboxNotFoundError

class TestSandboxEngine(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_engine.db")
        self.config = CuaConfig(
            provider="modal",
            default_image="test-image:latest",
            default_lease_minutes=10,
            db_path=self.db_path
        )
        self.engine = SandboxEngine(config=self.config)
        self.engine.session_manager = SessionManager(db_path=self.db_path)

    def tearDown(self):
        if hasattr(self.engine, "session_manager"):
            self.engine.session_manager.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    async def test_spawn_and_get_session(self):
        with patch.object(self.engine, "_get_cua") as mock_get_cua:
            mock_cua = MagicMock()
            mock_cua.create = AsyncMock(return_value=MagicMock(space=MagicMock(id="box-1")))
            mock_get_cua.return_value = mock_cua

            session = await self.engine.spawn_sandbox("box-1")
            self.assertEqual(session.space_id, "box-1")
            self.assertEqual(session.provider, "modal")

            fetched = self.engine.session_manager.get_session("box-1")
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.space_id, "box-1")

    async def test_virtual_mouse_click(self):
        with patch.object(self.engine, "execute_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"stdout": "", "stderr": "", "exit_code": 0}
            res = await self.engine.virtual_mouse_click("box-1", 100, 200, button="left")
            mock_exec.assert_called_once_with("box-1", "DISPLAY=:99 xdotool mousemove 100 200 click 1")

    async def test_virtual_keyboard_type(self):
        with patch.object(self.engine, "execute_command", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"stdout": "", "stderr": "", "exit_code": 0}
            res = await self.engine.virtual_keyboard_type("box-1", "hello world")
            self.assertTrue(mock_exec.called)
            args = mock_exec.call_args[0]
            self.assertIn("xdotool type", args[1])
            self.assertIn("hello world", args[1])

    async def test_reap_orphaned_sandboxes(self):
        self.engine.session_manager.register_session("box-expired", "modal", "img", lease_seconds=-10)
        with patch.object(self.engine, "_get_cua") as mock_get_cua:
            mock_cua = MagicMock()
            mock_cua.delete = AsyncMock()
            mock_get_cua.return_value = mock_cua

            reaped = await self.engine.reap_orphaned_sandboxes()
            self.assertEqual(reaped, 1)
            mock_cua.delete.assert_called_once_with("box-expired")

if __name__ == "__main__":
    unittest.main()
