import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import time

# Optimized script to copy from default to another database
print("Starting optimized database copy...")

# Load service account
cred = credentials.Certificate("../serviceAccountKey.json")
print(f"Service account project ID: {cred.project_id}")

# Initialize source app (default database)
source_app = firebase_admin.initialize_app(cred, name="source")
source_db = firestore.client(app=source_app)
print("Connected to source database (default)")

# Initialize target app for sj-eloquent-prod database
target_app = firebase_admin.initialize_app(cred, name="target")

# Connect to the target database using database_id parameter
target_db = firestore.client(app=target_app, database_id="sj-eloquent-prod")
print("Connected to target database (sj-eloquent-prod)")

# Get all data from source
print("Reading data from source...")
docs = []
words_ref = source_db.collection("words")
read_batch_size = 1000  # For reading

# Get documents in smaller batches to avoid memory issues
query = words_ref.limit(read_batch_size)
while True:
    batch = list(query.stream())
    if not batch:
        break
        
    docs.extend(batch)
    print(f"Read {len(docs)} documents so far...")
    
    # Get the last document as a starting point for the next batch
    last = batch[-1]
    query = words_ref.start_after(last).limit(read_batch_size)

total_docs = len(docs)
print(f"Total: Read {total_docs} documents from source")

# Try a single test document first
if docs:
    try:
        first_doc = docs[0]
        test_id = first_doc.id
        test_data = first_doc.to_dict()
        
        print(f"Testing with document ID: {test_id}")
        target_db.collection("words").document(test_id).set(test_data)
        print("✅ Successfully wrote test document")
    except Exception as e:
        print(f"❌ Error writing test document: {e}")
        firebase_admin.delete_app(source_app)
        firebase_admin.delete_app(target_app)
        exit(1)

# Write to target using batched writes (much faster)
print("Writing to target database using batched writes...")
success = 0
errors = 0
write_batch_size = 500  # Firestore limits batch to 500 writes

# Process documents in batches
for i in range(0, total_docs, write_batch_size):
    # Create a new batch
    batch = target_db.batch()
    
    # Add up to 500 documents to the batch
    end_idx = min(i + write_batch_size, total_docs)
    current_batch_docs = docs[i:end_idx]
    
    print(f"Preparing batch {i//write_batch_size + 1} ({len(current_batch_docs)} documents)")
    
    # Add each document to the batch
    for doc in current_batch_docs:
        doc_ref = target_db.collection("words").document(doc.id)
        batch.set(doc_ref, doc.to_dict())
    
    # Commit the batch
    try:
        batch.commit()
        batch_success = len(current_batch_docs)
        success += batch_success
        print(f"✅ Batch {i//write_batch_size + 1} committed successfully: {success}/{total_docs} documents copied")
    except Exception as e:
        errors += len(current_batch_docs)
        print(f"❌ Error committing batch {i//write_batch_size + 1}: {e}")
    
    # Small pause between batches to avoid throttling
    time.sleep(0.5)

print(f"\nComplete! Copied {success} documents with {errors} errors")

# Clean up
firebase_admin.delete_app(source_app)
firebase_admin.delete_app(target_app)
print("Done!")