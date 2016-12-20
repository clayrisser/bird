CWD := $(shell readlink -en $(dir $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))))


.PHONY: all
all: fetch_docker build_from_docker


## BUILD ##
.PHONY: build_from_docker
build_from_docker:
	docker run --rm -it -v $(CWD):/work jamrizzi/centos-dev:latest make build_centos
	docker run --rm -it -v $(CWD):/work jamrizzi/ubuntu-dev:latest make build_ubuntu
	$(info built from docker)

.PHONY: build_centos
build_centos: fetch_dependancies build beeduprandock-centos.tar.gz sweep
	$(info built for centos)

.PHONY: build_ubuntu
build_ubuntu: fetch_dependancies build beeduprandock-ubuntu.tar.gz sweep
	$(info built for ubuntu)

.PHONY: build
build: dist/master dist/node
	$(info built)

dist/master:
	pyinstaller --onefile --noupx src/master.py

dist/node:
	pyinstaller --onefile --noupx src/node.py


## PACKAGE ##
beeduprandock-centos.tar.gz:
	@mkdir beeduprandock
	@cp -r dist/* beeduprandock
	@tar -zcvf beeduprandock-centos.tar.gz beeduprandock
	@rm -rf beeduprandock

beeduprandock-ubuntu.tar.gz:
	@mkdir beeduprandock
	@cp -r dist/* beeduprandock
	@tar -zcvf beeduprandock-ubuntu.tar.gz beeduprandock
	@rm -rf beeduprandock


## CLEAN ##
.PHONY: clean
clean: sweep bleach
	$(info cleaned)

.PHONY: sweep
sweep:
	@rm -rf build dist *.spec */*.spec *.pyc */*.pyc get-pip.py beegfs-installer rancher-installer
	$(info swept)

.PHONY: bleach
bleach:
	@rm -rf beeduprandock beeduprandock-*
	$(info bleached)


## FETCH DEPENDANCIES ##
.PHONY: fetch_dependancies
fetch_dependancies: pip future ipgetter pyinstaller
	$(info fetched dependancies)

.PHONY: pip
pip:
ifeq ($(shell whereis pip), $(shell echo pip:))
	curl -O https://bootstrap.pypa.io/get-pip.py
	python get-pip.py
endif

.PHONY: future
future:
	pip install future

.PHONY: ipgetter
ipgetter:
	pip install ipgetter

.PHONY: pyinstaller
pyinstaller:
ifeq ($(shell whereis pyinstaller), $(shell echo pyinstaller:))
	pip install pyinstaller
endif

.PHONY: fetch_docker
fetch_docker:
ifeq ($(shell whereis docker), $(shell echo docker:))
	curl -L https://get.docker.com/ | bash
endif
	$(info fetched docker)
