# CSAP Bot and Cron Job Repository

<img src="https://user-images.githubusercontent.com/11940172/28176943-29f562c0-67c7-11e7-97c4-c5984623cf1b.jpg" width="600">

This repository contains the code for the following projects.

### CSAP Cron Job `csap-cron`

#### Outline
The CSAP cron job runs hourly to poll the Canvas LMS platform for updates to upcoming CSAP sections. If the section falls within a given threshold in the future, the script will create rooms in the appropriate teams for each section and invite the appropriate team members to each group. It also posts updates of each action on the **CSAP Bot Development** Spark room.

#### File Structure
```
.
├── poll-canvas.py          # The script that runs hourly as a cron job
└── poll-canvas.log         # The output of the poll-canvas.py, stored as a log for future reference
```

### CSAP Spark Bot `csap-bot`

#### Outline
The Spark bot serves as an automated assistant for CSAP classes. It currently responds to the following commands.

**`/question`**<br>
Stores the provided question into a question bank for the room. Each room (and section) will have a unique question bank.

**`/list`**<br>
Lists all the questions that are currently in the question bank, along with the name of the person who asked the question.

**`/group`**<br>
Randomly assigns all the members in the room to groups, based on the provided number of people in each group.

**`/pick`**<br>
Randomly picks a single person from the room.

**`/roster`**<br>
Lists all the members currently in the room.

#### File Structure
```
.
├── botenv                  # The virtual environment for running the bot as a gunicorn process
│   ├── ...          
├── app.py                  # Sets up the Flask app for serving the webhook, and the responses to the various commands
├── wsgi.py                 # Create the application object to hook the app onto gunicorn
├── log.file                # Log file for the gunicorn process, useful for debugging purposes
└── process.pid             # Contains the process ID for the currently running gunicorn process, which can be used to easily kill the process
```

### CSAP Data `csap-data`

#### Outline
This directory is a temporary data storage for the bot and cron job. We should potentially move this to a thread-safe database in the future if the application is scaled (however there is no immediate need to do so).

#### File Structure
```
.
├── config.py               # Contains the IDs for the CSAP bot and the security bot
├── created.csv             # A list of all the created rooms, which is checked before room creation to prevent duplicate rooms from being created
├── instructors.csv         # A list of all the instructors with their Cisco IDs, first and last names, and emails
├── questions               # This directory contains the question bank for each room (the file name is the room ID), which stores questions when `/question` is invoked with the bot
│   ├── Y2lzY29zcGFyazovL3VzL1JPT00vMzFmMzdjMzAtNWQxMC0xMWU3LTllN2MtOTNkMzMwMjYxMjI4.csv
│   ├── ... 
└── teams.csv               # Contains the team IDs for each of the created teams, which is retrieved when inviting the person to the appropriate team and room
```

### Useful Unix Commands

`$ sudo ssh -i instance-keypair.pem ec2-user@ec2-13-58-221-119.us-east-2.compute.amazonaws.com`
Log on to the EC2 instance via SSH.

`$ source /home/ec2-user/csap/csap-bot/botenv/bin/activate`
Activate the *botenv* virtual environment for testing the bot manually.

`$ gunicorn --bind 0.0.0.0:8000 /home/ec2-user/csap/csap-bot/wsgi:app -D --pid /home/ec2-user/csap/csap-bot/process.pid`
Manually launch the gunicorn process to serve the Flask app.
