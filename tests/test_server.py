import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from antigravity_cua.server import (
    cua_spawn_sandbox,
    cua_exec_isolated,
    cua_mouse_click,
    cua_keyboard_type,
    cua_keyboard_key,
    cua_mouse_scroll,
    cua_release_sandbox,
    cua_reap_orphans
)

class TestServerTools(unittest.IsolatedAsyncioTestCase):
    @patch("antigravity_cua.server.engine")
    async def test_cua_spawn_sandbox(self, mock_engine):
        mock_session = MagicMock()
        mock_session.space_id = "test-box"
        mock_session.provider = "modal"
        mock_session.status = "active"
        mock_engine.spawn_sandbox = AsyncMock(return_value=mock_session)

        res = await cua_spawn_sandbox("test-box", lease_minutes=20)
        self.assertIn("Sandbox spawned: id=test-box", res)
        self.assertIn("lease=20m", res)

    @patch("antigravity_cua.server.engine")
    async def test_cua_exec_isolated(self, mock_engine):
        mock_engine.execute_command = AsyncMock(return_value={
            "stdout": "total 4\nfile.txt",
            "stderr": "",
            "exit_code": 0
        })
        res = await cua_exec_isolated("ls -la", "test-box")
        self.assertIn("total 4", res)

    @patch("antigravity_cua.server.engine")
    async def test_cua_mouse_click(self, mock_engine):
        mock_engine.virtual_mouse_click = AsyncMock(return_value={"exit_code": 0})
        res = await cua_mouse_click(50, 100, button="right", space_id="test-box")
        self.assertIn("Clicked right at (50, 100)", res)

    @patch("antigravity_cua.server.engine")
    async def test_cua_keyboard_type(self, mock_engine):
        mock_engine.virtual_keyboard_type = AsyncMock(return_value={"exit_code": 0})
        res = await cua_keyboard_type("search query", space_id="test-box")
        self.assertIn("Typed 'search query...'", res)

    @patch("antigravity_cua.server.engine")
    async def test_cua_release_sandbox(self, mock_engine):
        mock_engine.terminate_sandbox = AsyncMock(return_value=True)
        res = await cua_release_sandbox("test-box")
        self.assertIn("Sandbox 'test-box' released.", res)

    @patch("antigravity_cua.server.engine")
    async def test_cua_reap_orphans(self, mock_engine):
        mock_engine.reap_orphaned_sandboxes = AsyncMock(return_value=3)
        res = await cua_reap_orphans()
        self.assertIn("Reaped 3 expired sandbox(es)", res)

if __name__ == "__main__":
    unittest.main()
