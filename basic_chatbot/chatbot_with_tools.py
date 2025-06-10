from dotenv import load_dotenv
import os
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, add_messages, END
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage

from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode


load_dotenv()

class  BasicChatBot(TypedDict):
    messages: Annotated[list, add_messages]


groq_model = os.getenv("groq_model")

search_tool = TavilySearchResults(max_results = 2)
tools = [search_tool]

llm = ChatGroq(model= groq_model)
llm_with_tools = llm.bind_tools(tools = tools)

def chatbot(state: BasicChatBot):
    return{
        "messages": [llm_with_tools.invoke(state["messages"])]
    }

def tools_router(state: BasicChatBot):
    last_message = state["messages"][-1]

    if(hasattr(last_message, "tool_calls") and len(last_message.tool_calls)> 0):
        return "tool_node"
    else:
        return END
    

tool_node = ToolNode(tools= tools)

graph = StateGraph(BasicChatBot)

graph.add_node("chatbot", chatbot)
graph.add_node("tool_node", tool_node)

graph.set_entry_point("chatbot")
graph.add_conditional_edges("chatbot", tools_router)
graph.add_edge("tool_node", "chatbot")
app = graph.compile()

while True:
    user_input = input("user: ")
    if(user_input in ["exit", "end"]):
        break
    else:
        result = app.invoke({
            "messages": [HumanMessage(content= user_input)]
        })
    print(result)