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
