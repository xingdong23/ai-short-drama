from pathlib import Path


class BGMMixer:
    def select_track(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        bgm_path = output_dir / "bgm.txt"
        bgm_path.write_text("bgm=placeholder", encoding="utf-8")
        return bgm_path
