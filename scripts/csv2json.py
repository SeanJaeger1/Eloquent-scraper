import csv
import json
import ast

# Open the CSV file and create a CSV reader
with open('final_scrape_no_capital.csv', 'r') as in_file:
    reader = csv.DictReader(in_file)
    
    # Initialize an empty list to store the rows
    data = []
    
    # Iterate through each row in the CSV
    for row in reader:
        # Convert the string in 'WordInfo' back to a dictionary
        row['WordInfo'] = ast.literal_eval(row['WordInfo'])
        data.append(row)
        
# Write the data to a JSON file
with open('final_scrape_no_capital.json', 'w') as out_file:
    json.dump(data, out_file)
