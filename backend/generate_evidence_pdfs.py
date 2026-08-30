import os
import sys
import random
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

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

def main():
    if len(sys.argv) < 2:
        output_dir = "data/synthetic_pdfs"
    else:
        output_dir = sys.argv[1]

    os.makedirs(output_dir, exist_ok=True)
    print(f"Generating noisy PDFs in {output_dir}...")

    # FIR 1
    create_pdf(
        os.path.join(output_dir, "FIR_001_Ravi_Kumar.pdf"),
        "FIRST INFORMATION REPORT (FIR) - 001",
        [
            "Date: 2024-03-15",
            "Location: Station Road, Mumbai",
            "Subject: Suspicious Activity and Money Laundering",
            "",
            "Details:",
            "A suspicious transaction was observed involving Ravi Kumar.",
            "His phone number is +91-9876543210. He is associated with",
            "an organization named 'Global Tech Solutions'.",
            "The suspect was seen meeting with another individual named Amit Singh.",
            "Amit Singh operates near Delhi. Phone: +91-8765432109.",
        ]
    )

    # FIR 2
    create_pdf(
        os.path.join(output_dir, "FIR_002_R_Kumar.pdf"),
        "FIRST INFORMATION REPORT (FIR) - 002",
        [
            "Date: 2024-03-20",
            "Location: Andheri West, Mumbai",
            "Subject: Fraudulent Company Registration",
            "",
            "Details:",
            "An investigation into 'Glob Tech Solutions' revealed that",
            "R. Kumar is the primary shareholder.",
            "Contact number provided is 9876543210.",
            "Vehicle seen near premises: MH-12 AB 1234.",
            "It is suspected to be a shell company for routing illegal funds.",
            "Another associate, A. Singh, is linked to the operations.",
        ]
    )

    # CDR 1
    create_pdf(
        os.path.join(output_dir, "CDR_Analysis_March2024.pdf"),
        "CALL DATA RECORD (CDR) ANALYSIS",
        [
            "Date Range: 01-Mar-2024 to 31-Mar-2024",
            "",
            "Caller: 9876543210 (Ravi K.)",
            "Receiver: 8765432109 (Amit S.)",
            "Duration: 450 seconds",
            "Timestamp: 2024-03-14 14:30:00",
            "",
            "Caller: 9876543210 (Ravi K.)",
            "Receiver: 7654321098 (Unknown)",
            "Duration: 120 seconds",
            "Timestamp: 2024-03-15 09:15:00",
            "",
            "Notes: High frequency of calls observed prior to the FIR 001 incident.",
        ]
    )

    # Bank Statement 1
    create_pdf(
        os.path.join(output_dir, "BankStatement_GlobalTech.pdf"),
        "BANK STATEMENT - GLOBAL TECH SOLUTIONS",
        [
            "Account Name: Global Tech Solutions",
            "Account Number: 112233445566",
            "Bank: National Bank of India",
            "",
            "Date       | Description                | Amount (INR) | Balance (INR)",
            "----------------------------------------------------------------------",
            "2024-03-10 | Transfer to A. Singh       | -5,00,000    | 15,00,000",
            "2024-03-12 | Deposit from Shell Corp A  | +20,00,000   | 35,00,000",
            "2024-03-14 | Transfer to Ravi Kumar     | -10,00,000   | 25,00,000",
            "",
            "Flagged by automated system due to rapid large transfers.",
        ]
    )
    
    # Intelligence Report
    create_pdf(
        os.path.join(output_dir, "Intel_Report_Amit.pdf"),
        "INTELLIGENCE REPORT - SUSPECT PROFILING",
        [
            "Subject: Amit Singh",
            "Known Aliases: Amit S., A. Singh",
            "Contact: +918765432109",
            "Associated Entities: Ravi Kumar (Mumbai associate)",
            "",
            "Summary:",
            "Subject is involved in cross-border financial irregularities.",
            "Frequently uses 'Glob Tech Solutions' accounts to wash funds.",
        ]
    )

    print(f"Successfully generated 5 noisy PDFs in {output_dir}")

if __name__ == "__main__":
    main()
