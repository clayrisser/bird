# bird
A stack for managing a highly available cloud platform.

bird stands for . . .

### [Beegfs](http://www.beegfs.com/)
Beegfs is used to maintain persistent storage accross the stack.
### [Ident](https://github.com/jamrizzi/ident)
Ident keeps the storage volumes in the stack safely backed up.
### [Rancher](http://rancher.com/)
Rancher is the orchastration platform. It is used to maintain a scalable and highly availble platform.
### [Docker](https://www.docker.com/)
Docker is the contianer engine. Any application packaged as a docker container can be run on the stack.

## Install
### Master
```sh
curl -L https://raw.githubusercontent.com/jamrizzi/bird/master/install.py | sudo python2 - master
```

### Node
```sh
curl -L https://raw.githubusercontent.com/jamrizzi/bird/master/install.py | sudo python2 - node
```
