import re
import io
import PyPDF2
from rapidfuzz import process, fuzz
import json
import hashlib
import spacy

_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import os
            if os.path.exists("ml/nlp/models/fine_tuned"):
                print("Loading custom fine-tuned NER model...")
                _nlp = spacy.load("ml/nlp/models/fine_tuned")
            else:
                _nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading language model for the first time...")
            from spacy.cli import download
            download("en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")
    return _nlp

def clean_ocr_noise(text):
    noise_map = {
        '0': 'O', '1': 'I', '@': 'a', '5': 's', '8': 'B',
        '#': '', '?': '', '!': '', '%': ''
    }
    
    cleaned = ""
    for char in text:
        if char in noise_map:
            cleaned += noise_map[char]
        else:
            cleaned += char
    
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned

def extract_entities_from_text(text, source_doc):
    entities = {}
    
    # Extract Phone Numbers
    phones = re.findall(r'\b\d{10}\b', text)
    for p in phones:
        idx = text.find(p)
        excerpt = text[max(0, idx-50):min(len(text), idx+100)].strip()
        entities[f"phone_{p}"] = {"id": f"phone_{p}", "type": "Phone", "name": p, "status": "VERIFIED", "evidence": f"...{excerpt}...", "source": source_doc}
        
    # Extract Vehicles
    vehicles = re.findall(r'\b[A-Z]{2}-\d{2}\s[A-Z]{1,2}\s\d{4}\b', text)
    for v in vehicles:
        idx = text.find(v)
        excerpt = text[max(0, idx-50):min(len(text), idx+100)].strip()
        entities[f"vehicle_{v.replace(' ','_')}"] = {"id": f"vehicle_{v.replace(' ','_')}", "type": "Vehicle", "name": v, "status": "VERIFIED", "evidence": f"...{excerpt}...", "source": source_doc}
        
    # Extract Account Numbers
    accounts = re.findall(r'\b(?:Account|account ending)\s+([A-Za-z0-9]{4,12})\b', text)
    for a in accounts:
        idx = text.find(a)
        excerpt = text[max(0, idx-50):min(len(text), idx+100)].strip()
        entities[f"ac_{a}"] = {"id": f"ac_{a}", "type": "Account", "name": f"A/C **{a[-4:]}", "status": "VERIFIED", "evidence": f"...{excerpt}...", "source": source_doc}
        
    # Dynamic Entity Extraction using spaCy (NER)
    nlp = get_nlp()
    doc = nlp(text)
    
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "LOC"]:
            label = ent.label_
            text_val = ent.text.strip()
            
            # Avoid extracting single character noise
            if len(text_val) <= 1:
                continue
                
            ent_type = "Location" if label in ["GPE", "LOC"] else ("Person" if label == "PERSON" else "Organization")
            prefix = "loc" if ent_type == "Location" else ("person" if ent_type == "Person" else "org")
            
            idx = ent.start_char
            excerpt = text[max(0, idx-50):min(len(text), idx+100)].strip()
            
            # Create a clean ID from the text
            safe_id = re.sub(r'[^a-zA-Z0-9]', '_', text_val)
            ent_id = f"{prefix}_{safe_id}"
            
            if ent_id not in entities:
                entities[ent_id] = {
                    "id": ent_id,
                    "type": ent_type,
                    "name": text_val,
                    "status": "VERIFIED",
                    "evidence": f"...{excerpt}...",
                    "source": source_doc
                }
            
    return entities

