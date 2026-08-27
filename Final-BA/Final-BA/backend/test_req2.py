import urllib.request, json
import urllib.error
import time

data = json.dumps({'file_path': 'app/sample_input_final.txt', 'max_retry_attempts': 3}).encode()
req = urllib.request.Request('http://localhost:8000/api/workflow/start', data=data, headers={'Content-Type':'application/json'})

try:
    print("Starting workflow...")
    res = urllib.request.urlopen(req)
    response_data = json.loads(res.read().decode())
    print("Start response:", response_data)
    
    workflow_id = response_data['workflow_id']
    print(f"\nPolling status for workflow: {workflow_id}")
    
    for _ in range(50):
        time.sleep(5)
        status_req = urllib.request.Request(f'http://localhost:8000/api/workflow/{workflow_id}/status')
        status_res = urllib.request.urlopen(status_req)
        status_data = json.loads(status_res.read().decode())
        print("Status:", status_data['workflow_status'])
        if status_data['workflow_status'] == 'FAILED':
            print("Status Data:", json.dumps(status_data, indent=2))
            break

            
except urllib.error.HTTPError as e:
    print("HTTP Error", e.code)
    print(e.read().decode())
