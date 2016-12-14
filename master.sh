#!/bin/bash

EMAIL=email@example.com
RANCHER_DOMAIN=cloud.yourdomain.com
MANAGEMENT_NODE=node01
METADATA_SERVICE_ID=1
DUPLICITY_TARGET_URL="imabucket/backup"
GS_ACCESS_KEY_ID="gs-access-key-id"
GS_SECRET_ACCESS_KEY="gs-secret-access-key"
CRON_SCHEDULE="0 0 0 * * *"
ALLOW_SOURCE_MISMATCH=false
VOLUMES_DIRECTORY=/volumes
VOLUMES_MOUNT=local
RANCHER_MYSQL_DATABASE=rancher
MYSQL_PASSWORD=hellodocker

if [ $(whoami) = "root" ]; then # if run as root

# gather information
read -p "Email ($EMAIL): " EMAIL_NEW
if [ "$EMAIL_NEW" ]; then
    EMAIL=$EMAIL_NEW
fi
read -p "Rancher Domain ($RANCHER_DOMAIN): " RANCHER_DOMAIN_NEW
if [ "$RANCHER_DOMAIN_NEW" ]; then
    RANCHER_DOMAIN=$RANCHER_DOMAIN_NEW
fi
read -p "Management Node ($MANAGEMENT_NODE): " MANAGEMENT_NODE_NEW
if [ "$MANAGEMENT_NODE_NEW" ]; then
    MANAGEMENT_NODE=$MANAGEMENT_NODE_NEW
fi
read -p "Metadata Service ID ($METADATA_SERVICE_ID): " METADATA_SERVICE_ID_NEW
if [ "$METADATA_SERVICE_ID_NEW" ]; then
    METADATA_SERVICE_ID=$METADATA_SERVICE_ID_NEW
fi
read -p "Duplicity Target URL ($DUPLICITY_TARGET_URL): " DUPLICITY_TARGET_URL_NEW
if [ "$DUPLICITY_TARGET_URL_NEW" ]; then
    DUPLICITY_TARGET_URL=$DUPLICITY_TARGET_URL_NEW
fi
read -p "Google Storage Access Key ID ($GS_ACCESS_KEY_ID): " GS_ACCESS_KEY_ID_NEW
if [ "$GS_ACCESS_KEY_ID_NEW" ]; then
    GS_ACCESS_KEY_ID=$GS_ACCESS_KEY_ID_NEW
fi
read -p "Google Storage Secret Access Key ($GS_SECRET_ACCESS_KEY): " GS_SECRET_ACCESS_KEY_NEW
if [ "$GS_SECRET_ACCESS_KEY_NEW" ]; then
    GS_SECRET_ACCESS_KEY=$GS_SECRET_ACCESS_KEY_NEW
fi
read -p "Cron Schedule ($CRON_SCHEDULE): " CRON_SCHEDULE_NEW
if [ "$CRON_SCHEDULE_NEW" ]; then
    CRON_SCHEDULE=$CRON_SCHEDULE_NEW
fi
read -p "Allow Source Mismatch ($ALLOW_SOURCE_MISMATCH): " ALLOW_SOURCE_MISMATCH_NEW
if [ "$ALLOW_SOURCE_MISMATCH_NEW" ]; then
    ALLOW_SOURCE_MISMATCH=$ALLOW_SOURCE_MISMATCH_NEW
fi
read -p "Volumes Directory ($VOLUMES_DIRECTORY): " VOLUMES_DIRECTORY_NEW
if [ "$VOLUMES_DIRECTORY_NEW" ]; then
    VOLUMES_DIRECTORY=$VOLUMES_DIRECTORY_NEW
fi
read -p "Volumes Mount - set as \"local\" for local disk ($VOLUMES_MOUNT): " VOLUMES_MOUNT_NEW
if [ "$VOLUMES_MOUNT_NEW" ]; then
    VOLUMES_MOUNT=$VOLUMES_MOUNT_NEW
fi
read -p "Rancher MYSQL Database ($RANCHER_MYSQL_DATABASE): " RANCHER_MYSQL_DATABASE_NEW
if [ "$RANCHER_MYSQL_DATABASE_NEW" ]; then
    RANCHER_MYSQL_DATABASE=$RANCHER_MYSQL_DATABASE_NEW
