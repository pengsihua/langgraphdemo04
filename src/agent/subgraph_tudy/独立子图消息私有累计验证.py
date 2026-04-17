from langgraph.constants import START
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import AIMessage, HumanMessage

# ======================================
# 子图：私有消息、自动累积、独立记忆
# ======================================
sub_builder = StateGraph(MessagesState)

def sub_agent(state: MessagesState):
    # 子图拿到的是【完整累积的历史消息】
    print(f"\n【子图内部】当前历史条数: {len(state['messages'])}")

    # 子图生成回复 → 自动追加到 messages（累积）
    return {"messages": [
        AIMessage(content=f"我是子Agent，我记得你说了{len(state['messages'])}轮话")
    ]}

sub_builder.add_node("sub_agent", sub_agent)
sub_builder.add_edge(START,"sub_agent")


# 子图自己的 checkpoint → 保存私有消息
sub_graph = sub_builder.compile(checkpointer=InMemorySaver())

# ======================================
# 父图：只负责调用子图，不污染、不查看内部
# ======================================
parent_builder = StateGraph(MessagesState)

def parent_node(state: MessagesState):
    print("\n==== 父节点调用子图 ====")

    # 🔥 关键：固定子图 thread_id → 消息永久累积
    sub_config = {"configurable": {"thread_id": "PRIVATE_SUB_AGENT_001"}}

    # 调用子图（不传消息，让子图自己从checkpoint读取历史）
    sub_graph.invoke({}, config=sub_config)
    return state

parent_builder.add_node("parent_node", parent_node)
parent_builder.add_edge(START,"parent_node")
parent_graph = parent_builder.compile(checkpointer=InMemorySaver())

# ======================================
# 运行 3 次，验证子图消息累积
# ======================================
if __name__ == "__main__":
    parent_config = {"configurable": {"thread_id": "PARENT_THREAD_1"}}

    print("======== 第 1 次调用父图 ========")
    parent_graph.invoke({}, parent_config)

    print("\n======== 第 2 次调用父图 ========")
    parent_graph.invoke({}, parent_config)

    print("\n======== 第 3 次调用父图 ========")
    parent_graph.invoke({}, parent_config)

    # ================================
    # 最终验证：查看子图累积的消息
    # ================================
    print("\n" + "="*60)
    sub_state = sub_graph.get_state({"configurable": {"thread_id": "PRIVATE_SUB_AGENT_001"}})
    print(f"【最终子图私有消息总数】: {len(sub_state.values['messages'])}")
    for vv in sub_state.values['messages']:
        print(vv)