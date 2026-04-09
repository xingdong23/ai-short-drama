import argparse
from pathlib import Path

from src.character.lora_trainer import LoRATrainer


def main() -> int:
    parser = argparse.ArgumentParser(description="Train placeholder LoRA weights")
    parser.add_argument("--character", required=True)
    parser.add_argument("--output-dir", default="assets/lora")
    args = parser.parse_args()

    output_path = LoRATrainer().train(args.character, Path(args.output_dir))
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
