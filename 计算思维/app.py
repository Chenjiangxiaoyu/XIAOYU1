import gradio as gr
import matplotlib.pyplot as plt
from collections import Counter
from dotenv import load_dotenv

from core.loader import load_skills
from core.intent_classifier import IntentClassifier
from core.retriever import SkillRetriever
from core.builder import PromptBuilder
from core.llm_router import call_llm
from core.history import add_record, load_history, delete_record

load_dotenv()

skills = load_skills()

classifier = IntentClassifier()

retriever = SkillRetriever()

builder = PromptBuilder()


# =========================
# 🧠 PIPELINE
# =========================
def pipeline(user_input, model):

    # ① Intent 分类
    intent = classifier.classify_intent(user_input)

    # ② 检索 Skill
    retrieved_skills = retriever.retrieve(intent)
    print(retrieved_skills)

    # ③ Prompt 重写
    prompt = builder.build(
        retrieved_skills,
        user_input
    )

    # ④ LLM
    result = call_llm(prompt, model)

    # ⑤ Skill 名称
    skill_names = ", ".join(
        [
            s["skill"]["name"]
            for s in retrieved_skills
        ]
    )

    # 保存历史
    add_record(
        user_input=user_input,
        skill=skill_names,
        prompt=prompt,
        answer=result
    )

    return (
        str(intent),
        skill_names,
        prompt,
        result
    )


# =========================
# 🎨 CSS（粉蓝UI）
# =========================
css = """
body {
    background: linear-gradient(135deg, #a8d8ff, #ffd6f3);
    font-family: Arial;
}

h1 {
    color: #333;
}

button {
    background: #89CFF0 !important;
    color: white !important;
    border-radius: 10px !important;
}
"""


# =========================
# 📜 HISTORY
# =========================
def show_history():
    data = load_history()

    if not data:
        return "暂无历史记录"

    output = ""
    for i, item in enumerate(reversed(data)):
        idx = len(data) - 1 - i

        output += f"""
---

## 🧠 {item['user_input']}

- ID: {idx}
- Skill: `{item['skill']}`
- Time: {item.get('time','')}

"""
    return output


def get_history_detail(index):
    data = load_history()

    if index < 0 or index >= len(data):
        return "无数据"

    item = data[index]

    return f"""
# 🧠 {item['user_input']}

## Skill
{item['skill']}

## Prompt
{item['prompt']}

## Answer
{item['answer']}
"""


def delete_history(index):
    try:
        index = int(index)
    except:
        return "请输入数字"

    ok = delete_record(index)
    return "✅ 删除成功" if ok else "❌ 删除失败"


def search_history(keyword):
    data = load_history()

    if not data:
        return "暂无历史"

    keyword = (keyword or "").lower()
    output = ""
    found = 0

    for i, item in enumerate(reversed(data)):
        text = (
            item["user_input"]
            + item["skill"]
            + item["prompt"]
            + item["answer"]
        ).lower()

        if keyword in text:
            found += 1
            output += f"""
---

## {item['user_input']}
- Skill: {item['skill']}
- Answer: {item['answer']}
"""

    return output if found else "❌ 没找到"


def skill_stats():
    data = load_history()

    if not data:
        return None, "暂无数据"

    counter = Counter([i["skill"] for i in data])

    labels = list(counter.keys())
    values = list(counter.values())

    plt.figure()
    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title("Skill Distribution")

    text = "\n".join([f"{k}: {v}" for k, v in counter.items()])

    return plt, text


# =========================
# 🧠 UI
# =========================
with gr.Blocks(css=css) as demo:

    gr.Markdown("# 🌈 Multi-Skill AI System")

    # ================= TAB 1 =================
    with gr.Tab("AI System"):

        user_input = gr.Textbox(label="Input", lines=4)

        model = gr.Radio(
            choices=["gpt", "deepseek"],
            value="gpt",
            label="Model"
        )

        btn = gr.Button("search 🚀")

        intent_box = gr.Textbox(
    label="Intent"
)
        skill_box = gr.Textbox(label="Skill")
        prompt_box = gr.Textbox(label="Prompt", lines=10)
        answer_box = gr.Textbox(label="Answer", lines=12)

        btn.click(
            fn=pipeline,
            inputs=[user_input, model],
            outputs=[
    intent_box,
    skill_box,
    prompt_box,
    answer_box
]
        )

    # ================= TAB 2 =================
    with gr.Tab("History & Stats"):

        # ===== stats =====
        stats_btn = gr.Button("Skill Stats")
        stats_plot = gr.Plot()
        stats_text = gr.Markdown()

        stats_btn.click(skill_stats, None, [stats_plot, stats_text])

        gr.Markdown("---")

        # ===== search =====
        search_box = gr.Textbox(label="Search History")
        search_btn = gr.Button("Search")
        search_out = gr.Markdown()

        search_btn.click(search_history, search_box, search_out)

        gr.Markdown("---")

        # ===== show all =====
        refresh_btn = gr.Button("Show All")
        history_out = gr.Markdown()

        refresh_btn.click(show_history, None, history_out)

        gr.Markdown("---")

        # ===== delete =====
        delete_box = gr.Textbox(label="Delete ID")
        delete_btn = gr.Button("Delete")

        delete_btn.click(delete_history, delete_box, search_out)

        # ===== detail =====
        detail_box = gr.Markdown()

        history_list = gr.Radio(label="History List", choices=[])

        def refresh_list():
            data = load_history()
            return gr.update(
                choices=[(item["user_input"], i) for i, item in enumerate(data)]
            )

        refresh_btn.click(refresh_list, None, history_list)

        history_list.change(get_history_detail, history_list, detail_box)


demo.launch()