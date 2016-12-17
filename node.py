#!/usr/bin/env python

import sys
import os
import platform
from builtins import input
import ipgetter

def main():
    if os.getenv("SUDO_USER") == None:
        print('Requires root privileges')
        sys.exit('Exiting installer')
    options = gather_information(get_defaults())
    prepare_system()
    create_storage_dir(options)
    install_docker()
    increase_max_map_count(options)
    install_storage_server(options)
    install_client_server(options)
    connect_to_rancher(options)
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

def prepare_system():
    if (platform.dist()[0] == 'Ubuntu'):
        os.system('apt-get update -y')
    elif (platform.dist()[0] == 'centos'):
        os.system('yum update -y')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')

def create_storage_dir(options):
    os.system('mkdir -p /mnt/myraid1')
    if (options['storage_mount'] != 'local'):
        os.system('mkfs.xfs -i size=512 ' + options['storage_mount'])
        os.system('echo ' + options['storage_mount'] + ' /mnt/myraid1 xfs defaults 1 2" >> /etc/fstab')
        os.system('mount -a && mount')

def install_docker():
    if (platform.dist()[0] == 'Ubuntu'):
        os.system('''
        apt-get install apt-transport-https ca-certificates
        apt-key adv \
        --keyserver hkp://ha.pool.sks-keyservers.net:80 \
        --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
        echo "deb https://apt.dockerproject.org/repo ubuntu-''' + platform.dist()[2] + ''' main\n" \
        | tee /etc/apt/sources.list/docker.list
        apt-get update -y
        apt-cache policy docker-engine
        apt-get install linux-image-extra-$(uname -r) linux-image-extra-virtual
        apt-get install docker-engine
        service docker start
        ''')
    elif (platform.dist()[0] == 'centos'):
        os.system('''
        yum check-update
        curl -fsSL https://get.docker.com/ | sh
        systemctl start docker
        systemctl status docker
        systemctl enable docker
        ''')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')
    os.system('docker run hello-world')

def increase_max_map_count(options):
    os.system('''
    sysctl vm.max_map_count=''' + options['max_map_count'] + ''' \
    echo "vm.max_map_count = ''' + options['max_map_count'] + '''" | tee -a /etc/sysctl.conf
    sysctl -p
    ''')

def install_storage_server(options):
    os.system('''
    curl -o storage-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/storage-install.sh
    (echo ''' + options['management_node'] + '; echo ' + options['storage_service_id'] + '; echo ' + options['storage_target_id'] + ''') | bash storage-install.sh
    rm storage-install.sh
    /etc/init.d/beegfs-storage status
    ''')

def install_client_server(options):
    kernel_module_autobuild = 'n'
    if (options['kernel_module_autobuild'] == 'true'):
        kernel_module_autobuild = 'y'
    os.system('''
    curl -o client-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/client-install.sh
    (echo ''' + options['management_node'] + '; echo ' + kernel_module_autobuild + '''; echo N) | bash client-install.sh
    rm client-install.sh
    /etc/init.d/beegfs-client status
    /etc/init.d/beegfs-helperd status
    ''')

def connect_to_rancher(options):
    os.system('''
    docker run -e CATTLE_AGENT_IP="''' + options['node_ip'] + '''"  -d --privileged \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /var/lib/rancher:/var/lib/rancher \
    rancher/agent:v1.1.1 https://''' + options['management_node'] + '/v1/scripts/' + options['registration_token'] + ''' \
    ''')

def reboot():
    print('Installation finished')
    reboot = 'true'
    reboot = default_prompt('Reboot', reboot)
    if (reboot == 'true'):
        os.system('reboot')
    else:
        print('Beegfs storage will not work until you reboot your system')
        sys.exit('Exiting installer')

main()
