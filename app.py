import os
import secrets
import logging
import requests

from flask import Flask, redirect, request
from pymongo import MongoClient
from flasgger import Swagger
from dotenv import load_dotenv
from flask_cors import CORS
import json

import utils

load_dotenv()

app = Flask(__name__)
swagger = Swagger(app=app)

# Enable CORS for all routes
CORS(app)

# MongoDB's  connection string
client = MongoClient(os.getenv('MONGO_URI'))
mongodb = client["FINVESTA"]
DigiLocker_Aadhar = mongodb["DigiLocker_Aadhar"]

app.secret_key = os.urandom(24)

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
DIGILOCKER_BASE_URL = 'https://api.digitallocker.gov.in/public/oauth2/1/'
REDIRECT_URI = 'http://localhost:5000/callback'

# Generates a random URL-safe string of 16 bytes
state = secrets.token_urlsafe(16)

# Empty aadhar store user
aadhar_number = []


@app.route('/')
def index():
    return "hello world v:01"


# Flask route to start the authorization flow digilocker
@app.route('/digilocker/start-authorization', methods=["GET"])
def start_authorization():
    """
        Begin the OAuth2 authorization process with Digilocker.
        /start-authorization use the url sign-in digilocker account
        ---
        tags:
          - Authorization

    """

    num = request.args.get('aadhar_number')
    aadhar_number.append(num)

    # Authorization URL
    authorization_url = (f"{DIGILOCKER_BASE_URL}/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri="
                         f"{REDIRECT_URI}&state={state}&code_challenge={utils.code_challenge_1}&"
                         f"code_challenge_method=S256")

    return authorization_url


# Flask route to handle the redirection after user authorization
@app.route('/callback', methods=["GET"])
def callback():
    """
        Callback endpoint to exchange the authorization code for an access token.

        Receives the authorization code and state as query parameters from Digilocker's authorization response.
        Verifies the received state parameter for security.
        Initiates the exchange of the authorization code for an access token and retrieves it from Digilocker's token endpoint.

        ---
        tags:
          - Callback
        parameters:
          - in: query
            name: code
            required: true
            description: Authorization code received from Digilocker
            schema:
              type: string
          - in: query
            name: state
            required: true
            description: State parameter received for verification
            schema:
              type: string
        responses:
          200:
            description: Access token retrieved successfully
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    access_token:
                      type: string
                    token_type:
                      type: string
                    expires_in:
                      type: integer
                    refresh_token:
                      type: string
                    scope:
                      type: string
          default:
            description: Unexpected error or missing parameters
        """
    if request.method == "GET":

        # Retrieve the authorization code and state from the query parameters
        authorization_code = request.args.get('code')
        received_state = request.args.get('state')

        # Split the received state to extract application-specific data
        if received_state != state:
            return "Invalid state code"

        # Verify that the authorization code is present
        if not authorization_code:
            return "Authorization code not received."

        token_endpoint = f"{DIGILOCKER_BASE_URL}/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        data = {
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'code_verifier': utils.code_verifier_1,
        }

        response = requests.post(token_endpoint, headers=headers, data=data)

        DigiLocker_Aadhar.insert_one(response.json())

        utils.log_data(message="After sign-in success Digilocker received ", event_type='digilocker_callback',
                       log_level=logging.INFO, additional_context={'received data from Digilocker': response.json()})

        data = response.json()

        # Extracting relevant information from the JSON response
        digilockerid = data.get('digilockerid')
        name = data.get('name')
        dob = data.get('dob')
        gender = data.get('gender')

        # Creating the received_data dictionary
        received_data = {
            'digilockerid': digilockerid,
            'name': name,
            'dob': dob,
            'gender': gender,
            'props': 2,
            'aadharnumber': aadhar_number
        }

        data_string = json.dumps(received_data)
        return redirect(f'https://self-agent-onboarding.fiaglobal.com/Digilocker?data={data_string}')
