import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from nlp_engine import NLPEngine

def test_nlp():
    nlp = NLPEngine()
    print(f"Total quotes loaded: {len(nlp.quotes)}")
    assert len(nlp.quotes) >= 50, "Quotes database should have at least 50 quotes"

    # Test 1: Greetings
    res = nlp.process_message("user_1", "Hello there!")
    print("\n[Test 1 Greet Result]:")
    print(res[0]["text"])
    assert "Hello" in res[0]["text"]
    assert len(res[0].get("buttons", [])) > 0

    # Test 2: Category Request
    res2 = nlp.process_message("user_1", "Give me a motivation quote")
    print("\n[Test 2 Category Result]:")
    print(res2[0]["text"])
    assert "custom" in res2[0] or (len(res2) > 1 and "custom" in res2[1])

    # Test 3: Mood expression
    res3 = nlp.process_message("user_1", "I feel so stressed and overwhelmed with work")
    print("\n[Test 3 Mood Result]:")
    for r in res3:
        print("- ", r["text"][:80])

    # Test 4: Rasa NLU Parse endpoint
    parse = nlp.parse_nlu("I want a funny quote to make me laugh")
    print("\n[Test 4 Parse Result]:")
    print(f"Intent: {parse['intent']['name']} (Confidence: {parse['intent']['confidence']:.2f})")
    print(f"Entities: {parse['entities']}")
    assert parse["intent"]["name"] in ["select_category", "request_quote"]

    # Test 5: Quote explanation
    res5 = nlp.process_message("user_1", "explain this quote please")
    print("\n[Test 5 Explanation Result]:")
    print(res5[0]["text"][:100])
    assert "Reflection" in res5[0]["text"]

    print("\n✅ ALL NLP TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_nlp()
