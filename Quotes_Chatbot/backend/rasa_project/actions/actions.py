from typing import Any, Text, Dict, List
import json
import os
import random
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# Load quotes database
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
QUOTES_PATH = os.path.join(CURRENT_DIR, "..", "..", "quotes_db.json")

def load_quotes() -> List[Dict]:
    try:
        with open(QUOTES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

class ActionRecommendQuote(Action):
    def name(self) -> Text:
        return "action_recommend_quote"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        quotes = load_quotes()
        category = tracker.get_slot("category")
        mood = tracker.get_slot("mood")

        filtered = quotes
        if category:
            filtered = [q for q in filtered if q.get("category", "").lower() == category.lower()]
        if mood and not filtered:
            filtered = [q for q in quotes if mood.lower() in [m.lower() for m in q.get("moods", [])]]
        elif mood:
            mood_matches = [q for q in filtered if mood.lower() in [m.lower() for m in q.get("moods", [])]]
            if mood_matches:
                filtered = mood_matches

        if not filtered:
            filtered = quotes

        chosen = random.choice(filtered)
        quote_text = f"“{chosen['text']}”\n— {chosen['author']}"

        # Send custom payload with quote object for rich web interface rendering
        dispatcher.utter_message(
            text=quote_text,
            json_message={
                "type": "quote_card",
                "quote_id": chosen["id"],
                "quote": chosen["text"],
                "author": chosen["author"],
                "category": chosen["category"],
                "reflection": chosen.get("reflection", ""),
                "tags": chosen.get("tags", [])
            }
        )

        return [SlotSet("last_quote_id", chosen["id"])]

class ActionExplainQuote(Action):
    def name(self) -> Text:
        return "action_explain_quote"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        quotes = load_quotes()
        last_id = tracker.get_slot("last_quote_id")
        
        quote = next((q for q in quotes if q["id"] == last_id), None)
        if quote and "reflection" in quote:
            explanation = f"💡 Deeper Reflection on this quote by {quote['author']}:\n{quote['reflection']}"
        else:
            explanation = "💡 Every quote holds a mirror to our own life experiences. Take a deep breath and consider how you can apply its wisdom today."

        dispatcher.utter_message(text=explanation)
        return []

class ActionAnalyzeEmotion(Action):
    def name(self) -> Text:
        return "action_analyze_emotion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mood = tracker.get_slot("mood")
        if mood:
            dispatcher.utter_message(text=f"I hear you. Feeling {mood} is completely natural. Let me share something to support you right now:")
        return []
