#!/usr/bin/python

import argparse
import os
import re
import requests
import subprocess
import sys
import tempfile

verify_ssl = False

# Path to java web start executable
JAVAWS='/usr/bin/javaws'

def main():
    # Parse command-line arguments 
    parser = argparse.ArgumentParser(description='Start remote graphical'
                                                 ' console session')
    parser.add_argument('--hostname', '-i', dest='hostname', required=True,
                        help='Hostname or IP address of BMC')
    parser.add_argument('--username', '-u', dest='username', default='root',
                        help='Username for logging into BMC')
    parser.add_argument('--password', '-p', dest='password', default='root',
                        help='Password for logging into BMC')
    parser.add_argument('--javaws', '-j', dest='javaws', default=JAVAWS,
                        help='Path to Java webstart executable '
                             '(defaults to %s)' % JAVAWS)

    args = parser.parse_args()

    login_url = 'https://%s/rpc/WEBSES/create.asp' % args.hostname
    jnlp_url = 'https://%s/Java/jviewer.jnlp' % args.hostname

    sess = setup_session(args.username, args.password, login_url)
    jnlp_file = write_jnlp(sess, jnlp_url)

    subprocess.call([JAVAWS, jnlp_file])

    # todo: trap signals and clean up
    os.unlink(jnlp_file)

def setup_session(username, password, login_url):

    # Setup our session
    sess = requests.Session()

    # Setup our post data
    login_data = {
        'WEBVAR_USERNAME': username,
        'WEBVAR_PASSWORD': password
    }

    # Make request
    response = sess.post(login_url, login_data, verify=verify_ssl)


    ##
    ## We don't receive valid JSON back, so use regex to extract session cookie
    ##

    string = response.content.replace('\n', '')
    m=re.match(".*'SESSION_COOKIE' : '([^']+)", string)

    if m:
        SESSION_COOKIE = m.group(1)
        print "Receieved session cookie: %s" % SESSION_COOKIE
        sess.headers['Cookie'] = "SessionCookie=%s" % SESSION_COOKIE
    else:
        raise Exception("Unable to retrieve session cookie.\nResponse was: %s" %
                        response.content)

    return sess


def write_jnlp(session, jnlp_url):
    ## Fetch the JNLP file
    response = session.get(jnlp_url, verify = verify_ssl)

    fd = tempfile.mkstemp(suffix='.jnlp')
    jnlp_file = fd[1]

    print "Writing to: %s" % jnlp_file
    os.write(fd[0], response.content)
    
    return jnlp_file

if __name__ == '__main__':
    main()
