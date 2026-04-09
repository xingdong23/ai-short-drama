from src.scriptwriter.engine import ScriptwriterEngine


class StubLLMClient:
    def __init__(self, response: str | Exception) -> None:
        self.response = response

    def generate_script(self, theme: str) -> str:
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_scriptwriter_uses_valid_llm_response() -> None:
    engine = ScriptwriterEngine(
        llm_client=StubLLMClient(
            """
            {
              "title": "Episode 1: Office Revenge",
              "theme": "office revenge",
              "scenes": [
                {
                  "id": "shot_001",
                  "type": "dialogue",
                  "prompt": "An employee confronts her manager in a glass meeting room",
                  "character": "xiaomei",
                  "dialogue": "You thought nobody would find out.",
                  "duration": 4,
                  "camera": "close_up"
                }
              ]
            }
            """
        )
    )

    script = engine.generate("office revenge")

    assert script.title == "Episode 1: Office Revenge"
    assert len(script.scenes) == 1
    assert script.scenes[0].dialogue == "You thought nobody would find out."


def test_scriptwriter_accepts_fenced_json_llm_response() -> None:
    engine = ScriptwriterEngine(
        llm_client=StubLLMClient(
            """```json
            {
              "title": "Episode 1: Campus Secrets",
              "theme": "campus secrets",
              "scenes": [
                {
                  "id": "shot_001",
                  "type": "establishing",
                  "prompt": "A rainy campus walkway at dusk",
                  "character": null,
                  "dialogue": null,
                  "duration": 3,
                  "camera": "slow_pan"
                }
              ]
            }
            ```"""
        )
    )

    script = engine.generate("campus secrets")

    assert script.title == "Episode 1: Campus Secrets"
    assert script.scenes[0].type == "establishing"


def test_scriptwriter_falls_back_when_llm_fails() -> None:
    engine = ScriptwriterEngine(llm_client=StubLLMClient(RuntimeError("boom")))

    script = engine.generate("city romance")

    assert script.title == "Episode 1: City Romance"
    assert len(script.scenes) == 3
    assert script.scenes[1].character == "xiaomei"
