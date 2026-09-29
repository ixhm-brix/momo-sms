import json
import os
import re
import xml.etree.ElementTree as ET


SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__))
XML_FILE = os.path.join(SCRIPT_FOLDER, "modified_sms_v2.xml")
JSON_FILE = os.path.join(SCRIPT_FOLDER, "transactions.json")

ACCOUNT_OWNER = "Account Owner"

CURRENCY = "RWF"

def find_text(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    if match is None:
        return None
    return match.group(1).strip()


def text_to_number(text):
    if text is None:
        return None
    return int(text.replace(",", ""))


def clean_name(name):
    if name is None:
        return None
    return " ".join(name.split())

def read_xml_file(file_path):
    if not os.path.exists(file_path):
        print(f"ERROR: Could not find the file: {file_path}")
        print("Make sure modified_sms_v2.xml is in the same folder as parser.py")
        raise SystemExit(1)

    tree = ET.parse(file_path)
    root = tree.getroot()          # the <smses> element
    return root.findall("sms")     # every <sms> inside it

def extract_basic_info(sms):
    return {
        "body": sms.get("body", ""),
        "date_ms": sms.get("date"),
        "readable_date": sms.get("readable_date"),
    }

def extract_amount(body):
    # Bundle messages in Kinyarwanda: "... igura 2,000 RWF ..." ("costs 2,000 RWF")
    amount = find_text(r"igura\s+([\d,]+)\s*RWF", body)
    if amount is not None:
        return text_to_number(amount)

    # Bank statement line: "... DEPOSIT RWF 25000 ..." (number after RWF)
    amount = find_text(r"DEPOSIT RWF\s+([\d,]+)", body)
    if amount is not None:
        return text_to_number(amount)

    # All other messages: the first "<number> RWF" is the amount
    amount = find_text(r"([\d,]+)\s*RWF", body)
    return text_to_number(amount)


def extract_transaction_details(body):
    # "Fee was 100 RWF" or "Fee paid: 350 RWF"
    fee = find_text(r"fee (?:was|paid):?\s*([\d,]+)\s*RWF", body)

    # "Your new balance: 2000 RWF" or "NEW BALANCE :40400 RWF"
    balance = find_text(r"new balance(?: is)?\s*:?\s*([\d,]+)\s*RWF", body)

    # "... at 2024-05-10 16:30:51 ..."
    timestamp = find_text(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", body)

    # "Financial Transaction Id: 76662021700" or "TxId: 73214484437"
    reference = find_text(r"Financial Transaction Id:\s*(\d+)", body)
    if reference is None:
        reference = find_text(r"TxId:\s*(\d+)", body)

    return {
        "amount": extract_amount(body),
        "fee": text_to_number(fee),
        "new_balance": text_to_number(balance),
        "timestamp": timestamp,
        "reference": reference,
    }

def classify_transaction(body):

    text = body.lower()   # lowercase so the checks ignore capital letters

    # "Your one-time password is ..."  (not a money transaction)
    if "one-time password" in text:
        return "otp_notification", "MTN MoMo", ACCOUNT_OWNER

    # "Your transaction to Jane Smith (...) has been reversed ..."
    if "reversed" in text or "reversal" in text:
        receiver = find_text(r"transaction to (.+?) \(", body)
        return "reversal", receiver, ACCOUNT_OWNER

    # "... transaction with amount 5000 RWF for DIRECT PAYMENT LTD with message ... failed at ..."
    if "failed at" in text and "transaction with amount" in text:
        receiver = find_text(r"RWF for (.+?) with message", body)
        return "failed_payment", ACCOUNT_OWNER, receiver

    # "A transaction of 3000 RWF by IREMBO Ltd on your MOMO account ..."
    if "a transaction of" in text:
        receiver = find_text(r"RWF by (.+?) on your MOMO account", body)
        return "direct_debit", ACCOUNT_OWNER, receiver

    # "Umaze kugura ..." (Kinyarwanda: "You have bought") or "Bundles and Packs"
    if "umaze kugura" in text or "bundles and packs" in text:
        return "bundle_purchase", ACCOUNT_OWNER, "Bundles"

    # "You have transferred 50000 RWF to Bank Name (...) ..."
    if "you have transferred" in text:
        receiver = find_text(r"RWF to (.+?) \(", body)
        return "bank_transfer", ACCOUNT_OWNER, receiver

    # "A bank deposit of 40000 RWF has been added ..." or "DEPOSIT RWF 25000"
    if "bank deposit" in text or "deposit rwf" in text:
        return "bank_deposit", "Bank", ACCOUNT_OWNER

    # "You have received 2000 RWF from Jane Smith (*********013) ..."
    if "you have received" in text:
        sender = find_text(r"from (.+?) \(", body)
        return "incoming_money", sender, ACCOUNT_OWNER

    # "... via agent: Agent Sophia (250790777777), withdrawn 20000 RWF ..."
    if "withdrawn" in text:
        receiver = find_text(r"via agent: (.+?) \(", body)
        return "withdrawal", ACCOUNT_OWNER, receiver

    # "*165*S*10000 RWF transferred to Samuel Carter (250791666666) ..."
    if "transferred to" in text:
        receiver = find_text(r"transferred to (.+?) \(", body)
        return "transfer", ACCOUNT_OWNER, receiver

    # "Your payment of 2000 RWF to Airtime with token ..."
    if "to airtime" in text:
        return "airtime", ACCOUNT_OWNER, "Airtime"

    # "Your payment of 5000 RWF to MTN Cash Power with token ..."
    if "cash power" in text:
        return "cash_power", ACCOUNT_OWNER, "Cash Power"

    # "Your payment of 1,000 RWF to Jane Smith 12845 has been completed ..."
    if "your payment of" in text:
        receiver = find_text(r"to (.+?) (?:\d+ )?has been completed", body)
        return "payment", ACCOUNT_OWNER, receiver

    # Nothing matched: see "HOW TO ADD A NEW MESSAGE TYPE" at the top of the file
    return "other", None, None


def get_status(body):
    """Return 'completed', 'failed', 'reversed' or 'info' (for OTP messages)."""
    text = body.lower()
    if "reversed" in text or "reversal" in text:
        return "reversed"
    if "failed" in text:
        return "failed"
    if "one-time password" in text:
        return "info"
    return "completed"


def build_transaction(record_id, basic, details, transaction_type, sender, receiver):
    """Combine everything we found into one transaction dictionary."""

    # Some messages have no time in the text; use the phone's date instead
    timestamp = details["timestamp"]
    if timestamp is None:
        timestamp = basic["readable_date"]

    return {
        "id": record_id,
        "transaction_type": transaction_type,
        "status": get_status(basic["body"]),
        "amount": details["amount"],
        "currency": CURRENCY,
        "sender": clean_name(sender),
        "receiver": clean_name(receiver),
        "timestamp": timestamp,
        "fee": details["fee"],
        "new_balance": details["new_balance"],
        "transaction_ref": details["reference"],
        "sms_date_ms": basic["date_ms"],
        "readable_date": basic["readable_date"],
        "body": basic["body"],   # keep the original text so results can be checked
    }


def save_to_json(transactions, file_path):
    """Write the list of transactions to a JSON file."""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(transactions, file, indent=2, ensure_ascii=False)

# Summary printed at the end, to help check the results

def print_summary(transactions):
    print(f"Parsed {len(transactions)} transactions -> {JSON_FILE}\n")

    # Count how many transactions there are of each type
    counts = {}
    for transaction in transactions:
        transaction_type = transaction["transaction_type"]
        counts[transaction_type] = counts.get(transaction_type, 0) + 1

    print("Transactions per type:")
    for transaction_type, count in counts.items():
        print(f"  {transaction_type:<18} {count}")

    # Show messages the parser did not recognise, so they can be fixed
    unrecognised = [t for t in transactions if t["transaction_type"] == "other"]
    if unrecognised:
        print(f"\nUnrecognised messages: {len(unrecognised)} (showing up to 5)")
        for transaction in unrecognised[:5]:
            print(f"  id {transaction['id']}: {transaction['body'][:100]}")
        print("See 'HOW TO ADD A NEW MESSAGE TYPE' at the top of parser.py")


# Main program
def main():
    # Step 1: Read the XML
    sms_records = read_xml_file(XML_FILE)

    transactions = []

    # Step 2: Loop through the SMS records
    # Step 3: Give each record a simple ID (1, 2, 3...)
    record_id = 1
    for sms in sms_records:

        # Step 4: Extract the basic information
        basic = extract_basic_info(sms)

        # Step 5: Extract transaction information from the SMS body
        details = extract_transaction_details(basic["body"])

        # Step 6: Classify the transaction
        transaction_type, sender, receiver = classify_transaction(basic["body"])

        # Step 7: Create the final dictionary
        transaction = build_transaction(
            record_id, basic, details, transaction_type, sender, receiver
        )
        transactions.append(transaction)

        record_id = record_id + 1

    # Step 8: Save everything to transactions.json
    save_to_json(transactions, JSON_FILE)

    print_summary(transactions)


# This runs main() only when you start the file directly (python parser.py),
# not when another file imports it.
if __name__ == "__main__":
    main()
