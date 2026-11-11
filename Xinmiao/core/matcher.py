# core/matcher.py

def match_skill(text, skills):
    text = text.lower()

    best_skill = None
    best_score = -1

    for skill in skills:
        score = 0

        # keyword匹配
        for kw in skill.get("keywords", []):
            if kw.lower() in text:
                score += 2

        # tag匹配
        for tag in skill.get("tags", []):
            if tag.lower() in text:
                score += 1

        # emotion boost（特殊加权）
        if skill["name"] == "emotion_skill":
            emo_words = ["焦虑", "压力", "烦", "崩溃", "不想学"]
            if any(w in text for w in emo_words):
                score += 5

        if score > best_score:
            best_score = score
            best_skill = skill

    return best_skill or skills[0]