"""
End-to-end integration test for the Flask/Rasa REST API server.
"""

import sys
import time
import requests
import subprocess
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5005"

def test_endpoints():
    print("Testing /health endpoint...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    print("Health response:", r.json())

    print("\nTesting /webhooks/rest/webhook with greeting...")
    r = requests.post(f"{BASE_URL}/webhooks/rest/webhook", json={
        "sender": "test_user",
        "message": "Hello"
    })
    assert r.status_code == 200
    res = r.json()
    print("Greeting response received:", len(res), "messages")
    print("Message 0 text:", res[0]["text"][:60], "...")

    print("\nTesting /webhooks/rest/webhook with emotion query...")
    r = requests.post(f"{BASE_URL}/webhooks/rest/webhook", json={
        "sender": "test_user",
        "message": "I feel stressed out with work"
    })
    assert r.status_code == 200
    res = r.json()
    print("Emotion response received:", len(res), "messages")
    for msg in res:
        print("-", msg.get("text", "")[:60])

    print("\nTesting /model/parse endpoint...")
    r = requests.post(f"{BASE_URL}/model/parse", json={
        "text": "Give me a motivation quote"
    })
    assert r.status_code == 200
    parse_data = r.json()
    print("Parsed Intent:", parse_data["intent"])
    print("Parsed Entities:", parse_data["entities"])

    print("\nTesting static frontend serving...")
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200
    assert "<title>AuraQuotes AI" in r.text
    print("Frontend HTML served successfully!")

    print("\n🎉 ALL END-TO-END SERVER TESTS PASSED!")

if __name__ == "__main__":
    test_endpoints()
