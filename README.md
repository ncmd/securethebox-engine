Scoring Engine

Flask + Websocket

Think of the scoring engine like a customer/user

A user needs to:
- Login
- Logout
- Purchase something
- Perform other actions

Security wise:
- App should be online
- App should be protected against by web app attacks
- App performance should be decently fast for good user experience
- Customer's information should be confidential/private
- Customer's data should not be modified without user's permission
- Customer's account should be working as intended by the Business


virtualenv venv
virtualenv -p /Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7 venv
source venv/bin/activate
pip install -r requirements.txt