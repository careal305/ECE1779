Contributor (Equal Contribution): 
Dongqing Zhu 
Yao Wang 
Xinyi Yuan



# A2
ece1779 assignment2
Achieved Requirements:
1. Manually add/delete worker
2. Worker numbers chart(Healthy host count)
3. For each worker: details, cpu utilization chart
4. Display load balanced user-app entry url
5. Initia.py: initialize the worker pool size to 1 once the manager-app starts, only run once when manager starts


Doing now:
1. auto-scaling.py(test it manually, seems good)
2. Stop the manager(Not tested yet)

To do list:
1. Terminate all workers
2. Documents, Results(auto-scaling)

HTTP requests received by each worker:
1. Having problem in cloudwatch custome metrics.
2. Create a table in the database to record the http requests
3. Can create graph without cloudwatch custome metrics

!!!!
It takes about 7min from launching an instance to registering it successfully to the target group(healthy). So the if condition in get_all_targets is '!= draining' in case the auto-scaling falls in unreliable algorithm(ref: ece1779a2.pdf-requirements-8). :|

https://utoronto.zoom.us/rec/share/bJGqDzkIQgVKwZzsSyhJQNRt8Cb6UEXmHmCoJnBbEO1ZK5IHHi-0_NEMWnbxch3X._NlUAUHnIuNKfJM6?startTime=1602094724000





