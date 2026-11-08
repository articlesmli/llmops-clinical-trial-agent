# src/database.py
import json
import os

class TrialDatabase:
    def __init__(self, db_path: str = "src/data/indexed_trials.json"):
        self.db_path = db_path
        self._ensure_db()

    _DEFAULT_TRIALS = {
        "NCT_104XB": {
            "trial_id": "NCT_104XB",
            "trial_title": "Phase Protocol 104XB Evaluation",
            "structured_criteria": {
                "inclusion_criteria": [],
                "exclusion_criteria": []
            }
        }
    }

    def _ensure_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump(self._DEFAULT_TRIALS, f, indent=2)

    def get_trial(self, trial_id: str) -> dict:
        """Retrieves trial record from the database."""
        if not os.path.exists(self.db_path):
            return self._DEFAULT_TRIALS.get(trial_id, {})
        with open(self.db_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        
        if isinstance(data, dict):
            return data.get(trial_id, self._DEFAULT_TRIALS.get(trial_id, {}))
        elif isinstance(data, list):
            for item in data:
                if item.get("trial_id") == trial_id:
                    return item
        return self._DEFAULT_TRIALS.get(trial_id, {})

    def save_trial(self, trial_id: str, trial_data: dict):
        """Saves or updates a trial record securely, preventing accidental overwrite of existing criteria with empty dicts."""
        data = {}
        if os.path.exists(self.db_path):
            with open(self.db_path, "r") as f:
                try:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        data = loaded
                    elif isinstance(loaded, list):
                        for item in loaded:
                            tid = item.get("trial_id")
                            if tid:
                                data[tid] = item
                except json.JSONDecodeError:
                    data = {}
        
        # Safeguard: If incoming trial data has empty criteria but existing record has criteria, preserve them.
        existing_record = data.get(trial_id, {})
        existing_criteria = existing_record.get("structured_criteria", {})
        new_criteria = trial_data.get("structured_criteria", {})
        
        has_new_criteria = bool(new_criteria.get("inclusion_criteria") or new_criteria.get("exclusion_criteria"))
        has_existing_criteria = bool(existing_criteria.get("inclusion_criteria") or existing_criteria.get("exclusion_criteria"))

        if not has_new_criteria and has_existing_criteria:
            trial_data["structured_criteria"] = existing_criteria

        data[trial_id] = trial_data
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)