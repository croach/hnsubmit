"""
This script will submit a new story to Hacker News. It can be used to submit
a story at the peak time for Hacker News submissions and, as such, it is meant
to be used in conjunction with a job scheduler, such as cron or atrun.

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
"""

import os
import sys
import re
import urlparse

import requests

HN_URL = 'https://news.ycombinator.com'

def get_homepage(s):
    # Retrieve the Hacker News homepage
    res = s.get(HN_URL)
    if res.status_code != 200:
        raise Exception('Could not reach the Hacker News homepage')
    homepage = res.content
    return homepage

def parse(regex, content, name=None):
    """Returns the first item that matches regex in the content

    Attempts to parse out some data from content with the given regular
    expression. If succesful, it returns the first instance of it, otherwise,
    it raises an exception. The exception can have a generic message based on
    the given regular expression or something more specific if the name param
    is set.
    """
    match = re.search(regex, content)
    if not match:
        if name:
            raise Exception('Could not find %s' % name)
        else:
            raise Exception("Could not find anything matching the regular expression '%s'" % regex)
    return match.groups()[0]
    return urlparse.urljoin(HN_URL, match.groups()[0])

def parse_url(regex, content, name=None):
    """Returns a URL based on the given regular expression

    Attempts to parse out the filepath portion of the URL from the content
    using the regex. If successful, the filepath is combined with base URL
    (i.e., the Hacker News homepage URL) and returned. Otherwise, an exception
    is raised
    """
    relative_url = parse(regex, content, name=name)
    return urlparse.urljoin(HN_URL, relative_url)

def parse_fnid(content):
    """Parses out and returns the fnid value from the given content
    """
    regex = r'<input type=hidden name="fnid" value="([^\"]+)">'
    return parse(regex, content, name="fnid")

def login(s, username, password):
    """Logs the user into Hacker News with the given credentials

        Arguments:
    s -- the current requests.Session object
    username -- Hacker News account username
    password -- Hacker News account password
    """
    homepage = get_homepage(s)
    login_url = parse_url('<a href="([^\"]+)">login</a>', homepage, name='Login form URL')

    # Login to HN
    res = s.get(login_url)
    loginpage = res.content
    login_submission_url = parse_url('<form method=post action="([^\"]+)">', loginpage, name='Login Submission URL')
    fnid = parse_fnid(loginpage)
    payload = {'u': username, 'p': password, 'fnid': fnid}
    res = s.post(login_submission_url, data=payload)
    if res.status_code != 200:
        raise Exception('Could not login to the Hacker News')

def submit_story(s, title, url):
    """Submits the story to Hacker News

    Arguments:
    s -- the current requests.Session object
    title -- the tile of the story
    url -- the URL for the story

    Returns a tuple representing the success/failure of the submission.
    """
    # Submit the story
    story_url = urlparse.urljoin(HN_URL, '/submit')
    res = s.get(story_url)
    if res.status_code != 200:
        raise Exception('Could not retrieve the Story Submission form page')
    storypage = res.content
    fnid = parse_fnid(storypage)
    story_submission_url = parse_url('<form method=post action="([^\"]+)">', storypage, name='Story Submission URL')
    payload = {'t': title, 'u': url, 'fnid': fnid}
    res = s.post(story_submission_url, data=payload)
    if res.status_code != 200:
        raise Exception('Could not submit the story')

    # Make sure the story submission was succesful by checking the title of
    # the response page. If it was "New Links", the submission was a success.
    # Otherwise, print out the resultant HTML, so that this script can be
    # updated with other options.
    page_title = re.search(r'<title>([^|]+)| Hacker News</title>', res.content).groups()[0].strip()
    if page_title == 'New Links':
        success = True
        message = 'Story Submission Success!'
    elif page_title == title:
        matches = re.search(r'<a href="(?P<url>user\?id=(?P<user>[^\"]+))">', res.content)
        user = matches.group('user')
        user_url = urlparse.urljoin(HN_URL, matches.group('url'))
        success = True
        message = 'The story has already been submitted by %s (%s)' % (user, user_url)
    else:
        success = False
        message = 'There was an error submitting the story\n\n%s' % res.content
    return (success, message)

def main(title, url, username, password):
    s = requests.Session()
    login(s, username, password)
    success, message = submit_story(s, title, url)
    s.close()
    if success:
        print message
    else:
        print >>sys.stderr, message


if __name__ == '__main__':
    title = os.environ['HN_SUBMITTER_STORY_TITLE']
    url = os.environ['HN_SUBMITTER_STORY_URL']
    username = os.environ['HN_SUBMITTER_USERNAME']
    password = os.environ['HN_SUBMITTER_PASSWORD']
    main(title, url, username, password)

