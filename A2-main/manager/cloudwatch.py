from datetime import datetime, timedelta
from ec2_metadata import ec2_metadata
import boto3
import mysql.connector
import requests
from config import db_config
from aws_crd import cred
'''
Functions for Database
'''

def connect_to_database():
	return mysql.connector.connect(user=db_config['user'],
									password=db_config['password'],
									ssl_ca=db_config['ssl_ca'],
									host=db_config['host'],
									database=db_config['database'])
def create_graph(instance_id):
	time = datetime.now()
	for i in range 30:
		cnx = connect_to_database()
		cursor = cnx.cursor()
		time = time - timedelta(minutes = 1)
		record_time = time.strftime("%d%m%Y%H%M")
		query = ''' SELECT * from http_request where instance_id = %s and record_time = %s'''
		cursor.execute(query,(instance_id,record_time))
		result = cursor.fetchall()
		value = len(result)
		value = str(value)
		#pair will be time,value

cred= requests.get('http://169.254.169.254/latest/meta-data/iam/security-credentials/ece1779a2').json()

'''Basic Configuration
'''
aws_access_key_id=cred['AccessKeyId']
aws_secret_access_key=cred['SecretAccessKey']
aws_session_token=cred['Token']

cloudwatch = boto3.client('cloudwatch',aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key,
					  aws_session_token=aws_session_token)

#instance_id = ec2_metadata.instance_id
instance_id ='i-0154f70fff1d2de04'
cnx = connect_to_database()
cursor = cnx.cursor()
#time = datetime.now()
#record_time = time.strftime("%d%m%Y%H%M")
time = '131120202045'
query = ''' SELECT * from http_request where instance_id = %s and record_time = %s'''
cursor.execute(query,(instance_id,time))
result = cursor.fetchall()
value = len(result)
value = str(value)

#command1 = "aws cloudwatch put-metric-data --metric-name HTTP_Requests --dimensions Instance="
#command2 = " --namespace \"HTTP_Requests\" --value "
#command = command1+instance_id+command2+value
#print(command)
cloudwatch.put_metric_data(
	MetricData=[
		{
			'MetricName': 'HTTP_requests',
			'Dimensions': [
				{
					'Name': 'HTTP_requests',
					'Value': str(value)
				},
			],
			'Unit' : 'None',
		},
	],
	Namespace = 'HTTP_requests'
)
#An error occurred (AccessDenied) when calling the PutMetricData operation: User: arn:aws:sts::327200236258:assumed-role/ece1779a2/i-045d51d784601f821 is not authorized to perform: cloudwatch:PutMetricData

