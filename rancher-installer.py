#!/usr/bin/env python

import sys
import os
import platform
from builtins import input

def main():
    helper.is_root()
    options = gather_information(get_defaults())
    helper.prepare()
    create_volumes_dir(options)
    install_docker()
    restore_volumes(options)
    install_nginx(options)
    install_mariadb(options)
    install_rancher(options)
    install_dockplicity(options)
    helper = Helper()

def get_defaults():
    return {
        'email': 'email@example.com',
        'rancher_domain': 'cloud.yourdomain.com',
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

def install_docker():
	os.system('curl -L https://get.docker.com/ | bash')

def restore_volumes(options):
    os.system('''
    docker run --rm \
    -v ''' + options['volumes_directory'] + '''/certs:/volumes/certs \
    -v ''' + options['volumes_directory'] + '''/rancher-data:/volumes/mysql \
    -e GS_ACCESS_KEY_ID=''' + options['gs_access_key_id'] + ''' \
    -e GS_SECRET_ACCESS_KEY=''' + options['gs_secret_access_key'] + ''' \
    -e TARGET_URL=''' + options['duplicity_target_url'] + ''' \
    -e ACTION=restore \
    -e FORCE=true \
    jamrizzi/dockplicity:latest
    ''')

def install_nginx(options):
    os.system('''
    docker run -d --name nginx --restart=always -p 80:80 -p 443:443 \
    --name nginx-proxy \
    -v ''' + options['volumes_directory'] + '''/certs:/etc/nginx/certs:ro \
    -v /etc/nginx/vhost.d \
    -v /usr/share/nginx/html \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    jwilder/nginx-proxy
    docker run -d --restart=unless-stopped \
    -v ''' + options['volumes_directory'] + '''/certs:/etc/nginx/certs:rw \
    --volumes-from nginx-proxy \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    alastaircoote/docker-letsencrypt-nginx-proxy-companion:latest
    ''')

def install_mariadb(options):
    os.system('''
    docker run -d --name rancherdb --restart=always \
    -v ''' + options['volumes_directory'] + '''/rancher-data:/var/lib/mysql \
    -e MYSQL_DATABASE=''' + options['rancher_mysql_database'] + ''' \
    -e MYSQL_ROOT_PASSWORD=''' + options['mysql_root_password'] + ''' \
    mariadb:latest
    ''')

def install_rancher(options):
    os.system('''
    docker run -d --name rancher --restart=unless-stopped --link rancherdb:mysql \
    -e CATTLE_DB_CATTLE_MYSQL_HOST=mysql \
    -e CATTLE_DB_CATTLE_MYSQL_PORT=3306 \
    -e CATTLE_DB_CATTLE_MYSQL_NAME=''' + options['rancher_mysql_database'] + ''' \
    -e CATTLE_DB_CATTLE_USERNAME=root \
    -e CATTLE_DB_CATTLE_PASSWORD=''' + options['mysql_root_password'] + ''' \
    -e VIRTUAL_HOST=''' + options['rancher_domain'] + ''' \
    -e VIRTUAL_PORT=8080 \
    -e LETSENCRYPT_HOST=''' + options['rancher_domain'] + ''' \
    -e LETSENCRYPT_EMAIL=''' + options['email'] + ''' \
    rancher/server:latest
    ''')

def install_dockplicity(options):
    os.system('''
    docker run -d --name dockplicity --restart=always \
    -v $VOLUMES_DIRECTORY/certs:/volumes/certs \
    -v $VOLUMES_DIRECTORY/rancher-data:/volumes/rancher-data \
    -e GS_ACCESS_KEY_ID=''' + options['gs_access_key_id'] + ''' \
    -e GS_SECRET_ACCESS_KEY=''' + options['gs_secret_access_key'] + '''] \
    -e TARGET_URL=''' + options['duplicity_target_url'] + ''' \
    -e CRON_SCHEDULE="''' + options['cron_schedule'] + '''" \
    -e ALLOW_SOURCE_MISMATCH=''' + options['allow_source_mismatch'] + ''' \
    jamrizzi/dockplicity:latest
    ''')

main()
