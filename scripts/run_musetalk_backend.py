import argparse
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Placeholder external backend for MuseTalk lip sync")
    parser.add_argument("output_path")
    args = parser.parse_args()

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(
            [
                "engine=musetalk",
                "backend=musetalk-wrapper-placeholder",
                f"shot_id={os.getenv('AISD_SHOT_ID', '')}",
                f"source_clip={os.getenv('AISD_SOURCE_CLIP_PATH', '') or 'none'}",
                f"audio_path={os.getenv('AISD_AUDIO_PATH', '') or 'none'}",
                f"model_id={os.getenv('AISD_MODEL_ID', '')}",
            ]
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
