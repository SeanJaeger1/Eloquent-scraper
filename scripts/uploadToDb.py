import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json

# Initialize Firebase
cred = credentials.Certificate('../serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Access Firestore
db = firestore.client()

# Load JSON data
with open('processed_words.json') as json_file:
    words_data = json.load(json_file)

# Upload words to Firestore
words_ref = db.collection('words')

idx = 0
didx = 0
difficulties = ['beginner', 'intermediate', 'advanced', 'expert']

for word in words_data:
    word_doc = word.copy()
    word_doc["index"] = idx
    word_doc["difficulty"] = difficulties[didx]
    words_ref.add(word_doc)

    if idx == 9000:
        if didx == 3:
            idx += 1
        else:
            didx += 1
            idx = 0
    else:
        idx += 1
    
    print(f"{difficulties[didx]}, {idx}, {word['word']}")

print('Upload completed successfully.')
