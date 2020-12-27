
import os
instances = ec2.instances.all()
for i in instances:
	instance_id = i.id
	command1 = "aws cloudwatch put-metric-data --metric-name HTTP_Requests --dimensions Instance="
	command2 = "  --namespace "HTTP_Requests" --value $(netstat -an | grep 80 | wc -l)"
	command = command1 + instance_id + command2
	run = os.system(command)
