import requests
import json

url = "http://localhost:8000/pipeline/run"
payload = {
    "project_path": "scratch/test_workspace/react_large",
    "run_until": "validation",
    "include_timings": True,
    "include_intermediate_outputs": True
}

try:
    res = requests.post(url, json=payload)
    print("Status code:", res.status_code)
    data = res.json()
    print("Pipeline run status:", data.get("status"))
    print("Completed stages:", data.get("completed_stages"))
    outputs = data.get("outputs", {})
    print("Outputs keys:", list(outputs.keys()))
    exec_report = outputs.get("execution_report")
    if exec_report:
        print("Execution report is present!")
        print(json.dumps(exec_report, indent=2)[:500])
    else:
        print("Execution report is missing!")
except Exception as e:
    print("Error calling endpoint:", e)
