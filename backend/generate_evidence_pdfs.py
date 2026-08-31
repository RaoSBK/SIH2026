import os
import sys
import random
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import uuid

# Pools of entities for dynamic generation
NAMES = ["Ravi Kumar", "Amit Singh", "Faisal Khan", "Ahmed Sheikh", "John Doe", "Jane Smith", "Priya Sharma"]
ORGANIZATIONS = ["Global Tech Solutions", "Crescent Traders", "Apex Holdings", "Blue Ocean Corp"]
LOCATIONS = ["Station Road, Mumbai", "Andheri West", "Hyderabad Rly Station", "New Delhi", "Sector 14, Gurgaon"]
VEHICLES = ["MH-12 AB 1234", "TS-09 CD 5678", "DL-4C 9876", "KA-01 XY 1122"]
PHONES = ["9876543210", "8765432109", "7654321098", "9998887776", "8887776665"]
ACCOUNTS = ["11223344", "55667788", "99001122", "33445566"]

def add_noise(text, noise_level=0.03):
    """Injects OCR-like noise into the text (e.g. O->0, l->1, i->1)"""
    noise_chars = {'O': '0', '0': 'O', 'I': '1', '1': 'I', 'l': '1', 'a': '@', 's': '5', 'S': '5', 'B': '8'}
    result = ""
    for char in text:
        if random.random() < noise_level and char in noise_chars:
            result += noise_chars[char]
        elif random.random() < noise_level * 0.5 and char.isalpha():
            result += random.choice(['#', '@', '?', '!', '%', '1', '0'])
        else:
            result += char
    return result

def create_pdf(filepath, title, content_lines):
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, title)
    
    # Body with noise
    c.setFont("Helvetica", 11)
    y_position = height - 80
    for line in content_lines:
        noisy_line = add_noise(line)
        c.drawString(50, y_position, noisy_line)
        y_position -= 20
        if y_position < 50:
            c.showPage()
            c.setFont("Helvetica", 11)
            y_position = height - 50

    c.save()

def generate_random_fir(output_dir, num):
    suspect = random.choice(NAMES)
    associate = random.choice(NAMES)
    while associate == suspect: associate = random.choice(NAMES)
    
    phone1 = random.choice(PHONES)
    phone2 = random.choice(PHONES)
    while phone2 == phone1: phone2 = random.choice(PHONES)
    
    org = random.choice(ORGANIZATIONS)
    loc = random.choice(LOCATIONS)
    vehicle = random.choice(VEHICLES)
    
    content = [
        f"Date: 2024-03-{random.randint(10, 25)}",
        f"Location: {loc}",
        "Subject: Suspicious Activity Report",
        "",
        "Details:",
        f"A suspicious transaction was observed involving {suspect}.",
        f"Contact number provided is {phone1}.",
        f"The suspect is associated with an organization named '{org}'.",
        f"Vehicle seen near premises: {vehicle}.",
        f"Another associate, {associate}, is linked to the operations.",
        f"Contact number for associate is {phone2}.",
        "It is suspected to be a shell company for routing illegal funds."
    ]
    
    filename = f"FIR_{num:03d}_{suspect.replace(' ', '_')}.pdf"
    create_pdf(os.path.join(output_dir, filename), f"FIRST INFORMATION REPORT (FIR) - {num:03d}", content)

def generate_random_cdr(output_dir, num):
    caller = random.choice(NAMES)
    receiver = random.choice(NAMES)
    phone1 = random.choice(PHONES)
    phone2 = random.choice(PHONES)
    
    content = [
        "Date Range: 01-Mar-2024 to 31-Mar-2024",
        "",
        f"Caller: {phone1} ({caller})",
        f"Receiver: {phone2} ({receiver})",
        f"Duration: {random.randint(30, 900)} seconds",
        f"Timestamp: 2024-03-14 14:30:00",
        "",
        "Notes: High frequency of calls observed.",
    ]
    filename = f"CDR_Analysis_{num:03d}.pdf"
    create_pdf(os.path.join(output_dir, filename), "CALL DATA RECORD (CDR) ANALYSIS", content)

def generate_random_transaction(output_dir, num):
    org = random.choice(ORGANIZATIONS)
    acct1 = random.choice(ACCOUNTS)
    acct2 = random.choice(ACCOUNTS)
    amount = random.choice(["2,40,000", "5,00,000", "15,50,000", "8,20,000"])
    
    content = [
        f"Account Name: {org}",
        f"Account Number: {acct1}",
        "Bank: National Bank of India",
        "",
        "Summary of flagged activity:",
        f"Transfer of ₹{amount} from account ending {acct1} to account ending {acct2}.",
        "Flagged by automated system due to rapid large transfers.",
    ]
    filename = f"BankStatement_{org.replace(' ', '_')}_{num}.pdf"
    create_pdf(os.path.join(output_dir, filename), f"BANK STATEMENT - {org.upper()}", content)

def main():
    if len(sys.argv) < 2:
        output_dir = "data/synthetic_pdfs"
    else:
        output_dir = sys.argv[1]

    os.makedirs(output_dir, exist_ok=True)
    print(f"Generating noisy random PDFs in {output_dir}...")
    
    # Generate random docs
    for i in range(2):
        generate_random_fir(output_dir, i+1)
        
    generate_random_cdr(output_dir, 1)
    
    for i in range(2):
        generate_random_transaction(output_dir, i+1)

    print(f"Successfully generated 5 random noisy PDFs in {output_dir}")

if __name__ == "__main__":
    main()
