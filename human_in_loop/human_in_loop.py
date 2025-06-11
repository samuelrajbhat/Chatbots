from typing import TypedDict, Annotated
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, add_messages, END
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from langchain_community.tools import TavilySearchResults

load_dotenv()

sqlite_connection = sqlite3.connect("human_in_loop.sqlite", check_same_thread= False)
memory = SqliteSaver(sqlite_connection)

groq_model = os.getenv("groq_model")

class BasicChatModel(TypedDict):
    messages: Annotated[list, add_messages]

search_tools = TavilySearchResults(max_results = 1)

tools = [search_tools]

llm  = ChatGroq(model = groq_model)
llm_with_tools = llm.bind_tools(tools= tools)



GENERATE_POST = "generate_post"
GET_REVIEW_DECISION = "get_review_decision"
POST = "post"
COLLECT_FEEDBACK = "collect_feedback"

def generate_post(state : BasicChatModel):
    return{
            "messages": [llm.invoke(state["messages"])]
        }
    
def get_review_decision(state: BasicChatModel):
    post_content = state["messages"][-1].content
    print("\n current Linked in post:\n")
    print(post_content)
    decision = input("Do you want to contiue with this post? Enter 1 to contiune : ")
    print("typeeeee",type(decision))
    if decision == "yes":
        return POST
    else:
        return COLLECT_FEEDBACK

def post(state: BasicChatModel):
    final_post = state["messages"][-1].content
    print("\n The final post to LinkedIn: \n")
    print(final_post)

def colllect_feedbacak(state: BasicChatModel):
    feedback = input("Enter you feedback for the above post:")
    return{
        "messages": [HumanMessage(content = feedback)]
    }
     


graph = StateGraph(BasicChatModel)

graph.add_node(GENERATE_POST, generate_post)
graph.set_entry_point(GENERATE_POST)

graph.add_node(GET_REVIEW_DECISION, get_review_decision)
graph.add_node(POST, post)
graph.add_node(COLLECT_FEEDBACK, colllect_feedbacak)

graph.add_conditional_edges(GENERATE_POST, get_review_decision)
graph.add_edge(COLLECT_FEEDBACK, GENERATE_POST)

graph.add_edge(POST, END)
app = graph.compile(checkpointer= memory)
config = {"configurable": {"thread_id": 1}}


while True:
    user_input = input("User: ")

    if user_input in ["end", "end"]:
        break
    else:
        result = app.invoke({
            "messages": [HumanMessage(content = user_input)]
        }, config=config)
    print("AI: ", result)
