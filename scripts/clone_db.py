import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import time
import os
import traceback

def clone_words_collection():
    # Get the correct path to the service account key
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    service_account_path = os.path.join(project_root, 'serviceAccountKey.json')
    
    print(f"Using service account key at: {service_account_path}")
    

    
    # 1. INITIALIZE SOURCE DATABASE (DEFAULT)
    try:
        cred = credentials.Certificate(service_account_path)
        default_app = firebase_admin.initialize_app(cred, name='default')
        source_db = firestore.client(app=default_app)
        print("✅ Successfully connected to source database (default)")
        
        # Test connection
        test_doc = source_db.collection('_test').document('test')
        test_doc.set({'timestamp': firestore.SERVER_TIMESTAMP})
        print("✅ Successfully wrote to source database")
        test_doc.delete()
    except Exception as e:
        print(f"❌ ERROR connecting to source database: {e}")
        print(traceback.format_exc())
        return
    
    # 2. INITIALIZE TARGET DATABASE (PROD)
    try:
        # NOTE: Using Admin SDK bypasses security rules
        prod_app = firebase_admin.initialize_app(cred, {
            'projectId': 'eloquent-sj',
            'databaseURL': 'https://eloquent-sj.firebaseio.com',
            'storageBucket': 'eloquent-sj.appspot.com',
            'firestoreDatabase': 'sj-eloquent-prod'
        }, name='prod')
        
        target_db = firestore.client(app=prod_app)
        print("✅ Successfully connected to target database (sj-eloquent-prod)")
        
        # Test connection
        try:
            test_doc = target_db.collection('_test').document('test')
            test_doc.set({'timestamp': firestore.SERVER_TIMESTAMP})
            print("✅ Successfully wrote to target database")
            test_doc.delete()
        except Exception as e:
            print(f"❌ ERROR writing to target database: {e}")
            print("This suggests security rules are blocking the operation even with Admin SDK")
            print(traceback.format_exc())
            return
    except Exception as e:
        print(f"❌ ERROR connecting to target database: {e}")
        print(traceback.format_exc())
        return
    
    # 3. FETCH SOURCE DATA
    try:
        words_ref = source_db.collection('words')
        words_docs = list(words_ref.stream())
        total_docs = len(words_docs)
        
        if total_docs == 0:
            print("⚠️ No documents found in source 'words' collection!")
            return
            
        print(f"✅ Found {total_docs} documents in the source 'words' collection")
        
        # Print sample document to verify structure
        sample_doc = words_docs[0].to_dict()
        print(f"Sample document structure: {list(sample_doc.keys())}")
    except Exception as e:
        print(f"❌ ERROR fetching source data: {e}")
        print(traceback.format_exc())
        return
    
    # 4. COPY DATA IN BATCHES
    batch_size = 400
    processed_docs = 0
    success_count = 0
    error_count = 0
    
    print("\n== Starting data transfer ==")
    
    # Special case: try a single document first
    try:
        first_doc = words_docs[0]
        first_doc_id = first_doc.id
        first_doc_data = first_doc.to_dict()
        
        print(f"Testing with single document (ID: {first_doc_id})")
        target_ref = target_db.collection('words').document(first_doc_id)
        target_ref.set(first_doc_data)
        
        # Verify it was written
        verification = target_ref.get()
        if verification.exists:
            print(f"✅ Successfully wrote and verified test document")
        else:
            print(f"❌ Test document was not written correctly")
            return
    except Exception as e:
        print(f"❌ ERROR with test document: {e}")
        print(traceback.format_exc())
        return
        
    # Continue with batch processing
    for i in range(0, total_docs, batch_size):
        try:
            batch = target_db.batch()
            end_idx = min(i + batch_size, total_docs)
            current_batch = words_docs[i:end_idx]
            
            print(f"\nProcessing batch {i//batch_size + 1}/{(total_docs-1)//batch_size + 1} ({len(current_batch)} documents)")
            
            for doc in current_batch:
                target_ref = target_db.collection('words').document(doc.id)
                batch.set(target_ref, doc.to_dict())
            
            # Commit the batch
            batch.commit()
            batch_count = len(current_batch)
            processed_docs += batch_count
            success_count += batch_count
            
            print(f"✅ Batch committed successfully")
            print(f"Progress: {processed_docs}/{total_docs} documents ({processed_docs/total_docs:.1%})")
            
            # Small delay to avoid hitting quota limits
            time.sleep(1)
            
        except Exception as e:
            error_count += len(current_batch)
            print(f"❌ ERROR processing batch {i//batch_size + 1}: {e}")
            print(traceback.format_exc())
            # Continue with next batch
    
    # 5. VERIFICATION
    try:
        # Count documents in target collection
        target_docs = list(target_db.collection('words').limit(10).stream())
        print(f"\n== Verification ==")
        print(f"Documents visible in target collection: {len(target_docs) if target_docs else 0}")
        if target_docs:
            print("Sample document IDs in target:")
            for doc in target_docs:
                print(f" - {doc.id}")
    except Exception as e:
        print(f"❌ ERROR during verification: {e}")
    
    # 6. SUMMARY
    print("\n== Summary ==")
    print(f"Total documents processed: {processed_docs}")
    print(f"Successful transfers: {success_count}")
    print(f"Failed transfers: {error_count}")
    
    if success_count > 0 and error_count == 0:
        print("✅ Cloning completed successfully!")
    elif success_count > 0:
        print("⚠️ Cloning completed with some errors.")
    else:
        print("❌ Cloning failed completely.")

    # Clean up Firebase apps
    try:
        firebase_admin.delete_app(default_app)
        firebase_admin.delete_app(prod_app)
        print("✅ Cleaned up Firebase app connections")
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")

if __name__ == "__main__":
    clone_words_collection()