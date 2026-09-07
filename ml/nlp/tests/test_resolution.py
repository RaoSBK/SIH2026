import pytest
from cias_er.matcher import score_pair

def test_entity_resolution_matching():
    ent1 = {"id": "p1", "name": "Ravi Kumar", "type": "Person", "phone": "9876543210"}
    ent2 = {"id": "p2", "name": "Ravee Kumar", "type": "Person", "phone": "9876543210"}
    
    score = score_pair(ent1, ent2)
    assert score > 0.8
