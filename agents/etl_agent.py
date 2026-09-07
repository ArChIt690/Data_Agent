from utils.llm_pick import llm_pick
from langchain_core.messages import HumanMessage, AIMessage , ToolMessage
from utils.etl_tools import EtlTools
from model.schema import EtlSchema
from langgraph.graph import StateGraph , START , END
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

#Agent Tools

@tool
def extract_load_tool(url : str, output_folder :str , format : str):
    """
    This tools is used to extract the data from the api by calling the extract_load function
    """

    etl_tool = EtlTools()
    return etl_tool.extract_data( url , output_folder , format)

@tool
def transform_load( input_file_path: str , output_file_path : str, output_format :str , user_question : str):
    """
    this node is responsible to transform the data from a desired location and load the 
    data to a specific location
    """

    etl_tools = EtlTools()
    top_3_rows = etl_tools.transform_load(input_file_path)

    #groq like the rest of the etl path. the openrouter free tier is capped per
    #day, and running out here means the extract succeeds and the transform 429s
    #halfway through the job.
    llm = llm_pick("low")

    prompt = f"""
             You are a Python Data Analyst who uses Pandas to analyze data. 
            You need to provide only the Pandas Code that will help to perform the right ETL operations on the data stored in the file : {input_file_path}
            as per the user's question. Do not provide any explanation or comments, only
            the code should be provided. The code should be in a format that can be executed 
            in a Python environment with Pandas installed. 
            Don't write anything else than Pandas Code. \n
            
            Create the Pandas Dataframe from the data stored in the file : {input_file_path} and then 
            write the code to transform and save the data at {output_file_path}.
            Here's the user's question: {user_question}\n
            Here's the context of the data you will be analyzing: {top_3_rows}\
            """

    response = llm.invoke(prompt).content

    #Optional Cleaning especially for low end llm

    pandas_code = response.strip().strip('```').strip().lstrip('python').strip()

    #execute the code given by llm
    results = etl_tools.execute_load(pandas_code)

    return f"Data Transformed and loaded into : f{output_file_path} as {output_format} format.\n\n Pandas code executed : {pandas_code} , result : {results}"

tools = [extract_load_tool , transform_load]

#same reason as the router: the free openrouter model is slow (20-90s a call)
#and often returns nothing usable. groq answers in about a second.
llm = llm_pick("low")
llm_bind = llm.bind_tools(tools)

def llm_node (state : EtlSchema):
    messages = state.messages

    prompt = f"""
            You are a Python Data Analyst who has access to tools that can extract and load, 
            transform and load data. You will be provided with a user's question 
            and you would need to perform the right ETL operations as per the user's question. 
            If the operation is performed then inform the user and end the coversation.
            Here's the chat history: {messages}\n
    """
    #llm_bind, not llm - only the bound one knows about the tools and can emit
    #tool_calls. keep the whole AIMessage too: .content is a plain str and
    #is_tool needs the .tool_calls attribute that only the message carries.
    response = llm_bind.invoke(prompt)

    #messages uses an `add` reducer, so langgraph appends whatever we return to
    #the existing state. returning the whole list appends it to itself and the
    #history grows geometrically - return only what is new.
    state.messages = [response]

    return state

def tool_node(state : EtlSchema):
    """this tool is responsible for making the right tool call"""

    tool_results = []
    tool_by_name = {tool.name : tool for tool in tools}
    tool_calls = state.messages[-1].tool_calls

    for tool_call in tool_calls:
        #models invent tool names and wrong arguments. crashing the graph loses
        #the whole run, so hand the mistake back as a ToolMessage and let the
        #next llm_node turn correct itself.
        tool = tool_by_name.get(tool_call['name'])

        if tool is None:
            observation = (
                f"there is no tool called {tool_call['name']}. "
                f"available tools: {', '.join(tool_by_name)}"
            )
        else:
            try:
                observation = tool.invoke(tool_call['args'])
            except Exception as e:
                observation = f"tool {tool_call['name']} failed: {type(e).__name__}: {e}"

        tool_results.append(ToolMessage(content=observation, tool_call_id = tool_call['id']))

    state.messages = tool_results

    return state   

etl_analyst_graph = StateGraph(EtlSchema)
etl_analyst_graph.add_node( "llm_node" , llm_node)
etl_analyst_graph.add_node("tool_node" , tool_node)

etl_analyst_graph.add_edge(START , "llm_node")

def is_tool(state : EtlSchema):
    tool_calls = state.messages[-1].tool_calls
    if tool_calls:
        return "tool_node"
    else:
        return "end"

etl_analyst_graph.add_conditional_edges("llm_node" , is_tool,{
        "tool_node" : "tool_node",
        "end" : END
    })
etl_analyst_graph.add_edge("tool_node" , "llm_node")

etl_analyst = etl_analyst_graph.compile()

if __name__ == "__main__":

    #visualise the graph
    from IPython.display import display, Image
    img = Image(etl_analyst.get_graph().draw_mermaid_png())
    with open("etl_analyst_graph.png", "wb") as f:
        f.write(img.data)

    response = etl_analyst.invoke(
        {"messages":[HumanMessage(content="I want to extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon' and save it to data/extract folder in the csv folder")]}
    )

    print(response)