fi
read -p "MYSQL Password ($MYSQL_PASSWORD): " MYSQL_PASSWORD_NEW
if [ "$MYSQL_PASSWORD_NEW" ]; then
    MYSQL_PASSWORD=$MYSQL_PASSWORD_NEW
fi

# prepare system
yum update -y

# mount and create volumes directory
mkdir -p $VOLUMES_DIRECTORY
if [ "$VOLUMES_MOUNT" != "local" ]; then
    mkfs.xfs -i size=512 $VOLUMES_MOUNT
    echo "$VOLUMES_MOUNT $VOLUMES_DIRECTORY xfs defaults 1 2" >> /etc/fstab
    mount -a && mount
fi

# install docker
yum check-update
curl -fsSL https://get.docker.com/ | sh
systemctl start docker
systemctl status docker
systemctl enable docker
docker run hello-world

# restore volumes
docker run --rm \
       -v $VOLUMES_DIRECTORY/certs:/volumes/certs \
       -v $VOLUMES_DIRECTORY/rancher-data:/volumes/mysql \
       -e GS_ACCESS_KEY_ID=$GS_ACCESS_KEY_ID \
       -e GS_SECRET_ACCESS_KEY=$GS_SECRET_ACCESS_KEY \
       -e TARGET_URL=$DUPLICITY_TARGET_URL \
       -e ACTION=restore \
       -e FORCE=true \
       jamrizzi/dockplicity:latest

# install nginx
docker run -d --name nginx --restart=always -p 80:80 -p 443:443 \
       --name nginx-proxy \
       -v $VOLUMES_DIRECTORY/certs:/etc/nginx/certs:ro \
       -v /etc/nginx/vhost.d \
       -v /usr/share/nginx/html \
       -v /var/run/docker.sock:/tmp/docker.sock:ro \
       jwilder/nginx-proxy
docker run -d --restart=unless-stopped \
       -v $VOLUMES_DIRECTORY/certs:/etc/nginx/certs:rw \
       --volumes-from nginx-proxy \
       -v /var/run/docker.sock:/var/run/docker.sock:ro \
       alastaircoote/docker-letsencrypt-nginx-proxy-companion:latest

# install mariadb
docker run -d --name rancherdb --restart=always \
       -v $VOLUMES_DIRECTORY/rancher-data:/var/lib/mysql \
       -e MYSQL_DATABASE=$RANCHER_MYSQL_DATABASE \
       -e MYSQL_ROOT_PASSWORD=$MYSQL_PASSWORD \
       mariadb:latest

# install rancher
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

# install dockplicity
docker run -d --name dockplicity --restart=always \
       -v $VOLUMES_DIRECTORY/certs:/volumes/certs \
       -v $VOLUMES_DIRECTORY/rancher-data:/volumes/rancher-data \
       -e GS_ACCESS_KEY_ID=$GS_ACCESS_KEY_ID \
       -e GS_SECRET_ACCESS_KEY=$GS_SECRET_ACCESS_KEY \
       -e TARGET_URL=$DUPLICITY_TARGET_URL \
       -e CRON_SCHEDULE="$CRON_SCHEDULE" \
       -e ALLOW_SOURCE_MISMATCH=$ALLOW_SOURCE_MISMATCH \
       jamrizzi/dockplicity:latest

# beegfs management server
curl -o management-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/management-install.sh
bash management-install.sh
rm management-install.sh
/etc/init.d/beegfs-mgmtd status

# beegfs metadata server
curl -o metadata-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/metadata-install.sh
(echo $MANAGEMENT_NODE; echo $METADATA_SERVICE_ID) | bash metadata-install.sh
rm metadata-install.sh
/etc/init.d/beegfs-meta status

# beegfs admon server
curl -o admon-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/admon-install.sh
(echo $MANAGEMENT_NODE) | bash admon-install.sh
rm admon-install.sh
/etc/init.d/beegfs-admon status

else # not run as root
    echo "this program must be run as root"
    echo "exiting"
fi
