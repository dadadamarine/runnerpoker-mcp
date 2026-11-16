import subprocess

import pytest

from runnerpoker_mcp import clipboard

KOREAN_HAND_LINE = "비질게: posts big blind 10000000"


class RecordingRun:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def __call__(self, command, **options):
        self.calls.append((command, options))
        if self.error:
            raise self.error
        return subprocess.CompletedProcess(command, 0)


def use_platform(monkeypatch, platform, run):
    monkeypatch.setattr(clipboard.sys, "platform", platform)
    monkeypatch.setattr(clipboard.subprocess, "run", run)


def test_copy_text_pipes_utf8_bytes_to_pbcopy_on_macos(monkeypatch):
    run = RecordingRun()
    use_platform(monkeypatch, "darwin", run)

    result = clipboard.copy_text(KOREAN_HAND_LINE)

    assert result == {"copied": True}
    [(command, options)] = run.calls
    assert command == ["/usr/bin/pbcopy"]
    assert options["input"] == KOREAN_HAND_LINE.encode("utf-8")
    assert options["env"]["LC_ALL"] == "en_US.UTF-8"
    assert options["check"] is True
    assert options["timeout"] == clipboard.COPY_TIMEOUT_SECONDS


@pytest.mark.parametrize("platform", ["linux", "win32"])
def test_copy_text_reports_unsupported_platform_without_running_a_command(monkeypatch, platform):
    run = RecordingRun()
    use_platform(monkeypatch, platform, run)

    result = clipboard.copy_text(KOREAN_HAND_LINE)

    assert result == {"copied": False, "reason": "clipboard copy supports macOS only"}
    assert run.calls == []


@pytest.mark.parametrize(
    "error,reason",
    [
        (FileNotFoundError("pbcopy"), "pbcopy failed: FileNotFoundError"),
        (subprocess.CalledProcessError(1, "pbcopy"), "pbcopy failed: CalledProcessError"),
        (subprocess.TimeoutExpired("pbcopy", 5), "pbcopy failed: TimeoutExpired"),
    ],
)
def test_copy_text_reports_the_failure_reason_when_pbcopy_fails(monkeypatch, error, reason):
    use_platform(monkeypatch, "darwin", RecordingRun(error))

    assert clipboard.copy_text(KOREAN_HAND_LINE) == {"copied": False, "reason": reason}
