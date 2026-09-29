import json
import sys
import time


def linear_search(transactions, target_id):
    for transaction in transactions:
        if transaction["id"] == target_id:
            return transaction
    return None


def dictionary_lookup(transaction_dict, target_id):
    return transaction_dict.get(target_id)


def load_transactions(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict) and "transactions" in data:
        return data["transactions"]

    return data


def main():
    if len(sys.argv) < 2:
        print("Usage: python dsa/search_comparison.py <json_file>")
        return

    filename = sys.argv[1]

    try:
        transactions = load_transactions(filename)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return
    except json.JSONDecodeError:
        print(f"Invalid JSON file: {filename}")
        return

    if len(transactions) < 20:
        print("At least 20 records are required.")
        return

    transaction_dict = {
        transaction["id"]: transaction
        for transaction in transactions
    }

    target_ids = [
        transaction["id"]
        for transaction in transactions[:20]
    ]

    repetitions = 10000

    start = time.perf_counter()

    for _ in range(repetitions):
        for target_id in target_ids:
            linear_search(transactions, target_id)

    linear_time = time.perf_counter() - start

    start = time.perf_counter()

    for _ in range(repetitions):
        for target_id in target_ids:
            dictionary_lookup(transaction_dict, target_id)

    dictionary_time = time.perf_counter() - start

    print("DSA Search Comparison")
    print("=====================")
    print(f"Records tested: {len(transactions)}")
    print(f"Records searched: {len(target_ids)}")
    print(f"Repetitions: {repetitions}")
    print()
    print(f"Linear search time:     {linear_time:.6f} seconds")
    print(f"Dictionary lookup time: {dictionary_time:.6f} seconds")
    print()

    if dictionary_time < linear_time:
        print("Dictionary lookup was faster.")
    else:
        print("Linear search was faster in this run.")


if __name__ == "__main__":
    main()
