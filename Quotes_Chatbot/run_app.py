
import sys
import os
import time
import webbrowser
import threading

# Reconfigure stdout for UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CURRENT_DIR, "backend")

sys.path.insert(0, BACKEND_DIR)

from app import app

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5005")

if __name__ == "__main__":
    print("=" * 65)
    print("🌟 QUOTES RECOMMENDATION CHATBOT USING NLP & RASA ARCHITECTURE 🌟")
    print("=" * 65)
    print("✓ NLP Intent Classifier loaded")
    print("✓ Emotion & Sentiment Analyzer ready")
    print("✓ Rasa REST API webhook active on: http://127.0.0.1:5005/webhooks/rest/webhook")
    print("✓ Rasa NLU parse active on:        http://127.0.0.1:5005/model/parse")
    print("✓ Web Interface live at:            http://127.0.0.1:5005/")
    print("=" * 65)
    print("Opening web interface in your default browser...\n")

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=5005, debug=False)
