from pydantic import BaseModel
from typing import List


class EvaluationCheck(BaseModel):
    criterion: str
    passed: bool
    reason: str


class EvaluationResult(BaseModel):
    overall_pass: bool
    checks: List[EvaluationCheck]
    summary: str