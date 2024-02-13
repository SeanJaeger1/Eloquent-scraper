import csv
import requests
import re
import time

# Open your text file and create a CSV writer
with open('word-frequency.txt', 'r') as in_file, open('final_scrape_pending.csv', 'w', newline='') as out_file:
    reader = csv.reader(in_file, delimiter='\t')
    writer = csv.writer(out_file)
    
    # Write the header row to the output CSV
    writer.writerow(['Word', 'WordInfo'])
    
    # Initialize a counter for the number of rows written to the output CSV
    row_count = 0
    
    # Iterate through each row in the text file
    for row in list(reader):
        row = re.split('\s+', row[0].strip())
        word = row[1]  # assuming the word is the second column
        
        # Ping the API with the word
        response = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}')

        while response.status_code == 429:
            # Wait for 5 minutes before trying again
            print('Too many requests. Waiting for 30s...')
            time.sleep(30)
            response = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}')
    
        if response.status_code == 200:
            # Write the word and the response to the output CSV
            wordInfo = response.json()  # replace this with actual extraction of wordInfo from the response
            print(wordInfo)
            writer.writerow([word, wordInfo])
            row_count += 1