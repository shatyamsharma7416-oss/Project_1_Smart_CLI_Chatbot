import json
filename = f"chat_history/chat_.json"

with open(filename, "w", encoding='utf-8') as f:
    json.dump({"hi": 1}, f, indent=4, ensure_ascii=False)
