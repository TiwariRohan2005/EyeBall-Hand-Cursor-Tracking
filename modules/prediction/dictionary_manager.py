import json
import os
import time
from functools import lru_cache

class DictionaryManager:
    def __init__(self, user_vocab_path=".user_vocab.json"):
        self.user_vocab_path = user_vocab_path
        
        # Base dictionary with frequencies (simulated small generic dictionary for UI purposes)
        self.base_dict = {
            "the": 1000, "be": 800, "to": 700, "of": 600, "and": 500, "a": 400, "in": 300, "that": 250, 
            "have": 200, "i": 180, "it": 150, "for": 130, "not": 100, "on": 90, "with": 80, "he": 70, 
            "as": 60, "you": 50, "do": 40, "at": 30, "this": 25, "but": 20, "his": 15, "by": 10, "from": 5,
            "project": 5, "hello": 5, "world": 5, "keyboard": 5, "system": 5, "ai": 5
        }
        
        self.user_vocab = {}      # { word: { count: int, last_used: float } }
        self.load_user_dict()

    def load_user_dict(self):
        if not os.path.exists(self.user_vocab_path):
            self.user_vocab = {}
            return
        try:
            with open(self.user_vocab_path, "r") as f:
                self.user_vocab = json.load(f)
        except Exception:
            self.user_vocab = {}

    def save_user_dict(self):
        with open(self.user_vocab_path, "w") as f:
            json.dump(self.user_vocab, f)

    def register_word(self, word: str):
        """Update local user dictionary frequencies and recent timestamps."""
        w = word.lower()
        if w not in self.user_vocab:
            self.user_vocab[w] = {"count": 0, "last_used": 0.0}
            
        self.user_vocab[w]["count"] += 1
        self.user_vocab[w]["last_used"] = time.time()
        self.save_user_dict()

    @lru_cache(maxsize=128)
    def levenshtein_distance(self, s1, s2):
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        return previous_row[-1]

    def fuzzy_search(self, prefix: str, limit=5, max_distance=2):
        """
        Searches base + user dictionary for words starting with or closely matching `prefix`.
        Ranks by Edit Distance (closest first) and then Frequency.
        """
        prefix = prefix.lower()
        results = []
        
        # Merge dictionaries for search space
        all_words = set(self.base_dict.keys()).union(set(self.user_vocab.keys()))
        now = time.time()
        
        for w in all_words:
            # Score logic
            dist = 0
            is_prefix = w.startswith(prefix)
            
            if not is_prefix:
                dist = self.levenshtein_distance(prefix, w[:len(prefix)])
                # Filter out garbage
                if dist > max_distance:
                    continue
                    
            # Calculate Frequency Weight
            base_freq = self.base_dict.get(w, 0)
            user_data = self.user_vocab.get(w, {"count": 0, "last_used": 0})
            user_freq = user_data["count"]
            
            # Recency Boost (words used in last 10 minutes get a huge spike)
            recency_boost = 1.0
            if now - user_data["last_used"] < 600:
                recency_boost = 2.0
                
            total_freq_score = (base_freq * 0.1) + (user_freq * 5.0 * recency_boost)
            
            # Confidence decreases geometricly as edit distance increases
            confidence = (1.0 - (dist / (max_distance + 1.0)))
            # Normalization scale (simulated arbitrarily for relative UI rendering)
            final_score = confidence * (1.0 + min(total_freq_score, 100) / 100.0)
            
            results.append((w, final_score))
            
        # Sort highest score first
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
