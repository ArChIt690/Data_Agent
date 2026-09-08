import pytest
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI

from utils.llm_pick import llm_pick

#every fallback loop in the project asks for a level and trusts it gets a
#different provider back. these tests check the levels really are three
#different companies, because a fallback between two models on one dead account
#would not help at all.


def test_low_gives_groq():
    assert isinstance(llm_pick("low"), ChatGroq)


def test_medium_gives_mistral():
    assert isinstance(llm_pick("medium"), ChatMistralAI)


def test_high_gives_gemini():
    assert isinstance(llm_pick("high"), ChatGoogleGenerativeAI)


def test_level_is_not_case_sensitive():
    #llm_pick lowercases the level, so a stray capital in a node should not
    #fall through to the error branch.
    assert isinstance(llm_pick("LOW"), ChatGroq)


def test_unknown_level_is_rejected():
    #llm_pick raises ValueError inside its own try block, and the except around
    #it re-raises that as a plain Exception - so a plain Exception is what a
    #caller actually has to catch.
    with pytest.raises(Exception) as error:
        llm_pick("banana")

    assert "Unknown level" in str(error.value)
