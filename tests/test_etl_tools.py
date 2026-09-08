import pandas as pd
import pytest

from utils.etl_tools import EtlTools


class FakeResponse:
    """stands in for what requests.get hands back.

    the extract tests should not need the pokemon api to be up, and should not
    be slow or fail on a train with no wifi.
    """

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def fake_get(payload):
    return lambda url: FakeResponse(payload)


def test_extract_data_writes_a_csv(tmp_path, monkeypatch):
    payload = {"results": [{"name": "bulbasaur"}, {"name": "ivysaur"}]}
    monkeypatch.setattr("utils.etl_tools.requests.get", fake_get(payload))

    result = EtlTools().extract_data("https://fake-api/pokemon", str(tmp_path), "csv")

    saved = pd.read_csv(tmp_path / "extracted_data.csv")
    assert "sucessfully extracted" in result
    assert len(saved) == 2


def test_extract_data_flips_a_single_record_into_rows(tmp_path, monkeypatch):
    #one record normalises to a single very wide row that nobody can read, so
    #extract_data transposes it into field/value rows. this is the branch worth
    #testing because it is the one that is easy to break later.
    payload = {"name": "pikachu", "height": 4, "weight": 60}
    monkeypatch.setattr("utils.etl_tools.requests.get", fake_get(payload))

    EtlTools().extract_data("https://fake-api/pokemon/pikachu", str(tmp_path), "csv")

    saved = pd.read_csv(tmp_path / "extracted_data.csv")
    assert list(saved.columns) == ["field", "value"]
    assert len(saved) == 3


def test_extract_data_rejects_an_unknown_format(tmp_path, monkeypatch):
    monkeypatch.setattr("utils.etl_tools.requests.get", fake_get({"results": [{"name": "bulbasaur"}]}))

    result = EtlTools().extract_data("https://fake-api/pokemon", str(tmp_path), "xml")

    assert result == "unsupported format"


def test_transform_load_reads_a_csv(tmp_path):
    file_path = tmp_path / "sample.csv"
    pd.DataFrame({"name": ["a", "b"], "price": [10, 20]}).to_csv(file_path, index=False)

    result = EtlTools().transform_load(str(file_path))

    #the return value is the head of the frame as text, which the etl agent
    #pastes into the prompt so the model can see the real column names.
    assert "name" in result
    assert "price" in result


def test_transform_load_rejects_an_unknown_extension(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("hello")

    result = EtlTools().transform_load(str(file_path))

    assert "Unsupported file extension" in result


def test_execute_load_runs_the_code(tmp_path):
    output = tmp_path / "written.txt"
    #a raw string for the path, otherwise the windows backslashes turn into
    #escape characters inside the generated code.
    code = f"open(r'{output}', 'w').write('done')"

    result = EtlTools().execute_load(code)

    assert result == "Code executed succesfully"
    assert output.read_text() == "done"


def test_execute_load_reports_bad_code_instead_of_crashing():
    #the model writes this code, so it will sometimes be wrong. the tool has to
    #hand the error back as text - a raise here would kill the whole graph run
    #instead of letting the next llm_node turn fix itself.
    result = EtlTools().execute_load("this is not python")

    assert "error occured while executing the code" in result
