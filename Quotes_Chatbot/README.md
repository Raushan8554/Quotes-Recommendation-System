# Quotes Recommendation Chatbot Using NLP & Rasa

An intelligent, context-aware conversational AI system designed to deliver personalized and meaningful quotes based on user emotional state, mood, preferences, and interests.

---

## 📖 Overview

The **Quotes Recommendation Chatbot** addresses the need for quick motivation, inspiration, humor, or emotional reassurance by offering instant, personalized quote recommendations through natural language conversations.

It leverages **Rasa Conversational AI Architecture** and an integrated **NLP/Machine Learning Engine** to:
- Understand user queries and identify intents with high confidence.
- Detect emotional states (e.g., sadness, stress, anxiety, lack of motivation, heartbreak, joy, ambition).
- Recommend context-aware quotes from categories: **Motivation**, **Inspiration**, **Success**, **Love**, and **Humor**.
- Engage users with follow-up satisfaction questions and deep reflections/life advice.
- Expose a standard **Rasa REST API channel (`/webhooks/rest/webhook`)** for seamless communication with a modern, responsive web frontend.

---

## 🛠️ Required Technologies & Skills

| Domain | Technology / Tool |
|---|---|
| **Natural Language Processing & ML** | `scikit-learn`, `TF-IDF Vectorizer`, `Multinomial Naive Bayes`, Sentiment & Emotion Analysis |
| **Conversational AI Framework** | Rasa 3.x Architecture (`nlu.yml`, `domain.yml`, `stories.yml`, `rules.yml`, `config.yml`, `actions.py`) |
| **Backend & REST API** | Python, `Flask`, `Flask-CORS`, REST API webhook integration |
| **Generative AI & Well-Being** | Contextual empathy generation, deeper quote reflections & life advice |
| **Frontend & UI/UX** | Modern HTML5, CSS3 Glassmorphism, JavaScript, Web Speech API (Voice input & Text-to-Speech) |
| **IDE & Development** | Visual Studio Code, Git, Python 3.x |

---

## 📁 Project Directory Structure

```text
Quotes_Chatbot/
├── backend/
│   ├── rasa_project/                  # Complete Rasa Conversational AI Project
│   │   ├── data/
│   │   │   ├── nlu.yml                # Rasa NLU training data (intents, entities, synonyms)
│   │   │   ├── stories.yml            # Dialogue conversation stories
│   │   │   └── rules.yml              # Conversational rules & fallbacks
│   │   ├── actions/
│   │   │   └── actions.py             # Rasa SDK custom action classes
│   │   ├── config.yml                 # NLU pipeline & dialogue policies
│   │   ├── domain.yml                 # Rasa domain (intents, entities, slots, responses)
│   │   ├── credentials.yml            # REST webhook channel configuration
│   │   └── endpoints.yml              # Action server & tracker configuration
│   ├── app.py                         # Rasa-compatible REST API Server
│   ├── nlp_engine.py                  # ML Intent Classifier, Emotion Analyzer & Dialogue State Manager
│   ├── quotes_db.json                 # Curated database of categorized & mood-tagged quotes
│   ├── test_nlp.py                    # Automated test suite
│   └── requirements.txt               # Backend Python dependencies
├── frontend/
│   ├── index.html                     # Responsive single-page web app
│   ├── css/
│   │   └── style.css                  # Modern UI styles, dark/light theme, quote cards
│   └── js/
│       └── app.js                     # REST API client, Web Speech TTS/STT, favorites manager
├── run_app.py                         # One-click launcher script
└── README.md                          # Project documentation
```



### 1. Install Dependencies
Open your terminal in the project root directory and run:
```bash
python -m pip install -r backend/requirements.txt
```

### 2. Start the Chatbot (One-Click Launcher)
Run the launcher script:
```bash
python run_app.py
```
This will:
1. Start the Rasa REST API server on `http://127.0.0.1:5005`.
2. Automatically launch the web interface in your default browser.

---

## 🌐 REST API Endpoints Reference

The backend implements the standard **Rasa REST Channel API**:

### 1. Rasa REST Webhook Channel
- **Endpoint**: `POST /webhooks/rest/webhook`
- **Request Payload**:
  ```json
  {
    "sender": "user_123",
    "message": "I feel stressed with work and need motivation"
  }
  ```
- **Response**:
  ```json
  [
    {
      "recipient_id": "user_123",
      "text": "Take a breath. Let's ease that stress with this perspective:\n\n“It always seems impossible until it's done.”\n— Nelson Mandela",
      "buttons": [
        {"title": "👍 Loved it!", "payload": "/feedback_positive"},
        {"title": "🔄 Another quote", "payload": "/feedback_negative"},
        {"title": "💡 Explain meaning", "payload": "/explain_quote"}
      ],
      "custom": {
        "type": "quote_card",
        "quote": "It always seems impossible until it's done.",
        "author": "Nelson Mandela",
        "category": "Motivation",
        "tags": ["triumph", "perseverance", "hope"]
      }
    }
  ]
  ```

### 2. Rasa NLU Model Parse
- **Endpoint**: `POST /model/parse`
- **Request Payload**:
  ```json
  {
    "text": "Tell me a funny quote"
  }
  ```
- **Response**:
  ```json
  {
    "text": "Tell me a funny quote",
    "intent": {
      "name": "select_category",
      "confidence": 0.94
    },
    "entities": [
      {
        "entity": "category",
        "value": "Humor",
        "confidence": 0.95
      }
    ],
    "intent_ranking": [...]
  }
  ```

### 3. Service Health & Metadata
- **Endpoint**: `GET /health` or `GET /status`
- **Response**: JSON status, version, and quote statistics.

---

## ✨ Features & User Experience

1. **Emotion-Aware Support**:
   - Understands moods such as *Feeling Down*, *Stressed / Burnout*, *Need Motivation*, *Anxious*, *Heartbroken*, *Ambitious*, and *Happy*.
   - Responds with empathetic validation and tailored quotes.
2. **5 Rich Categories**:
   - Motivation, Inspiration, Success, Love, Humor.
3. **Interactive Quote Cards**:
   - 🔊 **Text-to-Speech (TTS)**: Listen to quotes read aloud.
   - 📋 **Copy to Clipboard**: Quick copy with toast feedback.
   - ⭐ **Favorites**: Save quotes locally in browser memory.
   - 💡 **Explain Meaning**: Provides deeper reflections and practical life advice.
   - 📤 **Share**: Native Web Share API integration.
4. **Voice Input (Speech-to-Text)**:
   - Click the microphone button to talk naturally to the chatbot.
5. **Satisfaction Feedback Loop**:
   - Follow-up satisfaction questions (`👍 Loved it!`, `🔄 Another quote`, `💡 Explain meaning`).
6. **Live Rasa NLU Inspector**:
   - Real-time modal to inspect intent confidence rankings and entity extraction.
7. **Dark / Light Theme Toggle**:
   - Beautiful aesthetic with customizable themes.

---

## 🧪 Automated Testing

Run the automated NLP test suite:
```bash
python backend/test_nlp.py
```
This tests intent classification, entity extraction, mood handling, and Rasa response generation.
