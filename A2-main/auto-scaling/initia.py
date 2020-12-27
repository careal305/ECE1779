# Start this file once only when the manager starts
# Resize the worker pool to 1
import boto3

ELB = boto3.client('elbv2')
ec2 = boto3.resource('ec2')
EC2 = boto3.client('ec2')

def get_stopped_targets():
    # Get all the register targets(the workers that are registered with the elb[include initial, healthy, unused])
    target_group = ELB.describe_target_health(TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:327200236258:targetgroup/ece1779a2user/da2f671e55d83fc0')
    instances = []
    if target_group['TargetHealthDescriptions']:
        for target in target_group['TargetHealthDescriptions']:
            if target['TargetHealth']['State'] == 'unused': # targets that are in the stopped state
                instances.append(target)
    return instances

def remove_worker(id):
    target = [{'Id': id,
               'Port': 5000}]
    ELB.deregister_targets(TargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:327200236258:targetgroup/ece1779a2user/da2f671e55d83fc0', Targets=target)
    ec2.instances.filter(InstanceIds=[id]).terminate()

def init():
    stopped_instances = get_stopped_targets()
    if len(stopped_instances) > 1:
        #terminate all the other instances, only keep one instance
        one_instance_id = stopped_instances[0]['Target']['Id']
        for instance in stopped_instances:
            id = instance['Target']['Id']
            if id != one_instance_id:
                remove_worker(id)
            else:
                EC2.start_instances(InstanceIds=[one_instance_id])
    elif len(stopped_instances) == 1:
        id = stopped_instances[0]['Target']['Id']
        EC2.start_instances(InstanceIds=[id])

if __name__ == "__main__":
    init()


