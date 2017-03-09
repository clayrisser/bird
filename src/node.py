#!/usr/bin/env python2

import sys
import socket
import os
import platform
import ipgetter
from helper import Helper
helper = Helper()

def main():
    helper.is_root()
    options = gather_information(get_defaults())
    helper.prepare()
    prepare_system()
    mount_backup(options)
    install_docker()
    increase_max_map_count(options)
    connect_to_rancher(options)
    install_storage_server(options)
    install_client_server(options)

def get_defaults():
    print('Getting external ip . . .')
    defaults = {
        'master_domain': 'cloud.yourdomain.com',
        'node_ip': ipgetter.myip(),
        'registration_token': 'my-rancher-token',
        'storage_service_id': '3',
        'storage_target_id': '301',
        'storage_mount': 'local',
        'max_map_count': '262144'
    }
    return defaults

def gather_information(defaults):
    options = {}
    options['master_domain'] = helper.default_prompt('Master Domain', defaults['master_domain'], True)
    options['node_ip'] = helper.default_prompt('Node IP', defaults['node_ip'], True)
    options['registration_token'] = helper.default_prompt('Registration Token', defaults['registration_token'], True)
    options['storage_service_id'] = helper.default_prompt('Storage Service ID', defaults['storage_service_id'], True)
    options['storage_target_id'] = helper.default_prompt('Storage Target ID', defaults['storage_target_id'], True)
    options['storage_mount'] = helper.default_prompt('Storage Mount', defaults['storage_mount'], True)
    options['backup_mount'] = helper.default_prompt('Backup Mount', socket.gethostbyname(options['master_domain']) + ':/exports/cloud-backup', True)
    options['max_map_count'] = helper.default_prompt('Max Map Count', defaults['max_map_count'], True)
    return options

def prepare_system():
    if (platform.dist()[0] == 'centos'):
        os.system('yum install -y nfs-utils nfs-utils-lib')
    elif (platform.dist()[0] == 'Ubuntu'):
        os.system('apt-get install -y nfs-common')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')

def mount_backup(options):
    helper.mount(options['backup_mount'], '/mnt/backup')

def install_docker():
    os.system('''
    curl -L https://get.docker.com/ | bash
    docker run hello-world
    ''')

def increase_max_map_count(options):
    os.system('''
    sysctl vm.max_map_count=''' + options['max_map_count'] + ''' \
    echo "vm.max_map_count = ''' + options['max_map_count'] + '''" | tee -a /etc/sysctl.conf
    sysctl -p
    ''')

def connect_to_rancher(options):
    os.system('''
    docker run -e CATTLE_AGENT_IP="''' + options['node_ip'] + '''"  -d --privileged \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /var/lib/rancher:/var/lib/rancher \
    rancher/agent:v1.1.1 https://''' + options['master_domain'] + '/v1/scripts/' + options['registration_token'] + ''' \
    ''')

def install_storage_server(options):
    os.system('''
    curl -L -o beegfs.py http://bit.ly/2n5lDz5;
    (echo ''' + options['master_domain'] + '''; \
    echo ''' + options['storage_service_id'] + '''; \
    echo ''' + options['storage_target_id'] + '''; \
    echo ''' + options['storage_mount'] + ''') | sudo python2 beegfs.py storage
    ''')

def install_client_server(options):
    os.system('''
    curl -L -o beegfs.py http://bit.ly/2n5lDz5;
    (echo ''' + options['master_domain'] + ''') | sudo python2 beegfs.py client
    ''')

main()