def infer_relationships(document_entities, text=None):
    """Link entities intelligently using NLP dependency parsing to find real connections"""
    links = []
    if not text:
        return links
        
    nlp = get_nlp()
    
    # Safely parse text, truncating if it exceeds spaCy's default limit for performance
    if len(text) > 900000:
        text = text[:900000]
    
    doc = nlp(text)
    entities_list = list(document_entities.values())
    
    # Map entities to the sentences they appear in
    entity_sentences = {}
    for sent in doc.sents:
        sent_text = sent.text.lower()
        for ent in entities_list:
            ent_name = ent['name'].lower()
            # Require minimum length to avoid matching generic single characters
            if len(ent_name) > 2 and ent_name in sent_text:
                if ent['id'] not in entity_sentences:
                    entity_sentences[ent['id']] = []
                entity_sentences[ent['id']].append(sent)

    seen_links = set()
    
    for i in range(len(entities_list)):
        for j in range(i+1, len(entities_list)):
            u = entities_list[i]
            v = entities_list[j]
            
            u_sents = entity_sentences.get(u['id'], [])
            v_sents = entity_sentences.get(v['id'], [])
            
            # Find sentences where both entities co-occur
            shared_sents = [s for s in u_sents if s in v_sents]
            
            if shared_sents:
                rel_type = "ASSOCIATED_WITH"
                sent = shared_sents[0]
                
                # Attempt to extract dynamic verb from the syntactic dependency tree
                u_tokens = [t for t in sent if t.text.lower() in u['name'].lower() and len(t.text) > 2]
                v_tokens = [t for t in sent if t.text.lower() in v['name'].lower() and len(t.text) > 2]
                
                if u_tokens and v_tokens:
                    u_tok = u_tokens[0]
                    v_tok = v_tokens[0]
                    
                    lca_set = set(u_tok.ancestors)
                    common_verb = None
                    for anc in v_tok.ancestors:
                        if anc in lca_set and anc.pos_ == "VERB":
                            common_verb = anc.lemma_.upper()
                            break
                    
                    if common_verb:
                        rel_type = common_verb
                    else:
                        # Fallback for semantic sense if no clear verb links them in the tree
                        types = {u['type'], v['type']}
                        if types == {"Person", "Phone"}: rel_type = "USES"
                        elif types == {"Person", "Vehicle"}: rel_type = "DRIVES"
                        elif types == {"Person", "Location"}: rel_type = "LOCATED_AT"
                        elif types == {"Organization", "Account"}: rel_type = "OWNS"
                
                link_hash = f"{u['id']}-{v['id']}-{rel_type}"
                if link_hash not in seen_links:
                    seen_links.add(link_hash)
                    links.append({
                        "source": u['id'],
                        "target": v['id'],
                        "type": rel_type
                    })
            
    return links

def process_pdf_files(upload_files):
    global_nodes = {}
    global_links = []
    
    for file in upload_files:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file.file.read()))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            cleaned_text = clean_ocr_noise(text)
            doc_entities = extract_entities_from_text(cleaned_text, file.filename)
            
            # Merge entities
            for k, v in doc_entities.items():
                if k not in global_nodes:
                    global_nodes[k] = v
                
            # Infer links for this document
            doc_links = infer_relationships(doc_entities, cleaned_text)
            global_links.extend(doc_links)
            
        except Exception as e:
            print(f"Error processing {file.filename}: {e}")
            
    # Deduplicate Links
    unique_links = []
    seen_links = set()
    for l in global_links:
        # Sort to treat A->B and B->A as the same if we want undirected, but here we keep directed.
        link_hash = f"{l['source']}-{l['target']}-{l['type']}"
        if link_hash not in seen_links:
            seen_links.add(link_hash)
            unique_links.append(l)

    nodes = list(global_nodes.values())
    
    # Flagging logic: if a node has >= 3 connections, flag it
    degrees = {n['id']: 0 for n in nodes}
    for l in unique_links:
        if l['source'] in degrees: degrees[l['source']] += 1
        if l['target'] in degrees: degrees[l['target']] += 1
        
    for n in nodes:
        if degrees[n['id']] >= 3:
            n['status'] = 'REVIEW_REQUIRED'
            n['risk_color'] = 'orange'
        if degrees[n['id']] >= 5:
            n['risk_color'] = 'red'
            n['historical_firs'] = 1

    return {
        "nodes": nodes,
        "links": unique_links
    }
