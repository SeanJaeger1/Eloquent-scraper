import json
import os
from tqdm import tqdm
import ollama
import re

CONTRACTIONS = {
    "'ve": "have",
    "'s": "is",
    "'m": "am",
    "'re": "are",
    "'ll": "will",
    "'d": "would",
    "n't": "not"
}

def is_valid_word(word):
    valid_short_words = ['a', 'i', 'I'] + list(CONTRACTIONS.keys())
    invalid_words = ['et', 'al', 'etc', 'eg', 'ie']
    
    if word in valid_short_words:
        return True
    
    if word.lower() in invalid_words or (len(word) < 2 and word not in valid_short_words):
        return False
    
    if not re.match(r'^[a-zA-Z\'\-]+$', word):
        return False
    
    return True

def verify_entry_with_ai(entry):
    word = entry['word']
    is_contraction = word in CONTRACTIONS
    full_form = CONTRACTIONS.get(word, word)
    
    prompt = f'''Verify and improve the quality of the following word entry:

Word: {word}
{'This is a contraction of: ' + full_form if is_contraction else ''}
Definition: {entry['definition']}
Examples:
1. {entry['examples'][0]}
2. {entry['examples'][1]}
3. {entry['examples'][2]}

Requirements:
1. The definition MUST accurately describe the word or contraction.
2. For contractions, explain its usage and provide the full form.
3. The definition should be clear, accurate, and comprehensive.
4. Examples should correctly use the word in context.
5. Only suggest changes if they significantly improve the entry.

If the entry meets all requirements and is high quality, respond with "PASS". Otherwise, respond with "FAIL" followed by a corrected version of the entry in the same format as above. Your response should be either "PASS" or "FAIL: [corrected entry]".'''

    response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
    return response['message']['content'].strip()

def load_processed_words(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            return json.load(jsonfile)
    return []

def save_processed_words(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=2, ensure_ascii=False)

def parse_corrected_entry(correction, original_entry):
    try:
        word_match = re.search(r'Word:\s*(.*)', correction)
        definition_match = re.search(r'Definition:\s*(.*)', correction)
        examples_match = re.findall(r'\d\.\s*(.*)', correction)

        word = word_match.group(1) if word_match else original_entry['word']
        definition = definition_match.group(1) if definition_match else original_entry['definition']
        examples = examples_match if examples_match else original_entry['examples']

        while len(examples) < 3:
            examples.append(original_entry['examples'][len(examples)])
        examples = examples[:3]

        # For contractions, we don't require the contraction itself to be in the definition
        if word not in CONTRACTIONS and word.lower() not in definition.lower():
            print(f"Warning: Definition for '{word}' does not include the word itself. Keeping original definition.")
            definition = original_entry['definition']

        return {'word': word, 'definition': definition, 'examples': examples}
    except Exception as e:
        print(f"Error parsing corrected entry: {e}")
        print(f"Original correction text: {correction}")
        return original_entry

def process_batch(batch):
    updated = False
    words_to_remove = []
    
    for entry in batch:
        if not is_valid_word(entry['word']):
            print(f"Removing invalid word: '{entry['word']}'")
            words_to_remove.append(entry)
            updated = True
            continue

        try:
            result = verify_entry_with_ai(entry)
            if result.startswith("FAIL"):
                corrected_entry = parse_corrected_entry(result.split(': ', 1)[1], entry)
                if corrected_entry != entry:
                    print(f"\nUpdating entry for word '{entry['word']}':")
                    print(f"  Old definition: {entry['definition']}")
                    print(f"  New definition: {corrected_entry['definition']}")
                    print(f"  Old examples: {entry['examples']}")
                    print(f"  New examples: {corrected_entry['examples']}")
                    
                    entry.update(corrected_entry)
                    updated = True
        except Exception as e:
            print(f"Error processing entry for '{entry['word']}': {e}")
    
    for word in words_to_remove:
        batch.remove(word)
    
    return updated, words_to_remove

def main():
    input_file = 'processed_words.json'
    processed_words = load_processed_words(input_file)

    print(f"Total words to verify: {len(processed_words)}")

    batch_size = 10
    removed_words = []
    
    for i in tqdm(range(0, len(processed_words), batch_size), desc="Processing batches"):
        batch = processed_words[i:i+batch_size]
        updated, removed = process_batch(batch)
        removed_words.extend(removed)
        
        if updated:
            save_processed_words(input_file, processed_words)
            print(f"\nUpdated information saved to {input_file} (words {i+1}-{min(i+batch_size, len(processed_words))})")

    for word in removed_words:
        processed_words.remove(word)

    save_processed_words(input_file, processed_words)
    print(f"\nFinal update: Removed {len(removed_words)} invalid words.")
    print("\nVerification complete.")

if __name__ == "__main__":
    main()