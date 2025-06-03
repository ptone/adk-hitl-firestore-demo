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


"""A simple script to set up some approvals through the agent"""

import asyncio
import time


from dotenv import load_dotenv
from google.adk.agents.run_config import RunConfig
from google.adk.cli.utils import logs
from google.adk.runners import Runner
from google.adk.sessions import Session
from google.genai import types
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import DatabaseSessionService

from approve_agent import agent

load_dotenv(override=True)
logs.log_to_tmp_folder()


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
    session_11 = await runner.session_service.create_session(
        app_name=app_name, user_id=user_id_1
    )

    # session_11 = Session(
    #     id="31b0804c-516e-4abe-9fda-04b58a80547f",
    #     app_name=app_name,
    #     user_id=user_id_1)

    async def run_prompt(session: Session, new_message: str):
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=new_message)]
        )
        print("** User says:", content.model_dump(exclude_none=True))
        async for event in runner.run_async(
            user_id=user_id_1,
            session_id=session.id,
            new_message=content,
        ):
            if event.content.parts and event.content.parts[0].text:
                print(f"** {event.author}: {event.content.parts[0].text}")

    start_time = time.time()
    print("Start time:", start_time)
    print(session_11.id)
    print("------------------------------------")
    await run_prompt(session_11, "can you check on my approvals status")
    await run_prompt(session_11, "can you approve my chair for 500 dollars?")
    await run_prompt(session_11, "can you approve my desk for 5000 dollars?")
    await run_prompt(session_11, "can you check on my approvals status")
    end_time = time.time()
    print("------------------------------------")
    print("End time:", end_time)
    print("Total time:", end_time - start_time)


if __name__ == "__main__":
    asyncio.run(main())
