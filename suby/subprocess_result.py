from dataclasses import dataclass
from typing import Optional


@dataclass
class SubprocessResult:
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    returncode: Optional[int] = None
    killed_by_token: bool = False
