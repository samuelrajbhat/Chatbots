from langgraph.graph import StateGraph, END

from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict

memory = MemorySaver()
class BaseClass(TypedDict):
    msg: str
node = "Node"
def node_a(state: BaseClass):
    print(node+"_a")
    return Command(
        goto="node_b",
        update={
            "msg": state["msg"] + "a"
        }
    )

def node_b(state: BaseClass):
    print(node + "_b")
    human_response = interrupt("Do you want to gog to C or D? Type C/D")

    if (human_response == "C"):

        return Command(
            goto="node_c",
            update={
                "msg": state["msg"]+ "b"
            }
            )
    elif(human_response == "D"):
        return Command(
            goto= "node_d",
            update={
                "msg": state["msg"]+ "b"
            }
        )
    
def node_c(state: BaseClass):
    print(node+"_c")
    return Command(
        goto=END,
        update= {
            "msg": state["msg"]+ "_c"
        }
    )

def node_d(state: BaseClass):
    print(node+"_d")
    return Command(
        goto=END,
        update= {
            "msg": state["msg"]+ "_d"
        }
    )

graph = StateGraph(BaseClass)

graph.add_node("node_a", node_a)
graph.add_node("node_b", node_b)
graph.add_node("node_c", node_c)
graph.add_node("node_d", node_d)
graph.set_entry_point("node_a")

app =graph.compile(checkpointer= memory)
config = {"configurable": {"thread_id": "1"}}

initial_state = {
    "msg": ""
}

first_result = app.invoke(initial_state, config= config, stream_mode="updates")
print(first_result)
print(app.get_state(config).next)

second_result = app.invoke(Command(resume="D"), config=config, stream_mode="updates")
print (second_result) 