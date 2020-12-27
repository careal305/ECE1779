from flask import Flask

admin = Flask(__name__)
admin.config['SECRET_KEY'] = 'Hard to guess!'

from manager import main
from manager import worker
from manager import auto_scaling   #undo this once user app and rds(table:policy) / crontab is ready
#from manager import check_cpu


# Get credential(use it or WriteCredential.py)
cred= requests.get('http://169.254.169.254/latest/meta-data/iam/security-credentials/ece1779a2').json()

'''Basic Configuration
'''
aws_access_key_id=cred['AccessKeyId']
aws_secret_access_key=cred['SecretAccessKey']
aws_session_token=cred['Token']
