"""
rewriter.py
---------------------------------
Prompt Rewriter

作用：
根据 Retriever 返回的多个 Skill，
自动融合成一个最终 Prompt。

输入：
[
    {
        "score": 8,
        "skill": {...}
    },
    ...
]

输出：
一个完整 Prompt（字符串）
"""


class PromptRewriter:

    def __init__(self):
        pass

    def rewrite(self, retrieved_skills, user_input):
        """
        Parameters
        ----------
        retrieved_skills : list
            Retriever 返回结果

        user_input : str
            用户输入

        Returns
        -------
        str
            最终 Prompt
        """

        if not retrieved_skills:
            return user_input

        # ==========================
        # ROLE
        # ==========================

        role = None

        # 默认取最高分 Skill 作为 Role
        role_skill = retrieved_skills[0]

        role = role_skill.get(
            "description",
            "You are a helpful AI assistant."
        )

        # ==========================
        # Prompt
        # ==========================

        prompts = []

        procedures = []

        output_formats = []

        pitfalls = []

        used_prompt = set()
        used_procedure = set()

        for skill in retrieved_skills:

            prompt = skill.get("prompt", "")

        if prompt and prompt not in used_prompt:
            prompts.append(prompt)
            used_prompt.add(prompt)

        for p in skill.get("procedure", []):
            if p not in used_procedure:
                procedures.append(p)
                used_procedure.add(p)

        output = skill.get("output_format")
        if output:
            output_formats.append(output)

        pit = skill.get("pitfalls")
        if pit:
            pitfalls.append(pit)

        # ==========================
        # Build Prompt
        # ==========================

        final_prompt = []

        final_prompt.append("# ROLE\n")
        final_prompt.append(role)

        final_prompt.append("\n\n# INSTRUCTIONS\n")

        for p in prompts:
            final_prompt.append("\n")
            final_prompt.append(p)

        if procedures:

            final_prompt.append("\n\n# PROCEDURE\n")

            for step in procedures:
                final_prompt.append(f"- {step}")

        if output_formats:

            final_prompt.append("\n\n# OUTPUT FORMAT\n")

            for out in output_formats:
                final_prompt.append(str(out))

        if pitfalls:

            final_prompt.append("\n\n# NOTES\n")

            for p in pitfalls:
                final_prompt.append(str(p))

        final_prompt.append("\n\n# USER INPUT\n")

        final_prompt.append(user_input)

        return "\n".join(final_prompt)


# ======================================
# Test
# ======================================

if __name__ == "__main__":

    from core.intent_classifier import IntentClassifier
    from core.retriever import SkillRetriever

    classifier = IntentClassifier()

    retriever = SkillRetriever()

    rewriter = PromptRewriter()

    while True:

        text = input("\n请输入：")

        if text == "exit":
            break

        intent = classifier.classify_intent(text)

        skills = retriever.retrieve(intent)

        prompt = rewriter.rewrite(skills, text)

        print("\n" + "=" * 60)

        print(prompt)

        print("=" * 60)