# HITL Firestore Demo

This project demonstrates a Human-in-the-Loop (HITL) workflow for ADK using Google Cloud Firestore as the approval channel.

## Overview

The system is designed to showcase how an agent can pause and wait for human intervention (approval or rejection) before proceeding. Firestore is used as the backend to store requests that require approval and to listen for approval/rejection events.

## Components

*   **Request Submission:** When the agent receives a request that requires human approval, it invokes the `ask_for_approval` tool as an ADK long running function. This function stores a an approval request in Firestore with metadata about the function ID and session that initiated the request.
*   **Approval Interface:**  A Firestore backed web-app provides a way for a human to view pending requests and approve or reject them.
*   **Approval Watcher:**  A script or process that listens for changes in Firestore indicating that a request has been approved or rejected. In this example it uses the live "watch" feature of Firestore. But this could be switched to be push event driven on doc change using EventArc. When a change is detected, a function response is sent back to the agent, essentially closing the loop of the human in the loop. This is essentially identical to the model of a long running operation, where fullfillment of the operation is the human approval step.

## To run the demo

Use multiple terminal windows to operate the three main components

### Set up the Environment

* Clone this repo
* create a virtualenv `python3 -m venv .venv`
* activate the virtualenv `source .venv/bin/activate`
* `pip install -r requirements.txt`
* Be sure that Firestore is active in your project
* Set up ADC and .env file

      export GOOGLE_CLOUD_PROJECT='<project-id>'
      export GOOGLE_CLOUD_LOCATION='us-central1'
      export GOOGLE_GENAI_USE_VERTEXAI=TRUE


### Start the Firestore watcher

_in the root of this sample, in new terminal_

* Note for some async-glitch reason, you need to inject the project information inside the env of the thread by puttin your project info on line 81 of the `firestore_approval_watcher.py` file.
* activate the virtualenv `source .venv/bin/activate`
* `python firestore_approval_watcher.py`

### Start the agent

_again in another terminal in the same dir as this README_

We use a server script in order to use the db session service. 
* activate the virtualenv `source .venv/bin/activate`
* `python serve.py`

### Start the approvals UI

* `cd firestore-viewer`
* npm install
* npm run start
* open a browser to the resulting link

## Note

* While the Firestore watcher writes back to the session from where the approval was generated, the web dev UI does not auto refresh, but if you reload the view, you will see the events.

* The function that checks on approvals queries across sessions by userID

* You can use a sqlite DB viewer tool to inspect the innards of a session, including how the long running function ID is stored in the tool call event.

This is sample code and not suitable for production as is, this is not a Google Product.




