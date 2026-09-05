import os
import logging
from utils.llm_pick import llm_pick
from model.schema import AgentSchema
from langchain_core.messages import HumanMessage

logger = logging.getLogger("sql_agent")

def curated_prompt(state : AgentSchema) ->AgentSchema:
#takes the user input and changes to curated prompt
    try:
        user_input = state.user_question
        llm =llm_pick("low")
        response = llm.invoke(f"curate the following question: {user_input}")
        state.curated_prompt = response
        return state
    except Exception as e:
        return logger.error(f"Error occured when taking user input and changing to curated prompt due to: {e}")

def context(state : AgentSchema) -> AgentSchema:
    curated_question = state.curated_prompt

    conn_details = {
        "dbname" : os.getenv("dbname"),
        "host" : os.getenv("host"),
        "user" : os.getenv("user"),
        "password" : os.getenv("password"),
        "port" : os.getenv("port"),
    }

    obj = DataUtils(conn_details)

    schema_info = obj.schema_details(obj)
    Prompt = f"""
            You are an SQL analyst agent. Your task is to convert the user's natural language 
        query into Postgres SQL query that can be executed on the database. You are provided 
        with the user's original query and the schema details of the database, including
        table names, column names, data types, and sample data for each table so that 
        you can understand the structure of the database and generate an accurate SQL query.
        Unless user explicitly asks for specific number of rows, always limit the output to 10 rows.
        Note - Just generate the SQL query without any explanation or additional text because
        this query will be executed directly on the database. So, the output should be SQL
        ready to be executed without any modifications.  
        
        User's Original Query: {curated_question}

        Database Schema Details:
        {schema_info}
                """

    state.context = Prompt

    return state 