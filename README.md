#Beeworker
Beeworker is used with the [Beekeeper](https://github.com/jchin1968/beeworker) command line
interface (CLI) for running PHP Behat tests on a cluster of AWS EC2 instances. Each instance will
run a beeworker which will poll an AWS SQS queue for Behat tests to execute and then upload the
results to an AWS S3 Bucket for further processing by Beekeeper. 

##Requirements

* Python 2.7
* Git
* AWS credentials (i.e. access id and secret key) with full access to SQS and S3
* Behat running in headless mode. See below for instructions on how to do this. 

## AWS Configuration Files
Beeworker will need to access to the same SQS queue and S3 bucket that were created by Beekeeper.
So, you can use the same credentials here as in Beekeeper.
 
Create the file ~/.aws/credentials with the following:

    [default]
    aws_access_key_id = {your AWS access key id} 
    aws_secret_access_key = {your AWS secret access key}

Create the file ~/.aws/config with the following:

    [default]
    region = {the region the master instance is located in}

Refer to the [Boto 3 Configuration Guide]
(https://boto3.readthedocs.org/en/latest/guide/configuration.html#guide-configuration) for
more information.

## Installing Beeworker
You would install Beeworker on the same machine containing your web application and Behat tests.

If you're installing Beeworker for the first time:

* apt-get install python-pip (if you're on Ubuntu or Debian) 
* yum install python-pip (if you're on RHEL or Centos)
* cd ~
* git clone https://github.com/jchin1968/beeworker
* cd beeworker
* pip install .

To update Beeworker, just cd into the Beeworker source folder, do a git pull and rerun pip-install
with the upgrade option. For example:

* cd ~/beekworker
* git pull
* pip install . --upgrade

## Run Beeworker At Startup 
Use Upstart to automatically run Beeworker at startup. Upstart should already be installed by
default on most current Linux distros.

Create the file /etc/init/beeworker.conf with the following:

    description "Start beeworker as a one-time task"

    start on started phantomjs

    task

    script
        # Wait for apache2 to start. We need to check for an apache process id rather then the more
        # elegant "start on started ..." since apache2 still use the old System 5 init script found
        # in /etc/init.d  
        while [ -z "`pidof apache2`" ]; do
            sleep 1
        done
        exec /usr/local/bin/beeworker
    end script

Note: This assumes you are using phantomjs to run Behat in headless mode and that it has been configured
to run at startup. See below for running Behat in headless mode.
    
#Configuring Headless Behat
The easiest way to run Behat tests on a headless server is to use PhantomJS. On Ubuntu, you can simply install
using apt-get. 

* apt-get update
* apt-get install phantomjs

To have PhantomJS run on startup using Upstart, create the file /etc/init/phantomjs.conf with the following:

    description "Start phantomjs in webdriver mode"
    
    start on runlevel [2345]
    stop on [016] 
    
    exec phantomjs --webdriver=8643    
    
    

In your behat.yml file, you can instruct Behat to use PhantomJS instead of the default Selenium driver like so: 

    ...
    ...
    extensions:
      Behat\MinkExtension:
        ...
        ...
        selenium2:
          wd_host: "http://localhost:8643/wd/hub"
        ...
        ...     