import os
import spacy
from spacy.pipeline import EntityRuler

class NERModelManager:
    """
    Manages lazy loading and pipeline configuration for spaCy NER models.
    Checks for fine-tuned custom models before falling back to en_core_web_sm.
    """
    _instance = None
    _nlp = None

    @classmethod
    def get_nlp(cls):
        if cls._nlp is None:
            model_path = os.path.join(os.path.dirname(__file__), "../models/fine_tuned")
            if os.path.exists(model_path):
                try:
                    cls._nlp = spacy.load(model_path)
                except Exception:
                    cls._nlp = cls._load_fallback()
            else:
                cls._nlp = cls._load_fallback()

            cls._configure_entity_ruler(cls._nlp)

        return cls._nlp

    @classmethod
    def _load_fallback(cls):
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            return spacy.load("en_core_web_sm")

    @classmethod
    def _configure_entity_ruler(cls, nlp_obj):
        if "entity_ruler" not in nlp_obj.pipe_names:
            try:
                ruler = nlp_obj.add_pipe("entity_ruler", before="ner")
                patterns = [
                    {"label": "PHONE", "pattern": [{"TEXT": {"REGEX": r"\b\d{10}\b"}}]},
                    {"label": "VEHICLE", "pattern": [{"TEXT": {"REGEX": r"\b[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}\b"}}]},
                    {"label": "CASE_ID", "pattern": [{"TEXT": {"REGEX": r"\bCASE-\d{3}\b"}}]}
                ]
                ruler.add_patterns(patterns)
            except Exception:
                pass
