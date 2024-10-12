import csv
import json
import ollama
import os
from tqdm import tqdm

def process_word(word):
    prompt = f'''Generate a JSON object for the word '{word}' with the following structure: {{ "word": "{word}", "definition": "A clear and concise definition", "wordType": "The part of speech (e.g., noun, verb, adjective)", "examples": ["A sentence using the word", "Another example sentence", (provide three)], "synonyms": ["synonym1", "synonym2", "synonym3"], "antonyms": ["antonym1", "antonym2", "antonym3"] }} Ensure all fields contain accurate and unique information for the word '{word}'. The response should be valid JSON and nothing else as this will be put directly into my DB. DO NOT REPLY WITH ANYTHING OTHER THAN THE PYTHON OBJECT.'''

    response = ollama.chat(
        model="llama3",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    try:
        return json.loads(response["message"]["content"])
    except json.JSONDecodeError:
        print(f"Error decoding JSON for word '{word}'. Response: {response['message']['content']}")
        return None

def main():
    input_file = 'final_scrape.csv'
    output_file = 'processed_words.json'
    progress_file = 'progress.txt'
    
    # Load progress if exists
    start_index = 0
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            start_index = int(f.read().strip())
    
    processed_words = []
    
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
            
            # Save progress
            with open(progress_file, 'w') as f:
                f.write(str(i + 1))
            
            # Save results periodically
            if (i + 1) % 10 == 0:
                with open(output_file, 'w', encoding='utf-8') as jsonfile:
                    json.dump(processed_words, jsonfile, indent=2)
    
    except KeyboardInterrupt:
        print("\nProcess interrupted. Progress saved.")
    
    finally:
        # Save final results
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(processed_words, jsonfile, indent=2)
        
        print(f"Processed {len(processed_words)} words. Results saved to {output_file}")

if __name__ == "__main__":
    main()