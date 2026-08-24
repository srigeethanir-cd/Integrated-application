from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BaseEntity:
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class AuthenticationDTO(BaseEntity):
    """Data transfer object for Authentication."""
    # TODO: add fields
    data: Dict[str, Any] = field(default_factory=dict)


