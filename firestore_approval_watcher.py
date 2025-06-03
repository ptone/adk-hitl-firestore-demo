import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter # Added for potential future query optimization

from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types
import os

from approve_agent import agent

# Global variables
_firestore_initialized = False
_db = None
_event_loop = None # Main event loop, captured in main()

def initialize_firestore():
    """Initializes the Firestore client if not already initialized."""
    global _firestore_initialized, _db
    if not _firestore_initialized:
        try:
            if not firebase_admin._apps:
                # Use Application Default Credentials
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            _db = firestore.client()
            _firestore_initialized = True
            print("Firestore initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firestore: {e}")
            _db = None # Ensure db is None if initialization fails
            raise # Reraise the exception to halt if critical

# In-memory set to avoid reprocessing during a single run of the script.
_processed_doc_ids_current_session = set()

async def process_agent_notification(doc_id: str, doc_data: dict):
    """
    Processes the notification to the ADK agent based on the Firestore document change.
    This is an asynchronous function.
    Updates Firestore status before and potentially after agent interaction.
    """
    global _db
    approval_id = doc_data.get('approval_id')
    session_id = doc_data.get('session')
    user_id = doc_data.get('requestedBy')
    app_name = doc_data.get('appName')
    status = doc_data.get('status')
    original_function_name = "ask_for_approval"

    if not all([session_id, user_id, app_name, approval_id, status]):
        print(f"Missing critical data for doc ID {doc_id} ({approval_id=}, {session_id=}, {user_id=}, {app_name=}, {status=}). Skipping.")
        return

    doc_ref = _db.collection('approvals').document(doc_id)

    session_service = DatabaseSessionService('sqlite:///db.sqlite3')
    artifact_service = InMemoryArtifactService()
    runner = Runner(
        agent=agent.root_agent,
        app_name=app_name,
        artifact_service=artifact_service,
        session_service=session_service,
    )

    tool_output_data = {"status": status}
    function_response_part = types.Part(
        function_response=types.FunctionResponse(
            id=approval_id,
            name=original_function_name,
            response=tool_output_data,
        )
    )
    message_to_agent = types.Content(parts=[function_response_part], role="user")
    print(message_to_agent)

    try:
        print(f"Attempting to send response to agent for session {session_id}, approval_id {approval_id}")
        os.environ["GOOGLE_CLOUD_PROJECT"] = "ptone-misc"
        os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message_to_agent,
        ):
            if event.content.parts and event.content.parts[0].text:
                print(f"** {event.author}: {event.content.parts[0].text}")
        print(f"Successfully sent update to agent for doc ID {doc_id}.")
    except Exception as e:
        print(f"Error sending update to agent for doc ID {doc_id}: {e}")
        # try:
            # doc_ref.update({'status': status, 'agentErrorAt': firestore.SERVER_TIMESTAMP, 'agentError': str(e)})
            # print(f"Reverted Firestore status for {doc_id} to '{status}' due to agent error.")
        # except Exception as db_err:
            # print(f"Critical: Error reverting Firestore status for {doc_id} after agent error: {db_err}")
    # finally:
        # This removal is a safeguard; primary removal is in _handle_scheduled_task_result
        # if doc_id in _processed_doc_ids_current_session:
            # _processed_doc_ids_current_session.remove(doc_id)

def _handle_scheduled_task_result(future, doc_id):
    """Handles the result of the scheduled coroutine, including exceptions."""
    try:
        future.result()  # Raise exception if one occurred from process_agent_notification
    except Exception as e:
        print(f"Error during scheduled execution of process_agent_notification for doc ID {doc_id}: {e}")
        # Consider how to update Firestore if the task itself failed.
        # This might involve another threadsafe call if _db operations are needed and complex.
    finally:
        if doc_id in _processed_doc_ids_current_session:
            _processed_doc_ids_current_session.remove(doc_id)
        print(f"Finished processing for doc ID {doc_id}.")


def firestore_on_snapshot_sync_callback(col_snapshot, changes, read_time):
    """
    Synchronous callback for Firestore's on_snapshot listener.
    Schedules processing on the main event loop.
    """
    global _event_loop # Needed to schedule tasks on the loop

    for change in changes:
        doc_id = change.document.id
        doc_data = change.document.to_dict()
        current_status = doc_data.get('status')

        if current_status in ['approved', 'rejected'] and doc_id not in _processed_doc_ids_current_session:
            _processed_doc_ids_current_session.add(doc_id) # Add before scheduling
            print(f"Detected actionable change for doc ID {doc_id}: status '{current_status}'. Type: {change.type.name}")
            
            if _event_loop:
                future = asyncio.run_coroutine_threadsafe(
                    process_agent_notification(doc_id, doc_data), 
                    _event_loop
                )
                future.add_done_callback(lambda f: _handle_scheduled_task_result(f, doc_id))
            else:
                print(f"CRITICAL: Event loop not available for scheduling notification for doc ID {doc_id}.")
                if doc_id in _processed_doc_ids_current_session: # Clean up if scheduling failed
                     _processed_doc_ids_current_session.remove(doc_id)

async def watch_approvals_collection():
    """Sets up and runs the Firestore watcher for the 'approvals' collection."""
    global _db
    if not _db:
        print("Firestore database client not available. Watcher cannot start.")
        return
    
    if not _event_loop: # Should have been set by main()
        print("CRITICAL: Event loop not captured before starting watcher. Watcher cannot start safely.")
        return

    query = _db.collection('approvals').where(filter=FieldFilter("status", "in", ["approved", "rejected"]))
    watch = query.on_snapshot(firestore_on_snapshot_sync_callback) # Pass the sync callback
    print("Firestore watcher started for 'approvals' collection (listening for 'approved' or 'rejected' statuses).")
    try:
        while True:
            await asyncio.sleep(3600) 
    except KeyboardInterrupt:
        print("Watcher stopped by user (KeyboardInterrupt).")
    except asyncio.CancelledError:
        print("Watcher task cancelled.")
    finally:
        if watch:
            watch.unsubscribe()
            print("Firestore watch unsubscribed.")

async def main():
    """Main function to initialize Firestore and start the watcher."""
    global _event_loop # To assign the captured event loop
    try:
        _event_loop = asyncio.get_running_loop()
    except RuntimeError as e:
        print(f"Could not get running event loop in main: {e}. Halting.")
        return

    try:
        initialize_firestore()
    except Exception: # Error already printed by initialize_firestore
        print("Halting due to Firestore initialization failure.") 
        return

    if _db:
        await watch_approvals_collection()
    else:
        print("Firestore not initialized. Watcher did not start.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Main application interrupted. Exiting.")
    except Exception as e:
        print(f"An unexpected error occurred in main: {e}")
