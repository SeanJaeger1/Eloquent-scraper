import json
import re

def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

def check_swears(text, swears):
    words = re.findall(r'\b\w+\b', text.lower())
    for swear in swears:
        if swear.lower() in words:
            return swear
    return None

def process_word_data(word_data, swears):
    detected_swear = check_swears(word_data['word'], swears)
    if detected_swear:
        return detected_swear, 'word'

    detected_swear = check_swears(word_data['definition'], swears)
    if detected_swear:
        return detected_swear, 'definition'

    for example in word_data['examples']:
        detected_swear = check_swears(example, swears)
        if detected_swear:
            return detected_swear, 'example'

    for synonym in word_data['synonyms']:
        detected_swear = check_swears(synonym, swears)
        if detected_swear:
            return detected_swear, 'synonym'

    for antonym in word_data['antonyms']:
        detected_swear = check_swears(antonym, swears)
        if detected_swear:
            return detected_swear, 'antonym'

    return None, None

def main():
    swears = load_json('swears.json')
    processed_words = load_json('processed_words.json')

    for word_data in processed_words:
        detected_swear, location = process_word_data(word_data, swears)
        if detected_swear:
            print(f"Detected swear: '{detected_swear}' in {location}")
            print(json.dumps(word_data, indent=2))
            print('-' * 50)

if __name__ == "__main__":
    main()