subnet_id = 'subnet-db57afea'
ami_id = 'ami-0bf618774e7879c6a'
#manager
manager_id = 'i-045d51d784601f821'
#instance  user1
image_id = 'ami-0620b60a074c81804'
Iam_profile = { 'Name': 'ece1779a2'}
SecurityGroup_id = ['sg-05428fb146ee292de']
key_name = 'a2worker0'

# define userdata to run user-app at instance launch
user_data = 'Content-Type: multipart/mixed; boundary="//"\n' \
            'MIME-Version: 1.0\n' \
            '--//\n' \
            'Content-Type: text/cloud-config; charset="us-ascii"\n' \
            'MIME-Version: 1.0\n' \
            'Content-Transfer-Encoding: 7bit\n' \
            'Content-Disposition: attachment; filename="cloud-config.txt"\n' \
            '#cloud-config\n' \
            'cloud_final_modules:\n' \
            '- [scripts-user, always]\n' \
            '--//\n' \
            'Content-Type: text/x-shellscript; charset="us-ascii"\n' \
            'MIME-Version: 1.0\n' \
            'Content-Transfer-Encoding: 7bit\n' \
            'Content-Disposition: attachment; filename="userdata.txt"\n' \
            '#!/bin/bash\n' \
            'screen\n' \
            '/home/ubuntu/Desktop/ece1779a1/start.sh\n' \
            '--//'

#elb target group ARN
targetgroup = 'targetgroup/ece1779a2user/da2f671e55d83fc0'
targetgroupARN = 'arn:aws:elasticloadbalancing:us-east-1:327200236258:targetgroup/ece1779a2user/da2f671e55d83fc0'
#elb
loadbalancer = 'app/ece1779a2/5f33ad35c054e2bb'
loadbalancerARN = 'arn:aws:elasticloadbalancing:us-east-1:327200236258:loadbalancer/app/ece1779a2/5f33ad35c054e2bb'
loadbalancerDNS = 'ece1779a2-1322249347.us-east-1.elb.amazonaws.com'

# RDS - database
db_config = {'user': 'admin',
             'password': 'ece1779a2',
             'ssl_ca':'/home/ubuntu/Desktop/ece1779a1/rds-ca-2019-root.pem',
             'host': 'ece1779.cfgoq3p3aw7m.us-east-1.rds.amazonaws.com',
             'database': 'ece1779'}
