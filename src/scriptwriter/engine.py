import argparse
import json
import logging
import re
from typing import Protocol

from src.scriptwriter.llm_client import OpenAICompatibleLLMClient
from src.scriptwriter.storyboard import Script, Shot


logger = logging.getLogger(__name__)


class ScriptGenerationClient(Protocol):
    def generate_script(self, theme: str) -> str: ...


class ScriptwriterEngine:
    def __init__(self, llm_client: ScriptGenerationClient | None = None) -> None:
        self.llm_client = llm_client or OpenAICompatibleLLMClient.from_env()

    def generate(self, theme: str) -> Script:
        clean_theme = theme.strip() or "untitled story"
        llm_script = self._try_generate_from_llm(clean_theme)
        if llm_script is not None:
            return llm_script

        return self._generate_placeholder_script(clean_theme)

    def _try_generate_from_llm(self, theme: str) -> Script | None:
        if self.llm_client is None:
            return None

        try:
            raw_response = self.llm_client.generate_script(theme)
            payload = json.loads(self._strip_markdown_fences(raw_response))
            return Script.from_dict(payload)
        except Exception as exc:
            logger.warning("LLM script generation failed; falling back to placeholder script: %s", exc)
            return None

    def _generate_placeholder_script(self, clean_theme: str) -> Script:
        title = f"Episode 1: {clean_theme.title()}"
        scenes = [
            Shot(
                id="shot_001",
                type="establishing",
                prompt=f"Atmospheric city establishing shot for {clean_theme}",
                character=None,
                dialogue=None,
                duration=3,
                camera="slow_pan",
            ),
            Shot(
                id="shot_002",
                type="dialogue",
                prompt=f"Xiaomei reacts emotionally within the theme of {clean_theme}",
                character="xiaomei",
                dialogue=f"This story begins with {clean_theme}.",
                duration=4,
                camera="close_up",
            ),
            Shot(
                id="shot_003",
                type="transition",
                prompt=f"Transition shot that escalates tension around {clean_theme}",
                character=None,
                dialogue=None,
                duration=2,
                camera="push_in",
            ),
        ]
        return Script(title=title, theme=clean_theme, scenes=scenes)

    def _strip_markdown_fences(self, text: str) -> str:
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
        return stripped.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a placeholder AI short drama script.")
    parser.add_argument("--theme", required=True, help="Story theme or outline")
    args = parser.parse_args()

    script = ScriptwriterEngine().generate(args.theme)
    print(json.dumps(script.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
