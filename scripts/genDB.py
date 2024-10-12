import csv
import json
import ollama
import os
from tqdm import tqdm
import time

def process_word(word, max_retries=6):
    prompt = f'''Generate a JSON object for the word '{word}' with the following structure:
{{
    "word": "{word}",
    "definition": "A clear and concise definition",
    "wordType": "The part of speech (e.g., noun, verb, adjective)",
    "examples": [
        "A sentence using the word {word}",
        "Another example sentence using {word}",
        "A third example using {word}"
    ],
    "synonyms": ["synonym1", "synonym2", "synonym3"],
    "antonyms": ["antonym1", "antonym2", "antonym3"]
}}
Ensure all fields contain accurate and unique information for the word '{word}'.
The response should be valid JSON and nothing else as this will be put directly into my DB.
IMPORTANT: Make sure the word '{word}' is used in ALL example sentences.
DO NOT REPLY WITH ANYTHING OTHER THAN THE PYTHON OBJECT.'''

    for attempt in range(max_retries):
        try:
            response = ollama.chat(
                model="llama3",
                messages=[{"role": "user", "content": prompt}],
            )
            
            result = json.loads(response["message"]["content"])
            
            # Check if the word is used in all examples
            if all(word.lower() in example.lower() for example in result["examples"]):
                return result
            else:
                print(f"Retry for word '{word}': Word not used in all examples.")
                time.sleep(1)  # Add a small delay before retrying
        except json.JSONDecodeError:
            print(f"Retry {attempt + 1} for word '{word}': Invalid JSON.")
            time.sleep(1)  # Add a small delay before retrying
    
    print(f"Failed to process word '{word}' after {max_retries} attempts.")
    return None

def main():
    input_file = 'final_scrape.csv'
    output_file = 'processed_words.json'
    progress_file = 'progress.txt'
    failed_words_file = 'failed_words.txt'
    
    # Load progress if exists
    start_index = 0
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            start_index = int(f.read().strip())
    
    processed_words = []
    failed_words = []
    
    # Load existing processed words if any
    if os.path.exists(output_file):
        with open(output_file, 'r') as jsonfile:
            processed_words = json.load(jsonfile)
    
    with open(input_file, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header if present
        words = [row[0] for row in reader]  # Assuming the word is in the first column
    
    try:
        for i in tqdm(range(start_index, len(words)), initial=start_index, total=len(words)):
            word = words[i]
            result = process_word(word)
            if result:
                processed_words.append(result)
            else:
                failed_words.append(word)
            
            # Save progress
            with open(progress_file, 'w') as f:
                f.write(str(i + 1))
            
            # Save results periodically
            if (i + 1) % 10 == 0:
                with open(output_file, 'w', encoding='utf-8') as jsonfile:
                    json.dump(processed_words, jsonfile, indent=2)
                with open(failed_words_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(failed_words))
    
    except KeyboardInterrupt:
        print("\nProcess interrupted. Progress saved.")
    
    finally:
        # Save final results
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(processed_words, jsonfile, indent=2)
        with open(failed_words_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(failed_words))
        
        print(f"Processed {len(processed_words)} words. Results saved to {output_file}")
        print(f"Failed to process {len(failed_words)} words. List saved to {failed_words_file}")

if __name__ == "__main__":
    main()