# NTC and Arista Capstone Project (2023)

This project seeks to achieve a degree of network automation and Source of Truth by using Nautobot in conjunction with Ansible Playbooks and ChatOps.
Using Zabbix, we are able to query the devices for key pieces of information, with changes then being deployed idempotently from an Ansible Playbook for maximum efficiency.


## Table of Contents
[Google Cloud](https://github.com/KadeSherry/Capstone2023/edit/main/README.md#google-cloud) 

[Plugins](https://github.com/KadeSherry/Capstone2023/edit/main/README.md#plugins)

[Slack Tokens](https://github.com/KadeSherry/Capstone2023/edit/main/README.md#obtaining-slack-tokens)

[Connecting GitHub to Nautobot](https://github.com/KadeSherry/Capstone2023/edit/main/README.md#connecting-github-to-nautobot)

[Modifying Permissions](https://github.com/KadeSherry/Capstone2023/edit/main/README.md#modify-permissions)

[Installing the Nautobot Server](https://github.com/KadeSherry/Capstone2023/edit/main/README.md#installing-the-nautobot-server)

[Installing the Zabbix Server](https://github.com/KadeSherry/Capstone2023/edit/main/README.md#installing-the-zabbix-server)

[Setting Up Devices for Telementry/Zabbix Use](https://github.com/KadeSherry/Capstone2023/edit/main/README.md#setting-up-devices-for-telementryzabbix-use)

[Ansible](https://github.com/KadeSherry/Capstone2023/edit/main/README.md#ansible)

[Creating Docker Container](https://github.com/KadeSherry/Capstone2023/edit/main/README.md#creating-docker-container)

[Running the Files](https://github.com/KadeSherry/Capstone2023/edit/main/README.md#running-the-files)


## Getting Started (What we did)

### Google Cloud
We chose to use the Google Cloud Platform to host our VMs and containers due to ease of use and flexibility
-	We used the free subscription option found __[here](cloud.google.com)__
-	Enable Compute Engine API (*under Compute Engine > VM Instances*)
-	Select a close region, select the e2-standard-8 machine type
-	Set up bootdisk with Ubuntu with a zize of 20GB
-	Make sure you allow HTTP and HTTPS traffic
After that, Google Cloud was ready for hosting and we moved onto ContainerLab
ContainerLab acts as our test environment to simulate and manage our switches & other devices (also supports cEOS instances). To deploy:
-	Run this script to install docker ono the Linux VM:
```bash
bash -c "$(curl http://www.packetanglers.com/installdocker.sh)"
```
-	Download the cEOS Image and import it:
```bash
curl http://www.packetanglers.com/images/cEOS-lab-4.29.1F.tar.xz -o cEOS-lab-4.29.1F.tar.xz
docker import cEOS-lab-4.29.1F.tar.xz ceos:4.29.1F
```
-	Install ContainerLab:
```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
```
-	Clone the Example L2LS ContainerLab Topology Repo into the GCP instance:
```bash
git clone https://github.com/PacketAnglers/containerlab.git
```
-	Start Container Lab:
```bash
sudo clab deploy -t containerlab/topologies/L2LS/L2LS.yaml --reconfigure
```
-	Connect to ContainerLab:
http://< *VM public ip* >/graphite

### Plugins
Next, we need to install the proper plugins to complete our goals. The plugins are ChatOps for automating routine tasks, Golden Configuration to create a stable point that resists errors and misconfigurations, and Single Source of Truth (SSOT) for centralized management and storage.
-	Perform the following commands on the nautobot container and worker container:
```bash
pip install nautobot-plugin-nornir
pip install nautobot-golden-config
pip install nautobot-chatops
pip install nautobot-ssot
```
-	Add each plugin to the local_requirments.txt file:
```bash
echo nautobot-plugin-nornir >> local_requirements.txt
echo nautobot-golden-config >> local_requirements.txt
echo nautobot-chatops >> local_requirements.txt
echo nautobot-ssot >> local_requirements.txt
```
-	Open the nautobot_config.py file and add the following in the “plugin” section:
```python
PLUGINS = ["nautobot_ssot", "nautobot_plugin_nornir", "nautobot_golden_config", "nautobot_chatops"]
 
PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
        "use_config_context": {"secrets": False, "connection_options": True},
        # Optionally set global connection options.
        "connection_options": {
            "napalm": {
                "extras": {
                    "optional_args": {"global_delay_factor": 1},
                },
            },
            "netmiko": {
                "extras": {
                    "global_delay_factor": 1,
                },
            },
        },
        "nornir_settings": {
            "credentials": "nautobot_plugin_nornir.plugins.credentials.settings_vars.CredentialsSettingsVars",
            "runner": {
                "plugin": "threaded",
                "options": {
                    "num_workers": 20,
                },
            },
        },
        "username": #ADD SWITCH USERNAME HERE,
        "password": #ADD SWITCH PASSWORD HERE,
    },
    "nautobot_golden_config": {
        "per_feature_bar_width": 0.15,
        "per_feature_width": 13,
        "per_feature_height": 4,
        "enable_backup": True,
        "enable_compliance": True,
        "enable_intended": True,
        "enable_sotagg": True,
        "sot_agg_transposer": None,
        "enable_postprocessing": False,
        "postprocessing_callables": [],
        "postprocessing_subscribed": [],
        "platform_slug_map": None,
        # "get_custom_compliance": "my.custom_compliance.func"
    },
    "nautobot_chatops": {
        "enable_slack": True,
        "slack_api_token": #ADD SLACK API TOKEN HERE,
        "slack_app_token": #ADD SLACK APP TOKEN HERE,
        "slack_signing_secret": #ADD SLACK SIGNING SECRET HERE,
        "slack_slash_command_prefix": "/",
    }
```
### Obtaining Slack tokens:
-	Log in to __[slack](https://api.slack.com/apps)__ and select "Create New App". Select "From an app manifest."
-	Select the Slack Workspace you want your app to reside in.
-	In the window titled "Enter app manifest below," select the "YAML" formatting tab and copy/paste the contents of file nautobot_slack_manifest.yml from this repo. Update the below settings, then click Next.
-	On line 34, update socket_mode_enabled to true
-	Review the settings on the next window and click Create.
-	On the General > Basic Information page, note the Signing Secret near the bottom, under App Credentials. Put this in for the variable slack_signing_secret
-	On this same Basic Information page, select Install to Workspace. Select a channel to allow the app to post to (e.g. #general), and click Allow.
-	Under Settings > Basic Information, scroll down to section "App-Level Tokens" and click Generate Token and Scopes to generate an API token.
-	Token Name: This can be anything you want.
-	Scopes: Click Add Scope and select the option connections:write.
-	Click Generate. Copy this API token. Put this in for the variable slack_app_token
-	Under Settings > Install App, copy the Bot User OAuth Token here. Put this in for the variable slack_api_token
-	Restart the containers:
```bash
sudo docker restart <container-name>
```
-	In the Nautobot container, start the slack socke with the following commands:
```bash
nautobot-server start_slack_socket &
```
### Connecting Github to Nautobot
Next, we must connect Nautobot to Github to ensure we have version control and allow tracking of changes:
-	Create a GitHub account, then go to profile and select “Your Repositories:”
-	Click New
-	Name your repository and click “Create repository”
-	Now create a token for Nautobot to access the repository
-	Click your profile > Settings
-	Click Developer settings
-	Click Personal access tokens > Fine-grained tokens
-	Click Generate new token
-	Name the token, set an expiration date, and select the repository you made before to access.
-	Copy the token and go back to nautobot
-	In the VM, create two files, githubuser.txt and githubpass.txt
```bash
sudo nano githubuser.txt
```
-	Enter your Github username
```bash
sudo nano githubpass.txt
```
-	Enter your Github token
-	Copy these files to both containers
```bash
sudo docker cp githubuser.txt <container-name>:/opt/nautobot
```
-	In Nautobot, go to Secrets > Secrets
-	Click Add
-	Give the secret a name like GithubUser
-	Change the provider from Environment Variable to Text File
-	Enter the filepath of the githubuser.txt file
-	Repeat steps 9-12 for the GitHub token
-	In Nautobot, go to Secrets > Secret Groups
-	Give it a name like GithubSecretGroup
-	Under Secret Assignment, set the following secrets:

 ![image](https://user-images.githubusercontent.com/45835613/231946088-bf706ed0-bbb1-47f7-9de1-722868dd3e08.png)

-	Next, click Extensibility > Git Repositories
-	Click Add
-	Give the git repository a name and the URL of the GitHub repository
-	Select the secrets group created earlier
-	Your GitHub repository should now be connected to Nautobot!

### Modify Permissions
Next, we need to ensure that everyone is able to use it by modifying the associated permissions. This is a safety feature, to ensure that users only send what they are allowed to. The following example allows any user to send any commands, and should be modified to fit your specific project.
-	In Nautobot, go to Plugins > Nautobot ChatOps > Access Grants
-	Click Add
-	In command and subcommand, enter a *
-	Choose organization for the grant type
-	Put in the name of the Slack workspace that the app is on
-	Click Create and Add Another
-	In command and subcommand, enter a *
-	Choose channel for the grant type
-	Put in the name of the Slack channel the app should be on
-	Click Create and Add Another
-	In command and subcommand, enter a *
-	Choose user for the grant type
-	Put in the name of the Slack user that should be allowed to send commands
-	Click Create
-	Your user should now be able to send nautobot commands in the channel and workspace you selected

### Installing the Nautobot Server
Once that’s done, it is time to install the Nautobot server. We chose to use a Docker Container on our Ubuntu 18 VM that is hosted on our Google Cloud. To install Docker:
-	Run system package updates to get the latest versions. Install ca-certificates, curl and gnupg:
```bash
sudo apt-get update && sudo apt-get install \ ca-certificates \ curl \ gnupg
```
-	The next step is to add dockers GPG key to the system so the package updater can verify the docker server package:
```bash
sudo mkdir -m 0755 -p /etc/apt/keyrings && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```
-	Next you must setup the repo used to download docker:
```bash
echo \ "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \ "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
-	Finally, install the docker engine:
```bash
sudo apt-get update && sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
Now that Docker has been installed, we can install Nautobot with Docker’s Compose feature. We used the official docker compose image for nautobot, which can be found at __[here](https://github.com/nautobot/nautobot-docker-compose)__.
-	Clone docker compose file from GIT:
```bash
git clone https://github.com/nautobot/nautobot-docker-compose.git
```
-	Navigate to the following folder:
```bash
cd nautobot-docker-compose
```
-	Make a copy of the local.env.example file:
```bash
cp local.env.example local.env
```
-	Edit the local.env file and make the appropriate changes:
```bash
vi local.env
```
-	Note, you may need to change the web address port settings if you have more than one webserver running, in our case we choose :8080

 ![image](https://user-images.githubusercontent.com/45835613/231946184-c35dc3fe-b4e8-4c03-b143-a393dc0777b4.png)

-	Then run the docker compose command to create the docker containers based on the settings we laid out:
```bash
docker-compose up
```

Now that the Docker Container is up and running, we need to setup an admin account using the terminal commands for Nautobot, because by default there is no account setup to log into the web page. To do that:
-	Verify the docker containers are running:
```bash
docker container ls
```
-	Execute the shell on the nautobot container to “remote” in to the docker container and be able to run commands:
```bash
docker exec -it container name here bash
```
-	Create an admin super user:
```bash
nautobot-server createsuperuser
```
-	Fill in the prompts it gives you such as the username, password and email address. 
-	After the user is created you should be able to log into the webpage for nautobot:

 ![image](https://user-images.githubusercontent.com/45835613/231946221-b1d475f9-1cf8-45cc-b608-b97dddfc8345.png)

### Installing the Zabbix Server
Our next step is to install the Zabbix Server that we are using as our telemetry solution (We used Zabbix version 6.0 on ubuntu 18.04 using mySQL and apache2). To install the Zabbix server, perform the following steps:
-	The first step is to install the Zabbix repository:
```bash
wget https://repo.zabbix.com/zabbix/6.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.0-4+ubuntu18.04_all.deb 
dpkg -i zabbix-release_6.0-4+ubuntu18.04_all.deb 
apt update
```
-	Next, install Zabbix and its required plugins:
```bash
apt install zabbix-server-mysql zabbix-frontend-php zabbix-apache-conf zabbix-sql-scripts zabbix-agent
```
-	Using the mySQL server console, create the initial database that Zabbix will populate:
```bash
mysql -uroot -p create database zabbix character set utf8mb4 collate utf8mb4_bin; create user zabbix@localhost identified by 'password'; grant all privileges on zabbix.* to zabbix@localhost; set global log_bin_trust_function_creators = 1; quit;
```
-	Next using a prebuilt file, install the Zabbix default database into the blank one we just created:
```bash
zcat /usr/share/zabbix-sql-scripts/mysql/server.sql.gz | mysql --default-character-set=utf8mb4 -uzabbix -p zabbix 
```
-	Disable the special log bin trust option:
```bash
mysql -uroot -p set global log_bin_trust_function_creators = 0; quit; 
```
-	Edit the Zabbix server config file found at /etc/zabbix/zabbix_server.conf 
-	Make changes as necessary, we needed to change our default port information and change the default password used for the Zabbix database. 
-	We then needed to change the default ports that apache2 web server was running on:
```bash
sudo vi /etc/apache2/sites-available/000-default.conf
```
-	Finally restart the Zabbix server and apache2 processes and go to the web address X.X.X.X:8800/Zabbix and login using the default credentials:
```bash
sudo systemctl restart zabbix-server zabbix-agent apache2
sudo systemctl enable zabbix-server zabbix-agent apache2
```

### Setting Up Devices for Telementry/Zabbix Use
Now that the Zabbix Server has been installed, we need to make sure that we can actually pull data from the devices. To do this, we need to add SNMP v3 and Zabbix Agents. The agents should be installed on the main VM that is hosting the docker containers, whereas SNMPv3 will need to be used on each device. They are already installed on Zabbix, but we need to make sure that each device has a community string and a username and password for SNMP to work:
-	Go to configuration > Hosts 
-	Click create host in the top corner. 
-	Give the device a host name, template and group. 
-	Click the Add button near the interface and select SNMP
-	Fill in either the device DNS name or the IP address.
-	Then choose the SNMP version. For us we used SNMPv3.
-	Fill in the required security info such as the name, access level, and the authentication code set on each device. 
-	Click on the top Macros tab and enter in the SNMP community string. Ours being capstone.
-	Continue to add in all your remaining devices. 
-	Then log into the network devices to configure the SNMP server settings. 
-	For our devices we entered the following commands to enable the SNMP server and allow the traffic over our management network:
```bash
snmp-server community capstone
snmp-server vrf MGMT
```
-	Once this configuration is complete on each device, Zabbix should start reporting there is data flowing. 

Next we need to install an agent on the unbuntu server with docker. 
-	First, install the docker template from the Zabbix website, found __[here](https://www.zabbix.com/integrations/docker)__ (we chose to use version 6)
-	Then, Go to configuration > templates
-	Click on import at the top corner. 
-	Browse to the location of where you downloaded the template. 
-	Click import 

Once we have the docker template file, we can install the Zabbix agent onto the machine that has docker running:
-	Run:
```bash
sudo apt install Zabbix agent
```
-	Edit the Zabbix agent settings file:
```bash
sudo vi /etc/Zabbix/Zabbix_agentd.conf
```
-	Change the server and hostname fields
-	Restart the Zabbix agent:
```bash
sudo systemctl restart Zabbix-agent
```
-	Create a host in Zabbix using the newly added template for docker and using the Zabbix agent interface option. 
After all of this you should have a host’s screen that looks like this:
 ![image](https://user-images.githubusercontent.com/45835613/231945825-1156b1fc-90fd-494c-83ad-128a9d55831a.png)


### Ansible
## Creating Docker Container
This section goes over the process of creating a Docker container for rining the Ansible Dynamic Inventory and Playbooks.
This is so you can have your Ansible materials segmented from the container that Nautobot is running on, but still be able to query Nautobot for the required information like hostname and IP address.

- Install Docker onto your machine with the below commands, starting by updating the machine you’re putting Docker on.
```bash
sudo apt-get update
sudo apt install docker.io -y
```
- To verify that Docker was installed run the command “docker -version”. If Docker installed successfully you will see the Docker version in the command line.
![image](https://user-images.githubusercontent.com/45835613/236310212-a407870c-0106-4135-8828-9fe839cafd13.png)
- Next, you want to create a Docker container image for building your Docker container. The below code is what we included in our file but if you have other requirements that we did not include you can add them to the file as well:
```bash
FROM ubuntu:18.04
	
ENV DEBIAN_FRONTEND=noninteractive
	
RUN apt-get update && \
apt-get install python3-pip -y && \
pip3 install --upgrade pip && \
pip3 install --upgrade virtualenv && \
pip3 install ansible && \
ansible-galaxy collection install networktocode.nautobot
```
- Next, build the image for Docker using the directories from your Docker file. Use the below command to build the image.
```bash
docker build -t ansible:host 
```
- Then run the Docker container you created in interactive mode by entering the below command:
```bash
docker run -it ansible
```
- To switch to the Ansible container enter the below command. Replace the “ID” field with your Docker container’s ID or assigned name to switch to it:
```bash
sudo docker exec -it “ID” /bin/bash
```
Note: If you have issues creating a Docker container with the Docker file please see the below method to manually create a container.
- To create a Docker container manually use the below command:
```bash
Docker run -it --name Ansible ubuntu /bin/bash
```
- To install the necessary requirements for Ansible run the below commands:
```bash
apt-get update
apt-get install python3-pip -y
pip3 install --upgrade pip
pip3 install --upgrade virtualenv
pip3 install ansible
ansible-galaxy collection install networktocode.nautobot
apt install vim
apt install sudo
```

## Running the Files
To run the included file, use the following commands:
- Switch to the Ansible container that you created previously:
```bash
sudo docker exec -it ae03d02f6e81 /bin/bash
```
![image](https://user-images.githubusercontent.com/45835613/236314773-1c1ba4ba-9188-4a8f-86af-ccdeb8c442fd.png)

- Change to the directory that contains your Ansible configuration file to run your playbooks from:
```bash
cd Capstone2023/AnsibleCore/
```
![image](https://user-images.githubusercontent.com/45835613/236314732-1c14f69a-acb3-451a-827e-11970ef1b439.png)

- First, run the get_GQL_Inv.yml file to query Nautobot GraphQL for device information like hostname and IP address:
```bash
ansible-playbook GQL_Inv/get_GQL_Inv.yml
```
![image](https://user-images.githubusercontent.com/45835613/236314696-8bb15f71-cf3b-4cff-a788-ad93ba706dc4.png)

- Change to the directory with your device query, outputted device information file, and Python formatting file:
```bash
cd GQL_Inv/
```
![image](https://user-images.githubusercontent.com/45835613/236314638-d3736197-7193-4eb3-ba27-883a045987fc.png)

- After you have changed directories run the python file extract_GQL_IP.py. This file will take the JSON output from the previous command and format it into an inventory.ini file for Ansible to use:
```bash
python3 extract_GQL_IP.py
```
![image](https://user-images.githubusercontent.com/45835613/236314604-a4a92eac-9eab-4d68-b279-c826b21f5ed2.png)

-	Now that you have queried Nautobot GraphQL for device information and it has been formatted into a usable inventory by Ansible use the below commands. These will change you back to the directory with your Ansible configuration file where you can run your plays from.
```bash
cd ..
ansible-playbook -u admin -k playbook.yml
```
![image](https://user-images.githubusercontent.com/45835613/236314561-fc9141b3-cc97-4a59-9ea5-c620a63efb96.png)

Note: Replace “playbook.yml” with the file path of the playbooks that you have created like in the screenshot provided. Additionally, with the ansible-playbook command -u specifies the username to log into the device, and -k prompts the user for a password to log into the device.






