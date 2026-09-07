import sys

from agents.data_agent import data_Agent
from langchain_core.messages import HumanMessage

if __name__ == "__main__":

    #windows consoles default to cp1252 and the models emit em dashes, accents
    #and narrow spaces, which would crash print() after the work is done
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    question = "I want to extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon' and save it to data/extract folder in the csv folder"

    response = data_Agent.invoke({"messages": [HumanMessage(content=question)]})

    #response is the graph's whole state. pull out the few bits worth reading
    #instead of dumping every message with its token metadata.
    answer = response["messages"][-1].content

    print()
    print("=" * 70)
    print(f"QUESTION   {question}")
    print(f"HANDLED BY {response['route_resp']} agent")
    print("=" * 70)
    print()
    print(answer)
    print()
