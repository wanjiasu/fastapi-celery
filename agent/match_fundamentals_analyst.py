from dotenv import load_dotenv
import os
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from typing import Dict, Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
load_dotenv()
from agent.api_football_tools import get_fixture_basic_info, get_standing_home_info, get_standing_away_info, get_fixture_head2head, get_home_last_10, get_away_last_10, get_injuries, get_fixture_odds

# 模型初始化
# 注意：langchain-openai 1.0.x 使用参数 `model` 而不是 `model_name`
# 为了兼容不同的后端（特别是自定义 OpenAI 风格服务），从环境变量读取模型名
def _ensure_v1_base_url(url: str | None) -> str | None:
    """确保 base_url 以 /v1 结尾，避免非 JSON 响应导致 SDK 解析失败。"""
    if not url:
        return url
    u = url.rstrip("/")
    if not u.endswith("/v1"):
        u = f"{u}/v1"
    return u

llm = ChatOpenAI(
    model=os.getenv("YUNWU_MODEL") or "gpt-5",
    api_key=os.getenv("YUNWU_API_KEY"),
    base_url=_ensure_v1_base_url(os.getenv("YUNWU_API_BASE_URL")),
)



# 完整的状态定义
class AgentState(MessagesState):
    fixture_id: Annotated[int, "Fixture ID for the current match"]
    fundamentals_report: Annotated[str, "Fundamentals report for the current match"]
    if_bet: int | None = None
    predict_winner: str | None = None
    confidence: float | None = None
    key_tag_evidence: str | None = None
    languages: Sequence[str] | None = None
    translations: Dict[str, Dict[str, str]] | None = None

def create_evaluator_node(llm):
    def evaluator_node(state: AgentState):
        report = state.get("fundamentals_report")
        if not report:
            return {}
        prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                'You are a highly constrained football betting analyst. Your sole task is to analyze the provided Markdown fundamentals report and output the prediction data. STRICTLY adhere to the following rules:'
                ' 1. Output MUST be a single-line, valid JSON object.'
                ' 2. DO NOT include any markdown, code fences (```json), explanations, or preamble.'
                ' 3. you must know who is home team and who is away team, don\'t get mix the two teams.'
                ' 4. Use the exact following structure (Schema Definition):'
                '    - \'if_bet\': Integer (1 = Yes, 0 = No). Please make a bold conclusion: return 0 if you hold a wait-and-see attitude, return 1 if you hold a betting attitude.'
                '    - \'predict_winner\': String (\'home\' or \'away\')'
                '    - \'confidence\': Float (ranging from 0.0 to 1.0)'
                '    - \'key_tag_evidence\': String (Core evidence tags, separated by a \'/\' character).'
            ),
            (
                "human",
                "Fixture {fixture_id} report:\n\n{report}",
            ),
        ])
        chain = prompt_template | llm
        fixture_id = state["fixture_id"]
        result = chain.invoke({"fixture_id": fixture_id, "report": report})
        try:
            import json
            prediction_data = json.loads(result.content)
            return {
                "if_bet": prediction_data.get("if_bet"),
                "predict_winner": prediction_data.get("predict_winner"),
                "confidence": prediction_data.get("confidence"),
                "key_tag_evidence": prediction_data.get("key_tag_evidence"),
            }
        except Exception:
            return {
                "if_bet": None,
                "predict_winner": None,
                "confidence": None,
                "key_tag_evidence": None,
            }
    return evaluator_node

def create_translator_node(llm):
    def translator_node(state: AgentState):
        report = state.get("fundamentals_report")
        predict_winner = state.get("predict_winner")
        key_tag_evidence = state.get("key_tag_evidence")
        if not report:
            return {}
        lang_str = os.getenv("LANGUAGE_LIST", "")
        items = [s.strip() for s in lang_str.split(",") if s.strip()]
        pairs = []
        for it in items:
            name_locale = it.split(":", 1)
            if len(name_locale) == 2:
                pairs.append((name_locale[0].strip(), name_locale[1].strip()))
        if not pairs:
            return {}
        translations: Dict[str, Dict[str, str]] = {}
        for name, locale in pairs:
            prompt_template = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "Translate the content to {target_name} (locale {target_locale}). Return a single-line valid JSON object with keys: 'report', 'predict_winner', 'key_tag_evidence'. Do not include markdown fences or extra text.",
                ),
                (
                    "human",
                    '{{"report": "{report}", "predict_winner": "{predict_winner}", "key_tag_evidence": "{key_tag_evidence}"}}',
                ),
            ])
            chain = prompt_template | llm
            result = chain.invoke({
                "target_name": name,
                "target_locale": locale,
                "report": report,
                "predict_winner": predict_winner or "",
                "key_tag_evidence": key_tag_evidence or "",
            })
            try:
                import json
                data = json.loads(result.content)
                translations[name] = {
                    "report": data.get("report", ""),
                    "predict_winner": data.get("predict_winner", ""),
                    "key_tag_evidence": data.get("key_tag_evidence", ""),
                }
            except Exception:
                translations[name] = {
                    "report": result.content if hasattr(result, "content") else str(result),
                    "predict_winner": "",
                    "key_tag_evidence": "",
                }
        return {"languages": [n for n, _ in pairs], "translations": translations}
    return translator_node

