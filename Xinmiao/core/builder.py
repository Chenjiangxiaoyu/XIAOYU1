"""
builder.py
-----------------------------
Prompt Builder
负责把 Retriever 找到的多个 Skill
融合成一个最终 Prompt
"""

from core.rewriter import PromptRewriter


class PromptBuilder:

    def __init__(self):
        self.rewriter = PromptRewriter()

    def build(self, retrieved_skills, user_input):
        """
        Parameters
        ----------
        retrieved_skills :
            [
                {
                    "score": 8,
                    "skill": {...}
                },
                ...
            ]

        user_input : str

        Returns
        -------
        str
            最终 Prompt
        """

        skills = []

        # retriever 返回的是
        # {"score":xx,"skill":{...}}
        for item in retrieved_skills:

            if isinstance(item, dict) and "skill" in item:
                skills.append(item["skill"])

            else:
                skills.append(item)

        prompt = self.rewriter.rewrite(
            retrieved_skills=skills,
            user_input=user_input
        )

        return prompt


# -----------------------------
# Test
# -----------------------------
if __name__ == "__main__":

    from core.intent_classifier import IntentClassifier
    from core.retriever import SkillRetriever

    classifier = IntentClassifier()

    retriever = SkillRetriever()

    builder = PromptBuilder()

    while True:

        text = input("请输入：")

        if text == "exit":
            break

        intent = classifier.classify_intent(text)

        skills = retriever.retrieve(intent)

        prompt = builder.build(
            skills,
            text
        )

        print("=" * 60)
        print(prompt)
        print("=" * 60)