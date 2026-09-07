import sys
import time

from agents.data_agent import data_Agent
from langchain_core.messages import HumanMessage


def ask(question):
    #stream instead of invoke so each node reports as it finishes. the free
    #models take 20-90s per call, and a silent invoke() looks like a freeze.
    t0 = time.time()
    state = {"messages": [HumanMessage(content=question)], "route_resp": ""}

    print(f"\n[{time.time() - t0:5.1f}s] routing...", flush=True)

    for chunk in data_Agent.stream(state, {"recursion_limit": 15}):
        for node, value in chunk.items():
            state.update(value)
            print(f"[{time.time() - t0:5.1f}s] {node} done", flush=True)

    #state is the graph's whole state. pull out the few bits worth reading
    #instead of dumping every message with its token metadata.
    answer = state["messages"][-1].content

    print()
    print("=" * 70)
    print(f"QUESTION   {question}")
    print(f"HANDLED BY {state['route_resp']} agent")
    print(f"TOOK       {time.time() - t0:.1f}s")
    print("=" * 70)
    print()
    print(answer)
    print()


if __name__ == "__main__":

    #windows consoles default to cp1252 and the models emit em dashes, accents
    #and narrow spaces, which would crash print() after the work is done
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

    #one-shot mode: python main.py "extract the data from ..."
    if len(sys.argv) > 1:
        ask(" ".join(sys.argv[1:]))
        sys.exit(0)

    #otherwise keep asking until the user leaves
    print("Data Agent ready. Type your question, or 'exit' to quit.")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            break

        #one bad answer from the model should not kill the session
        try:
            ask(question)
        except Exception as e:
            print(f"\nthat run failed: {type(e).__name__}: {e}\n")
