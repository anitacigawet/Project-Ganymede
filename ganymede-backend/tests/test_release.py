from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.services.substrate import ClaudeCliRunner, assemble_corpus


class ReleaseBoundaryTests(unittest.TestCase):
    def test_foundation_corpus_is_present(self) -> None:
        corpus = assemble_corpus()
        self.assertGreater(len(corpus), 10_000)
        self.assertIn("FOUNDATION DOCUMENT", corpus)

    def test_engine_command_disables_tools(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            system_file = Path(directory) / "system.txt"
            system_file.write_text("test", encoding="utf-8")
            with patch.dict(os.environ, {"GANYMEDE_CLAUDE_BIN": sys.executable}):
                command = ClaudeCliRunner()._base_command(
                    system_file=system_file, tools=[]
                )
        self.assertIn("--tools", command)
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertIn("--strict-mcp-config", command)
        self.assertIn("--no-session-persistence", command)

    def test_research_command_allows_only_web_search(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            system_file = Path(directory) / "system.txt"
            system_file.write_text("test", encoding="utf-8")
            with patch.dict(os.environ, {"GANYMEDE_CLAUDE_BIN": sys.executable}):
                command = ClaudeCliRunner()._base_command(
                    system_file=system_file, tools=["WebSearch"]
                )
        self.assertEqual(command[command.index("--tools") + 1], "WebSearch")
        allowed = command[command.index("--allowedTools") + 1 :]
        self.assertEqual(allowed, ["WebSearch"])

    def test_release_does_not_ship_notebook_runtime(self) -> None:
        forbidden = [
            BACKEND / "app" / "services" / "notebooklm",
            BACKEND / "app" / "v2_notebook_routes.py",
            REPO / "ganymede-backend" / "venv_312",
        ]
        self.assertFalse(any(path.exists() for path in forbidden))


if __name__ == "__main__":
    unittest.main()
