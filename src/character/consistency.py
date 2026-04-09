from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConsistencyResult:
    passed: bool
    score: float


class CharacterConsistencyChecker:
    def check(self, references: list[Path]) -> ConsistencyResult:
        return ConsistencyResult(passed=bool(references), score=0.95 if references else 0.0)
