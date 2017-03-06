#!/usr/bin/env python2

import os
import sys

def main():
    if os.getuid() != 0:
        print('Requires root privileges')
        sys.exit('Exiting installer')

    if (platform.dist()[0] == 'centos'):
        os.system('''
        yum update -y
        yum install -y git curl
        ''')
    elif (platform.dist()[0] == 'Ubuntu'):
        os.system('''
        apt-get update -y
        apt-get install -y git curl
        ''')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')

    os.system('''
    curl -L https://bootstrap.pypa.io/get-pip.py | python2.7
    git clone https://github.com/jamrizzi/bird.git
    pip install future
    pip install ipgetter
    ''')

    if sys.argv[1] == 'master':
        os.system('python2 ./bird/src/master.py')
    elif sys.argv[1] == 'master':
        os.system('python2 ./bird/src/master.py')

    os.system('rm -rf ./bird')

main()
