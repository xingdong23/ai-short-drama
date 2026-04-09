import argparse
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Placeholder external backend for CosyVoice synthesis")
    parser.add_argument("output_path")
    args = parser.parse_args()

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(
            [
                "engine=cosyvoice",
                "backend=cosyvoice-wrapper-placeholder",
                f"shot_id={os.getenv('AISD_SHOT_ID', '')}",
                f"character={os.getenv('AISD_CHARACTER', '')}",
                f"dialogue={os.getenv('AISD_SHOT_DIALOGUE', '')}",
                f"model_id={os.getenv('AISD_MODEL_ID', '')}",
            ]
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
