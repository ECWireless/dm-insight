import uuid
import os
from dotenv import load_dotenv

from google.cloud.dialogflowcx_v3beta1.services.agents import AgentsClient
from google.cloud.dialogflowcx_v3beta1.services.sessions import SessionsClient
from google.cloud.dialogflowcx_v3beta1.types import session

load_dotenv()
DIALOGFLOW_PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID')
DIALOGFLOW_AGENT_ID = os.getenv('AGENT_ID')
GOOGLE_APPLICATION_CREDENTIALS = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
DIALOGFLOW_LANGUAGE_CODE = 'en-US'
SESSION_ID = 'current-user-id'


async def run_intent_session(question):
    project_id = DIALOGFLOW_PROJECT_ID
    # For more information about regionalization see https://cloud.google.com/dialogflow/cx/docs/how/region
    location_id = 'us-central1'
    # For more info on agents see https://cloud.google.com/dialogflow/cx/docs/concept/agent
    agent_id = DIALOGFLOW_AGENT_ID
    agent = f"projects/{project_id}/locations/{location_id}/agents/{agent_id}"
    # For more information on sessions see https://cloud.google.com/dialogflow/cx/docs/concept/session
    session_id = uuid.uuid4()
    texts = ["Hello", question]
    # For more supported languages see https://cloud.google.com/dialogflow/es/docs/reference/language
    language_code = "en-us"

    return await detect_intent_texts(agent, session_id, texts, language_code)


async def detect_intent_texts(agent, session_id, texts, language_code):
    """Returns the result of detect intent with texts as inputs.

    Using the same `session_id` between requests allows continuation
    of the conversation."""
    session_path = f"{agent}/sessions/{session_id}"
    print(f"Session path: {session_path}\n")
    client_options = None
    agent_components = AgentsClient.parse_agent_path(agent)
    location_id = agent_components["location"]
    if location_id != "global":
        api_endpoint = f"{location_id}-dialogflow.googleapis.com:443"
        print(f"API Endpoint: {api_endpoint}\n")
        client_options = {"api_endpoint": api_endpoint}
    session_client = SessionsClient(client_options=client_options)

    for text in texts:
        text_input = session.TextInput(text=text)
        query_input = session.QueryInput(
            text=text_input, language_code=language_code)
        request = session.DetectIntentRequest(
            session=session_path, query_input=query_input
        )
        response = session_client.detect_intent(request=request)

        # print("=" * 20)
        # print(f"Query text: {response.query_result.text}")
        response_messages = [
            " ".join(msg.text.text) for msg in response.query_result.response_messages
        ]
        # print(f"Response text: {' '.join(response_messages)}\n")
        if 'get_member' in response_messages:
            return True
    return False
