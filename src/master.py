#!/usr/bin/env python2

import sys
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
    setup_backup_cloud(options)
    install_rancher(options)
    install_beegfs_management(options)
    install_beegfs_metadata(options)
    install_beegfs_admon(options)

def get_defaults():
    print('Getting external ip . . .')
    return {
        'email': 'email@example.com',
        'master_domain': 'cloud.yourdomain.com',
        'metadata_service_id': '2',
        'cron_schedule': '0 0 * * *',
        'backup_cloud_mount': 'local',
        'volumes_mount': 'local',
        'backup_volumes_mount': 'local',
        'rancher_mysql_database': 'rancher',
        'mysql_root_password': 'hellodocker'
    }

def gather_information(defaults):
    options = {}
    options['email'] = helper.default_prompt('Email', defaults['email'], True)
    options['master_domain'] = helper.default_prompt('Master Domain', defaults['master_domain'], True)
    options['metadata_service_id'] = helper.default_prompt('Metadata Service ID', defaults['metadata_service_id'], True)
    options['cron_schedule'] = helper.default_prompt('Cron Schedule', defaults['cron_schedule'], True)
    options['backup_cloud_mount'] = helper.default_prompt('Backup Cloud Mount', defaults['backup_cloud_mount'], True)
    options['volumes_mount'] = helper.default_prompt('Volumes Mount', defaults['volumes_mount'], True)
    options['backup_volumes_mount'] = helper.default_prompt('Backup Volumes Mount', defaults['backup_volumes_mount'], True)
    options['rancher_mysql_database'] = helper.default_prompt('Rancher Mysql Database', defaults['rancher_mysql_database'], True)
    options['mysql_root_password'] = helper.default_prompt('MYSQL Root Password', defaults['mysql_root_password'], True)
    return options

def prepare_system():
    os.system('curl -L https://raw.githubusercontent.com/jamrizzi/beegfs-installer/master/scripts/download.sh | bash')
    if (platform.dist()[0] == 'centos'):
        os.system('''
        yum install -y nfs-utils rpcbind
        ''')
    elif (platform.dist()[0] == 'Ubuntu'):
        os.system('apt-get install -y nfs-kernel-server')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')

def setup_backup_cloud(options):
    helper.mount(options['backup_cloud_mount'], '/exports/cloud-backup')
    os.system('''
    chmod 777 /exports/cloud-backup
    echo "/exports/cloud-backup    *(rw,sync,no_subtree_check)" | tee -a /etc/exports
    ''')
    os.system('curl -L https://raw.githubusercontent.com/jamrizzi/beegfs-installer/master/scripts/download.sh | bash')
    if (platform.dist()[0] == 'centos'):
        os.system('exportfs -a')
    elif (platform.dist()[0] == 'Ubuntu'):
        os.system('systemctl restart nfs-kernel-server')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')

def install_rancher(options):
    os.system('''
    curl -L https://raw.githubusercontent.com/jamrizzi/rancher-ident/master/scripts/download.sh | bash
    (echo ''' + options['email'] + '''; \
    echo ''' + options['master_domain'] + '''; \
    echo ''' + options['volumes_mount'] + '''; \
    echo ''' + options['backup_volumes_mount'] + '''; \
    echo ''' + options['cron_schedule'] + '''; \
    echo ''' + options['rancher_mysql_database'] + '''; \
    echo ''' + options['mysql_root_password'] + ''') | ./rancher-ident
    ''')

def install_beegfs_management(options):
    os.system('beegfs-installer/management-install')

def install_beegfs_metadata(options):
    os.system('''
    (echo ''' + options['master_domain'] + '''; \
    echo ''' + options['metadata_service_id'] + ''') | beegfs-installer/metadata-install
    ''')

def install_beegfs_admon(options):
    os.system('(echo ' + options['master_domain'] + ') | beegfs-installer/admon-install')

main()
