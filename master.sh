#!/bin/bash

EMAIL=email@example.com
RANCHER_MYSQL_DATABASE=rancher
MYSQL_PASSWORD=hellodocker
RANCHER_DOMAIN=cloud.yourdomain.com
MANAGEMENT_NODE=node01
METADATA_SERVICE_ID=2

if [ $(whoami) = "root" ]; then # if run as root

# gather information
read -p "Email ($EMAIL): " EMAIL_NEW
if [ $EMAIL_NEW ]; then
    EMAIL=$EMAIL_NEW
fi
read -p "Rancher MYSQL Database ($RANCHER_MYSQL_DATABASE): " RANCHER_MYSQL_DATABASE_NEW
if [ $RANCHER_MYSQL_DATABASE_NEW ]; then
    RANCHER_MYSQL_DATABASE=$RANCHER_MYSQL_DATABASE_NEW
fi
read -p "MYSQL Password ($MYSQL_PASSWORD): " MYSQL_PASSWORD_NEW
if [ $MYSQL_PASSWORD_NEW ]; then
    MYSQL_PASSWORD=$MYSQL_PASSWORD_NEW
fi
read -p "Rancher Domain ($RANCHER_DOMAIN): " RANCHER_DOMAIN_NEW
if [ $RANCHER_DOMAIN_NEW ]; then
    RANCHER_DOMAIN=$RANCHER_DOMAIN_NEW
fi
read -p "Management Node ($MANAGEMENT_NODE): " MANAGEMENT_NODE_NEW
if [ $MANAGEMENT_NODE_NEW ]; then
    MANAGEMENT_NODE=$MANAGEMENT_NODE_NEW
fi
read -p "Metadata Service ID ($METADATA_SERVICE_ID): " METADATA_SERVICE_ID_NEW
if [ $METADATA_SERVICE_ID_NEW ]; then
    METADATA_SERVICE_ID=$METADATA_SERVICE_ID_NEW
fi

# prepare system
yum update -y

# install docker
yum check-update
curl -fsSL https://get.docker.com/ | sh
systemctl start docker
systemctl status docker
systemctl enable docker
docker run hello-world

# install nginx
docker run -d --name nginx --restart=unless-stopped -p 80:80 -p 443:443 \
       --name nginx-proxy \
       -v /exports/certs:/etc/nginx/certs:ro \
       -v /etc/nginx/vhost.d \
       -v /usr/share/nginx/html \
       -v /var/run/docker.sock:/tmp/docker.sock:ro \
       jwilder/nginx-proxy
docker run -d --restart=unless-stopped \
       -v /exports/certs:/etc/nginx/certs:rw \
       --volumes-from nginx-proxy \
       -v /var/run/docker.sock:/var/run/docker.sock:ro \
       jrcs/letsencrypt-nginx-proxy-companion

# install mariadb
docker run -d --name rancherdb --restart=unless-stopped \
       -v /exports/rancher/mysql:/var/lib/mysql \
       -e MYSQL_DATABASE=$RANCHER_MYSQL_DATABASE \
       -e MYSQL_ROOT_PASSWORD=$MYSQL_PASSWORD \
       mariadb:latest

# install rancher
docker run -d --restart=unless-stopped --link rancherdb:mysql \
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