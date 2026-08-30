import os
import json
import csv
import random
from datetime import datetime, timedelta

def generate_data():
    base_dir = r"c:\Users\sahid\Desktop\SIH\data"
    os.makedirs(os.path.join(base_dir, "fir"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "cdr"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "financial"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "surveillance"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "intelligence"), exist_ok=True)
    
    locations = [f"Location_{i}" for i in range(1, 16)]
    organizations = [f"Org_{i}" for i in range(1, 9)]
    cases = [f"CASE-{str(i).zfill(3)}" for i in range(1, 6)]
    towers = [f"TOWER-{i}" for i in range(1, 6)]
    
    first_names = ["Ravi", "Amit", "Suresh", "Vikram", "Priya", "Neha", "Kiran", "Raj", "Manoj", "Anil", "Sunil", "Pooja", "Arun", "Sanjay", "Rahul"]
    last_names = ["Kumar", "Singh", "Sharma", "Verma", "Patil", "Deshmukh", "Joshi", "Gupta", "Rao", "Reddy", "Mehta", "Das"]
    
    people = []
    for i in range(1, 41):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        canonical = f"{fn} {ln}"
        
        variants = [
            canonical,
            f"{fn[0]}. {ln}",
            f"{fn} {ln[0]}.",
            canonical.upper()
        ]
        
        people.append({
            "person_id": f"P{str(i).zfill(3)}",
            "canonical_name": canonical,
            "name_variants": variants,
            "phone": f"9{random.randint(100000000, 999999999)}",
            "bank_account": f"ACC{random.randint(10000, 99999)}",
            "vehicle": f"MH12{random.choice(['AB','XY','PQ'])}{random.randint(1000,9999)}" if random.random() > 0.5 else None,
            "home_location": random.choice(locations),
            "organization": random.choice(organizations) if random.random() > 0.5 else None
        })

    ring1 = random.sample(people, 5)
    remaining = [p for p in people if p not in ring1]
    ring2 = random.sample(remaining, 5)
    
    # Bridge person
    bridge = ring1[0]
    if bridge not in ring2:
        ring2[0] = bridge

    # Ground truth
    answer_key = {
        "master_entities": people,
        "rings": [
            [p["person_id"] for p in ring1],
            [p["person_id"] for p in ring2]
        ],
        "bridge_person": bridge["person_id"]
    }
    
    with open(r"c:\Users\sahid\Desktop\SIH\answer_key.json", "w") as f:
        json.dump(answer_key, f, indent=2)

    # Generate FIRs
    for i in range(25):
        case = random.choice(cases)
        date = (datetime.now() - timedelta(days=random.randint(0, 100))).strftime("%Y-%m-%d")
        fir_people = random.sample(people, random.randint(2, 4))
        
        text = f"Case ID: {case}\nDate Filed: {date}\nSource Type: FIR\n\n"
        text += "Investigation report:\n"
        for p in fir_people:
            name_var = random.choice(p["name_variants"])
            text += f"Subject {name_var} was identified during the initial check. "
            if p["vehicle"]:
                text += f"A vehicle bearing plate {p['vehicle']} was noted near {random.choice(locations)}. "
            else:
                text += f"The individual was seen near {random.choice(locations)}. "
        text += f"Contact number {fir_people[0]['phone']} was recovered from the scene.\n"
        
        with open(os.path.join(base_dir, "fir", f"fir_{i+1}.txt"), "w") as f:
            f.write(text)

    # Generate CDR
    start_date = datetime.now() - timedelta(days=90)
    cdr_rows = []
    
    ring_members = set([p["person_id"] for p in ring1 + ring2])
    
    for _ in range(800):
        is_ring = random.random() < 0.35
        
        if is_ring:
            caller = random.choice(ring1 + ring2)
            # Find someone in the same ring
            r_pool = ring1 if caller in ring1 else ring2
            if caller in ring1 and caller in ring2:
                r_pool = ring1 + ring2
            
            receiver = random.choice([p for p in r_pool if p != caller])
            timestamp = (start_date + timedelta(days=random.randint(40, 50))).isoformat()
        else:
            caller, receiver = random.sample(people, 2)
            timestamp = (start_date + timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))).isoformat()
            
        cdr_rows.append({
            "caller": caller["phone"],
            "receiver": receiver["phone"],
            "timestamp": timestamp,
            "duration_sec": random.randint(10, 1800),
            "cell_tower": random.choice(towers)
        })
        
    with open(os.path.join(base_dir, "cdr", "calls.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["caller", "receiver", "timestamp", "duration_sec", "cell_tower"])
        writer.writeheader()
        writer.writerows(cdr_rows)

    # Generate Financial
    fin_rows = []
    for _ in range(300):
        is_ring = random.random() < 0.35
        
        if is_ring:
            sender = random.choice(ring1 + ring2)
            r_pool = ring1 if sender in ring1 else ring2
            receiver = random.choice([p for p in r_pool if p != sender])
            amt = random.randint(50000, 500000)
            timestamp = (start_date + timedelta(days=random.randint(40, 50))).isoformat()
        else:
            sender, receiver = random.sample(people, 2)
            amt = random.randint(500, 20000)
            timestamp = (start_date + timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))).isoformat()
            
        fin_rows.append({
            "sender": sender["bank_account"],
            "receiver": receiver["bank_account"],
            "amount": amt,
            "timestamp": timestamp,
            "account": sender["bank_account"]
        })
        
    # Noise transfer
    n1, n2 = random.sample(people, 2)
    fin_rows.append({
        "sender": n1["bank_account"],
        "receiver": n2["bank_account"],
        "amount": 9999999,
        "timestamp": start_date.isoformat(),
        "account": n1["bank_account"]
    })
    
    with open(os.path.join(base_dir, "financial", "transactions.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sender", "receiver", "amount", "timestamp", "account"])
        writer.writeheader()
        writer.writerows(fin_rows)

    # Generate Surveillance
    for i in range(10):
        p1 = random.choice(people)
        p2 = random.choice(people)
        text = f"Subject observed at {random.choice(locations)}, in contact with {random.choice(p2['name_variants'])}. Subject name variant: {random.choice(p1['name_variants'])}."
        with open(os.path.join(base_dir, "surveillance", f"report_{i+1}.txt"), "w") as f:
            f.write(text)

    # Generate Intelligence
    for i in range(10):
        p = random.choice(people)
        org = p["organization"] or "unknown organization"
        text = f"Informant suggests {random.choice(p['name_variants'])} might be affiliated with {org}. Last seen near {random.choice(locations)}."
        with open(os.path.join(base_dir, "intelligence", f"note_{i+1}.txt"), "w") as f:
            f.write(text)

if __name__ == "__main__":
    generate_data()
    print("Dataset generated successfully.")
