"""
retriever.py
---------------------------------
根据 IntentClassifier 的输出，
从 skills 文件夹中检索最匹配的 Skill。
"""

from core.loader import load_skills


class SkillRetriever:

    def __init__(self):
        self.skills = load_skills()

    def retrieve(self, intent_result, top_k=3):
        """
        intent_result:
        {
            "matched_intents":[...]
        }

        返回：
        [
            skill_json,
            skill_json,
            ...
        ]
        """

        matched_intents = intent_result.get("matched_intents", [])

        scored_skills = []

        for skill in self.skills:

            score = 0

            # tags 匹配
            tags = skill.get("tags", [])

            for tag in tags:
                if tag in matched_intents:
                    score += 2

            # keywords 匹配
            keywords = skill.get("keywords", [])

            original = intent_result.get("original_input", "")

            for keyword in keywords:
                if keyword in original:
                    score += 1

            if score > 0:
                scored_skills.append(
                    {
                        "score": score,
                        "skill": skill
                    }
                )

        # 分数排序
        scored_skills.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        # 返回 Top K
        results = scored_skills[:top_k]

        

        # 一个都没有时
        if len(results) == 0:

            for skill in self.skills:
                if skill["name"] == "general_skill":
                    results.append(
    {
        "score": 0,
        "skill": skill
    }
)
                    break

        return results


# ------------------------
# Test
# ------------------------

if __name__ == "__main__":

    from core.intent_classifier import IntentClassifier

    classifier = IntentClassifier()

    retriever = SkillRetriever()

    while True:

        text = input("请输入：")

        if text == "exit":
            break

        intent = classifier.classify_intent(text)

        skills = retriever.retrieve(intent)

        print("\nIntent")

        print(intent)

        print("\nMatched Skills")

        for s in skills:

            print(
        s["skill"]["name"],
        "Score:",
        s["score"]
    )
