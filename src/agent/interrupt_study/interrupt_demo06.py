import sqlite3
from typing import TypedDict, Annotated

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt


class AgentState(TypedDict):
    messages: list[dict]


@tool("send_email", description="这是发送邮件的的工具")
def send_email(to: Annotated[str, "收件人地址"],
               subject: Annotated[str, "邮件主题"],
               body: Annotated[str, "邮件内容"]):
    # """Send an email to a recipient."""

    # Pause before sending; payload surfaces in result["__interrupt__"]
    print("response")
    response = interrupt({
        "action": "send_email",
        "to": to,
        "subject": subject,
        "body": body,
        "message": "Approve sending this email?",
    })

    print("response:", response)

    if response.get("action") == "approve":
        final_to = response.get("to", to)
        final_subject = response.get("subject", subject)
        final_body = response.get("body", body)

        # Actually send the email (your implementation here)
        print(f"[send_email] to={final_to} subject={final_subject} body={final_body}")
        return f"Email sent to {final_to} successfully!"

    return "Email cancelled by user"


model = init_chat_model(model="glm-5",
                        model_provider="openai",
                        api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                        tags=["joke"]
                        ).bind_tools([send_email])


def agent_node(state: AgentState):
    # LLM may decide to call the tool; interrupt pauses before sending
    result = model.invoke(state["messages"])
    return {"messages": state["messages"] + [result]}


def tool_executor(state: AgentState):
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        tool_call = last_msg.tool_calls[0]
        tool_name = tool_call["name"]
        args = tool_call["args"]

        if tool_name == "send_email":
            result = send_email.invoke(args)
            return {"messages": state["messages"] + [{"role": "tool", "content": result}]}

    return {"messages": state["messages"]}


def should_continue(state: AgentState):
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tool_executor"
    return END


builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tool_executor", tool_executor)

builder.add_edge(START, "agent")

builder.add_conditional_edges("agent", should_continue)

builder.add_edge("tool_executor", END)

checkpointer = SqliteSaver(sqlite3.connect("tool-approval.db", check_same_thread=False))
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "email-workflow"}}
initial = graph.invoke(
    {
        "messages": [
            {"role": "user",
             "content": "发邮件一份关于会议的邮件给alice@example.com,主题：会议，邮件内容：记得4月14日早上10点办公室开会"}
        ]
    },
    config=config,
    version='v2'
)
print(initial)  # -> [Interrupt(value={'action': 'send_email', ...})]

print(initial.interrupts)  # -> [Interrupt(value={'action': 'send_email', ...})]

actioninfo = input("please input the action: \n")

# Resume with approval and optionally edited arguments
resumed = graph.invoke(
    Command(resume={"action": actioninfo, "subject": "Updated subject", "body": "记得4月14日早上10点办公室开会"}),
    config=config,
)
print(resumed["messages"][-1])  # -> Tool result returned by send_email
