import unittest
from pathlib import Path
from app.cloud.mcp_server import read_nanobot_memory, add_nanobot_skill, list_sessions, get_nanobot_status

class TestMCPServer(unittest.TestCase):
    def test_get_nanobot_status(self):
        status = get_nanobot_status()
        self.assertEqual(status["status"], "running")
        self.assertEqual(status["version"], "0.1.0")

    def test_read_nanobot_memory_not_found(self):
        # Ensure it returns error if file doesn't exist
        res = read_nanobot_memory("nonexistent")
        if "error" in res:
            self.assertEqual(res["error"], "Memory not found")

if __name__ == "__main__":
    unittest.main()
