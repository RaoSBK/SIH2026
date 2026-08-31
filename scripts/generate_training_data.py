import os
import json
import random
import re

NAMES = ["Ravi Kumar", "Amit Singh", "Faisal Khan", "Ahmed Sheikh", "John Doe", "Jane Smith", "Priya Sharma", "Vikram Patel", "Neha Gupta", "Suresh Menon", "David Chen", "Maria Garcia"]
ORGANIZATIONS = ["Global Tech Solutions", "Crescent Traders", "Apex Holdings", "Blue Ocean Corp", "Synergy Logistics", "Quantum Financial", "Red Shield Security"]
LOCATIONS = ["Station Road, Mumbai", "Andheri West", "Hyderabad Rly Station", "New Delhi", "Sector 14, Gurgaon", "MG Road, Bangalore", "Connaught Place", "Cyber City"]
VEHICLES = ["MH-12 AB 1234", "TS-09 CD 5678", "DL-4C 9876", "KA-01 XY 1122", "UP-32 FZ 9999", "TN-07 BW 4455"]
PHONES = ["9876543210", "8765432109", "7654321098", "9998887776", "8887776665", "9123456789", "8123456789"]
ACCOUNTS = ["11223344", "55667788", "99001122", "33445566", "77889900", "44556677"]

TEMPLATES = [
    # Murder / Violent Crime
    "On {date}, a homicide occurred at {location}. The victim, {name1}, was found deceased. A witness reported seeing {name2} fleeing the scene in a {vehicle}. Phone records show the suspect contacted {phone1} shortly after the incident.",
    "Violent assault reported near {location}. {name1} was attacked by {name2}. Authorities are tracking the suspect's vehicle, license plate {vehicle}. If seen, contact {phone1}.",
    
    # Financial Fraud
    "Suspicious activity flagged for {organization}. An unexpected wire transfer of INR {amount} was sent to account {account1} by {name1}. The transaction was authorized using phone {phone1}. {name2} is the suspected beneficiary.",
    "Audit of {organization} reveals anomalies. {name1} approved transfers to {account1} totaling INR {amount}. The linked contact number is {phone1}. {name2} is under investigation.",
    
    # Robbery / Theft
    "Armed robbery at {organization} branch in {location}. The suspect, later identified as {name1}, escaped in a getaway car with plate {vehicle}. An accomplice, {name2}, was seen waiting. Tipsters can call {phone1}.",
    "Break-in reported at {location}. Stolen goods were loaded into {vehicle}. The primary suspect is {name1}, who is known to associate with {name2}. Suspect's last known number is {phone1}.",
    
    # Cybercrime
    "{organization} reported a severe data breach. The malicious IP traces back to {location}. Cyber forensics indicate {name1} orchestrated the attack. Ransom funds were demanded to account {account1}. Accomplice {name2} may be involved.",
]

def generate_example():
    template = random.choice(TEMPLATES)
    
    date = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    amount = f"{random.randint(10, 900)},000"
    
    # Pick unique names
    name1, name2 = random.sample(NAMES, 2)
    org = random.choice(ORGANIZATIONS)
    loc = random.choice(LOCATIONS)
    veh = random.choice(VEHICLES)
    phone1 = random.choice(PHONES)
    acct1 = random.choice(ACCOUNTS)
    
    replacements = {
        "{date}": date,
        "{amount}": amount,
        "{name1}": (name1, "Person"),
        "{name2}": (name2, "Person"),
        "{organization}": (org, "Organization"),
        "{location}": (loc, "Location"),
        "{vehicle}": (veh, "Vehicle"),
        "{phone1}": (phone1, "Phone"),
        "{account1}": (acct1, "Account")
    }
    
    # We must substitute the string and keep track of character offsets.
    text = template
    entities = []
    
    # To avoid offset shifting issues, we'll replace placeholders one by one
    # and find the newly inserted string's exact position.
    for placeholder, val in replacements.items():
        if isinstance(val, tuple):
            value_str, label = val
            while placeholder in text:
                start = text.find(placeholder)
                text = text.replace(placeholder, value_str, 1)
                end = start + len(value_str)
                entities.append((start, end, label))
        else:
            # Just a string replacement (e.g. date, amount) - no label
            text = text.replace(placeholder, val)
            
    # Sort entities by start position and ensure no overlaps (though our templates don't overlap)
    entities = sorted(entities, key=lambda x: x[0])
    
    return {
        "text": text,
        "entities": entities
    }

def main():
    output_dir = "data/synthetic/training"
    os.makedirs(output_dir, exist_ok=True)
    
    train_data = []
    for _ in range(2000):
        train_data.append(generate_example())
        
    dev_data = []
    for _ in range(500):
        dev_data.append(generate_example())
        
    with open(os.path.join(output_dir, "train.json"), "w") as f:
        json.dump(train_data, f, indent=2)
        
    with open(os.path.join(output_dir, "dev.json"), "w") as f:
        json.dump(dev_data, f, indent=2)
        
    print(f"Generated 2000 training and 500 evaluation examples in {output_dir}")

if __name__ == "__main__":
    main()
