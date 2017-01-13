#!/usr/bin/env python

import sys
import os
import platform
import ipgetter
from builtins import input
from helper import Helper
helper = Helper()

def main():
    helper.is_root()
    options = gather_information(get_defaults())
    helper.prepare()
    prepare_system()
    setup_backup_cloud(options)
    install_rancher(options)
    install_beegfs_management(options)
    install_beegfs_metadata(options)
    install_beegfs_admon(options)

def get_defaults():
    print('Getting external ip . . .')
    return {
        'email': 'email@example.com',
        'rancher_domain': 'cloud.yourdomain.com',
        'management_node': 'node01',
        'metadata_service_id': '1',
        'cron_schedule': '0 0 0 * * *',
        'backup_cloud_mount': 'local',
        'volumes_mount': 'local',
        'backup_volumes_mount': 'local',
        'backup_volumes_target_url': '',
        'backup_volumes_access_key': '',
        'backup_volumes_secret_key': '',
        'rancher_mysql_database': 'rancher',
        'mysql_root_password': 'hellodocker'
    }

def gather_information(defaults):
    options = {}
    options['email'] = default_prompt('Email', defaults['email'], True)
    options['rancher_domain'] = default_prompt('Rancher Domain', defaults['rancher_domain'], True)
    options['management_node'] = default_prompt('Management Node', defaults['management_node'], True)
    options['metadata_service_id'] = default_prompt('Metadata Service ID', defaults['metadata_service_id'], True)
    options['cron_schedule'] = default_prompt('Cron Schedule', defaults['cron_schedule'], True)
    options['backup_cloud_mount'] = default_prompt('Backup Cloud Mount', defaults['backup_cloud_mount'], True)
    options['volumes_mount'] = default_prompt('Volumes Mount', defaults['volumes_mount'], True)
    options['backup_volumes_mount'] = default_prompt('Backup Volumes Mount', defaults['backup_volumes_mount'], True)
    options['backup_volumes_target_url'] = default_prompt('Backup Volumes Target URL', defaults['backup_volumes_target_url'], False)
    options['backup_volumes_access_key'] = default_prompt('Backup Volumes Access Key', defaults['backup_volumes_access_key'], False)
    options['backup_volumes_secret_key'] = default_prompt('Backup Volumes Secret Key', defaults['backup_volumes_secret_key'], False)
    options['rancher_mysql_database'] = default_prompt('Rancher Mysql Database', defaults['rancher_mysql_database'], True)
    options['mysql_root_password'] = default_prompt('MYSQL Root Password', defaults['mysql_root_password'], True)
    return options

def default_prompt(name, fallback, prompt):
    if (prompt == False):
        return fallback
    message = name + ': '
    if fallback != '':
        message = name + ' (' + fallback + '): '
    response = input(message)
    assert isinstance(response, str)
    if (response):
        return response
    else:
        return fallback

def setup_backup_cloud(options):
    mount(options['backup_cloud_mount'], '/cloud-backup')
    os.system('''
    chmod 777 /cloud-backup
    echo "/cloud-backup    *(rw,sync,no_subtree_check)" | tee -a /etc/exports
    ''')
    os.system('curl -L https://raw.githubusercontent.com/jamrizzi/beegfs-installer/master/scripts/download.sh | bash')
    if (platform.dist()[0] == 'centos'):
        os.system('exportfs -a')
    elif (platform.dist()[0] == 'Ubuntu'):
        os.system('systemctl restart nfs-kernel-server')
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

def prepare_system():
    os.system('curl -L https://raw.githubusercontent.com/jamrizzi/beegfs-installer/master/scripts/download.sh | bash')
    if (platform.dist()[0] == 'centos'):
        os.system('''
        yum install -y nfs-utils nfs-utils-lib rpcbind
        chkconfig nfs on
        service rpcbind start
        service nfs start
        ''')
    elif (platform.dist()[0] == 'Ubuntu'):
        os.system('apt-get install -y nfs-kernel-server')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')

def install_rancher(options):
    os.system('''
    curl -L https://raw.githubusercontent.com/jamrizzi/rancher-ident/master/scripts/download.sh | bash
    (echo ''' + options['email'] + '''; \
    echo ''' + options['rancher_domain'] + '''; \
    echo ''' + options['volumes_mount'] + '''; \
    echo ''' + options['backup_volumes_mount'] + '''; \
    echo ''' + options['backup_volumes_target_url'] + '''; \
    echo ''' + options['backup_volumes_access_key'] + '''; \
    echo ''' + options['backup_volumes_secret_key'] + '''; \
    echo ''' + options['cron_schedule'] + '''; \
    echo ''' + options['rancher_mysql_database'] + '''; \
    echo ''' + options['mysql_root_password'] + ''') | ./rancher-ident
    ''')

def install_beegfs_management(options):
    os.system('beegfs-installer/management-install')

def install_beegfs_metadata(options):
    os.system('''
    (echo ''' + options['management_node'] + '''; \
    echo ''' + options['metadata_service_id'] + ''') | beegfs-installer/metadata-install
    ''')

def install_beegfs_admon(options):
    os.system('(echo ' + options['management_node'] + ') | beegfs-installer/admon-install')

main()
