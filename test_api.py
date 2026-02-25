import requests
try:
    r = requests.get('http://127.0.0.1:8000/api/verbs?limit=1')
    print(r.status_code)
    print(r.json())
except Exception as e:
    print(e)
