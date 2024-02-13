from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid1


@dataclass
class SubprocessResult:
    id: str = field(default_factory=lambda: str(uuid1()).replace('-', ''))
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    returncode: Optional[int] = None
    killed_by_token: bool = False
