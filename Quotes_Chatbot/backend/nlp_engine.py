"""
Natural Language Processing (NLP) & Conversational Engine
Implements Machine Learning Intent Classification, Emotion Detection,
Entity Extraction, and Rasa-compatible Dialogue Management.
"""

import json
import os
import re
import random
from typing import Dict, List, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
QUOTES_DB_PATH = os.path.join(CURRENT_DIR, "quotes_db.json")
NLU_DATA_PATH = os.path.join(CURRENT_DIR, "rasa_project", "data", "nlu.yml")

# Emotion lexicons and mapping to recommendation strategies
EMOTION_PATTERNS = {
    "sad": [r"\bsad\b", r"\bdepressed\b", r"\bdown\b", r"\bunhappy\b", r"\bcrying\b", r"\bmiserable\b", r"\blonely\b", r"\bhopeless\b", r"\bgloom\b"],
    "stressed": [r"\bstressed\b", r"\boverwhelmed\b", r"\bburnout\b", r"\bburnt out\b", r"\bexhausted\b", r"\btired\b", r"\bpressure\b", r"\bworkload\b"],
    "anxious": [r"\banxious\b", r"\banxiety\b", r"\bworried\b", r"\bnervous\b", r"\bscared\b", r"\bfearful\b", r"\bpanic\b"],
    "unmotivated": [r"\bunmotivated\b", r"\blazy\b", r"\bprocrastinat\w*", r"\bno drive\b", r"\bbored\b", r"\bsluggish\b", r"\bstuck\b", r"\bcan't study\b"],
    "heartbroken": [r"\bheartbroken\b", r"\bbreakup\b", r"\bbroken heart\b", r"\brejected\b", r"\bdumped\b", r"\blost love\b", r"\bhurting\b"],
    "happy": [r"\bhappy\b", r"\bgreat\b", r"\bjoyful\b", r"\bexcited\b", r"\bcheerful\b", r"\bblessed\b", r"\bwonderful\b", r"\bcelebrating\b", r"\bgood mood\b"],
    "ambitious": [r"\bambitious\b", r"\bhustle\b", r"\bachieve\b", r"\bwin\b", r"\bgoal\b", r"\bdream big\b", r"\bconquer\b", r"\bgrind\b"]
}

CATEGORY_KEYWORDS = {
    "Motivation": ["motivation", "motivate", "motivational", "inspire me to work", "boost", "energy", "discipline"],
    "Inspiration": ["inspiration", "inspirational", "inspire", "hope", "uplifting", "dreams", "possibility"],
    "Success": ["success", "successful", "career", "wealth", "achieve", "goals", "triumph", "winning"],
    "Love": ["love", "romance", "romantic", "relationship", "affection", "heart", "compassion"],
    "Humor": ["humor", "funny", "joke", "laugh", "smile", "fun", "hilarious", "chuckle", "wit"]
}

# Emotion to category default priority
EMOTION_TO_CATEGORY = {
    "sad": "Inspiration",
    "stressed": "Humor",
    "anxious": "Inspiration",
    "unmotivated": "Motivation",
    "heartbroken": "Love",
    "happy": "Success",
    "ambitious": "Success"
}