# 创建fundamentals analyst 节点函数
def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        # 保证 fixture_id 是整数，避免后续工具调用出现类型不一致
        try:
            fixture_id = int(state["fixture_id"]) if state.get("fixture_id") is not None else None
        except Exception:
            fixture_id = state["fixture_id"]

        tools = [
            get_fixture_head2head,
            get_home_last_10,
            get_away_last_10,
            get_injuries,
            get_fixture_basic_info,
            get_standing_home_info,
            get_standing_away_info,
            get_fixture_odds,
        ]

        system_message = (
            "你是一名研究员, 负责分析一场足球比赛的基本面信息. 请用英文撰写一份全面的足球比赛的基本面信息报告, 内容包括球队实力面, 球队近期状态, 阵容与伤停, 战意, 以便下注者全面了解这场足球比赛. 确保包含尽可能多的细节，不要简单陈述趋势好坏，需提供详细且精细的分析与见解，以帮助交易者做出决策。"
            + "请在报告末尾附加一个Markdown表格，用于整理报告中的关键要点，确保内容条理清晰、易于阅读。"
            + "请使用以下可用工具: "
            + "get_fixture_head2head: 获取主队和客队的最近比赛记录."
            + "get_home_last_10: 获取主队最近10场比赛记录."
            + "get_away_last_10: 获取客队最近10场比赛记录."
            + "get_injuries: 获取球队伤停信息."
            + "get_fixture_basic_info: 获取比赛基本信息."
            + "get_standing_home_info: 获取主队积分榜信息."
            + "get_standing_away_info: 获取客队积分榜信息."
            + "get_fixture_odds: 获取比赛赔率信息."
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "你是一个有帮助的AI助手，正在与其他助手协作。"
                " 请使用提供的工具逐步回答问题。"
                " 如果无法完全回答也没关系，其他拥有不同工具的助手会接续你的工作。请尽你所能推进进度。"
                " 如果你或任何其他助手已有最终交易建议：下注/观望或者可交付成果，"
                " 请在回复前加上'最终交易建议：下注/观望'，以便团队停止后续操作。"
                " 你可使用以下工具：{tool_names}。\n{system_message}"
                " 供你参考，我们要分析的比赛id是{fixture_id}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(fixture_id=fixture_id)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke({"messages": state["messages"], "fixture_id": fixture_id})

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node

# 创建消息清理节点
def create_msg_delete():
    def msg_delete_node(state):
        return {"messages": []}
    return msg_delete_node

# 条件逻辑函数
def should_continue_fundamentals(state: AgentState):
    """Determine if fundamentals analysis should continue."""
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools_fundamentals"
    return "Msg Clear Fundamentals"

tools = [
            get_fixture_head2head,
            get_home_last_10,
            get_away_last_10,
            get_injuries,
            get_fixture_basic_info,
            get_standing_home_info,
            get_standing_away_info,
            get_fixture_odds,
        ]

tool_node = ToolNode(tools=tools)

def create_fundamentals_graph():

    # 创建节点
    fundamentals_analyst = create_fundamentals_analyst(llm)
    msg_clear = create_msg_delete()
    evaluator = create_evaluator_node(llm)
    translator = create_translator_node(llm)

    # 创建工作流
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("Fundamentals Analyst", fundamentals_analyst)
    workflow.add_node("Msg Clear Fundamentals", msg_clear)
    workflow.add_node("tools_fundamentals", tool_node)
    workflow.add_node("evaluator", evaluator)
    workflow.add_node("translator", translator)

    # 添加边
    workflow.add_edge(START, "Fundamentals Analyst")
    workflow.add_conditional_edges(
        "Fundamentals Analyst",
        should_continue_fundamentals,
        {
            "tools_fundamentals": "tools_fundamentals",
            "Msg Clear Fundamentals": "Msg Clear Fundamentals",
        },
    )
    workflow.add_edge("tools_fundamentals", "Fundamentals Analyst")
    workflow.add_edge("Msg Clear Fundamentals", "evaluator")
    workflow.add_edge("evaluator", "translator")
    workflow.add_edge("translator", END)

    # compile
    return workflow.compile()

# 创建图的实例
graph = create_fundamentals_graph()

# 测试函数
def test_fundamentals_analyst(fixture_id: int = 1347805):
    """测试 fundamentals analyst"""
    initial_state = {
        "messages": [HumanMessage(content=f"分析比赛id为 {fixture_id} 的基本面数据")],
        "fixture_id": fixture_id,
        "sender": "user",
        "fundamentals_report": "",
    }
    
    # 运行图
    result = graph.invoke(initial_state)
    translations = result.get("translations") or {}
    languages = result.get("languages") or list(translations.keys())
    print(", ".join(languages))
    return translations

if __name__ == "__main__":
    t = test_fundamentals_analyst(fixture_id=1347805)
    import json
    print(json.dumps(t, ensure_ascii=False))
