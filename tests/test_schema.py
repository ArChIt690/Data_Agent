import pytest
from pydantic import ValidationError

from model.schema import AgentSchema, DataAgentSchema, JudgeSchema, RouterSchema

#the schemas are what stops a bad model answer from reaching the graph, so
#these tests check the values that are allowed in and the ones that are not.


@pytest.mark.parametrize("answer", ["sql", "etl"])
def test_router_accepts_both_agents(answer):
    route = RouterSchema(answer=answer, comments="picked from the question")

    assert route.answer == answer


def test_router_rejects_anything_else():
    #agent_decider turns this field straight into an edge name, so a value like
    #"sqlite" would send the run to a node that does not exist.
    with pytest.raises(ValidationError):
        RouterSchema(answer="mongodb", comments="not one of the two agents")


@pytest.mark.parametrize("verdict", ["Yes", "No"])
def test_safe_checker_accepts_the_two_verdicts(agent_state, verdict):
    agent_state["safe_checker"] = verdict
    state = AgentSchema(**agent_state)

    assert state.safe_checker == verdict


def test_safe_checker_rejects_a_third_verdict(agent_state):
    #this is the guardrail's field. anything other than Yes or No must fail
    #loudly here rather than quietly become a "not yes" and skip the check.
    agent_state["safe_checker"] = "Maybe"

    with pytest.raises(ValidationError):
        AgentSchema(**agent_state)


def test_route_response_starts_empty():
    #the router node is what fills this in, so it needs a default. without one
    #the very first state handed to the graph would fail validation.
    state = DataAgentSchema(messages=[])

    assert state.route_resp == ""


def test_judge_carries_its_reason_with_the_verdict():
    #cancel_sql prints these comments back to the user, so a verdict on its own
    #is not enough.
    judge = JudgeSchema(answer="No", comments="the query contains a DROP")

    assert judge.answer == "No"
    assert "DROP" in judge.comments