class NLPEngine:
    def __init__(self):
        self.quotes: List[Dict] = []
        self.load_database()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.train_intent_classifier()

    def load_database(self):
        try:
            with open(QUOTES_DB_PATH, "r", encoding="utf-8") as f:
                self.quotes = json.load(f)
        except Exception as e:
            print(f"Warning loading quotes: {e}")
            self.quotes = []

    def train_intent_classifier(self):
        """Train TF-IDF + Multinomial Naive Bayes intent classifier from training samples."""
        training_samples = [
            # greet
            ("hello", "greet"), ("hi", "greet"), ("hey", "greet"), ("good morning", "greet"),
            ("good evening", "greet"), ("hey there", "greet"), ("howdy", "greet"), ("hi bot", "greet"),
            # goodbye
            ("bye", "goodbye"), ("goodbye", "goodbye"), ("see you later", "goodbye"),
            ("talk to you soon", "goodbye"), ("cya", "goodbye"), ("have a good day", "goodbye"),
            # request_quote
            ("give me a quote", "request_quote"), ("tell me a quote", "request_quote"),
            ("recommend a quote", "request_quote"), ("i want a quote", "request_quote"),
            ("share an inspiring quote", "request_quote"), ("quote please", "request_quote"),
            ("can you give me words of wisdom", "request_quote"), ("show me a quote", "request_quote"),
            # select_category
            ("i want motivation", "select_category"), ("give me motivation quotes", "select_category"),
            ("show me motivational quotes", "select_category"), ("motivation", "select_category"),
            ("i need inspiration", "select_category"), ("give me inspirational quotes", "select_category"),
            ("inspiration", "select_category"), ("i want success quotes", "select_category"),
            ("show me quotes about success", "select_category"), ("success", "select_category"),
            ("show me love quotes", "select_category"), ("love", "select_category"),
            ("romantic quotes", "select_category"), ("make me laugh", "select_category"),
            ("tell me a funny quote", "select_category"), ("humor", "select_category"),
            ("funny quote", "select_category"),
            # express_mood
            ("i feel sad today", "express_mood"), ("i am so depressed and lonely", "express_mood"),
            ("feeling down and lost", "express_mood"), ("i am feeling very stressed", "express_mood"),
            ("work is stressing me out", "express_mood"), ("feeling anxious about exam", "express_mood"),
            ("i have so much anxiety", "express_mood"), ("i feel unmotivated to study", "express_mood"),
            ("feeling lazy and tired", "express_mood"), ("i am heartbroken over my ex", "express_mood"),
            ("my heart hurts so much", "express_mood"), ("i am feeling very happy today", "express_mood"),
            ("feeling joyful and blessed", "express_mood"), ("feeling ambitious to achieve goals", "express_mood"),
            # feedback_positive
            ("that was great", "feedback_positive"), ("loved it", "feedback_positive"),
            ("that really helped me", "feedback_positive"), ("beautiful quote", "feedback_positive"),
            ("yes", "feedback_positive"), ("yup", "feedback_positive"), ("thanks, this inspired me", "feedback_positive"),
            # feedback_negative
            ("no", "feedback_negative"), ("nope", "feedback_negative"), ("didn't like it", "feedback_negative"),
            ("show me another quote", "feedback_negative"), ("give me a different one", "feedback_negative"),
            ("try another one", "feedback_negative"), ("not quite what i wanted", "feedback_negative"),
            # explain_quote
            ("explain this quote", "explain_quote"), ("what does this quote mean", "explain_quote"),
            ("can you break down the meaning", "explain_quote"), ("give me advice on this quote", "explain_quote"),
            ("tell me deeper reflection", "explain_quote"), ("explain it", "explain_quote"),
            # bot_challenge
            ("are you a bot", "bot_challenge"), ("are you human", "bot_challenge"), ("who made you", "bot_challenge"),
            # ask_help
            ("help", "ask_help"), ("what can you do", "ask_help"), ("show me categories", "ask_help"),
            ("how does this chatbot work", "ask_help"), ("features", "ask_help")
        ]

        texts = [s[0] for s in training_samples]
        labels = [s[1] for s in training_samples]

        self.pipeline = make_pipeline(
            TfidfVectorizer(ngram_range=(1, 2), lowercase=True),
            MultinomialNB(alpha=0.1)
        )
        self.pipeline.fit(texts, labels)

    def detect_emotion(self, text: str) -> Optional[str]:
        """Detect dominant emotion in user message."""
        lower_text = text.lower()
        for emotion, patterns in EMOTION_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, lower_text):
                    return emotion
        return None

    def extract_category(self, text: str) -> Optional[str]:
        """Extract requested quote category."""
        lower_text = text.lower()
        for cat, kws in CATEGORY_KEYWORDS.items():
            for kw in kws:
                if re.search(rf"\b{re.escape(kw)}\b", lower_text):
                    return cat
        return None

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract category, mood, and author entities."""
        entities = []
        cat = self.extract_category(text)
        if cat:
            entities.append({
                "entity": "category",
                "value": cat,
                "confidence": 0.95
            })

        mood = self.detect_emotion(text)
        if mood:
            entities.append({
                "entity": "mood",
                "value": mood,
                "confidence": 0.90
            })

        # Check for specific author mentions
        for q in self.quotes:
            author = q.get("author", "")
            if len(author) > 3 and author.lower() in text.lower():
                entities.append({
                    "entity": "author",
                    "value": author,
                    "confidence": 0.95
                })
                break

        return entities

    def parse_nlu(self, text: str) -> Dict[str, Any]:
        """Rasa-compatible /model/parse response."""
        probas = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        ranked = sorted(zip(classes, probas), key=lambda x: x[1], reverse=True)

        top_intent, top_confidence = ranked[0]
        entities = self.extract_entities(text)

        # Heuristic boost: if mood or category keywords exist, reinforce intent
        if self.detect_emotion(text) and top_intent not in ["express_mood", "feedback_positive", "feedback_negative"]:
            top_intent = "express_mood"
            top_confidence = 0.92
        elif self.extract_category(text) and top_intent not in ["select_category", "feedback_positive", "feedback_negative"]:
            top_intent = "select_category"
            top_confidence = 0.92

        return {
            "text": text,
            "intent": {
                "name": top_intent,
                "confidence": float(top_confidence)
            },
            "intent_ranking": [
                {"name": name, "confidence": float(score)} for name, score in ranked[:5]
            ],
            "entities": entities
        }

    def get_or_create_session(self, sender_id: str) -> Dict[str, Any]:
        if sender_id not in self.sessions:
            self.sessions[sender_id] = {
                "last_quote_id": None,
                "category": None,
                "mood": None,
                "history": []
            }
        return self.sessions[sender_id]

    def select_quote(self, category: Optional[str] = None, mood: Optional[str] = None, exclude_id: Optional[int] = None) -> Dict:
        """Select contextually relevant quote based on category, mood, and history."""
        candidates = self.quotes

        if exclude_id is not None and len(candidates) > 1:
            candidates = [q for q in candidates if q.get("id") != exclude_id]

        # Filter by category if specified
        if category:
            cat_matches = [q for q in candidates if q.get("category", "").lower() == category.lower()]
            if cat_matches:
                candidates = cat_matches

        # If mood is specified, prioritize quotes matching that mood
        if mood:
            mood_matches = [q for q in candidates if mood.lower() in [m.lower() for m in q.get("moods", [])]]
            if mood_matches:
                candidates = mood_matches
            elif not category and mood in EMOTION_TO_CATEGORY:
                recommended_cat = EMOTION_TO_CATEGORY[mood]
                cat_matches = [q for q in self.quotes if q.get("category", "").lower() == recommended_cat.lower()]
                if cat_matches:
                    candidates = cat_matches

        return random.choice(candidates if candidates else self.quotes)

    def generate_generative_reflection(self, quote: Dict, mood: Optional[str] = None) -> str:
        """Generate a personalized, empathetic reflection bridging the quote with emotional well-being."""
        author = quote.get("author", "Unknown")
        reflection = quote.get("reflection", "")
        category = quote.get("category", "Inspiration")

        if mood:
            empathy_lines = {
                "sad": f"When sadness weighs heavy, remember that this moment is temporary. {author}'s words remind us that light often re-emerges right when things feel darkest.",
                "stressed": f"Take a slow, deep breath. The pressure you feel is proof of how much you care, but peace comes from focusing only on what is in your hands right now.",
                "anxious": f"Anxiety projects fears into an unwritten future. Anchor yourself in the present moment—you possess more strength than your doubts lead you to believe.",
                "unmotivated": f"Motivation follows action, not the other way around. Don't worry about finishing the whole journey today; just take the very next tiny step.",
                "heartbroken": f"A wounded heart is proof of great courage—it means you dared to care deeply. Give yourself grace and space to heal; new chapters await you.",
                "happy": f"Hold onto this joyful momentum! Positivity shared multiplies, so let your bright spirit uplift those around you today.",
                "ambitious": f"Harness this fire with laser discipline. Dream with audacity, execute with consistency, and celebrate every milestone."
            }
            empathy = empathy_lines.get(mood, "Reflect on how this wisdom speaks to your current journey.")
            return f"{empathy}\n\n💡 Reflection: {reflection}"
        else:
            return f"💡 Reflection on {author}'s wisdom:\n{reflection}\n\nAsk yourself: What is one small way you can apply this perspective to your day?"

    def process_message(self, sender_id: str, message: str) -> List[Dict[str, Any]]:
        """Process incoming user message and return Rasa REST API response array."""
        session = self.get_or_create_session(sender_id)
        parse_result = self.parse_nlu(message)
        intent = parse_result["intent"]["name"]
        entities = parse_result["entities"]

        # Update slots from entities
        for ent in entities:
            if ent["entity"] == "category":
                session["category"] = ent["value"]
            elif ent["entity"] == "mood":
                session["mood"] = ent["value"]

        responses = []

        # Intent handling
        if intent == "greet":
            responses.append({
                "recipient_id": sender_id,
                "text": "Hello there! ✨ I'm your AI Quotes & Well-Being Assistant.\nTell me how you're feeling today, or pick a category below to receive personalized wisdom.",
                "buttons": [
                    {"title": "🌟 Inspiration", "payload": "/select_category{\"category\":\"Inspiration\"}"},
                    {"title": "💪 Motivation", "payload": "/select_category{\"category\":\"Motivation\"}"},
                    {"title": "🏆 Success", "payload": "/select_category{\"category\":\"Success\"}"},
                    {"title": "❤️ Love", "payload": "/select_category{\"category\":\"Love\"}"},
                    {"title": "😄 Humor", "payload": "/select_category{\"category\":\"Humor\"}"}
                ]
            })

        elif intent == "goodbye":
            responses.append({
                "recipient_id": sender_id,
                "text": "Wishing you peace, motivation, and joy ahead! Come back whenever you need inspiration. 👋✨"
            })

        elif intent == "bot_challenge":
            responses.append({
                "recipient_id": sender_id,
                "text": "I am an intelligent Quotes Recommendation Chatbot powered by NLP and Natural Language Understanding, ready to match you with meaningful quotes! 🤖💬"
            })

        elif intent == "ask_help":
            responses.append({
                "recipient_id": sender_id,
                "text": "Here is what I can do for you:\n\n"
                        "✨ **Recommend by Category**: Ask for Motivation, Inspiration, Success, Love, or Humor.\n"
                        "🧠 **Emotion-Aware Support**: Tell me if you feel stressed, sad, anxious, unmotivated, or happy.\n"
                        "💡 **Quote Meaning & Advice**: Ask 'explain this quote' for deep reflections.\n"
                        "🎙️ **Voice & Audio**: Use voice input or listen to quotes read aloud!",
                "buttons": [
                    {"title": "Give me Motivation", "payload": "/select_category{\"category\":\"Motivation\"}"},
                    {"title": "I feel stressed", "payload": "/express_mood{\"mood\":\"stressed\"}"},
                    {"title": "Surprise me with a Quote", "payload": "/request_quote"}
                ]
            })

        elif intent in ["request_quote", "select_category", "express_mood", "feedback_negative"]:
            # Handle mood empathy preface
            if intent == "express_mood" and session["mood"]:
                empathy_ack = {
                    "sad": "I hear you, and it's okay to feel down. Here is an uplifting thought to comfort you:",
                    "stressed": "Take a breath. Let's ease that stress with this perspective:",
                    "anxious": "Sending you calming thoughts. Here is a grounding reflection:",
                    "unmotivated": "We all hit slow patches. Here is a spark to reignite your momentum:",
                    "heartbroken": "Heartbreak is tough, but you are resilient. Let this thought hold space for you:",
                    "happy": "Love that positive energy! Here is a quote celebrating your great mood:",
                    "ambitious": "That drive is unstoppable! Here is fuel for your ambition:"
                }
                responses.append({
                    "recipient_id": sender_id,
                    "text": empathy_ack.get(session["mood"], "Here is a quote tailored to how you are feeling:")
                })

            elif intent == "feedback_negative":
                responses.append({
                    "recipient_id": sender_id,
                    "text": "No worries! Let me find a different quote that fits you better:"
                })

            # Pick a quote
            quote = self.select_quote(
                category=session.get("category"),
                mood=session.get("mood"),
                exclude_id=session.get("last_quote_id")
            )
            session["last_quote_id"] = quote["id"]

            quote_display = f"“{quote['text']}”\n\n— {quote['author']}"
            responses.append({
                "recipient_id": sender_id,
                "text": quote_display,
                "custom": {
                    "type": "quote_card",
                    "quote_id": quote["id"],
                    "quote": quote["text"],
                    "author": quote["author"],
                    "category": quote["category"],
                    "reflection": quote.get("reflection", ""),
                    "tags": quote.get("tags", [])
                },
                "buttons": [
                    {"title": "👍 Loved it!", "payload": "/feedback_positive"},
                    {"title": "🔄 Another quote", "payload": "/feedback_negative"},
                    {"title": "💡 Explain meaning", "payload": "/explain_quote"}
                ]
            })

        elif intent == "explain_quote":
            last_id = session.get("last_quote_id")
            quote = next((q for q in self.quotes if q["id"] == last_id), None)
            if not quote:
                quote = self.quotes[0]

            reflection_text = self.generate_generative_reflection(quote, session.get("mood"))
            responses.append({
                "recipient_id": sender_id,
                "text": reflection_text,
                "buttons": [
                    {"title": "🔄 Recommend another quote", "payload": "/request_quote"},
                    {"title": "🌟 Change category", "payload": "/ask_help"}
                ]
            })

        elif intent == "feedback_positive":
            responses.append({
                "recipient_id": sender_id,
                "text": "I'm so glad that resonated with you! 🌈 Keep that positive mindset close. Feel free to ask for another quote or tell me what's on your mind.",
                "buttons": [
                    {"title": "🌟 Another quote", "payload": "/request_quote"}
                ]
            })

        else:
            # Fallback
            quote = self.select_quote(category=session.get("category"), mood=session.get("mood"))
            session["last_quote_id"] = quote["id"]
            responses.append({
                "recipient_id": sender_id,
                "text": f"Here is some wisdom to ponder:\n\n“{quote['text']}”\n— {quote['author']}",
                "custom": {
                    "type": "quote_card",
                    "quote_id": quote["id"],
                    "quote": quote["text"],
                    "author": quote["author"],
                    "category": quote["category"],
                    "reflection": quote.get("reflection", ""),
                    "tags": quote.get("tags", [])
                },
                "buttons": [
                    {"title": "👍 Good quote", "payload": "/feedback_positive"},
                    {"title": "🔄 Another quote", "payload": "/request_quote"},
                    {"title": "💡 Explain meaning", "payload": "/explain_quote"}
                ]
            })

        return responses
