import unittest
import json
from antigravity_cua.spacesd_client import SpacesDClient, ExecStreamChunk

class TestSpacesDClient(unittest.TestCase):
    def test_client_init(self):
        client = SpacesDClient("http://127.0.0.1:4444", token="secret")
        self.assertEqual(client.base_url, "http://127.0.0.1:4444")
        self.assertEqual(client._headers.get("Authorization"), "Bearer secret")

    def test_exec_stream_chunk_structure(self):
        chunk = ExecStreamChunk(stream="stdout", data="hello world\n", exit_code=None)
        self.assertEqual(chunk.stream, "stdout")
        self.assertEqual(chunk.data, "hello world\n")
        self.assertIsNone(chunk.exit_code)

if __name__ == "__main__":
    unittest.main()
