from flask import render_template, redirect, url_for, request, g
import boto3
import time
import mysql.connector
from datetime import datetime, timedelta
from operator import itemgetter
from manager import admin
from manager import config

ec2 = boto3.resource('ec2')
EC2 = boto3.client('ec2')
elb = boto3.client('elbv2')
CLOUDWATCH = boto3.client('cloudwatch')

'''
Functions for Database (for delete all data)

def connect_to_database():
	return mysql.connector.connect(user=db_config['user'],
					password=db_config['password'],
					host=db_config['host'],
					database=db_config['database'])

def get_db():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = connect_to_database()
	return db

@admin.teardown_appcontext
# this will execute every time when the context is closed
def teardown_db(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()
'''



'''
Functions for Worker List and Chart
'''
@admin.route('/',methods=['GET'])
@admin.route('/ec2_list',methods=['GET', 'POST'])
# Display an HTML list of all ec2 instances
def ec2_list():
    target_instances = get_all_targets()
    num_worker_stats = ec2_chart()
    return render_template('main.html', target_instances=target_instances, num_worker_stats=num_worker_stats)

def get_all_targets():
    # Get all the register targets(the workers that are registered with the elb[include initial, healthy, unused])
    target_group = elb.describe_target_health(TargetGroupArn=config.targetgroupARN)
    instances = []
    if target_group['TargetHealthDescriptions']:
        for target in target_group['TargetHealthDescriptions']:
            if target['TargetHealth']['State'] != 'draining':
                instances.append(target)
    return instances

def ec2_chart():
    # Display a chart of the num of workers in the last 30min.
    metric_name = 'HealthyHostCount'
    namespace = 'AWS/ApplicationELB'
    statistic = 'Average'

    num_worker = CLOUDWATCH.get_metric_statistics(
        Period=1 * 60,  # resolution 60s
        StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName=metric_name,
        Namespace=namespace,  # Unit='Percent',
        Statistics=[statistic],
        Dimensions=[{'Name': 'TargetGroup', 'Value': config.targetgroup},
                    {'Name': 'LoadBalancer', 'Value': config.loadbalancer}]
    )
    num_worker_stats = []
    for point in num_worker['Datapoints']:
        hour = point['Timestamp'].hour
        minute = point['Timestamp'].minute
        time = hour + minute / 60
        num_worker_stats.append([time, point['Average']])

    num_worker_stats = sorted(num_worker_stats, key=itemgetter(0))
    return num_worker_stats

'''
Functions for Each Worker's Details
'''
@admin.route('/ec2_details/<id>',methods=['GET'])
#Display CPU&HTTP request charts about a specific instance.
def ec2_details(id):
    # To get instance details
    instance = ec2.Instance(id)
    #Chart1: Total cpu utilization of the worker for the past 30mins, resolution = 1min
    cpu_stats = get_cpu_stats(id)
    #Chart2: The rate of the http request received by the worker in the past 30mins, resolution = 1min
    http_requests = get_http_requests(id)
    return render_template('ec2_details.html', instance=instance, cpu_stats=cpu_stats, http_requests=http_requests)

def get_cpu_stats(instance_id):
    metric_name = 'CPUUtilization'
    namespace = 'AWS/EC2'
    statistic = 'Average'  # could be Sum,Maximum,Minimum,SampleCount,Average

    cpu = CLOUDWATCH.get_metric_statistics(
        Period=1 * 60,  # resolution 60s
        StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
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
        cpu_stats.append([time, point['Average']])
    cpu_stats = sorted(cpu_stats, key=itemgetter(0))
    return cpu_stats

def get_http_requests(instance_id):
    metric_name = 'HTTP_requests'
    namespace = 'HTTP_requests'
    statistic = 'Maximum'  # could be Sum,Maximum,Minimum,SampleCount,Average

    http = CLOUDWATCH.get_metric_statistics(
        Period=1 * 60,  # resolution 60s
        StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
        EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
        MetricName=metric_name,
        Namespace=namespace,  # Unit='Percent',
        Statistics=[statistic],
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}]
    )
    http_requests = []
    for point in http['Datapoints']:
        hour = point['Timestamp'].hour
        minute = point['Timestamp'].minute
        time = hour + minute / 60
        http_requests.append([time, point['Maximum']])
    http_requests = sorted(http_requests, key=itemgetter(0))
    return http_requests

'''
Functions for Adding New Worker to Worker Pool
'''
@admin.route('/add_worker',methods=['POST'])
# Add new worker
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
    return redirect(url_for('ec2_list'))

def ec2_create():
    # Create a new ec2 instance
    new_instance = EC2.run_instances(ImageId=config.image_id,
                                        KeyName=config.key_name,
                                        MinCount=1,
                                        MaxCount=1,
                                        UserData=config.user_data,
                                        InstanceType='t2.medium',
                                        Monitoring={'Enabled': True},
                                        SecurityGroupIds=config.SecurityGroup_id,  #copy security group
                                        IamInstanceProfile=config.Iam_profile      #copy IAM role
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
    elb.register_targets(TargetGroupArn=config.targetgroupARN, Targets=target)

'''
Functions for Deleting Worker from Worker Pool
'''
@admin.route('/remove_worker/<id>',methods=['POST'])
# Terminate a EC2 instance
def remove_worker(id):
    target = [{'Id': id,
               'Port': 5000}]
    elb.deregister_targets(TargetGroupArn=config.targetgroupARN, Targets=target)
    ec2.instances.filter(InstanceIds=[id]).terminate()
    return redirect(url_for('ec2_list'))
'''
Functions for stopping manager and terminating all the workers

@admin.route('/stop_manager', methods=['POST'])
def stop_manager():
    #terminate workers
    instances = get_all_targets()
    for instance in instances:
        id = instance['Target']['Id']
        remove_worker(id)        
    #stop the manager
    ec2.instances.filter(InstanceIds=[config.manager_id].stop()   
'''





