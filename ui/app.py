import sys
import time
from pathlib import Path

import pandas as pd
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

#where the etl agent writes what it extracts and transforms
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
READABLE_FORMATS = {".csv", ".json", ".parquet"}

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


def data_files():
    """every readable data file under data/, most recently written first.

    the etl agent takes its output folder from the user's question, so rather
    than hardcoding data/extract and data/transform this walks the whole folder.
    sorting by modified time puts whatever the last run produced at the top,
    which is the file the user actually wants to look at.
    """
    if not DATA_DIR.exists():
        return []

    files = [f for f in DATA_DIR.rglob("*") if f.suffix.lower() in READABLE_FORMATS]

    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


def load_file(file_path):
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(file_path)

    if suffix == ".json":
        #extract_data writes json with lines=True, so try that first. a file
        #from anywhere else is more likely to be a plain array, so fall back to
        #that instead of failing.
        try:
            return pd.read_json(file_path, lines=True)
        except ValueError:
            return pd.read_json(file_path)

    return pd.read_parquet(file_path)


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
        if st.button(example, width="stretch"):
            st.session_state.pending = example

    st.divider()

    if st.button("Clear chat", width="stretch"):
        st.session_state.messages = []
        st.rerun()

st.title("Data Agent")
st.caption("Ask about the database, or ask for data to be fetched and reshaped.")

#collapsed by default so it stays out of the way until there is a reason to open
#it. the count in the label is enough to tell the user a new file has appeared.
files = data_files()

with st.expander(f"Data files ({len(files)})"):
    if not files:
        st.caption("Nothing here yet. Ask the ETL agent to fetch or transform something.")
    else:
        #show the path relative to data/ so the dropdown reads
        #"extract/extracted_data.csv" rather than the whole absolute path
        options = {f.relative_to(DATA_DIR).as_posix(): f for f in files}
        choice = st.selectbox("File", list(options), label_visibility="collapsed")
        file_path = options[choice]

        try:
            df = load_file(file_path)
        except Exception as e:
            st.error(f"Could not read that file: {type(e).__name__}: {e}")
        else:
            st.caption(f"{len(df):,} rows, {len(df.columns)} columns")
            st.dataframe(df, width="stretch", height=300)

            #hand back the file exactly as it was written rather than
            #re-serialising the dataframe, so a json download stays json.
            st.download_button(
                f"Download {file_path.name}",
                data=file_path.read_bytes(),
                file_name=file_path.name,
                width="stretch",
            )

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
