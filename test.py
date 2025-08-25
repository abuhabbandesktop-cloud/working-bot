import requests

url = "http://127.0.0.1:8000/api/auth/login"
payload = {"username": "admin", "password": "admin"}

res = requests.post(url, json=payload)
print(res.json())
