from typing import List, Dict

# In-memory store for session history
_history_store: Dict[str, List[str]] = {}

def get_history(user_id: str) -> List[str]:
    return _history_store.get(user_id, [])

def add_to_history(user_id: str, turn: str):
    if user_id not in _history_store:
        _history_store[user_id] = []
    _history_store[user_id].append(turn)
    # Keep only last 10 turns to prevent token bloat
    if len(_history_store[user_id]) > 10:
        _history_store[user_id] = _history_store[user_id][-10:]
