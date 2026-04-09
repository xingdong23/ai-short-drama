from pathlib import Path


class LoRATrainer:
    def train(self, character_name: str, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        weights_path = output_dir / f"{character_name}.safetensors"
        weights_path.write_text("placeholder-lora-weights", encoding="utf-8")
        return weights_path
