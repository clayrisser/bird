#!/usr/bin/env python

import sys
import os
import platform
from builtins import input
from helper import Helper
helper = Helper()

def main():
    helper.is_root()
    options = gather_information(get_defaults())
    helper.prepare()
    prepare_system()
    create_volumes_dir(options)
    install_rancher(options)
    install_beegfs_management(options)
    install_beegfs_metadata(options)
    install_beegfs_admon(options)

def get_defaults():
    return {
        'email': 'email@example.com',
        'rancher_domain': 'cloud.yourdomain.com',
        'management_node': 'node01',
        'metadata_service_id': '1',
        'duplicity_target_url': 'imabucket/backup',
        'gs_access_key_id': 'gs-access-key-id',
        'gs_secret_access_key': 'gs-secret-access-key',
        'cron_schedule': '0 0 0 * * *',
        'allow_source_mismatch': 'false',
        'volumes_directory': '/volumes',
        'volumes_mount': 'local',
        'rancher_mysql_database': 'rancher',
        'mysql_root_password': 'hellodocker'
    }

def gather_information(defaults):
    options = {}
    options['email'] = default_prompt('Email', defaults['email'])
    options['rancher_domain'] = default_prompt('Rancher Domain', defaults['rancher_domain'])
    options['management_node'] = default_prompt('Management Node', defaults['management_node'])
    options['metadata_service_id'] = default_prompt('Metadata Service ID', defaults['metadata_service_id'])
    options['duplicity_target_url'] = default_prompt('Duplicity Target URL', defaults['duplicity_target_url'])
    options['gs_access_key_id'] = default_prompt('Google Storage Access Key ID', defaults['gs_access_key_id'])
    options['gs_secret_access_key'] = default_prompt('Google Storage Secret Access Key', defaults['gs_secret_access_key'])
    options['cron_schedule'] = default_prompt('Cron Schedule', defaults['cron_schedule'])
    options['allow_source_mismatch'] = default_prompt('Allow Source Mismatch', defaults['allow_source_mismatch'])
    options['volumes_directory'] = default_prompt('Volumes Directory', defaults['volumes_directory'])
    options['volumes_mount'] = default_prompt('Volumes Mount', defaults['volumes_mount'])
    options['rancher_mysql_database'] = default_prompt('Rancher Mysql Database', defaults['rancher_mysql_database'])
    options['mysql_root_password'] = default_prompt('MYSQL Root Password', defaults['mysql_root_password'])
    return options

def default_prompt(name, fallback):
    response = input(name + ' (' + fallback + '): ')
    assert isinstance(response, str)
    if (response):
        return response
    else:
        return fallback

def create_volumes_dir(options):
    os.system('mkdir -p ' + options['volumes_directory'])
    if os.system(options['volumes_mount']):
        os.system('mkfs.xfs -i size=512 ' + options['volumes_mount'])
        os.system('echo ' + options['volumes_mount'] + options['volumes_directory'] + ' xfs defaults 1 2" >> /etc/fstab')
        os.system('mount -a && mount')

def prepare_system():
    os.system('curl -L https://raw.githubusercontent.com/jamrizzi/beegfs-installer/master/scripts/download.sh | bash')

def install_rancher(options):
    os.system('''
    curl -L https://raw.githubusercontent.com/jamrizzi/rancher-installer/master/scripts/download.sh | bash
    (echo ''' + options['email'] + '''; \
    echo ''' + options['rancher_domain'] + '''; \
    echo ''' + options['duplicity_target_url'] + '''; \
    echo ''' + options['gs_access_key_id'] + '''; \
    echo ''' + options['gs_secret_access_key'] + '''; \
    echo ''' + options['cron_schedule'] + '''; \
    echo ''' + options['allow_source_mismatch'] + '''; \
    echo ''' + options['volumes_directory'] + '''; \
    echo ''' + options['volumes_mount'] + '''; \
    echo ''' + options['rancher_mysql_database'] + '''; \
    echo ''' + options['mysql_root_password'] + ''') | ./rancher-installer
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
