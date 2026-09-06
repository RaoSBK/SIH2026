import pytest
from backend.app.ingestion.relevance import assess_relevance

def test_irrelevant_hostel_menu():
    menu_text = """
    HOSTEL MESS MENU - MARCH 2024
    Breakfast: Puri, Chole, Tea
    Lunch: Dal, Rice, Biscuits Chick
    Dinner: Roti, Paneer Butter Masala
    """
    res = assess_relevance(menu_text)
    assert res["is_relevant"] is False
    assert "Low relevance" in res["reason"]
    assert res["signal_count"] == 0

def test_relevant_fir_document():
    fir_text = """
    FIRST INFORMATION REPORT (Under Section 154 Cr.P.C.)
    P.S. Bandra Police Station, District Mumbai. FIR-2024-8841.
    Complainant: Ramesh Sharma stated that accused Vijay Kumar met suspect near railway station.
    Contact Mobile: +919876543210.
    """
    res = assess_relevance(fir_text)
    assert res["is_relevant"] is True
    assert res["matched_regexes"] != []
    assert len(res["matched_keywords"]) >= 3

def test_borderline_note():
    note_text = "Ravi was seen near the police station."
    res = assess_relevance(note_text)
    assert res["is_relevant"] is True
    assert res["is_borderline"] is True
    assert "police" in res["matched_keywords"]
    assert "station" in res["matched_keywords"]
