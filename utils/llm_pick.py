import os
from dotenv import load_dotenv
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI

load_dotenv(override=True)
logger = logging.getLogger("llm-pick")

try:
    #this function is used to choose llm according to the difficuly
    def llm_pick(level = str):
        if level.lower() == "lower":
            llm = ChatMistralAI(
                api_key= os.getenv("MISTRAL_API_KEY"),
                model_name="mistral-large-latest",
                temperature=0.7,
            )

        elif level.lower() == "high":
            llm = ChatGoogleGenerativeAI(
                model = "gemini-3-flash",
                api_key = os.getenv("GEMINI_API_KEY"),
                temperature = 0.7,
            )
        else:
            logger.error("Wrong level chosen")

        logger.info("LLM chosen succesfully from llm_pick.py")

except Exception as e:
    logger.error(f"error caused during llm_pick due to : {e}")