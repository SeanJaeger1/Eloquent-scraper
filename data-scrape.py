import csv
import requests
import pandas as pd
import re
import time

# Open your text file and create a CSV writer
with open('word-frequency.txt', 'r') as in_file, open('final_scrape_pending.csv', 'w', newline='') as out_file:
    reader = csv.reader(in_file, delimiter='\t')
    writer = csv.writer(out_file)
    
    # Write the header row to the output CSV
    writer.writerow(['Word', 'Difficulty'])
    
    # Initialize a counter for the number of rows written to the output CSV
    row_count = 0
    
    # Iterate through each row in the text file
    for row in list(reader)[29262:]:
        row = re.split('\s+', row[0].strip())
        word = row[1]  # assuming the word is the second column
        
        # Ping the API with the word
        response = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}')  # replace 'your_api_url' with the actual API URL
        print(row[0], word, response)

        while response.status_code == 429:
            # Wait for 5 minutes before trying again
            print('Too many requests. Waiting for 30s...')
            time.sleep(30)
            response = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}')  # try the request again
        
        if response.status_code == 200:
            # Write the word and the response to the output CSV
            difficulty = response.json()  # replace this with actual extraction of difficulty from the response
            writer.writerow([word, difficulty])
            row_count += 1