import urllib.request, json
import urllib.error

data = json.dumps({'issue_key':'KAN-2'}).encode()
req = urllib.request.Request('http://localhost:8000/api/workflow/mcp/jira/start', data=data, headers={'Content-Type':'application/json'})
try:
    res = urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print("HTTP Error", e.code)
    print(e.read().decode())
