# import json
from os.path import isfile
from json import load, dump
from typing import TypeAlias, Literal
import logging


SubRedditMode: TypeAlias = Literal["old", "new", "hot"]
FilePath: TypeAlias = str
Key: TypeAlias = str
# FILE HANDLING


def read_file(fp: str):
    with open(fp, "r") as file:
        data = load(file)
    return data


def save_json(data, file_path):
    with open(file_path, "w") as f:
        dump(data, f, indent=4)


def update_json(file_path, updates):
    # Load the existing JSON data
    data = read_file(file_path)
    # Update the specified fields
    for key, value in updates.items():
        data[key] = value
    # Save the updated JSON data
    save_json(data, file_path)

# PARSING


def parse_text(text: str) -> list[str]:
    words = text.lower().split()
    return words

# NETWORKING


def limit_rate(header) -> int:
    """Returns sleep time (ms) to prevent exceeding sending limit"""
    used, remaining, reset = header['x-ratelimit-used'],
    header['x-ratelimit-remaining'], header['x-ratelimit-reset']
    print(f'Used: {used}, Remaining: {remaining}, Reset: {reset}')
    if float(remaining) < 10:
        return 2
    return 0
