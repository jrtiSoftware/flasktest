# Jared Tauler 9/30/21

import os
import pathlib
import yaml

from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
from googleapiclient.discovery import build

from pip._vendor import cachecontrol

import requests

# For typehints
from typing import Union, List
PathLike = Union[str, bytes, os.PathLike]

class GoogleSession():
    def __init__(self,
                 redirect_uri: str = None,
                 google_client_id: str = None,
                 credentials: PathLike = "credentials.json",
                 scopes: List[str] = None
                ):
        # Load from config file if not passed.
        if redirect_uri or google_client_id or scopes is None:
            with open("google.yaml", "r") as f:
                cfg = yaml.safe_load(f)
            if not redirect_uri: redirect_uri = cfg["redirect_uri"]
            if not google_client_id: google_client_id = cfg["google_client_id"]
            if not scopes: scopes = cfg["scopes"]

        self.google_client_id = google_client_id
        client_secrets_file = os.path.join(pathlib.Path(__file__).parent, credentials)
        self.flow = Flow.from_client_secrets_file(
            client_secrets_file=client_secrets_file,
            scopes=scopes,
            redirect_uri=redirect_uri
        )


    def CreateCredentials(self, request):
        self.flow.fetch_token(authorization_response=request.url)  # Retrieve stuff from google auth
        credentials = self.flow.credentials
        request_session = requests.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        id_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=self.google_client_id
        )

        return id_info, credentials

def GmailResource(creds):
    return build("gmail", "v1", credentials=creds)
