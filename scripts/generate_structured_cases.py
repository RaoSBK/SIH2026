import os
import random
import csv
import json

def generate_cases(num_cases=5, output_dir="data/cases"):
    os.makedirs(output_dir, exist_ok=True)
    
    first_names = ["Arjun", "Vikram", "Rahul", "Amit", "Suresh", "Ramesh", "Karan", "Ravi", "Sanjay", "Anil"]
    last_names = ["Sharma", "Singh", "Verma", "Patel", "Kumar", "Gupta", "Das", "Jain", "Mehta", "Bose"]
    locations = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat"]
    orgs = ["Global Tech", "Apex Holdings", "Crescent Traders", "Blue Ocean", "Pinnacle Group"]
    
    for i in range(1, num_cases + 1):
        case_id = f"CASE-{100 + i}"
        case_dir = os.path.join(output_dir, f"case_{i:02d}")
        os.makedirs(case_dir, exist_ok=True)
        
        # Pick unique entities for this case to make it completely different
        suspect = f"{random.choice(first_names)} {random.choice(last_names)}"
        associate = f"{random.choice(first_names)} {random.choice(last_names)}"
        while associate == suspect:
            associate = f"{random.choice(first_names)} {random.choice(last_names)}"
            
        suspect_phone = f"+91{random.randint(6000000000, 9999999999)}"
        associate_phone = f"+91{random.randint(6000000000, 9999999999)}"
        
        suspect_acc = f"ACC-{suspect.split()[0].upper()[:3]}-{random.randint(1000, 9999)}"
        associate_acc = f"ACC-{associate.split()[0].upper()[:3]}-{random.randint(1000, 9999)}"
        
        location = random.choice(locations)
        org = random.choice(orgs)
        
        # 1. Generate Unstructured Text (FIR)
        fir_content = f"""FIRST INFORMATION REPORT - {case_id}
Date: 2024-03-{random.randint(10, 25):02d}
Location: {location}
Subject: Suspicious Activity

Details:
A suspicious transaction was observed involving {suspect}.
The contact number provided is {suspect_phone}.
The suspect is associated with an organization named {org}.
Another associate, {associate}, is linked to the operations.
The contact number for the associate is {associate_phone}.
They were seen transferring funds through {suspect_acc} and {associate_acc}.
"""
        with open(os.path.join(case_dir, "FIR.txt"), "w", encoding="utf-8") as f:
            f.write(fir_content)
            
        # 2. Generate Structured Data (CDR.csv)
        # Needs columns: caller_number, callee_number, call_timestamp, duration, location
        cdr_data = [
            ["caller_number", "callee_number", "call_timestamp", "duration", "location"],
            [suspect_phone, associate_phone, f"2024-03-14 10:{random.randint(10,59)}:00", random.randint(30, 300), location],
            [associate_phone, suspect_phone, f"2024-03-15 14:{random.randint(10,59)}:00", random.randint(60, 600), location],
            [suspect_phone, f"+91{random.randint(6000000000, 9999999999)}", f"2024-03-16 09:{random.randint(10,59)}:00", random.randint(10, 120), location]
        ]
        with open(os.path.join(case_dir, "CDR.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(cdr_data)
            
        # 3. Generate Structured Data (Financial.csv)
        # Needs columns: sender_account, receiver_account, amount, call_timestamp, person_mentioned
        fin_data = [
            ["sender_account", "receiver_account", "amount", "call_timestamp", "person_mentioned"],
            [suspect_acc, associate_acc, random.randint(50000, 500000), "2024-03-14 11:00:00", associate],
            [associate_acc, suspect_acc, random.randint(10000, 100000), "2024-03-15 15:00:00", suspect],
            [suspect_acc, f"ACC-UNK-{random.randint(1000, 9999)}", random.randint(200000, 900000), "2024-03-16 10:00:00", "Unknown Entity"]
        ]
        with open(os.path.join(case_dir, "Financial.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(fin_data)
            
        # 4. Generate metadata.json to identify it as a specific case for ingestion
        metadata = {
            "case_id": case_id,
            "description": f"Generated case data for {suspect} and {associate}."
        }
        with open(os.path.join(case_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
            
    print(f"Successfully generated {num_cases} cases in {output_dir}")

if __name__ == "__main__":
    generate_cases(10)
