import os
import base64
import hashlib
import logging
import uuid

from logging.handlers import TimedRotatingFileHandler
from flask import Flask, request

app = Flask(__name__)


# Logging_config
logging.basicConfig(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s --- %(levelname)s --- %(message)s')
log_file = "Aadhar.logs"
file_handler = TimedRotatingFileHandler(log_file, when="D", interval=1, backupCount=5)
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
logging.shutdown()


# Logger
def log_data(message, event_type, log_level, additional_context=None):
    """
    Log an event with contextual information.

    Parameters:
    - user_id (int): The identifier of the user triggering the event.
    - message (str): The message or details of the event.
    - event_type (str): The type or category of the event.
    - log_level (int): The severity level of the log (e.g., logging.INFO, logging.WARNING).
    - additional_context (str or None): Additional context or information related to the event (optional).

    This function generates unique request and response IDs, extracts browser information and IP address
    from the request headers, and constructs a log message. The log message is then logged using the specified log level.

    Example:
    log(5, "Mandatory ifsc is missing", "IMPS Transaction Inquiry", logging. WARNING)

    """

    request_id = generate_id()
    response_id = generate_id()
    browser_info = request.headers.get('User-Agent')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    log_message = (f"message: {message}  --- Event: {event_type} --- request_id: {request_id} ---"
                   f" response_id: {response_id} --- browser_info: {browser_info} --- ip_address: {ip_address} --- "
                   f"{additional_context}")

    app.logger.log(log_level, log_message)


# Generates an id's
def generate_id():
    """
    Generates an ID for the request_id,response_id.

    Returns:
    str: The generated session ID.
    """
    return str(uuid.uuid4())[:18]


# Function to generate a secure random string fulfilling the code_verifier
def generate_code_verifier():
    """
        Generates a secure random string suitable for PKCE (Proof Key for Code Exchange) purposes.

        Returns:
        - str: A randomly generated code_verifier string encoded in URL-safe Base64 without padding.
        """
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('=')
    return code_verifier


# Function to calculate SHA256 hash and Base64URL encode it code_challenge
def generate_code_challenge(code_verifier):
    """
        Generates a code challenge for PKCE (Proof Key for Code Exchange) by hashing the provided code verifier
        using SHA256 and encoding the hash in URL-safe Base64 without padding.

        Parameters:
        - code_verifier (str): The code verifier string to be hashed and encoded.

        Returns:
        - str: The code challenge generated for the provided code_verifier.
        """
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip('=')
    return code_challenge


# Code_verifier pass the value code_challenge
code_verifier_1 = generate_code_verifier()
code_challenge_1 = generate_code_challenge(code_verifier_1)

