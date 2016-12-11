#!/bin/bash

# settings
DATA_DIRECTORY=/exports/
VOLUME_MOUNT=/dev/disk/by-id/google-disk-1
MANAGEMENT_NODE=node01
STORAGE_SERVICE_ID=3
STORAGE_TARGET_ID=301
KERNEL_MODULE_AUTOBUILD=N

if [ $(whoami) = "root" ]; then # if run as root

# gather information
read -p "Data Directory ($DATA_DIRECTORY): " DATA_DIRECTORY_NEW
if [ $DATA_DIRECTORY_NEW ]; then
    DATA_DIRECTORY=$DATA_DIRECTORY_NEW
fi
read -p "Volume Mount ($VOLUME_MOUNT): " VOLUME_MOUNT_NEW
if [ $VOLUME_MOUNT_NEW ]; then
    VOLUME_MOUNT=$VOLUME_MOUNT_NEW
fi
read -p "Management Node ($MANAGEMENT_NODE): " MANAGEMENT_NODE_NEW
if [ $MANAGEMENT_NODE_NEW ]; then
    MANAGEMENT_NODE=$MANAGEMENT_NODE_NEW
fi
read -p "Storage Service ID ($STORAGE_SERVICE_ID): " STORAGE_SERVICE_ID_NEW
if [ $STORAGE_SERVICE_ID_NEW ]; then
    STORAGE_SERVICE_ID=$STORAGE_SERVICE_ID_NEW
fi
read -p "Storage Target ID ($STORAGE_TARGET_ID): " STORAGE_TARGET_ID_NEW
if [ $STORAGE_TARGET_ID_NEW ]; then
    STORAGE_TARGET_ID=$STORAGE_TARGET_ID_NEW
fi
read -p "Kernel Module Autobuild (y|N): " KERNEL_MODULE_AUTOBUILD_NEW
if [ $KERNEL_MODULE_AUTOBUILD_NEW ]; then
    KERNEL_MODULE_AUTOBUILD=$KERNEL_MODULE_AUTOBUILD_NEW
fi

# prepare system
yum update -y

# mount and create data directory
mkfs.xfs -i size=512 $VOLUME_MOUNT
mkdir -p $DATA_DIRECTORY
echo "$VOLUME_MOUNT $DATA_DIRECTORY xfs defaults 1 2" >> /etc/fstab
mount -a && mount
chmod -R 777 $DATA_DIRECTORY

# install storage server
(echo $MANAGEMENT_NODE; echo $STORAGE_SERVICE_ID; echo $STORAGE_TARGET_ID) | curl -o storage-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/storage-install.sh
bash storage-install.sh
rm storage-install.sh
/beegfs-storage status

# install client server
(echo $MANAGEMENT_NODE; echo $KERNEL_MODULE_AUTOBUILD; echo N) | curl -o client-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/client-install.sh
bash client-install.sh
rm client-install.sh
/etc/init.d/beegfs-client status
/etc/init.d/beegfs-helperd status

# restart
read -p "Restart Machine? (Y|n): " RESTART_NEW
if [ $RESTART_NEW ]; then
    RESTART=$RESTART_NEW
fi
if [ ${RESTART,,}=y ]; then
    restart
fi

else # not run as root
    echo "this program must be run as root"
    echo "exiting"
fi
