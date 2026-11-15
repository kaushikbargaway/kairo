import runpy
from unittest.mock import Mock

from servers.notepad.app import mcp


def test_server_starts_and_registers_capabilities(monkeypatch):
    mock_run = Mock()
    monkeypatch.setattr(mcp, "run", mock_run)

    runpy.run_module(
        "servers.notepad.server",
        run_name="__main__"
    )

    mock_run.assert_called_once()

    import servers.notepad.tools
    import servers.notepad.resources
    import servers.notepad.prompts