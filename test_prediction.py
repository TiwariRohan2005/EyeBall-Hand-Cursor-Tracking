from modules.prediction.ngram_engine import NgramPredictionEngine

def main():
    print("=== Testing Local AI Prediction Engine ===")
    engine = NgramPredictionEngine()
    
    print("\n[Case 1] Fuzzy Searching (Autocomplete)")
    print("Testing 'proj' (Expects 'project'): ", engine.suggest_completions("proj"))
    print("Testing 'teh' (Typo for 'the'): ", engine.suggest_completions("teh"))
    
    print("\n[Case 2] Learning a Custom Sentence")
    custom_sentence = "hello intelligent virtual keyboard"
    print(f"Teaching engine: '{custom_sentence}'...")
    engine.learn_sentence(custom_sentence)
    
    # Simulate a second usage to boost frequency/recency
    engine.learn_sentence(custom_sentence)
    
    print("\n[Case 3] Custom Vocabulary Autocomplete")
    print("Testing 'intell' (Should suggest intelligent due to user training):")
    print(engine.suggest_completions("intell"))
    
    print("\n[Case 4] Next-Word Prediction (N-Gram Context)")
    print("Context: 'hello intelligent'")
    print("Predictions: ", engine.predict_next_words("hello intelligent"))
    
    print("Context: 'virtual'")
    print("Predictions: ", engine.predict_next_words("virtual"))
    
    print("\nTests Complete!")

if __name__ == "__main__":
    main()
