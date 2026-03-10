from pydantic import Field
from typing import Any, Optional

from vellum.workflows.inputs import BaseInputs


class Inputs(BaseInputs):
    instructor_preferences: Optional[list[dict[str, Any]]] = Field(default_factory=list)
    lessons: list[dict[str, Any]]
