from pathlib import Path

from src.utils.binaries import resolve_binary


def test_resolve_binary_prefers_explicit_path(tmp_path: Path, monkeypatch) -> None:
    explicit = tmp_path / "ffmpeg"
    explicit.write_text("binary", encoding="utf-8")

    monkeypatch.setenv("AISD_FFMPEG_PATH", str(tmp_path / "ignored"))
    monkeypatch.setattr("shutil.which", lambda _: str(tmp_path / "which"))

    resolution = resolve_binary(
        explicit_path=explicit,
        env_var_name="AISD_FFMPEG_PATH",
        fallback_names=["ffmpeg"],
    )

    assert resolution is not None
    assert resolution.path == explicit
    assert resolution.source == "explicit"


def test_resolve_binary_uses_env_before_path(tmp_path: Path, monkeypatch) -> None:
    env_binary = tmp_path / "ffprobe"
    env_binary.write_text("binary", encoding="utf-8")

    monkeypatch.setenv("AISD_FFPROBE_PATH", str(env_binary))
    monkeypatch.setattr("shutil.which", lambda _: str(tmp_path / "which"))

    resolution = resolve_binary(
        explicit_path=None,
        env_var_name="AISD_FFPROBE_PATH",
        fallback_names=["ffprobe"],
    )

    assert resolution is not None
    assert resolution.path == env_binary
    assert resolution.source == "env"


def test_resolve_binary_falls_back_to_path_lookup(monkeypatch) -> None:
    monkeypatch.delenv("AISD_FFMPEG_PATH", raising=False)
    monkeypatch.setattr("shutil.which", lambda _: "/usr/local/bin/ffmpeg")

    resolution = resolve_binary(
        explicit_path=None,
        env_var_name="AISD_FFMPEG_PATH",
        fallback_names=["ffmpeg"],
    )

    assert resolution is not None
    assert resolution.path == Path("/usr/local/bin/ffmpeg")
    assert resolution.source == "path"


def test_resolve_binary_returns_none_when_missing(monkeypatch) -> None:
    monkeypatch.delenv("AISD_FFMPEG_PATH", raising=False)
    monkeypatch.setattr("shutil.which", lambda _: None)

    resolution = resolve_binary(
        explicit_path=None,
        env_var_name="AISD_FFMPEG_PATH",
        fallback_names=["ffmpeg"],
    )

    assert resolution is None
