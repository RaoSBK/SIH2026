const fs = require('fs');
const path = require('path');

// Dummy database mapping for the mock criminal history lookup
const CRIMINAL_DB = {
    "priya joshi": {firs: 1, risk: "yellow"},
    "s. rao": {firs: 4, risk: "orange"},
    "a. reddy": {firs: 2, risk: "yellow"},
    "vikram g.": {firs: 8, risk: "red"}
};

function normalize(text) {
    if (!text) return "";
    return text.toLowerCase().replace(/[^\w\s]/g, '').trim();
}

function calculateScore(a, b) {
    if (a.phone && b.phone && a.phone === b.phone) return 0.95;
    
    let n1 = normalize(a.name);
    let n2 = normalize(b.name);
    if (n1 === n2 && n1 !== "") return 0.88;
    
    // Very basic fuzzy logic for JS implementation
    if (n1 && n2 && (n1.includes(n2) || n2.includes(n1))) return 0.7; // Triggers dotted line
    
    return 0.0;
}

function extractEntities(filePath, docId) {
    const text = fs.readFileSync(filePath, 'utf-8');
    const entities = [];
    
    const subjectRegex = /Subject\s+(.+?)\s+was/g;
    const phoneRegex = /Contact number\s+(\d+)\s+was/g;
    
    let subjects = [];
    let match;
    while ((match = subjectRegex.exec(text)) !== null) {
        subjects.push(match[1].trim());
    }
    
    let phones = [];
    while ((match = phoneRegex.exec(text)) !== null) {
        phones.push(match[1]);
    }
    
    subjects.forEach((name, i) => {
        const phone = phones.length > 0 ? phones[0] : "";
        entities.push({
            id: `${docId}_E${i+1}`,
            name: name,
            phone: phone,
            doc_id: docId
        });
    });
    
    return entities;
}

function processData() {
    const dataDir = path.join(__dirname, '..', 'data');
    const firDir = path.join(dataDir, 'fir');
    const files = fs.readdirSync(firDir);
    
    let entities = [];
    files.forEach(f => {
        if (f.endsWith('.txt')) {
            const docId = f.replace('.txt', '');
            entities = entities.concat(extractEntities(path.join(firDir, f), docId));
        }
    });
    
    const scores = {};
    for (let i=0; i<entities.length; i++) {
        for (let j=i+1; j<entities.length; j++) {
            let score = calculateScore(entities[i], entities[j]);
            if (score > 0.0) {
                scores[`${entities[i].id}|${entities[j].id}`] = score;
            }
        }
    }
    
    let parent = {};
    entities.forEach(e => parent[e.id] = e.id);
    
    function find(i) {
        if (parent[i] === i) return i;
        return parent[i] = find(parent[i]);
    }
    function union(i, j) {
        let rootI = find(i);
        let rootJ = find(j);
        if (rootI !== rootJ) parent[rootI] = rootJ;
    }
    
    const links = [];
    for (const [key, conf] of Object.entries(scores)) {
        if (conf >= 0.5) {
            let [a, b] = key.split('|');
            union(a, b);
            links.push({
                source: a,
                target: b,
                confidence: conf,
                line_type: conf >= 0.85 ? "solid" : "dotted"
            });
        }
    }
    
    const clustersMap = {};
    entities.forEach(e => {
        let cId = find(e.id);
        if (!clustersMap[cId]) clustersMap[cId] = [];
        clustersMap[cId].push(e.id);
    });
    
    const nodes = [];
    entities.forEach(e => {
        let nLower = e.name.toLowerCase();
        let history = CRIMINAL_DB[nLower] || {firs: 0, risk: "none"};
        
        let cId = find(e.id);
        let clusterMembers = clustersMap[cId];
        
        let needsReview = false;
        for (let link of links) {
            if ((clusterMembers.includes(link.source) || clusterMembers.includes(link.target)) && link.line_type === 'dotted') {
                needsReview = true;
                break;
            }
        }
        
        nodes.push({
            id: e.id,
            name: e.name,
            cluster_id: cId,
            status: needsReview ? "REVIEW_REQUIRED" : "HIGH_CONFIDENCE",
            historical_firs: history.firs,
            risk_color: history.risk
        });
    });
    
    const result = {
        nodes: nodes,
        links: links,
        clusters: Object.keys(clustersMap).map(k => ({
            cluster_id: k,
            members: clustersMap[k],
            status: "HIGH_CONFIDENCE"
        }))
    };
    
    fs.writeFileSync(path.join(dataDir, 'resolved_graph.json'), JSON.stringify(result, null, 2));
    console.log(`Generated resolved_graph.json with ${nodes.length} nodes and ${links.length} links.`);
}

processData();
