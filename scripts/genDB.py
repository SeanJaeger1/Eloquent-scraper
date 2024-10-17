import csv
import json
import ollama
import os
import time
from tqdm import tqdm

def process_word(word, max_attempts=80):
    prompt = f'''Generate a JSON object for the word '{word}'. Strictly adhere to this structure:
{{
    "word": "{word}",
    "definition": "A clear, concise definition.",
    "wordType": "The part of speech (noun, verb, adjective, etc.).",
    "examples": [
        "A sentence using {word}.",
        "Another example with {word}.",
        "A third instance of {word} usage."
    ],
    "synonyms": ["synonym1", "synonym2", "synonym3"],
    "antonyms": ["antonym1", "antonym2", "antonym3"]
}}
Ensure all fields are accurately filled. The "word" field MUST match '{word}' exactly.
Use the word in all examples. Provide real synonyms and antonyms.
Your response MUST be valid JSON. Do not include any text outside the JSON structure.'''

    for attempt in range(max_attempts):
        try:
            response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
            result = json.loads(response['message']['content'])
            
            if result['word'].lower() == word.lower():
                return result, None
        except json.JSONDecodeError:
            continue
        except Exception as e:
            if attempt == max_attempts - 1:
                return None, str(e)
    
    return None, "Failed to generate valid JSON after maximum attempts"

def load_words(file_path):
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        return [row[0] for row in reader]

def load_processed_words(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            return json.load(jsonfile)
    return []

def save_results(file_path, data, backup=False):
    if backup:
        backup_file = f"{file_path}.bak.{int(time.time())}"
        with open(backup_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2)
        print(f"Backup saved: {backup_file}")
    
    with open(file_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=2)

def save_progress(file_path, index):
    with open(file_path, 'w') as f:
        f.write(str(index))

def main():
    input_file = 'final_scrape.csv'
    output_file = 'processed_words.json'
    progress_file = 'progress.txt'
    
    all_words = load_words(input_file)
    processed_words = load_processed_words(output_file)
    processed_set = set(word['word'].lower() for word in processed_words)
    
    start_index = 0
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            start_index = int(f.read().strip())
    
    print(f"Total words: {len(all_words)}")
    print(f"Processed words: {len(processed_set)}")
    print(f"Starting from index: {start_index}")
    
    try:
        for i in tqdm(range(start_index, len(all_words)), initial=start_index, total=len(all_words)):
            word = all_words[i]
            if word.lower() not in processed_set:
                result, error = process_word(word)
                if result and not error:
                    processed_words.append(result)
                    processed_set.add(result['word'].lower())
                else:
                    print(f"Failed to process '{word}': {error}")
            
            save_progress(progress_file, i + 1)
            
            if (i + 1) % 1000 == 0:
                save_results(output_file, processed_words, backup=True)
            elif (i + 1) % 100 == 0:
                save_results(output_file, processed_words)
    
    except KeyboardInterrupt:
        print("\nProcess interrupted. Saving progress...")
    
    finally:
        save_results(output_file, processed_words, backup=True)
        print(f"Processed {len(processed_words)} words. Results saved to {output_file}")
        print(f"Remaining words: {len(all_words) - len(processed_set)}")

if __name__ == "__main__":
    main()