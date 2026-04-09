import argparse
import json

from src.scriptwriter.storyboard import Script, Shot


class ScriptwriterEngine:
    def generate(self, theme: str) -> Script:
        clean_theme = theme.strip() or "untitled story"
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a placeholder AI short drama script.")
    parser.add_argument("--theme", required=True, help="Story theme or outline")
    args = parser.parse_args()

    script = ScriptwriterEngine().generate(args.theme)
    print(json.dumps(script.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
