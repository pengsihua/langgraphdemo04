from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

basic_model = ChatOpenAI(model="glm-5",
                         api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                         base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
advanced_model = ChatOpenAI(model="glm-5.1",
                            api_key="sk-1f87f2a8548e479f9d1a75973554786b",
                            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")


@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """Choose model based on conversation complexity."""
    # for it in enumerate(request.state):
    #     print("it:",it)
    message_count = len(request.state["messages"])
    print("state:",request.state)
    if message_count > 10:
        # Use an advanced model for longer conversations
        model = advanced_model
    else:
        model = basic_model

    return handler(request.override(model=model))


agent = create_agent(
    model=basic_model,  # Default model
    # tools=tools,
    middleware=[dynamic_model_selection]
)

respend = agent.invoke({"messages": [HumanMessage("你好")]})

print(respend)
