from __future__ import annotations

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_all_streamlit_routes_render():
    app = AppTest.from_file(
        str(ROOT / "streamlit" / "app.py"), default_timeout=60
    ).run()
    assert not app.exception
    for option in app.radio[0].options:
        app.radio[0].set_value(option).run()
        assert not app.exception


def test_prediction_forms_execute():
    app = AppTest.from_file(
        str(ROOT / "streamlit" / "app.py"), default_timeout=60
    ).run()
    app.radio[0].set_value(app.radio[0].options[6]).run()
    for label in [
        "Analyze readmission risk",
        "Estimate waiting time",
        "Forecast revenue scenario",
    ]:
        [button for button in app.button if button.label == label][0].click().run()
        assert not app.exception


def test_assistant_handles_patient_status_and_recovery_questions():
    patient_id = str(
        pd.read_csv(
            ROOT / "datasets" / "processed" / "model_features.csv",
            usecols=["patient_id"],
            nrows=1,
        ).iloc[0, 0]
    )
    answers = {}
    for question in [
        "whats the condition of the patient",
        "how much time it will cure",
    ]:
        app = AppTest.from_file(
            str(ROOT / "streamlit" / "app.py"), default_timeout=60
        ).run()
        app.radio[0].set_value(app.radio[0].options[-2]).run()
        app.text_input[0].set_value(patient_id).run()
        app.chat_input[0].set_value(question).run()
        assert not app.exception
        answers[question] = app.markdown[-3].value

    assert patient_id in answers["whats the condition of the patient"]
    assert "latest recorded encounter" in answers[
        "whats the condition of the patient"
    ]
    assert "cannot predict" in answers["how much time it will cure"]
    assert "observed stay" in answers["how much time it will cure"]
