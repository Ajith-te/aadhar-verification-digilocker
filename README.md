# Digilocker Sign-In with Python Flask REST API

This project provides a Python Flask-based REST API to initiate and handle the sign-in process with Digilocker.

## Overview

This application allows users to sign in with Digilocker through OAuth2 authorization, enabling them to securely access their data on Digilocker.

## Prerequisites

- Python installed (version X.X.X)
- Flask (`pip install flask`)
- Flasgger (`pip install flasgger`)
- dotenv (`pip install python-dotenv`)

## Configuration

Before running the application, make sure to set the following environment variables in a `.env` file:

## Installation

1. Clone the repository.
2. Install dependencies using `pip install -r requirements.txt`.
3. Set up the environment variables in a `.env` file.
4. Run the application with `python app.py`.

## Usage

### Starting Authorization Process

To start the authorization process with Digilocker:

- Make a GET request to `/start-authorization`.
- This will redirect you to the Digilocker authorization page.

### Callback Endpoint

The callback URL (`/callback`) handles the redirection after user authorization:

- The authorization code is exchanged for an access token.
- The obtained access token can be used for further operations with Digilocker.

## Documentation

For detailed API documentation, refer to the Swagger documentation integrated into the application.

Access the Swagger UI by navigating to `http://localhost:5000/apidocs`.

## Contributing

Feel free to contribute to this project by submitting issues or pull requests.

## License

This project is licensed under the [License Name] - see the [LICENSE](LICENSE) file for details.

## Contact

For any questions or support, contact [Your Contact Information].
