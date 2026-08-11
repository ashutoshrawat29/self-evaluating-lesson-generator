from typing import TypedDict, Optional, List, Dict, Any


class LessonState(TypedDict):

    topic: str

    lesson: str

    evaluation: Optional[Dict[str, Any]]

    rejection_log: List[Dict[str, Any]]

    retry_count: int

    max_retries: int

    memory: List[Dict[str, Any]]

    precheck_results: Dict[str, bool]

    status: str