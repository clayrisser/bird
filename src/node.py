#!/usr/bin/env python

import sys
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
    create_storage_dir(options)
    install_docker()
    increase_max_map_count(options)
    connect_to_rancher(options)
    install_storage_server(options)
    install_client_server(options)
    reboot()

def get_defaults():
    print('Getting external ip . . .')
    return {
        'management_node': 'node01',
        'node_ip': ipgetter.myip(),
        'registration_token': 'my-rancher-token',
        'storage_service_id': '2',
        'storage_target_id': '201',
        'kernel_module_autobuild': 'false',
        'storage_mount': 'local',
        'max_map_count': '262144'
    }

def gather_information(defaults):
    options = {}
    options['management_node'] = default_prompt('Management Node', defaults['management_node'])
    options['node_ip'] = default_prompt('Node IP', defaults['node_ip'])
    options['registration_token'] = default_prompt('Registration Token', defaults['registration_token'])
    options['storage_service_id'] = default_prompt('Storage Service ID', defaults['storage_service_id'])
    options['storage_target_id'] = default_prompt('Storage Target ID', defaults['storage_target_id'])
    options['kernel_module_autobuild'] = default_prompt('Kernel Module Autobuild', defaults['kernel_module_autobuild'])
    options['storage_mount'] = default_prompt('Storage Mount', defaults['storage_mount'])
    options['max_map_count'] = default_prompt('Max Map Count', defaults['max_map_count'])
    return options

def default_prompt(name, fallback):
    response = input(name + ' (' + fallback + '): ')
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

def create_storage_dir(options):
    os.system('mkdir -p /mnt/myraid1')
    if (options['storage_mount'] != 'local'):
        os.system('mkfs.xfs -i size=512 ' + options['storage_mount'])
        os.system('echo ' + options['storage_mount'] + ' /mnt/myraid1 xfs defaults 1 2" >> /etc/fstab')
        os.system('mount -a && mount')

def install_docker():
    os.system('''
    curl -L https://get.docker.com/ | bash
    service docker start
    service docker status
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
    rancher/agent:v1.1.1 https://''' + options['management_node'] + '/v1/scripts/' + options['registration_token'] + ''' \
    ''')

def install_storage_server(options):
    os.system('''
    (echo + ''' + options['management_node'] + '''; \
    echo + ''' + options['storage_service_id'] + '''; \
    echo + ''' + options['storage_target_id'] + ''') | beegfs-installer/storage-install
    ''')

def install_client_server(options):
    os.system('''
    (echo + ''' + options['management_node'] + '''; \
    echo + ''' + options['kernel_module_autobuild'] + ''' \
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
