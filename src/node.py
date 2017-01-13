#!/usr/bin/env python

import sys
import socket
import os
import platform
from builtins import input
import ipgetter
from helper import Helper
helper = Helper()

def main():
    helper.is_root()
    options = gather_information(get_defaults())
    helper.prepare()
    prepare_system()
    mount_storage(options)
    mount_backup(options)
    install_docker()
    increase_max_map_count(options)
    connect_to_rancher(options)
    install_storage_server(options)
    install_client_server(options)
    reboot()

def get_defaults():
    print('Getting external ip . . .')
    defaults = {
        'management_node': 'node01',
        'rancher_domain': 'cloud.yourdomain.com',
        'node_ip': ipgetter.myip(),
        'registration_token': 'my-rancher-token',
        'storage_service_id': '2',
        'storage_target_id': '201',
        'kernel_module_autobuild': 'false',
        'storage_mount': 'local',
        'max_map_count': '262144'
    }
    return defaults

def gather_information(defaults):
    options = {}
    options['management_node'] = default_prompt('Management Node', defaults['management_node'])
    options['rancher_domain'] = default_prompt('Rancher Domain', defaults['rancher_domain'])
    options['node_ip'] = default_prompt('Node IP', defaults['node_ip'])
    options['registration_token'] = default_prompt('Registration Token', defaults['registration_token'])
    options['storage_service_id'] = default_prompt('Storage Service ID', defaults['storage_service_id'])
    options['storage_target_id'] = default_prompt('Storage Target ID', defaults['storage_target_id'])
    options['kernel_module_autobuild'] = default_prompt('Kernel Module Autobuild', defaults['kernel_module_autobuild'])
    options['storage_mount'] = default_prompt('Storage Mount', defaults['storage_mount'])
    options['backup_mount'] = default_prompt('Backup Mount', socket.gethostbyname(options['management_node']) + ':/cloud-backup')
    options['max_map_count'] = default_prompt('Max Map Count', defaults['max_map_count'])
    return options

def default_prompt(name, fallback):
    message = name + ': '
    if fallback != '':
        message = name + ' (' + fallback + '): '
    response = input(message)
    assert isinstance(response, str)
    if (response):
        return response
    else:
        return fallback

def boolean_prompt(name, fallback):
    default = 'Y|n'
    fallback = fallback.upper()
    if (fallback == 'N'):
        default = 'y|N'
    response = input(name + ' (' + default + '): ')
    assert isinstance(response, str)
    if (response):
        return response.upper()
    else:
        return fallback

def prepare_system():
    os.system('curl -L https://raw.githubusercontent.com/jamrizzi/beegfs-installer/master/scripts/download.sh | bash')
    if (platform.dist()[0] == 'centos'):
        os.system('yum install -y nfs-utils nfs-utils-lib')
    elif (platform.dist()[0] == 'Ubuntu'):
        os.system('apt-get install -y nfs-common')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')

def mount(mount_from, mount_to):
    os.system('mkdir -p ' + mount_to)
    if mount_from != 'local':
        if mount_from[:4] == '/dev':
            os.system('mkfs.xfs -i size=512 ' + mount_from)
            os.system('echo "' + mount_from + ' ' +  mount_to + ' xfs defaults 1 2" | tee -a /etc/fstab')
            os.system('mount -a && mount')
        else:
            os.system('mount -t nfs -o proto=tcp,port=2049 ' + mount_from + ' ' + mount_to)
            os.system('echo "' + mount_from + ' ' + mount_to + ' nfs rsize=8192,wsize=8192,timeo=14,intr" | tee -a /etc/fstab')

def mount_storage(options):
    mount(options['storage_mount'], '/mnt/myraid1')

def mount_backup(options):
    mount(options['backup_mount'], '/backup')

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
    rancher/agent:v1.1.1 https://''' + options['rancher_domain'] + '/v1/scripts/' + options['registration_token'] + ''' \
    ''')

def install_storage_server(options):
    os.system('''
    (echo ''' + options['management_node'] + '''; \
    echo ''' + options['storage_service_id'] + '''; \
    echo ''' + options['storage_target_id'] + ''') | beegfs-installer/storage-install
    ''')

def install_client_server(options):
    os.system('''
    (echo ''' + options['management_node'] + '''; \
    echo ''' + options['kernel_module_autobuild'] + '''; \
    echo N) | beegfs-installer/client-install
    ''')

def reboot():
    print('Installation finished')
    reboot = boolean_prompt('Reboot', 'Y')
    if (reboot == 'Y'):
        os.system('reboot')
        sys.exit('Rebooting . . .')
    else:
        print('Beegfs client will not work until you reboot your system')
        sys.exit('Exiting installer')

main()
