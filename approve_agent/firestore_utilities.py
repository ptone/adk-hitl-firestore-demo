'''Utilities for interacting with Firestore.'''
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter, And

def add_item(item_data):
    """Adds an item to the 'approvals' collection in Firestore.

    Initializes the Firestore client if not already initialized.

    Args:
        item_data (dict): A dictionary containing the data for the item to be approved.
                          Example: {'item_id': '123', 'description': 'Approve new feature', 'status': 'pending'}

    Returns:
        The ID of the newly created document in Firestore, or None if an error occurs.
    """
    try:
        if not firebase_admin._apps:
            # Use Application Default Credentials
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        approvals_ref = db.collection('approvals')
        # Add a new document with a generated ID
        update_time, doc_ref = approvals_ref.add(item_data)
        print(f"Added document with ID: {doc_ref.id} at {update_time}")
        return doc_ref.id
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_items_by_user(user_id: str):
    """Queries Firestore for items matching a user ID and session ID.

    Args:
        user_id (str): The user ID to filter by.
        session_id (str): The session ID to filter by.

    Returns:
        list[tuple[str, str]]: A list of tuples, where each tuple contains
                                 (itemName, status) for matching documents.
                                 Returns an empty list if no matches are found or an error occurs.
    """
    try:
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        approvals_ref = db.collection('approvals')

        # Use FieldFilter with the 'filter' keyword argument to construct the query
        query = approvals_ref.where(filter=And([
            FieldFilter('requestedBy', '==', user_id),
            # FieldFilter('session', '==', session_id)
        ]))
        results = query.stream()

        items = []
        for doc in results:
            data = doc.to_dict()
            item_name = data.get('itemName')
            status = data.get('status')
            if item_name and status:
                items.append((item_name, status))
        print(items)
        return items
    except Exception as e:
        print(f"An error occurred while querying items: {e}")
        return []
