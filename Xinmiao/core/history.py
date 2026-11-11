import json
import os

HISTORY_FILE = "history.json"


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_record(user_input, skill, prompt, answer):
    data = load_history()

    data.append({
        "user_input": user_input,
        "skill": skill,
        "prompt": prompt,
        "answer": answer
    })

    save_history(data)


# =========================
# 🗑 删除单条
# =========================
def delete_record(index):
    data = load_history()

    if 0 <= index < len(data):
        data.pop(index)
        save_history(data)
        return True

    return False


# =========================
# 💣 删除全部
# =========================
def clear_history():
    save_history([])
    return True