from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class Command:
    id: str
    display_name: str
    context: str
    required_permission: Optional[str]
    handler: Callable
    description: str
    is_safe: bool = True
