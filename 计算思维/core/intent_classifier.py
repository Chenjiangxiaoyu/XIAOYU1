import json
import re
from typing import Dict, List, Optional, Tuple

class IntentClassifier:
    """基于技能文件的意图分类器"""
    
    def __init__(self, skills_config_path: str = "skills/study_skill.json"):
        """
        初始化意图分类器
        
        Args:
            skills_config_path: 技能配置文件路径
        """
        self.skills_config_path = skills_config_path
        self.skill_config = self._load_skill_config()
        self.intent_patterns = self._build_intent_patterns()
        
    def _load_skill_config(self) -> Dict:
        """加载技能配置文件"""
        try:
            with open(self.skills_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 如果文件不存在，使用默认配置
            return self._get_default_config()
        except json.JSONDecodeError:
            print("⚠️  JSON 格式错误，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """默认配置（当 study_skill.json 不存在时使用）"""
        return {
            "name": "Study Skill",
            "description": "帮助大学生制定高效学习计划和复习策略",
            "tags": ["study", "exam", "learning", "planning"],
            "when_to_use": [
                "preparing for an exam",
                "needs a study or review plan",
                "does not know where to start learning",
                "wants to improve study efficiency",
                "feels overwhelmed by course content"
            ],
            "user_profile": ["大学生", "初学者", "基础薄弱的学生", "准备期末考试的学生"]
        }
    
    def _build_intent_patterns(self) -> Dict[str, List[str]]:
        """构建意图匹配模式"""
        return {


        # 学习
        "study": [
            "学习", "学习方法", "怎么学", "如何学习",
            "学不会", "不会学", "看不懂", "知识点",
            "课程", "高数", "概率论", "线代", "大物",
            "基础", "入门", "零基础", "薄弱"
        ],

        # 考试
        "exam": [
            "考试", "exam", "期末", "final",
            "复习", "备考", "冲刺",
            "准备考试", "考前",
            "真题", "模拟题"
        ],

        # 学习规划
        "planning": [
            "学习计划", "study plan",
            "计划", "规划", "安排",
            "schedule",
            "时间管理", "时间表",
            "来不及", "时间不够"
        ],

        # 编程
        "coding": [
            "python", "代码", "编程",
            "bug", "报错", "调试",
            "算法", "开发"
        ],

        # 英语
        "english": [
            "英语", "四级", "六级",
            "四六级",
            "翻译", "听力",
            "阅读", "作文"
        ],

        # 论文
        "paper": [
            "论文",
            "摘要",
            "参考文献",
            "查重",
            "润色"
        ],

        # PPT
        "ppt": [
            "ppt",
            "演讲",
            "汇报",
            "答辩"
        ],

        # 写作
        "writer": [
            "写作",
            "文案",
            "报告",
            "发言稿",
            "文章"
        ],

        # 通用
        "general": [
            "帮助",
            "怎么办",
            "建议",
            "请问",
            "help"
        ]
    }
    
    def classify_intent(self, user_input: str) -> Dict:
        """
        分类用户输入，返回意图和相关信息
        
        Args:
            user_input: 用户输入的文本
        
        Returns:
            包含意图、置信度、提取信息的字典
        """
        input_lower = user_input.lower()
        
        # 检测所有匹配的意图
        matched_intents = []
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in input_lower:
                    matched_intents.append(intent)
                    break
        
        # 如果没有匹配到任何意图
        if not matched_intents:
            return {
                "intent": "general",
                "confidence": 0.3,
                "original_input": user_input,
                "matched_intents": [],
                "skill_used": self.skill_config.get("name", "Study Skill"),
                "entities": self._extract_entities(user_input)
            }
        
        # 提取主要意图（出现次数最多的）
        from collections import Counter
        intent_counter = Counter(matched_intents)
        primary_intent = intent_counter.most_common(1)[0][0]
        confidence = min(0.9, 0.5 + (len(matched_intents) * 0.1))
        
        # 提取实体信息
        entities = self._extract_entities(user_input)
        
        # 生成回复建议（基于技能配置）
        suggestion = self._generate_suggestion(primary_intent, entities)
        
        return {
            "intent": primary_intent,
            "confidence": round(confidence, 2),
            "original_input": user_input,
            "matched_intents": list(set(matched_intents)),
            "skill_used": self.skill_config.get("name", "Study Skill"),
            "skill_description": self.skill_config.get("description", ""),
            "entities": entities,
            "suggestion": suggestion,
            "study_plan_ready": primary_intent in ["exam", "planning"]
        }
    
    def _extract_entities(self, text: str) -> Dict[str, Optional[str]]:
        """从用户输入中提取实体信息"""
        entities = {}
        
        # 提取课程/科目
        course_patterns = [
            r"(数学|英语|语文|物理|化学|生物|历史|地理|政治|编程|计算机|高数|线代|概率|统计|经济学|管理学|法律|医学|文学|哲学|心理学)"
        ]
        for pattern in course_patterns:
            match = re.search(pattern, text)
            if match:
                entities["course"] = match.group(1)
                break
        
        # 提取时间信息
        time_patterns = [
            r"(\d+)\s*(天|周|月|小时|分钟)",
            r"(明天|后天|今天|下周|下个月|期末|期中|马上)"
        ]
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                entities["time"] = match.group(0)
                break
        
        # 提取考试类型
        exam_patterns = [
            r"(期末|期中|月考|模拟|小测|测验|考试|exam|final|midterm)"
        ]
        for pattern in exam_patterns:
            match = re.search(pattern, text)
            if match:
                entities["exam_type"] = match.group(1)
                break
        
        return entities
    
    def _generate_suggestion(self, intent: str, entities: Dict) -> str:
        """根据意图生成建议"""
        suggestions = {
            "exam": f"建议你制定一个{'针对' + entities.get('course', '') if entities.get('course') else ''}考试的复习计划。先评估剩余时间，然后按重要程度分配复习内容。",
            "planning": f"制定学习计划时，建议先确定{'的' + entities.get('course', '') + ' ' if entities.get('course') else ''}学习目标，再拆解为每日可执行的小任务。",
            "study_efficiency": "提高学习效率可以从这几个方面入手：创造专注环境、使用番茄工作法、主动回忆和间隔重复。",
            "course_content": f"梳理{'的' + entities.get('course', '') + ' ' if entities.get('course') else ''}知识点时，建议先看目录和章节总结，建立知识框架。",
            "time_management": "时间紧迫时，建议使用80/20法则，优先复习最重要的20%内容，它们通常占考试分数的80%。",
            "difficulty": "遇到难点时，先理解基本概念，再做针对性练习，也可以查找相关视频或请教他人。",
            "foundation": "基础薄弱时，建议从最基本的概念和例题开始，建立信心后再逐步深入。",
            "practice": "练习时建议：先做例题，再做变式题，最后做综合题，循序渐进。",
            "review": "复习时建议：先做知识梳理（思维导图），再做错题复盘，最后做模拟测试。",
            "help_request": f"很高兴能帮到你！请告诉我更多关于{entities.get('course', '你的学习')}的具体情况，我可以提供更精准的建议。"
        }
        
        return suggestions.get(intent, "请告诉我更多关于你学习情况的具体信息，我可以帮你制定更精准的计划。")
    
    def generate_study_plan(self, user_input: str) -> Dict:
        """
        生成学习计划（如果意图匹配）
        
        Args:
            user_input: 用户输入
        
        Returns:
            包含学习计划的字典
        """
        result = self.classify_intent(user_input)
        
        if result["study_plan_ready"]:
            # 这里可以调用更复杂的学习计划生成逻辑
            result["study_plan"] = {
                "title": f"{result['entities'].get('course', '学习')}复习计划",
                "status": "生成的计划基于当前输入，建议进一步细化",
                "suggested_steps": [
                    "1. 明确学习目标",
                    "2. 评估当前水平",
                    "3. 识别重点章节",
                    "4. 制定每日任务",
                    "5. 安排复习时间",
                    "6. 定期自我检测"
                ]
            }
        
        return result


def main():
    """测试入口"""
    print("=" * 60)
    print("🎯 意图分类器测试 (基于 Study Skill)")
    print("=" * 60)
    print("\n💡 支持的意图类型:")
    print("  - exam_preparation (考试准备)")
    print("  - study_plan (学习计划)")
    print("  - study_efficiency (学习效率)")
    print("  - course_content (课程内容)")
    print("  - time_management (时间管理)")
    print("  - difficulty (遇到难点)")
    print("  - foundation (基础薄弱)")
    print("  - practice (练习建议)")
    print("  - review (复习建议)")
    print("  - help_request (寻求帮助)")
    print("  - general_query (一般问题)")
    print("\n" + "=" * 60)
    
    # 创建分类器实例
    classifier = IntentClassifier()
    
    while True:
        user_input = input("\n📝 请输入你的问题 (输入 'exit' 或 'quit' 退出): ")
        
        if user_input.lower() in ["exit", "quit", "退出"]:
            print("👋 再见！祝学习顺利！")
            break
        
        if not user_input.strip():
            print("⚠️  输入不能为空，请重新输入")
            continue
        
        # 分类意图
        result = classifier.classify_intent(user_input)
        
        # 美化输出
        print("\n" + "-" * 60)
        print("📊 分类结果:")
        print("-" * 60)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("-" * 60)
        
        # 如果匹配到学习计划意图，生成计划
        if result["study_plan_ready"]:
            print("\n📚 学习计划建议:")
            print("-" * 60)
            plan_result = classifier.generate_study_plan(user_input)
            if "study_plan" in plan_result:
                print(f"📌 {plan_result['study_plan']['title']}")
                print(f"   {plan_result['study_plan']['status']}")
                for step in plan_result['study_plan']['suggested_steps']:
                    print(f"   {step}")
            print("-" * 60)


if __name__ == "__main__":
    main()