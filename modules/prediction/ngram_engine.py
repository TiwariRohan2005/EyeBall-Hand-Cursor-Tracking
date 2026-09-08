from . import BasePredictionEngine
from .dictionary_manager import DictionaryManager

class NgramPredictionEngine(BasePredictionEngine):
    def __init__(self):
        self.dict_manager = DictionaryManager()
        
        # Local context arrays
        self.bigrams = {}   # { word: { next_word: count } }
        self.trigrams = {}  # { word1_word2: { next_word: count } }

    def suggest_completions(self, current_word: str) -> list[tuple[str, float]]:
        """
        Implementation of the interface using Dictionary Manager's fuzzy matching.
        """
        if not current_word:
            return []
            
        # Returns [(word, conf), ...]
        return self.dict_manager.fuzzy_search(current_word, limit=5, max_distance=2)

    def predict_next_words(self, context_text: str) -> list[tuple[str, float]]:
        """
        Uses N-Grams (Stupid Backoff Algorithm simplified) for next-word prediction.
        """
        words = context_text.strip().lower().split()
        if not words:
            return []
            
        suggestions = {}
        
        # 1. Trigram Context (Highest confidence)
        if len(words) >= 2:
            trigram_key = f"{words[-2]}_{words[-1]}"
            if trigram_key in self.trigrams:
                for next_word, count in self.trigrams[trigram_key].items():
                    suggestions[next_word] = count * 1.0 # 1.0 weight
                    
        # 2. Bigram Context (Medium confidence)
        bigram_key = words[-1]
        if bigram_key in self.bigrams:
            for next_word, count in self.bigrams[bigram_key].items():
                if next_word not in suggestions:
                    suggestions[next_word] = count * 0.4 # Stupid backoff penalty factor
                else:
                    suggestions[next_word] += count * 0.4
                    
        # Sort and return top 3
        sorted_suggs = sorted(suggestions.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Normalize arbitrarily for UI presentation
        return [(w, min(s / 10.0, 1.0)) for w, s in sorted_suggs]

    def learn_sentence(self, sentence: str):
        """
        Updates Unigram frequencies in DictionaryManager and 
        Bigram/Trigram models locally.
        """
        if not sentence: return
        
        words = sentence.strip().lower().split()
        if not words: return
        
        for w in words:
            self.dict_manager.register_word(w)
            
        for i in range(len(words) - 1):
            w1 = words[i]
            w2 = words[i+1]
            
            # Bigram update
            if w1 not in self.bigrams:
                self.bigrams[w1] = {}
            if w2 not in self.bigrams[w1]:
                self.bigrams[w1][w2] = 0
            self.bigrams[w1][w2] += 1
            
            # Trigram update
            if i < len(words) - 2:
                w3 = words[i+2]
                tri_key = f"{w1}_{w2}"
                if tri_key not in self.trigrams:
                    self.trigrams[tri_key] = {}
                if w3 not in self.trigrams[tri_key]:
                    self.trigrams[tri_key][w3] = 0
                self.trigrams[tri_key][w3] += 1
