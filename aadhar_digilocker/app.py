import os
import time
import json
import secrets
import logging
import requests
import redis

from flask import Flask, redirect, request, jsonify
from pymongo import MongoClient
from flasgger import Swagger
from dotenv import load_dotenv
from flask_cors import CORS

from aadhar_digilocker.utils import log_data, code_verifier_1, code_challenge_1

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
# Digilocker base url
DIGILOCKER_BASE_URL =  os.environ.get("DIGILOCKER_BASE_URL")
# Digilocker After verify redirect in our this url 
CALLBACK_DIGILOCKER  =  os.environ.get("CALLBACK_DIGILOCKER")


# After redirect to fron-end url  
AGENT_SELF_REDIRECT_URL = os.environ.get("AGENT_SELF_REDIRECT_URL")
AGENT_TM_REDIRECT_URL = os.environ.get("AGENT_TM_REDIRECT_URL") 
DS_FINVESTA_REDIRECT_URL = os.environ.get("DS_FINVESTA_REDIRECT_URL")


# Redis server
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)


@app.route('/')
def index():
    return "hello world Digilocker Finvesta V.02"


# Generates a random URL-safe string of 16 bytes
random_string = secrets.token_urlsafe(16)

# Append a timestamp to make it more unique
state = f"{random_string}{int(time.time())}"

# Flask route to start the authorization flow for DigiLocker
@app.route('/start-authorization', methods=["POST"])
def start_authorization():
    try:
        user_type = request.args.get('user_type')
        if user_type not in ["agent_self", "agent_tm", "ds", "tm"]:
            return {"error": "User type is invalid. Allowed values are 'agent_self', 'agent_tm', 'ds', 'tm'"}, 400

        aadhar_number = request.args.get('aadhar_number')

        # Generate authorization URL
        authorization_url = (f"{DIGILOCKER_BASE_URL}/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri="
                         f"{CALLBACK_DIGILOCKER}&state={state}&code_challenge={code_challenge_1}&code_challenge_method=S256")

        # Create data dictionary to insert into database
        data = {"state": state, "user_type": user_type, "aadhar_number": aadhar_number}

        # Store user data in Redis
        redis_key = f"user:{state}"
        redis_data = {"user_type": user_type, "aadhar_number": aadhar_number}
        redis_client.setex(redis_key, 300, json.dumps(redis_data))

        # Log the event
        log_data(message="Link created to DigiLocker URL", event_type="/start-authorization",
                 log_level=logging.INFO, additional_context={'user_data': data, "authorization_url": authorization_url})

        # Return the authorization URL
        return authorization_url 
    
    except Exception as e:

        # Log any exceptions that occur
        log_data(message={"error": str(e)},event_type="/start-authorization", log_level=logging.ERROR)
        # Return an error message or appropriate response
        return {"error": str(e)}, 500



# Digilocker callback this api for live domain name is  https://finvestaapiuat.fiaglobal.com/aadharverify/callback
@app.route('/callback', methods=["GET"])
def callback():
    try:
        # Retrieve the authorization code and state from the query parameters
        authorization_code = request.args.get('code')
        received_state = request.args.get('state')

        # Split the received state to extract application-specific data
        if received_state != state:
            return "Invalid state code"
        
        # Verify that the authorization code is present
        if not authorization_code:
            return "Authorization code not received."

        # Token api send to data after get aadhar details
        token_endpoint = f"{DIGILOCKER_BASE_URL}/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        data = {
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': CALLBACK_DIGILOCKER,
            'code_verifier': code_verifier_1,
        }

        response = requests.post(token_endpoint, headers=headers, data=data)

        aadhar_data = response.json()

        redirect_type_json = redis_client.get(f"user:{received_state}")
            
        if redirect_type_json is None:
            return {"error": "Redirect type not found for the received state"}, 400
        
        redirect_type = json.loads(redirect_type_json)
        
        user_type = redirect_type.get('user_type')
        aadhar_number = redirect_type.get('aadhar_number')

      # Add the user_type field to the Aadhar data
        aadhar_data["user_type"] = user_type
        DigiLocker_Aadhar.insert_one(aadhar_data)

        # Agent  self on-boarding Redirect  
        if user_type == 'agent_self':

            log_data(message="Agent self on-boarding completed aadhar data", event_type = '/callback',
                            log_level=logging.INFO, additional_context={'Received data from Digilocker': aadhar_data})

            received_data = {
                    'digilocker_id': aadhar_data.get('digilockerid'),
                    'name': aadhar_data.get('name'),
                    'dob': aadhar_data.get('dob'),
                    'gender': aadhar_data.get('gender'),
                    'aadhar_number': aadhar_number,
                    'props': 2,
            }

            data_string = json.dumps(received_data)

            return redirect(f'{AGENT_SELF_REDIRECT_URL}?data={data_string}')
        
        # Agent  self on-boarding Redirect  
        if user_type == 'agent_tm':

            log_data(message="Agent TM via on-boarding verification completed aadhar data", event_type = '/callback',
                            log_level=logging.INFO, additional_context={'Received data from Digilocker': aadhar_data})

            received_data = {
                    'digilocker_id': aadhar_data.get('digilockerid'),
                    'name': aadhar_data.get('name'),
                    'dob': aadhar_data.get('dob'),
                    'gender': aadhar_data.get('gender'),
                    'aadhar_number': aadhar_number,
                    'props': 2,
            }

            data_string = json.dumps(received_data)

            return redirect(f'{AGENT_TM_REDIRECT_URL}?data={data_string}')

        # Distributor on-boarding Redirect 
        if user_type == 'ds':

            log_data(message = "Distributor TM verification completed aadhar data", event_type = '/callback',
                            log_level=logging.INFO, additional_context = {'Received data from Digilocker': aadhar_data})
            
            return redirect(f'{DS_FINVESTA_REDIRECT_URL}')

    except Exception as e:
        # Log any exceptions that occur
        log_data(message = {"error": str(e)}, event_type = "/callback", log_level = logging.ERROR)
        # Return an error message or appropriate response
        return {"error": str(e)}, 500
