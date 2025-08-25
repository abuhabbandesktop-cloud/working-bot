import requests

BASE_URL = "http://127.0.0.1:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImtpbmQiOiJhY2Nlc3MiLCJpYXQiOjE3NTU5OTQ4MTcsImV4cCI6MTc1NjAzODAxN30.68EWaOEiJdVr7JF7k9RlrUZ8zkPsKfx7K-heXPTqmf8"   # paste from login response
CHAT_ID = "1033291787"      # replace with actual chat id

headers = {"Authorization": f"Bearer {TOKEN}"}

# List chats
res_chats = requests.get(f"{BASE_URL}/api/chats", headers=headers)
print("Chats:", res_chats.json())

# List messages for a chat
res_msgs = requests.get(f"{BASE_URL}/api/messages?chat_id={CHAT_ID}", headers=headers)
print("Messages:", res_msgs.json())
