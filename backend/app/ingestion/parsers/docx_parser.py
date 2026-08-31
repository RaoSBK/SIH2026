import docx
from docx.document import Document
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl

def iter_block_items(parent):
    """
    Yield each paragraph and table child within *parent*, in document order.
    """
    if isinstance(parent, Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Something's not right")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def parse_docx(file_path: str) -> dict:
    """Extracts text from a Word document, preserving paragraph and table order."""
    text_content = []
    try:
        doc = docx.Document(file_path)
        
        for block in iter_block_items(doc):
            if isinstance(block, Paragraph):
                if block.text.strip():
                    text_content.append(block.text.strip())
            elif isinstance(block, Table):
                for row in block.rows:
                    row_data = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
                    if any(row_data):
                        text_content.append(" | ".join(row_data))
                        
        return {
            "data_shape": "unstructured",
            "content": "\n".join(text_content),
            "detected_subtype": "unknown", # Usually classified later (e.g. fir vs surveillance)
            "warnings": []
        }
    except Exception as e:
        raise Exception(f"Failed to parse DOCX: {str(e)}")
