# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
A simple script to manually send back the function response to a pending approval
you need to set session and function ID after running the ask_approve script
"""

import asyncio
import time

from dotenv import load_dotenv
from google.adk.agents.run_config import RunConfig
from google.adk.cli.utils import logs
from google.adk.runners import Runner
from google.adk.sessions import Session
from google.genai import types
from google.adk.artifacts import InMemoryArtifactService
# from google.adk.sessions import InMemorySessionService
from google.adk.sessions import DatabaseSessionService
import os

from approve_agent import agent

load_dotenv(override=True)
logs.log_to_tmp_folder()

session_id = os.environ.get("SESSION_ID")
function_id = os.environ.get("FUNCTION_ID")


async def main():
    app_name = "my_app"
    user_id_1 = "user1"
    session_service = DatabaseSessionService('sqlite:///db.sqlite3')
    artifact_service = InMemoryArtifactService()
    runner = Runner(
        agent=agent.root_agent,
        app_name=app_name,
        artifact_service=artifact_service,
        session_service=session_service,
    )
  

    async def run_prompt(session: Session, new_message):
        async for event in runner.run_async(
            user_id=user_id_1,
            session_id=session.id,
            new_message=new_message,
        ):
            if event.content.parts and event.content.parts[0].text:
                print(f"** {event.author}: {event.content.parts[0].text}")

    start_time = time.time()
    print("Start time:", start_time)
    print("------------------------------------")
    updated_tool_output_data = {
    "status": "rejected",
    "ticket-id": "zya", # from original call
    # ... other relevant updated data
    }
    updated_function_response_part = types.Part(
        function_response=types.FunctionResponse(
            id=function_id,   # Original call ID
            name="ask_for_approval", # Original call name
            response=updated_tool_output_data,
        )
    )
    new_message=types.Content(
        parts=[updated_function_response_part], role="user"
    )
    session_11 = Session(
        id=session_id,
        app_name=app_name,
        user_id=user_id_1)
    await run_prompt(session_11, new_message)
    end_time = time.time()
    print("------------------------------------")
    print("End time:", end_time)
    print("Total time:", end_time - start_time)


if __name__ == "__main__":
    asyncio.run(main())
