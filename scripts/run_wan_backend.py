import argparse
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Placeholder external backend for Wan video generation")
    parser.add_argument("output_path")
    parser.add_argument("mode")
    args = parser.parse_args()

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(
            [
                "engine=wan21",
                "backend=wan-wrapper-placeholder",
                f"mode={args.mode}",
                f"prompt={os.getenv('AISD_SHOT_PROMPT', '')}",
                f"reference={os.getenv('AISD_REFERENCE_PATH', '') or 'none'}",
                f"model_id={os.getenv('AISD_MODEL_ID', '')}",
            ]
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
