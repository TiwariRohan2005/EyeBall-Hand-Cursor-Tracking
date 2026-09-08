class BasePredictionEngine:
    """
    Abstract interface for prediction engines.
    Ensures future Transformer/LLM models can be swapped effortlessly
    without breaking the keyboard interaction code.
    """
    def predict_next_words(self, context_text: str) -> list[tuple[str, float]]:
        """Given previous context, predict highly likely next words with confidence."""
        raise NotImplementedError

    def suggest_completions(self, current_word: str) -> list[tuple[str, float]]:
        """Given a partial or mistyped word, suggest completions with confidence."""
        raise NotImplementedError

    def learn_sentence(self, sentence: str):
        """Consume a typed sentence to update local user vocabulary and weights."""
        raise NotImplementedError
