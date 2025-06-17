from langgraph.graph import StateGraph, START, add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt, Command

from langchain_groq import ChatGroq

from typing import TypedDict, Annotated, List


import uuid
from dotenv import load_dotenv
import os

load_dotenv()

groq_model = os.getenv("groq_model")
llm = ChatGroq(model=groq_model)

class StateClass(TypedDict):
    linkedin_topic : str
    generated_post : Annotated[list[str], add_messages]
    human_feedback : Annotated[List[str], add_messages]


def model(state: StateClass):
    """Here, We are using thr LLM to generate a linkedIn post with human feedback incorporated"""
    print("[MODEL] Generating Content")
    linkedin_topic = state["linkedin_topic"]
    feedback = state["human_feedback"] if "human_feedback" in state else ["No Feedback Yet"]

    # Define the PROMPT

    prompt = f"""
        LinkedIn Topic: {linkedin_topic}
        Human Feedback: {feedback[-1] if feedback else "No feedback yet"}
        Generate a structured and well-written LinledIN post based on the given topic
        Consider previous human feedback to refine the response.
        """
    response = llm.invoke([
        SystemMessage(content="You are an expert LinkedIn content writer"),
        HumanMessage(content = prompt)
        ])
    
    generated_linkedin_post = response.content
    
    print(f"[model_node] Generated Post : \n {generated_linkedin_post}")

    return {
        "generated_post": generated_linkedin_post,
        "human_feedback": feedback
    }

def human_node(state: StateClass):
    """Human Interventation node
    -> Loops back to model node untill human inputs are done"""

    print("\n [human node] awaiting hujman feedback ...")
    
    generated_post = state["generated_post"]
    
    user_feedback = interrupt(
        {
            "generated_post": generated_post,
            "message": "Provide feedback or type 'done' to finish giving feedback "
        }
    )

    print(f"[humann node] Received human feedback: {user_feedback}")

    #  Transation to END if user types 'done'

    if user_feedback.lower() == "done":
        return Command(update = {"human_feedback": state["human_feedback"]+ ["Finalized"]}, goto= "end_node")
    
    # UPdate feedback and return to model to regenerate  the response based on the response

    return Command(update={"human_feedback": state["human_feedback"]+ [user_feedback]}, goto= "model")

def end_node(state: StateClass):
    """Final Nodde"""
    print("\n [end node] Process finished")
    print("Finall Generated Post: ", state["generated_post"][-1])
    print("Final Human Feedback:", state["human_feedback"])

    return {
        "generated_text":state["generated_post"], 
        "human_feedback": state["human_feedback"]
    }

# Building Graph

graph = StateGraph(StateClass)

graph.add_node("model", model)
graph.add_node("human_node", human_node)
graph.add_node("end_node", end_node)
graph.set_entry_point("model")

graph.add_edge("model", "human_node")
graph.add_edge("human_node", "model")
graph.set_finish_point("end_node")

checkpointer = MemorySaver()

app = graph.compile(checkpointer= checkpointer)

thread_config = {"configurable": {"thread_id": uuid.uuid4()}}

linkedin_topic = input("Enter your LinkkedIn topic")

initial_state = {
    "linkedin_topic": linkedin_topic,
    "generated_post": [],
    "human_feedback": [],
}

for chunk in app.stream(initial_state, config= thread_config):
    for node_id, value in chunk.items():
        if(node_id == "__interrupt__"):
            while True: 
                user_feedback = input("provide feedback or  type 'done' when finished")

                # Resume the graph execution with the user's feedback

                app.invoke(Command(resume=user_feedback),config = thread_config)

                # exit loop if users says done
                if user_feedback.lower() == "done":
                    break