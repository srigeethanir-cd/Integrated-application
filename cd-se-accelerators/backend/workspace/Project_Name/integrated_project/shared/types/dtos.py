from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class BaseEntity:
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


