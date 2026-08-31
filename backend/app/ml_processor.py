import re
import io
import PyPDF2
from rapidfuzz import process, fuzz
import json
import hashlib

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
        
    # Heuristic Name Extraction (Checking against our suspected pool for fuzzy match to simulate NER)
    NAMES = ["Ravi Kumar", "Amit Singh", "Faisal Khan", "Ahmed Sheikh", "John Doe", "Jane Smith", "Priya Sharma"]
    for name in NAMES:
        match = process.extractOne(name, [text], scorer=fuzz.partial_ratio)
        if match and match[1] > 90:
            idx = text.lower().find(name.lower()[:5]) # Approximation
            excerpt = text[max(0, idx-50):min(len(text), idx+100)].strip()
            entities[f"person_{name.replace(' ','_')}"] = {"id": f"person_{name.replace(' ','_')}", "type": "Person", "name": name, "status": "VERIFIED", "evidence": f"...{excerpt}...", "source": source_doc}
            
    # Organizations
    ORGS = ["Global Tech Solutions", "Crescent Traders", "Apex Holdings", "Blue Ocean Corp"]
    for org in ORGS:
        match = process.extractOne(org, [text], scorer=fuzz.partial_ratio)
        if match and match[1] > 90:
            idx = text.lower().find(org.lower()[:5])
            excerpt = text[max(0, idx-50):min(len(text), idx+100)].strip()
            entities[f"org_{org.replace(' ','_')}"] = {"id": f"org_{org.replace(' ','_')}", "type": "Organization", "name": org, "status": "VERIFIED", "evidence": f"...{excerpt}...", "source": source_doc}
            
    # Locations
    LOCS = ["Station Road, Mumbai", "Andheri West", "Hyderabad Rly Station", "New Delhi", "Sector 14, Gurgaon"]
    for loc in LOCS:
        match = process.extractOne(loc, [text], scorer=fuzz.partial_ratio)
        if match and match[1] > 90:
            idx = text.lower().find(loc.lower()[:5])
            excerpt = text[max(0, idx-50):min(len(text), idx+100)].strip()
            entities[f"loc_{loc.replace(' ','_')}"] = {"id": f"loc_{loc.replace(' ','_')}", "type": "Location", "name": loc, "status": "VERIFIED", "evidence": f"...{excerpt}...", "source": source_doc}
            
    return entities

def infer_relationships(document_entities):
    """Link entities that appear in the same document"""
    links = []
    entities_list = list(document_entities.values())
    
    for i in range(len(entities_list)):
        for j in range(i+1, len(entities_list)):
            u = entities_list[i]
            v = entities_list[j]
            
            # Simple heuristic linkage based on types
            rel_type = "LINKED_TO"
            
            types = {u['type'], v['type']}
            if types == {"Person", "Phone"}: rel_type = "USES"
            elif types == {"Person", "Vehicle"}: rel_type = "DRIVES"
            elif types == {"Person", "Location"}: rel_type = "VISITED"
            elif types == {"Person", "Organization"}: rel_type = "ASSOCIATED_WITH"
            elif types == {"Phone", "Phone"}: rel_type = "CALLED"
            elif types == {"Account", "Account"}: rel_type = "TRANSFERRED"
            elif types == {"Organization", "Account"}: rel_type = "OWNS"
            
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
            doc_links = infer_relationships(doc_entities)
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
