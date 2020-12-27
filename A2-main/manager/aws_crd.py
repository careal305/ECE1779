import requests

cred_response = requests.get('http://169.254.169.254/latest/meta-data/iam/security-credentials/ece1779a2')
cred=cred_response.json()



