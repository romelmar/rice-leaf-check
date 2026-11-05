"""Smoke-test startup without requiring the user's trained model."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

root = Path(__file__).resolve().parents[1]
app = AppTest.from_file(str(root / 'app.py'), default_timeout=90).run()
assert not app.exception, [item.message for item in app.exception]
assert app.title[0].value == 'A closer look at your rice leaves'
assert any('model files' in item.value for item in app.warning)
print('App startup and missing-model instructions passed.')
