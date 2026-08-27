import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_url(url):
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

project_id = "0a1786cf-b4d9-4b1b-93cb-5594db0de143"
state_url = f"http://localhost:8000/projects/{project_id}/pipeline-state"
state = get_url(state_url)
print("=== PIPELINE STATE FOR 0a1786cf-b4d9-4b1b-93cb-5594db0de143 ===")
print(json.dumps(state, indent=2))
