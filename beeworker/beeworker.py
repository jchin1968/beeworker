import os
import boto3
import json
import requests
import subprocess
import time

def work():
    """Beeworker instance main executable. Fetch tasks from SQS queue, run Behat tests and
    upload results to S3 bucket"""

    # Read user meta data which contain the SQS task url, the S3 result bucket and behat folder.
    # Exit if user meta data does not exists. This would occur when the master instance starts up.
    # Worker instances would have user meta data set by beekeeper
    url = 'http://169.254.169.254/latest/user-data/'
    response = requests.get(url)
    if response.status_code != 200:
        exit()

    # Extract user meta data into a list
    json_text = response.text
    user_data = json.loads(json_text)

    # Instantiate S3 client and initialize some variables
    s3_client = boto3.client('s3')
    bucket_name = user_data['s3_result_bucket_name']
    behat_project_folder = user_data['behat_project_folder']
    auto_shutdown = user_data['auto_shutdown']
    timeout = float(user_data['timeout'])
    log = open('/tmp/beeworker.log', 'w', 1)        # 1 = line buffering

    # Check SQS task queue for messages
    sqs_client = boto3.client('sqs')
    message_available = True
    while message_available:
        # Retrieve only 1 task at a time, allow up to the timeout period for a task to complete
        # wait up to 20 seconds when retrieving a task
        response = sqs_client.receive_message(
            QueueUrl=user_data['sqs_task_queue_url'],
            MaxNumberOfMessages=1,
            VisibilityTimeout=int(timeout),
            WaitTimeSeconds=20
        )

        if 'Messages' in response:
            # Task is available
            receipt_handle = response['Messages'][0]['ReceiptHandle']
            task_name = response['Messages'][0]['Body']
            log.write('Working on task %s\n' % task_name)

            # Go to the Behat project folder and execute a test
            behat_feature_file = 'features/' + task_name
            result_file = '/tmp/' + task_name + '.result'

            os.chdir(behat_project_folder)
            job = subprocess.Popen(['/usr/local/bin/behat', '-o', result_file, behat_feature_file])
            start_time = time.time()
            elapsed_time = 0.0
            job_status = None

            # Monitor the progress of the job.
            while job_status == None and elapsed_time < timeout:
                job_status = job.poll()
                elapsed_time = time.time() - start_time
                time.sleep(1)

            if elapsed_time > timeout:
                # Kill the job since it seems the job has hung which does happen with phantomjs for
                # no apparent reason. Note: when the job is killed, AWS SQS VisibilityTimeout
                # will also expire and the job is placed back into the SQS task queue
                job.kill()
                log.write('job %s exceeded the %d second timeout and was killed\n'
                    % (task_name, int(timeout)))

            if job_status != None:
                # Job completed. Send result to the S3 result bucket
                response = s3_client.upload_file(result_file, bucket_name, task_name + '.result')

                # Delete task from task queue
                response = sqs_client.delete_message(
                    QueueUrl=user_data['sqs_task_queue_url'],
                    ReceiptHandle=receipt_handle
                )

                log.write('job %s completed\n' % task_name)
        else:
            # No more messages. Shutdown the system in 2 minutes
            log.write('No more tasks available\n')
            message_available = False
            if auto_shutdown:
                log.write('Shutting down\n')
                os.system("sudo shutdown -h 2")
            else:
                log.write('Auto shutdown disabled\n')