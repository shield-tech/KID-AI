import pytest

from kid.security import PermissionDeniedError, ToolExecutor


def test_tool_executor_blocks_outside_allowed_roots():
    executor = ToolExecutor()
    with pytest.raises(PermissionDeniedError):
        executor.read_text("/etc/passwd")


def test_tool_executor_allows_local_project_files(tmp_path):
    executor = ToolExecutor()
    target = tmp_path / "example.txt"
    target.write_text("hello", encoding="utf-8")
    assert executor.read_text(target) == "hello"


def test_tool_executor_rejects_unsafe_commands():
    executor = ToolExecutor()
    with pytest.raises(PermissionDeniedError):
        executor.run_command("rm -rf /tmp")
