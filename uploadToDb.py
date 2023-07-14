import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json

# Initialize Firebase
cred = credentials.Certificate('serviceAccountKey.json')  # Path to your service account key JSON file
firebase_admin.initialize_app(cred)

# Access Firestore
db = firestore.client()

# Load JSON data
with open('word_data_processed.json') as json_file:  # Path to your JSON file with words data
    words_data = json.load(json_file)

# Upload words to Firestore
words_ref = db.collection('words')

idx = 0
didx = 0
difficulties = ['beginner', 'intermediate', 'advanced', 'expert']

for word in words_data:

    word["index"] = idx
    word["difficulty"] = difficulties[didx]
    words_ref.add(word)

    if idx == 5000:
        if didx == 3:
            idx += 1
            pass
        else:
            didx += 1
            idx = 0
    else:
        idx += 1
    
    print(difficulties[didx], idx, word["word"])

print('Upload completed successfully.')
