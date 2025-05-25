"""
Functions for saving and retrieving translation results from CSV as cache and JSON files for debug.
"""
import os
import csv
import json
from dotenv import load_dotenv

load_dotenv()

cache_path = os.getenv("CACHE_CSV")
nllb_json_file = os.getenv("NLLB_JSON")


def save_to_csv(
    target_language_tag: str,
    original_sentence: str,
    final_response: str,
    context: str,
    csv_path = cache_path):
    """
    Appends a translated sentence to a CSV file.

    Args:
        target_language_tag (str): Language code of the translated text (e.g., 'eng_Latn').
        original_sentence (str): The original sentence before translation.
        final_response (str): The final translated sentence.
        csv_path (str): Path to the CSV file. Defaults to '/app/translated_data.csv'.

    Notes:
        If the file is empty, a header row will be written first.
    """
    with open(csv_path, mode='a', newline= '', encoding= 'utf-8') as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(["target_language_tag" , "Original Sentence", "Translated Sentence", "context"])
        writer.writerow([target_language_tag ,original_sentence, final_response, context])


def check_existing_translation(
    target_language_tag: str,
    original_sentence: str,
    context: str,
    csv_path = cache_path):
    """
    Checks if a translation for the given sentence and language tag already exists in the CSV file.

    Args:
        target_language_tag (str): Language code of the translation (e.g., 'eng_Latn').
        original_sentence (str): The original sentence to look for.
        csv_path (str): Path to the CSV file. Defaults to '/app/translated_data.csv'.

    Returns:
        str or None: The existing translated sentence if found, otherwise None.
    """
    try:
        with open(csv_path, mode='r', newline='', encoding= 'utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row[0] == target_language_tag and row[1] == original_sentence and row[3] == context:
                    return row[2]
    except FileNotFoundError:
        return None
    return None


def save_debug_json(data: dict, path= nllb_json_file):
    """
    Saves the given dictionary as a formatted JSON file.

    Args:
        data (dict): The data to be saved in JSON format.
        path (str): The file path where the JSON should be saved. Defaults to '/app/nllb_data.json'.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)