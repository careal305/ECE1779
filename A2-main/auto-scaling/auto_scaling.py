# run this file every one min
import math
import random
import pymysql
import boto3
import time
from datetime import datetime, timedelta
from operator import itemgetter

ec2 = boto3.resource('ec2')
EC2 = boto3.client('ec2')
ELB = boto3.client('elbv2')
CLOUDWATCH = boto3.client('cloudwatch')

connection = pymysql.connect(user='admin',
                             password='ece1779a2',
                             host='ece1779.cfgoq3p3aw7m.us-east-1.rds.amazonaws.com',
                             port=3306,
                             database='ece1779',
                            )

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

def get_policy():
    cursor = connection.cursor()
    sql_get = "select * from autoScaling where id=1"
    cursor.execute(sql_get)
    record = cursor.fetchone()
    return record

def get_all_targets():
    # Get all the register targets(the workers that are registered with the elb[include initial, healthy, unused])
    target_group = ELB.describe_target_health(TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:327200236258:targetgroup/ece1779a2user/da2f671e55d83fc0')
    instances = []
    if target_group['TargetHealthDescriptions']:
        for target in target_group['TargetHealthDescriptions']:
            if target['TargetHealth']['State'] != 'draining':
                instances.append(target)
    return instances

def get_cpu_stats(instance_id):
    metric_name = 'CPUUtilization'
    namespace = 'AWS/EC2'
    statistic = 'Sum'  # could be Sum,Maximum,Minimum,SampleCount,Average

    cpu = CLOUDWATCH.get_metric_statistics(
        Period=1 * 60,  # resolution 60s
        StartTime=datetime.utcnow() - timedelta(seconds=2 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName=metric_name,
        Namespace=namespace,
        Statistics=[statistic],
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}]
    )
    cpu_stats = []
    for point in cpu['Datapoints']:
        hour = point['Timestamp'].hour
        minute = point['Timestamp'].minute
        time = hour + minute / 60
        cpu_stats.append([time, point['Sum']])
    cpu_stats = sorted(cpu_stats, key=itemgetter(0))
    return cpu_stats

def add_worker():
    # If stopped instance exists, just start it.
    stopped_instance = get_stopped_instances()['Reservations']
    if stopped_instance:
        instance_id = stopped_instance[0]['Instances'][0]['InstanceId']
        EC2.start_instances(InstanceIds=[instance_id])
    else:  # Create a new instance
        new_instance_id = ec2_create()
        # Loop until the status of the new instance is running in order to register to elb.
        status = EC2.describe_instance_status(InstanceIds=[new_instance_id])
        # At beginning, the status['InstanceStatuses'] is empty, it needs time to generate info
        while len(status['InstanceStatuses']) < 1:
            time.sleep(1)
            status = EC2.describe_instance_status(InstanceIds=[new_instance_id])
        # It needs time to transfer the state from 'pending' to 'running'
        while status['InstanceStatuses'][0]['InstanceState']['Name'] != 'running':
            time.sleep(1)
            status = EC2.describe_instance_status(InstanceIds=[new_instance_id])
        register_instance(new_instance_id)

def ec2_create():
    # Create a new ec2 instance
    new_instance = EC2.run_instances(ImageId='ami-0620b60a074c81804',
                                        KeyName='a2worker0',
                                        MinCount=1,
                                        MaxCount=1,
                                        UserData=user_data,
                                        InstanceType='t2.medium',
                                        Monitoring={'Enabled': True},
                                        SecurityGroupIds=['sg-05428fb146ee292de'],  #copy security group
                                        IamInstanceProfile={ 'Name': 'ece1779a2'}      #copy IAM role
                                        )
    # Get the new instance id
    return new_instance['Instances'][0]['InstanceId']

def get_stopped_instances():
    ec2_filter = [{'Name': 'instance-state-name', 'Values': ['stopped','stopping']}]
    return EC2.describe_instances(Filters=ec2_filter)

def register_instance(new_instance_id):
    # Register the newly created ec2 to the elb
    target = [{'Id': new_instance_id,
               'Port': 5000}, ]
    ELB.register_targets(TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:327200236258:targetgroup/ece1779a2user/da2f671e55d83fc0', Targets=target)

def remove_worker(id):
    target = [{'Id': id,
               'Port': 5000}]
    ELB.deregister_targets(TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:327200236258:targetgroup/ece1779a2user/da2f671e55d83fc0', Targets=target)
    ec2.instances.filter(InstanceIds=[id]).terminate()

def auto_scaling():
    instances = get_all_targets()
    cpu_list = []
    instance_id = []
    for instance in instances:
        id = instance['Target']['Id']
        cpu_stats = get_cpu_stats(id)
        print(cpu_stats)
        if len(cpu_stats) > 0:
            instance_id.append(id)
            # Confusing, why the num of points returned by get_cpu_stats is different, sometimes 1, sometimes 2. I have no choice.
            if len(cpu_stats) == 2:
                average = (cpu_stats[0][1] + cpu_stats[1][1])/ 2  # average cpu in last 2 min
            elif len(cpu_stats) == 1:
                average = cpu_stats[0][1]
            cpu_list.append(average)
    num = len(cpu_list)
    cpu_average = sum(cpu_list) / num

    (grow_threshold, shrink_threshold, expand_ratio, shrink_ratio, id) = get_policy()
    print(cpu_average)
    if cpu_average < grow_threshold:
        num_add = int((expand_ratio - 1) * num)
        print(num_add)
        # the maximum size of worker pool is set to 8
        if expand_ratio * num <= 8:
            for n in range(num_add):
                add_worker()
        else:
            num_add = 8 - num
            for n in range(num_add):
                add_worker()

    elif cpu_average > shrink_threshold:
        num_remove = int(math.ceil(num * shrink_ratio))
        # the minimum size of worker pool is set to 1
        if num - num_remove >= 1 :
            for n in range(num_remove):
                random.shuffle(instance_id)
                remove_worker(instance_id[n])
        else:
            num_remove = num - 1
            for n in range(num_remove):
                random.shuffle(instance_id)
                remove_worker(instance_id[n])

if __name__ == "__main__":
    auto_scaling()

