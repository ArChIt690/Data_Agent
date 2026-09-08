import pytest
from langchain_core.messages import AIMessage

from agents.data_agent import agent_decider
from agents.etl_agent import is_tool
from agents.sql_agent import safety_router
from model.schema import AgentSchema, DataAgentSchema, EtlSchema

#the three functions that decide which edge the graph takes next. they are the
#only parts of the agents that can be tested without calling a model, and they
#are also the parts where a mistake sends the whole run the wrong way.


def test_sql_question_goes_to_the_sql_node():
    state = DataAgentSchema(messages=[], route_resp="sql")

    assert agent_decider(state) == "sql_node"


def test_etl_question_goes_to_the_etl_node():
    state = DataAgentSchema(messages=[], route_resp="etl")

    assert agent_decider(state) == "etl_node"


def test_an_empty_route_is_an_error():
    #if the router model returns nothing usable, stopping here is better than
    #quietly sending every question to whichever agent happens to be first.
    with pytest.raises(ValueError):
        agent_decider(DataAgentSchema(messages=[]))


def test_a_safe_query_goes_to_the_database(agent_state):
    agent_state["safe_checker"] = "Yes"

    assert safety_router(AgentSchema(**agent_state)) == "final_sql_out"


def test_an_unsafe_query_is_cancelled(agent_state):
    agent_state["safe_checker"] = "No"

    assert safety_router(AgentSchema(**agent_state)) == "cancel_sql"


def test_a_tool_call_goes_to_the_tool_node():
    message = AIMessage(
        content="",
        tool_calls=[{"name": "extract_load_tool", "args": {}, "id": "call_1"}],
    )

    assert is_tool(EtlSchema(messages=[message])) == "tool_node"


def test_a_plain_answer_ends_the_run():
    #once the model replies with words instead of a tool call the etl job is
    #finished, so the graph has to stop rather than loop back for another turn.
    message = AIMessage(content="the data is saved", tool_calls=[])

    assert is_tool(EtlSchema(messages=[message])) == "end"
