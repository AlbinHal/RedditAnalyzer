import json

# FILE HANDLING
def read_file(fp: str):
    with open(fp, "r") as file:
        response = json.load(file)
    return response

# PARSING
def parse_text(text :str) -> list[str]:
    words = text.lower().split()
    return words

# NETWORKING
