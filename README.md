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

```sh

```
### Master
```sh
curl -L https://raw.githubusercontent.com/jamrizzi/beeduprandock/master/scripts/download.sh | bash && sudo beeduprandock/master
```

### Node
```sh
curl -L https://raw.githubusercontent.com/jamrizzi/beeduprandock/master/scripts/download.sh | bash && sudo beeduprandock/node
```
