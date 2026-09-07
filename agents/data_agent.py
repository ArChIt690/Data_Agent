from agents import sql_agent
from utils.llm_pick import llm_pick
from utils.etl_tools import EtlTools
from model.schema import RouterSchema, DataAgentSchema
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from agents.etl_agent import etl_analyst
from agents.sql_agent import sql_analyst

llm = llm_pick("openrouter")
llm_router = llm.with_structured_output(RouterSchema)

def router_node(state: DataAgentSchema):
    message = state.messages[-1].content

    #the bare question gives the model nothing to route on, so spell out what
    #each agent actually does.
    prompt = f"""
    You are a router that decides which agent should answer a user's question.

    Choose "sql" when the question is about data that already lives in the
    Postgres database - users, drivers, vehicles, rides, payments, ratings.
    Anything phrased as "in our database", asking for counts, totals, lists or
    breakdowns of existing records, belongs here.

    Choose "etl" when the question asks to fetch data from an external API or
    URL, or to convert, reshape or move a file between locations and formats.

    Here is the user's question: {message}
    """

    rout_response_dict = llm_router.invoke(prompt).model_dump()
    route_resp = rout_response_dict['answer']
    state.route_resp = route_resp

    #return no messages. this node adds nothing to the conversation, and
    #messages uses an `add` reducer, so handing back the existing list would
    #append it to itself.
    state.messages = []

    return state

def etl_node(state:DataAgentSchema):

    message = state.messages[-1].content

    response = etl_analyst.invoke(
        {"messages": [HumanMessage(content=message)]}
    )

    #invoke() hands back the sub agent's whole state dict, not a message, so
    #pull its last message out. return only the new one - messages uses an
    #`add` reducer, so langgraph appends what we return to what is already there.
    state.messages = [response["messages"][-1]]

    return state

def sql_node(state : DataAgentSchema):
    messages = state.messages[-1].content

    input_schema = {
                "messages": [],
                "user_question": f"{messages}",
                "curated_prompt": "",
                "context": "",
                "sql_from_llm": "",
                "safe_checker": "No",
                "comments": "",
                "final_sql_out": "",
                "final_ans": ""
            }

    response = sql_analyst.invoke(input_schema)

    #same here - take the sql agent's user facing answer and wrap it back up
    #as a message, returning only the new one for the `add` reducer.
    state.messages = [AIMessage(content=response["final_ans"])]

    return state

data_agent_graph = StateGraph(DataAgentSchema)

data_agent_graph.add_node("router_node" ,router_node)
data_agent_graph.add_node("etl_node" ,etl_node)
data_agent_graph.add_node("sql_node" ,sql_node)

data_agent_graph.add_edge(START, "router_node")

def agent_decider(state: DataAgentSchema):
    if state.route_resp == "sql":
        return "sql_node"
    elif state.route_resp == "etl":
        return "etl_node"
    else:
        raise ValueError(f"Invalid route response : {state.route_resp}")

data_agent_graph.add_conditional_edges("router_node" , agent_decider , {
    "sql_node" : "sql_node",
    "etl_node" : "etl_node",
})

data_Agent = data_agent_graph.compile()

from IPython.display import display, Image
img = Image(data_Agent.get_graph().draw_mermaid_png())
with open("data_agent_graph.png", "wb") as f:
    f.write(img.data)

if __name__ == "__main__":

    response = data_Agent.invoke(
        {"messages":[HumanMessage(content="I want to extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon' and save it to data/extract folder in the csv folder")],
         "route_response": ""}
    )

    print(response)