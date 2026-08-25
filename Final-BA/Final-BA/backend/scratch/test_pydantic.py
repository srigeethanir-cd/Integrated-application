import sys
from pathlib import Path

backend_dir = Path(r"D:\Design\Final-BA\Final-BA\backend")
sys.path.insert(0, str(backend_dir))

from app.agents.epic_agent_2 import EpicGenerationOutput
from pydantic import ValidationError

invalid_json = """
{
  "epics": [
    {
      "id": "EPIC-001",
      "name": "Auth",
      "description": "Auth stuff"
    }
  ]
}
"""

try:
    parsed = EpicGenerationOutput.model_validate_json(invalid_json)
    print("SUCCESS")
    print(parsed.model_dump_json(indent=2))
except ValidationError as exc:
    print(str(exc))
