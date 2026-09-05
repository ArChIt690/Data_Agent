import os
from dotenv import load_dotenv
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv(override=True)
logger = logging.getLogger("llm-pick")

#this function is used to choose llm according to the difficuly
def llm_pick(level: str):
    try:
        if level.lower() == "low":
            llm = ChatGroq(
                model="openai/gpt-oss-120b",
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=0.7,
            )

        elif level.lower() == "high":
            llm = ChatGoogleGenerativeAI(
                model="gemini-3.8-flash",
                api_key=os.getenv("GEMINI_API_KEY"),
                temperature=0.7,
            )
        else:
            logger.error("Wrong level chosen")
            raise ValueError(f"Unknown level: {level!r}. Use 'low' or 'high'.")

        logger.info("LLM chosen succesfully from llm_pick.py")
        return llm

    except Exception as e:
        raise Exception(f"error caused during llm_pick due to : {e}")
