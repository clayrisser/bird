#!/bin/bash

# settings

MANAGEMENT_NODE=node01
STORAGE_SERVICE_ID=2
STORAGE_TARGET_ID=201
KERNEL_MODULE_AUTOBUILD=false
STORAGE_MOUNT=local

if [ $(whoami) = "root" ]; then # if run as root

# gather information
# read -p "Data Directory ($DATA_DIRECTORY): " DATA_DIRECTORY_NEW
# if [ $DATA_DIRECTORY_NEW ]; then
#     DATA_DIRECTORY=$DATA_DIRECTORY_NEW
# fi
# read -p "Volume Mount ($VOLUME_MOUNT): " VOLUME_MOUNT_NEW
# if [ $VOLUME_MOUNT_NEW ]; then
#     VOLUME_MOUNT=$VOLUME_MOUNT_NEW
# fi
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
read -p "Kernel Module Autobuild ($KERNEL_MODULE_AUTOBUILD): " KERNEL_MODULE_AUTOBUILD_NEW
if [ $KERNEL_MODULE_AUTOBUILD_NEW ]; then
    KERNEL_MODULE_AUTOBUILD=$KERNEL_MODULE_AUTOBUILD_NEW
fi
read -p "Storage Mount ($STORAGE_MOUNT): " STORAGE_MOUNT_NEW
if [ $STORAGE_MOUNT_NEW ]; then
    STORAGE_MOUNT=$STORAGE_MOUNT_NEW
fi

# prepare system
yum update -y

# mount and create storage directory
mkdir -p /mnt/beegfs
if [ "$STORAGE_MOUNT" != "local" ]; then
    mkfs.xfs -i size=512 $STORAGE_MOUNT
    echo "$STORAGE_MOUNT /mnt/beegfs xfs defaults 1 2" >> /etc/fstab
    mount -a && mount
fi

# install storage server
curl -o storage-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/storage-install.sh
(echo $MANAGEMENT_NODE; echo $STORAGE_SERVICE_ID; echo $STORAGE_TARGET_ID) | bash storage-install.sh
rm storage-install.sh
/etc/init.d/beegfs-storage status

if [ "$KERNEL_MODULE_AUTOBUILD" == "true" ]; then
    _KERNEL_MODULE_AUTOBUILD=y
else
    _KERNEL_MODULE_AUTOBUILD=n
fi
# install client server
curl -o client-install.sh https://raw.githubusercontent.com/jamrizzi/beegfs-docker/master/client-install.sh
(echo $MANAGEMENT_NODE; echo $_KERNEL_MODULE_AUTOBUILD; echo N) | bash client-install.sh
rm client-install.sh
/etc/init.d/beegfs-client status
/etc/init.d/beegfs-helperd status

# restart
read -p "Restart Machine? (Y|n): " RESTART_NEW
if [ $RESTART_NEW ]; then
    RESTART=$RESTART_NEW
fi
if [ ${RESTART,,}=y ]; then
    reboot
fi

else # not run as root
    echo "this program must be run as root"
    echo "exiting"
fi
