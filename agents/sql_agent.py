import os
import logging
from utils.llm_pick import llm_pick
from model.schema import AgentSchema

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
    ssd