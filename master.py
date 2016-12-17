#!/usr/bin/env python

import sys
import os
import platform
from builtins import input

def main():
    if os.getenv("SUDO_USER") == None:
        print('Requires root privileges')
        sys.exit('Exiting installer')
    options = gather_information(get_defaults())
    prepare_system()
    create_volumes_dir(options)
    install_docker()
    restore_volumes(options)
    install_nginx(options)
    install_mariadb(options)
    install_rancher(options)
    install_dockplicity(options)

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

def prepare_system():
    if (platform.dist()[0] == 'Ubuntu'):
        os.system('apt-get update -y')
    elif (platform.dist()[0] == 'centos'):
        os.system('yum update -y')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')

def create_volumes_dir(options):
    os.system('mkdir -p ' + options['volumes_directory'])
    if os.system(options['volumes_mount']):
        os.system('mkfs.xfs -i size=512 ' + options['volumes_mount'])
        os.system('echo ' + options['volumes_mount'] + options['volumes_directory'] + ' xfs defaults 1 2" >> /etc/fstab')
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

def install_nginx():
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


def install_mariadb():
    os.system('''
    docker run -d --name rancherdb --restart=always \
    -v ''' + options['volumes_directory'] + '''/rancher-data:/var/lib/mysql \
    -e MYSQL_DATABASE=''' + options['rancher_mysql_database'] + ''' \
    -e MYSQL_ROOT_PASSWORD=''' + options['mysql_root_password'] + ''' \
    mariadb:latest
    ''')

def install_rancher():
    os.system('''
    docker run -d --name rancher --restart=unless-stopped --link rancherdb:mysql \
    -e CATTLE_DB_CATTLE_MYSQL_HOST=$MYSQL_PORT_3306_TCP_ADDR \
    -e CATTLE_DB_CATTLE_MYSQL_PORT=3306 \
    -e CATTLE_DB_CATTLE_MYSQL_NAME=$RANCHER_MYSQL_DATABASE \
    -e CATTLE_DB_CATTLE_USERNAME=root \
    -e CATTLE_DB_CATTLE_PASSWORD=$MYSQL_PASSWORD \
    -e VIRTUAL_HOST=$RANCHER_DOMAIN \
    -e VIRTUAL_PORT=8080 \
    -e LETSENCRYPT_HOST=$RANCHER_DOMAIN \
    -e LETSENCRYPT_EMAIL=$EMAIL \
    rancher/server:latest
    ''')

def install_dockplicity():
    os.system('''
    docker run -d --name dockplicity --restart=always \
    -v $VOLUMES_DIRECTORY/certs:/volumes/certs \
    -v $VOLUMES_DIRECTORY/rancher-data:/volumes/rancher-data \
    -e GS_ACCESS_KEY_ID=$GS_ACCESS_KEY_ID \
    -e GS_SECRET_ACCESS_KEY=$GS_SECRET_ACCESS_KEY \
    -e TARGET_URL=$DUPLICITY_TARGET_URL \
    -e CRON_SCHEDULE="$CRON_SCHEDULE" \
    -e ALLOW_SOURCE_MISMATCH=$ALLOW_SOURCE_MISMATCH \
    jamrizzi/dockplicity:latest
    ''')


def install_beegfs_management():
    if (platform.dist()[0] == 'centos'):
        os.system('''
        curl -o management-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/management-install.sh
        bash management-install.sh
        rm management-install.sh
        /etc/init.d/beegfs-mgmtd status
        ''')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')




def install_beegfs_metadata():
    if (platform.dist()[0] == 'centos'):
        os.system('''
        curl -o metadata-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/metadata-install.sh
        (echo $MANAGEMENT_NODE; echo $METADATA_SERVICE_ID) | bash metadata-install.sh
        rm metadata-install.sh
        /etc/init.d/beegfs-meta status
        ''')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')


def beegfs_admon_server():
    if (platform.dist()[0] == 'centos'):
        os.system('''
        curl -o admon-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/admon-install.sh
        (echo $MANAGEMENT_NODE) | bash admon-install.sh
        rm admon-install.sh
        /etc/init.d/beegfs-admon status
        ''')
    else:
        print('Operating system not supported')
        sys.exit('Exiting installer')

main()
