# beeduprandock
A stack for managing a highly available cloud platform.

Bee-dup-ran-dock stands for . . .

### [Beegfs](http://www.beegfs.com/)
Beegfs is used to maintain persistent storage accross the stack.
### [Duplicity](http://duplicity.nongnu.org/)
Duplicity keeps the storage volumes in the stack safely backed up.
### [Rancher](http://rancher.com/)
Rancher is the orchastration platform. It is used to maintain a scalable and highly availble platform.
### [Docker](https://www.docker.com/)
Docker is the contianer engine. Any application packaged as a docker container can be run on the stack.

## Install
### Master
```sh
curl -o master.sh https://raw.githubusercontent.com/jamrizzi/beeduprandock/master/master.sh && sudo bash master.sh
```

### Node
```sh
curl -o node.sh https://raw.githubusercontent.com/jamrizzi/beeduprandock/master/node.sh && sudo bash node.sh
```
