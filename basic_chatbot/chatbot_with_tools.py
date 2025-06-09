from dotenv import load_dotenv
import os
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, add_messages, END
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage

from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode


load_dotenv()
groq_model = os.getenv("groq_model")

llm = ChatGroq(model= groq_model)

search_tool = TavilySearchResults(max_results = 2)
tools = [search_tool]

llm_with_tools = llm.bind_tools(tools = tools)
result = llm_with_tools.invoke("whats the weather in kathmandu?")
print(result)