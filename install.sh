#!/bin/bash

# Determine OS
UNAME=$(uname | tr "[:upper:]" "[:lower:]")
if [ "$UNAME" == "linux" ]; then
    if [ -f /etc/lsb-release -o -d /etc/lsb-release.d ]; then
        export DISTRO=$(lsb_release -i | cut -d: -f2 | sed s/'^\t'//)
    else
        export DISTRO=$(ls -d /etc/[A-Za-z]*[_-][rv]e[lr]* | grep -v "lsb" | cut -d'/' -f3 | cut -d'-' -f1 | cut -d'_' -f1)
    fi
fi
[ "$DISTRO" == "" ] && export DISTRO=$UNAME
unset UNAME
if [ "$(echo $DISTRO | awk '{print substr($0,0,6)}')" == "centos" ]; then
    export DISTRO=centos
fi

# OS Specific Operations
if [ "$DISTRO" == "Ubuntu" ]; then
    apt-get update -y
    apt-get install -y git curl
elif [ "$DISTRO" == "centos" ]; then
    yum update -y
    yum install -y git curl
fi

# Universal Operations
curl -L https://bootstrap.pypa.io/get-pip.py | python2.7
git clone https://github.com/jamrizzi/bird.git

# Python dependencies
pip install future
pip install ipgetter

# Installation
if [ "$1" == "master" ]; then
    python2 ./bird/src/master.py
elif [ "$1" == "node" ]; then
    python2 ./bird/src/node.py
fi

# Cleanup
rm -rf ./bird
