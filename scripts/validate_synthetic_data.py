import argparse
import csv
import json
import os
import sys

REQUIRED_CDR_COLS = ["caller", "receiver", "timestamp", "duration_sec", "cell_tower"]
REQUIRED_FIN_COLS = ["sender", "receiver", "amount", "timestamp", "account"]
REQUIRED_SUBFOLDERS = ["fir", "cdr", "financial", "surveillance", "intelligence"]


def fail(msg):
    print(f"  [FAIL] {msg}")
    return False


def ok(msg):
    print(f"  [ OK ] {msg}")
    return True


def check_structure(data_dir):
    print("\n1. Folder structure")
    all_ok = True
    for sub in REQUIRED_SUBFOLDERS:
        path = os.path.join(data_dir, sub)
        if os.path.isdir(path) and any(os.scandir(path)):
            ok(f"{sub}/ exists and is non-empty")
        else:
            all_ok = fail(f"{sub}/ missing or empty")
    return all_ok


def check_csv_schema(path, required_cols, label):
    if not os.path.exists(path):
        return fail(f"{label} file not found: {path}")
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        rows = list(reader)
    if header != required_cols:
        return fail(f"{label} columns are {header}, expected {required_cols}")
    if len(rows) < 10:
        return fail(f"{label} only has {len(rows)} rows — too few to be useful")
    ok(f"{label}: {len(rows)} rows, columns correct")
    return True, rows


def check_cdr_financial(data_dir, answer_key):
    print("\n2. CDR & financial schema + coverage")
    all_ok = True

    cdr_path = os.path.join(data_dir, "cdr", "calls.csv")
    result = check_csv_schema(cdr_path, REQUIRED_CDR_COLS, "CDR")
    cdr_rows = result[1] if isinstance(result, tuple) else []
    all_ok &= bool(result) if not isinstance(result, tuple) else True

    fin_path = os.path.join(data_dir, "financial", "transactions.csv")
    result2 = check_csv_schema(fin_path, REQUIRED_FIN_COLS, "Financial")
    fin_rows = result2[1] if isinstance(result2, tuple) else []
    all_ok &= bool(result2) if not isinstance(result2, tuple) else True

    if cdr_rows and fin_rows:
        phones_in_cdr = {r[0] for r in cdr_rows} | {r[1] for r in cdr_rows}
        accounts_in_fin = {r[0] for r in fin_rows} | {r[1] for r in fin_rows}
        missing_phone = [p["person_id"] for p in answer_key["people"] if p["phone"] not in phones_in_cdr]
        missing_acct = [p["person_id"] for p in answer_key["people"] if p["account"] not in accounts_in_fin]
        if missing_phone:
            fail(f"{len(missing_phone)} people never appear in any CDR row: {missing_phone[:5]}...")
        else:
            ok("every person's phone appears in at least one CDR row")
        if missing_acct:
            fail(f"{len(missing_acct)} people never appear in any financial row: {missing_acct[:5]}...")
        else:
            ok("every person's account appears in at least one financial row")

    return all_ok


def check_text_sources(data_dir, answer_key):
    print("\n3. Text sources (FIR / surveillance / intelligence) use name variants")
    all_variants = set()
    canonical_names = set()
    for p in answer_key["people"]:
        canonical_names.add(p["canonical_name"])
        all_variants.update(p["name_variants"])

    hits = 0
    files_checked = 0
    for sub in ["fir", "surveillance", "intelligence"]:
        folder = os.path.join(data_dir, sub)
        if not os.path.isdir(folder):
            continue
        for fname in os.listdir(folder):
            path = os.path.join(folder, fname)
            if not os.path.isfile(path):
                continue
            files_checked += 1
            with open(path, errors="ignore") as f:
                text = f.read()
            if any(v in text for v in all_variants):
                hits += 1

    if files_checked == 0:
        return fail("no text files found in fir/surveillance/intelligence")
    ratio = hits / files_checked
    if ratio < 0.8:
        return fail(f"only {hits}/{files_checked} text files reference a known name variant ({ratio:.0%})")
    ok(f"{hits}/{files_checked} text files reference a known name variant ({ratio:.0%})")
    return True


def check_hidden_rings(answer_key):
    print("\n4. Hidden ring structure")
    rings = answer_key.get("hidden_rings", {})
    bridge = answer_key.get("bridge_person")
    all_ok = True
    if len(rings) < 2:
        all_ok = fail(f"expected at least 2 hidden rings, found {len(rings)}")
    else:
        ok(f"{len(rings)} hidden rings found: " + ", ".join(f"{k} ({len(v)} people)" for k, v in rings.items()))
    small = [k for k, v in rings.items() if len(v) < 3]
    if small:
        all_ok = fail(f"rings too small to be meaningful: {small}")
    if not bridge:
        all_ok = fail("no bridge_person recorded")
    else:
        in_two = sum(1 for v in rings.values() if bridge in v)
        if in_two >= 2:
            ok(f"bridge person {bridge} correctly appears in {in_two} rings")
        else:
            all_ok = fail(f"bridge person {bridge} only appears in {in_two} ring(s)")
    return all_ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="./data")
    parser.add_argument("--answer-key", default="./answer_key.json")
    args = parser.parse_args()

    if not os.path.exists(args.answer_key):
        print(f"Answer key not found at {args.answer_key} — did you run generate_synthetic_data.py first?")
        sys.exit(1)
    with open(args.answer_key) as f:
        answer_key = json.load(f)

    results = []
    results.append(check_structure(args.data))
    results.append(check_cdr_financial(args.data, answer_key))
    results.append(check_text_sources(args.data, answer_key))
    results.append(check_hidden_rings(answer_key))

    print("\n" + "=" * 50)
    if all(results):
        print("ALL CHECKS PASSED — dataset is structurally sound.")
        print("Next: build ingestion + NER, then run entity resolution and check")
        print("if it actually merges the name variants back into single people.")
    else:
        print("SOME CHECKS FAILED — see [FAIL] lines above.")
    print("=" * 50)


if __name__ == "__main__":
    main()
