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

from typing import Any

from google.adk import Agent
from google.adk.tools import ToolContext
from google.adk.tools.long_running_tool import LongRunningFunctionTool
from google.genai import types
from firebase_admin import firestore # Added for SERVER_TIMESTAMP

from .firestore_utilities import add_item, get_items_by_user



def reimburse(purpose: str, amount: float) -> str:
  """Reimburse the amount of money to the employee."""
  return {'status': 'ok'}


def ask_for_approval(
    purpose: str, amount: float, tool_context: ToolContext
) -> dict[str, Any]:
  """Ask for approval for the reimbursement."""
  if not add_item({
      "itemName": purpose,
      "amount": amount,
      "status": "pending",
      "session": tool_context._invocation_context.session.id,
      "approval_id": tool_context.function_call_id,
      "requestedBy": tool_context._invocation_context.user_id,
      "appName": tool_context._invocation_context.app_name,
      "requestedAt": firestore.SERVER_TIMESTAMP, # Added requestedAt field
  }
  ):
    return {'status': 'error'}
  print(tool_context.function_call_id)
  return {'status': 'pending'}

def check_approvals(tool_context: ToolContext) -> list[list[str]]:
  """Check the approvals for the reimbursement. Returns a list of items and their approval status"""
  items = get_items_by_user(
      user_id=tool_context._invocation_context.user_id,
      # session_id=tool_context._invocation_context.session.id,
  )
  if not items:
    return []
  return items
  

root_agent = Agent(
    model='gemini-2.0-flash',
    name='reimbursement_agent',
    instruction="""
      You are an agent whose job is to handle the reimbursement process for
      the employees. If the amount is less than $100, you will automatically
      approve the reimbursement.

      If the amount is greater than $100, you will
      ask for approval from the manager. If the manager approves, you will
      call reimburse() to reimburse the amount to the employee. If the manager
      rejects, you will inform the employee of the rejection.
""",
    tools=[reimburse, LongRunningFunctionTool(func=ask_for_approval), check_approvals],
    generate_content_config=types.GenerateContentConfig(temperature=0.1),
)