import sys
import os
import platform
from builtins import input

class Helper:
    def prepare(self):
        if (platform.dist()[0] == 'centos'):
            os.system('''
            yum clean all
            rpm --rebuilddb
            yum update -y
            ''')
        elif (platform.dist()[0] == 'Ubuntu'):
            os.system('''
            apt-get update -y
            ''')
        else:
            print('Operating system not supported')
            sys.exit('Exiting installer')

    def is_root(self):
        if os.getuid() != 0:
            print('Requires root privileges')
            sys.exit('Exiting installer')

    def default_prompt(self, name, fallback):
        message = name + ': '
        if fallback != '':
            message = name + ' (' + fallback + '): '
        response = input(message)
        assert isinstance(response, str)
        if (response):
            return response
        else:
            return fallback

    def mount(self, mount_from, mount_to):
        os.system('mkdir -p ' + mount_to)
        if mount_from != 'local':
            if mount_from[:4] == '/dev':
                os.system('''
                mkfs.xfs ''' + mount_from + '''
                echo "''' + mount_from + ' ' +  mount_to + ''' xfs defaults 0 2" | tee -a /etc/fstab
                mount -a && mount
                ''')
            else:
                os.system('''
                echo "''' + mount_from + ' ' + mount_to + ''' nfs auto 0 2" | tee -a /etc/fstab
                mount -a && mount
                chmod 777 ''' +  mount_to + '''
                ''')
