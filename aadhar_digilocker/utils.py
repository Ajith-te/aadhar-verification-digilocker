import os
import base64
import hashlib
import logging


from logging.handlers import TimedRotatingFileHandler
from flask import Flask, request

app = Flask(__name__)

# Logging_config
logging.basicConfig(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s --- %(levelname)s --- %(message)s')
log_file = "Aadhar_Digilocker.logs"
file_handler = TimedRotatingFileHandler(log_file, when="D", interval=1, backupCount=5)
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
logging.shutdown()


# Logger
def log_data(message, event_type, log_level, additional_context=None):
       
    browser_info = request.headers.get('User-Agent')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    log_message = (f"message: {message}  ---- Event: {event_type} ---- browser_info: {browser_info} ---- ip_address: {ip_address} ---- "
                   f"{additional_context}")

    app.logger.log(log_level, log_message)


# Function to generate a secure random string fulfilling the code_verifier
def generate_code_verifier():
 
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('=')
    return code_verifier


# Function to calculate SHA256 hash and Base64URL encode it code_challenge
def generate_code_challenge(code_verifier):
    
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip('=')
    return code_challenge


# Code_verifier pass the value code_challenge
code_verifier_1 = generate_code_verifier()
code_challenge_1 = generate_code_challenge(code_verifier_1)
