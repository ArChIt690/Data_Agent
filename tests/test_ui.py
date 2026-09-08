from pathlib import Path

from streamlit.testing.v1 import AppTest

#AppTest runs the streamlit script the same way the browser does, without a
#browser. these are smoke tests: they check the page builds and the controls
#are there. asking a real question is left out on purpose, because that would
#call the models and hit the database.

APP = str(Path(__file__).resolve().parent.parent / "ui" / "app.py")


def test_the_page_loads():
    app = AppTest.from_file(APP).run()

    assert not app.exception
    assert app.title[0].value == "Data Agent"


def test_the_question_box_is_there():
    app = AppTest.from_file(APP).run()

    assert app.chat_input[0].placeholder == "Ask a question"


def test_clear_chat_empties_the_history():
    app = AppTest.from_file(APP).run()
    app.session_state["messages"] = [{"role": "user", "content": "hello"}]

    clear_button = [button for button in app.button if button.label == "Clear chat"][0]
    clear_button.click().run()

    assert app.session_state["messages"] == []


def test_the_data_files_panel_lists_what_the_agent_wrote():
    app = AppTest.from_file(APP).run()

    #the etl agent's output folders are checked in, so there is always
    #something in the list rather than only after a run
    assert app.expander[0].label.startswith("Data files")
    assert "extract/extracted_data.csv" in app.selectbox[0].options


def test_picking_a_file_previews_it_and_offers_a_download():
    app = AppTest.from_file(APP).run()

    app.selectbox[0].set_value("rides.csv").run()

    #the caption reports the shape and the button hands back that same file
    assert any("rows" in caption.value for caption in app.caption)
    assert app.download_button[0].label == "Download rides.csv"
