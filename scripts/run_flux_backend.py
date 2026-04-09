import argparse
import os
from pathlib import Path

from backend_wrapper_common import build_template_fields
from backend_wrapper_common import run_delegate_command


def main() -> int:
    parser = argparse.ArgumentParser(description="Placeholder external backend for Flux reference generation")
    parser.add_argument("output_path")
    parser.add_argument("character")
    args = parser.parse_args()

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    delegate_result = run_delegate_command(
        "AISD_FLUX_DELEGATE_CMD",
        build_template_fields(
            output_path,
            character=args.character,
        ),
    )
    if delegate_result is not None:
        return delegate_result

    output_path.write_text(
        "\n".join(
            [
                "generator=flux-wrapper-placeholder",
                f"character={args.character}",
                f"prompt={os.getenv('AISD_SHOT_PROMPT', '')}",
                f"model_id={os.getenv('AISD_MODEL_ID', '')}",
            ]
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
