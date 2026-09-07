import os
from dotenv import load_dotenv
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI 

load_dotenv(override=True)
logger = logging.getLogger("llm-pick")

#seconds to wait on one request before giving up. the openai client defaults to
#600s and retries twice, so a free tier model that stalls hangs the agent for
#half an hour with nothing printed. fail fast and let the caller see the error.
REQUEST_TIMEOUT = 90
MAX_RETRIES = 1

#this function is used to choose llm according to the difficuly
def llm_pick(level: str):
    try:
        if level.lower() == "low":
            llm = ChatGroq(
                model="openai/gpt-oss-120b",
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=0.0,
                request_timeout=REQUEST_TIMEOUT,
                max_retries=MAX_RETRIES,
            )

        elif level.lower() == "high":
            llm = ChatGoogleGenerativeAI(
                model="gemini-3.8-flash",
                api_key=os.getenv("GEMINI_API_KEY"),
                temperature=0.0,
                timeout=REQUEST_TIMEOUT,
                max_retries=MAX_RETRIES,
            )
        elif level.lower() =="medium":
            llm =  ChatMistralAI(
                model_name="mistral-small-latest",
                api_key=os.getenv("MISTRAL_API_KEY"),
                temperature=0.0,
                timeout=REQUEST_TIMEOUT,
                max_retries=MAX_RETRIES,
            )
        elif level.lower() == "openrouter":
            llm = ChatOpenAI(
                model="nvidia/nemotron-3.5-lightning:free",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                temperature=0.0,
                request_timeout=REQUEST_TIMEOUT,
                max_retries=MAX_RETRIES,
            )
        elif level.lower() == "openai":
            llm = ChatOpenAI(
                model="gpt-4o",
                api_key=os.getenv("OPENAI_API_KEY"),
                model_kwargs={
                    "reasoning_effort" : "none",
                },
                request_timeout=REQUEST_TIMEOUT,
                max_retries=MAX_RETRIES,
            )
        else:
            logger.error("Wrong level chosen")
            raise ValueError(f"Unknown level: {level!r}. Use 'low', 'medium', 'high', 'openai' or 'openrouter'.")

        logger.info("LLM chosen succesfully from llm_pick.py")
        return llm

    except Exception as e:
        raise Exception(f"error caused during llm_pick due to : {e}")
