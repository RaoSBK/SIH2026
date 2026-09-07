# -*- coding: utf-8 -*-

from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class EntityDetail(BaseModel):
    id: str
    properties: Dict[str, Any]
    labels: List[str]
    relationships: List[Dict[str, Any]]
