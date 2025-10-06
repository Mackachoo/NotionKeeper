from io import TextIOWrapper
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Element:
    name: str
    context: Optional[str] = None
    subelements: List["Element"] = None

    def __post_init__(self):
        if self.subelements is None:
            self.subelements = []
