import os
import json
import pickle
import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def Create_Service(api_name, api_version, scopes):
    """
    Creates a Google API service client.
    Handles OAuth flow, token persistence, and refresh logic.
    Uses GOOGLE_CREDENTIALS environment variable instead of a file.
    """
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = scopes

    cred = None
    pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}.pickle'

    # Load existing credentials if available
    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)

    # Refresh or request new credentials if needed
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            creds_json = os.environ.get("GOOGLE_CREDENTIALS")
            if not creds_json:
                raise Exception("GOOGLE_CREDENTIALS environment variable not set")
            creds_dict = json.loads(creds_json)

            flow = InstalledAppFlow.from_client_config(
                creds_dict,
                scopes=SCOPES,
                redirect_uri="https://ranchoddasarogyabhavanmatheran.onrender.com/oauth2callback"
            )
            # For local dev: creds = flow.run_local_server(port=5000)
            # On Render, you’ll handle via /oauth2callback route
            cred = flow.run_local_server(port=0)

        # Save credentials for reuse
        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)

    # Build the service
    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        print(API_SERVICE_NAME, 'service created successfully')
        return service
    except Exception as e:
        print('Unable to connect.')
        print(e)
        return None

def convert_to_RFC_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    """
    Converts a given date/time into RFC3339 format required by Google APIs.
    """
    dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + 'Z'
    return dt