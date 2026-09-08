const fs = require('fs');
const path = require('path');

function generateCases(numCases = 10, outputDir = 'data/cases') {
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const firstNames = ["Arjun", "Vikram", "Rahul", "Amit", "Suresh", "Ramesh", "Karan", "Ravi", "Sanjay", "Anil"];
    const lastNames = ["Sharma", "Singh", "Verma", "Patel", "Kumar", "Gupta", "Das", "Jain", "Mehta", "Bose"];
    const locations = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat"];
    const orgs = ["Global Tech", "Apex Holdings", "Crescent Traders", "Blue Ocean", "Pinnacle Group"];

    for (let i = 1; i <= numCases; i++) {
        const caseId = `CASE-${100 + i}`;
        const caseDir = path.join(outputDir, `case_${i.toString().padStart(2, '0')}`);
        
        if (!fs.existsSync(caseDir)) {
            fs.mkdirSync(caseDir, { recursive: true });
        }

        const suspect = `${firstNames[Math.floor(Math.random() * firstNames.length)]} ${lastNames[Math.floor(Math.random() * lastNames.length)]}`;
        let associate = `${firstNames[Math.floor(Math.random() * firstNames.length)]} ${lastNames[Math.floor(Math.random() * lastNames.length)]}`;
        while (associate === suspect) {
            associate = `${firstNames[Math.floor(Math.random() * firstNames.length)]} ${lastNames[Math.floor(Math.random() * lastNames.length)]}`;
        }

        const suspectPhone = `+91${Math.floor(Math.random() * 4000000000 + 6000000000)}`;
        const associatePhone = `+91${Math.floor(Math.random() * 4000000000 + 6000000000)}`;

        const suspectAcc = `ACC-${suspect.split(' ')[0].toUpperCase().substring(0, 3)}-${Math.floor(Math.random() * 9000 + 1000)}`;
        const associateAcc = `ACC-${associate.split(' ')[0].toUpperCase().substring(0, 3)}-${Math.floor(Math.random() * 9000 + 1000)}`;

        const location = locations[Math.floor(Math.random() * locations.length)];
        const org = orgs[Math.floor(Math.random() * orgs.length)];

        // 1. FIR.txt
        const firContent = `FIRST INFORMATION REPORT - ${caseId}
Date: 2024-03-${Math.floor(Math.random() * 16 + 10).toString().padStart(2, '0')}
Location: ${location}
Subject: Suspicious Activity

Details:
A suspicious transaction was observed involving ${suspect}.
The contact number provided is ${suspectPhone}.
The suspect is associated with an organization named ${org}.
Another associate, ${associate}, is linked to the operations.
The contact number for the associate is ${associatePhone}.
They were seen transferring funds through ${suspectAcc} and ${associateAcc}.
`;
        fs.writeFileSync(path.join(caseDir, 'FIR.txt'), firContent, 'utf8');

        // 2. CDR.csv
        const cdrData = [
            ["caller_number", "callee_number", "call_timestamp", "duration", "location"],
            [suspectPhone, associatePhone, `2024-03-14 10:${Math.floor(Math.random() * 50 + 10)}:00`, Math.floor(Math.random() * 270 + 30), location],
            [associatePhone, suspectPhone, `2024-03-15 14:${Math.floor(Math.random() * 50 + 10)}:00`, Math.floor(Math.random() * 540 + 60), location],
            [suspectPhone, `+91${Math.floor(Math.random() * 4000000000 + 6000000000)}`, `2024-03-16 09:${Math.floor(Math.random() * 50 + 10)}:00`, Math.floor(Math.random() * 110 + 10), location]
        ];
        const cdrCsv = cdrData.map(row => row.join(',')).join('\n');
        fs.writeFileSync(path.join(caseDir, 'CDR.csv'), cdrCsv, 'utf8');

        // 3. Financial.csv
        const finData = [
            ["sender_account", "receiver_account", "amount", "call_timestamp", "person_mentioned"],
            [suspectAcc, associateAcc, Math.floor(Math.random() * 450000 + 50000), "2024-03-14 11:00:00", associate],
            [associateAcc, suspectAcc, Math.floor(Math.random() * 90000 + 10000), "2024-03-15 15:00:00", suspect],
            [suspectAcc, `ACC-UNK-${Math.floor(Math.random() * 9000 + 1000)}`, Math.floor(Math.random() * 700000 + 200000), "2024-03-16 10:00:00", "Unknown Entity"]
        ];
        const finCsv = finData.map(row => row.join(',')).join('\n');
        fs.writeFileSync(path.join(caseDir, 'Financial.csv'), finCsv, 'utf8');

        // 4. metadata.json
        const metadata = {
            case_id: caseId,
            description: `Generated case data for ${suspect} and ${associate}.`
        };
        fs.writeFileSync(path.join(caseDir, 'metadata.json'), JSON.stringify(metadata, null, 4), 'utf8');
    }

    console.log(`Successfully generated ${numCases} cases in ${outputDir}`);
}

generateCases(10);
