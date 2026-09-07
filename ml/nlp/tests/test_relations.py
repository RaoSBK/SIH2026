import pytest
from ml.nlp.cias_nlp import process_text

def test_relation_extraction():
    sample_text = "Ravi Kumar was seen near Andheri. Contact 9876543210 was used by him."
    res = process_text(sample_text)
    assert "entities" in res
    assert "relations" in res
    assert isinstance(res["relations"], list)
