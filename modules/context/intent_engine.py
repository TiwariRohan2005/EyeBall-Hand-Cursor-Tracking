import json
import os

class IntentEngine:
    """
    Acts as the translation gateway. It absorbs a raw physical gesture (e.g. 'PINCH')
    and matches it against the current Context Mode (e.g. 'Media').
    """
    def __init__(self, mapping_file="action_mappings.json"):
        self.mappings = {}
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, "r") as f:
                    self.mappings = json.load(f)
            except Exception as e:
                print(f"[!] Error loading mappings: {e}")
                self.mappings = {}

    def reload(self, mapping_file="action_mappings.json"):
         if os.path.exists(mapping_file):
             with open(mapping_file, "r") as f:
                 self.mappings = json.load(f)

    def evaluate(self, current_mode, gesture):
        """
        Translates physical gesture to contextual smart Intent.
        Falls back to General Desktop rules if the app is currently unhandled.
        """
        if not gesture: return "NONE"
        
        mode_mapping = self.mappings.get(current_mode)
        if not mode_mapping:
            # Fallback
            mode_mapping = self.mappings.get("General Desktop", {})
            
        intent = mode_mapping.get(gesture, "NONE")
        return intent
