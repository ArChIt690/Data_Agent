import sys
import time
from pathlib import Path

import streamlit as st

#streamlit puts the script's own folder on sys.path, not the project root, so
#`streamlit run ui/app.py` cannot find the agents/ and utils/ packages without this.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.data_agent import data_Agent
from langchain_core.messages import HumanMessage

EXAMPLES = [
    "What are the different types of payment methods in our database?",
    "How many rides do we have, broken down by status?",
    "Extract the data from 'https://pokeapi.co/api/v2/pokemon' into data/extract as csv",
]

st.set_page_config(page_title="Data Agent", page_icon="*", layout="centered")

#the stock chat page is very wide and the rows run into each other. only
#spacing and borders are touched here, colours are left to streamlit so the
#page still looks right in both the light and the dark theme.
st.markdown(
    """
    <style>
    .block-container { padding-top: 3rem; max-width: 820px; }

    [data-testid="stChatMessage"] {
        background: rgba(128, 128, 128, 0.06);
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-radius: 12px;
        padding: 0.75rem 1rem;
    }

    /* the example questions are buttons, but they read better as list items */
    section[data-testid="stSidebar"] .stButton button {
        justify-content: flex-start;
        text-align: left;
        font-weight: 400;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_agent(question):
    #stream instead of invoke, same reason as the cli: the free models take
    #20-90s per call, and a silent invoke() just looks like a frozen page.
    t0 = time.time()
    state = {"messages": [HumanMessage(content=question)], "route_resp": ""}

    with st.status("routing the question...", expanded=True) as status:
        for chunk in data_Agent.stream(state, {"recursion_limit": 15}):
            for node, value in chunk.items():
                state.update(value)
                status.write(f"`{node}` done - {time.time() - t0:.1f}s")

        status.update(
            label=f"answered in {time.time() - t0:.1f}s", state="complete", expanded=False
        )

    #state is the graph's whole state. pull out the two bits worth showing
    #instead of dumping every message with its token metadata.
    answer = state["messages"][-1].content
    meta = f"handled by the {state['route_resp']} agent  |  {time.time() - t0:.1f}s"

    return answer, meta


#streamlit reruns this whole file on every click, so the chat has to live in
#session_state or the page would come back empty after each question.
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Data Agent")
    st.caption("one router, two agents")

    st.markdown(
        "**SQL agent** answers questions about data already in Postgres - users, "
        "drivers, vehicles, rides, payments and ratings.\n\n"
        "**ETL agent** pulls data from an API, or reshapes and moves a file "
        "between formats."
    )

    st.divider()

    st.caption("Try one of these")
    for example in EXAMPLES:
        #a button cannot write straight into the chat, so park the question and
        #let the rerun below pick it up like any typed one.
        if st.button(example, use_container_width=True):
            st.session_state.pending = example

    st.divider()

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("Data Agent")
st.caption("Ask about the database, or ask for data to be fetched and reshaped.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("meta"):
            st.caption(message["meta"])

#pop, not read - the parked question has to be cleared or it would fire again
#on the next rerun.
question = st.chat_input("Ask a question") or st.session_state.pop("pending", None)

if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        #one bad answer from a model should leave the chat usable, so show the
        #failure as the reply instead of letting streamlit blank the page.
        try:
            answer, meta = run_agent(question)
        except Exception as e:
            answer, meta = f"That run failed: `{type(e).__name__}: {e}`", ""

        st.markdown(answer)
        if meta:
            st.caption(meta)

    st.session_state.messages.append({"role": "assistant", "content": answer, "meta": meta})
