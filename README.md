# Hacker News Story Submitter

This script will submit a new story to Hacker News. It can be used to submit
a story at the peak time for Hacker News submissions and, as such, it is meant
to be used in conjunction with a job scheduler, such as cron or atrun.

The reason for this script can be found in [this article][2]. In the article, Hacker News data is examined to determine the very best time to post to Hacker News to get the most views. Incidentally, the best time to post to Hacker News appears to be right around **9AM to 10AM** Eastern Standard Time.

## Installing the script

Basically, you just need to download the source and install all of the requirements, which at this point in time is just the [requests][1] library.

    $ git clone https://github.com/croach/hn_submitter.git
    $ cd hn_submitter
    $ pip install -r requirements.txt

## Scheduling a story

To schedule a one off story submission using the at command on OS X, you'll
first need to enable atrun which is disabled by default on OS X systems. To
enable atrun, run the following command (which can be found in the manpage for
atrun):

    $ sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.atrun.plist

Once atrun has been enabled, a new job can be scheduled by creating a job
script which is a simple shell script that sets up the appropriate environment
variables and then runs the hn_submitter.py script. Then the file can be
scheduled to run using the at command's -f option to pass in the name of the
script. An example can be seen below:

    #!/bin/sh
    # story.sh

    export HN_SUBMITTER_STORY_TITLE="Some Story's Title"
    export HN_SUBMITTER_STORY_URL="http://somedomain.com/sample/story"
    export HN_SUBMITTER_USERNAME="username"
    export HN_SUBMITTER_PASSWORD="password"

    # NB: Make sure you redirect stdout to the log file before you redirect
    # stderr to stdout. Otherwise, if there's an error, it gets sent to stdout
    # before stdout is redirected to the log file and we lose all of the error
    # information.
    /virtualenv/bin/python hn_submitter.py >> /path/to/log 2>&1

Note: By giving the full path to the python executable, you can choose the
python executable associated with a specific virtualenv which will make the
hn_submitter.py script run as if you had first activated that virtualenv.

To schedule the job, for example tomorrow at 8am, you just need to call the
following commands:

    $ chmod +x story.sh
    $ at -f story.sh 8am tomorrow
    
### Prevent Sleep
Sadly the cron job will not execute if you system goes to sleep. One way to prevent sleep on OSX is to use `caffeinate`.
To prevent OSX from sleeping for the next 24 hours run `caffeinate -t 864000 &`.

## To Do

1. Get rid of the dependency on [requests][1], so a virtualenv is not needed to run this script.


[1]: http://docs.python-requests.org/en/latest/
[2]: http://nathanael.hevenet.com/the-best-time-to-post-on-hacker-news-a-comprehensive-answer/
