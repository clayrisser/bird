CWD := $(shell readlink -en $(dir $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))))


.PHONY: all
all: fetch_docker build_from_docker


## BUILD ##
.PHONY: build_from_docker
build_from_docker:
	docker run --rm -v $(CWD):/work jamrizzi/centos-dev:latest make build_centos
	docker run --rm -v $(CWD):/work jamrizzi/ubuntu-dev:latest make build_ubuntu
	$(info built from docker)

.PHONY: build_centos
build_centos: fetch_dependancies build rancher-installer-centos.tar.gz sweep
$(info built for centos)

.PHONY: build_ubuntu
build_ubuntu: fetch_dependancies build rancher-installer-ubuntu.tar.gz sweep
$(info built for ubuntu)

.PHONY: build
build: dist/rancher-installer
	$(info built)

dist/rancher-installer:
	pyinstaller --onefile --noupx rancher-installer.py


## PACKAGE ##
rancher-installer-centos.tar.gz:
	@tar -zcvf rancher-installer-centos.tar.gz dist/rancher-installer

rancher-installer-ubuntu.tar.gz:
	@tar -zcvf rancher-installer-ubuntu.tar.gz dist/rancher-installer


## CLEAN ##
.PHONY: clean
clean: sweep bleach
	$(info cleaned)

.PHONY: sweep
sweep:
	@rm -rf build dist *.spec */*.spec *.pyc */*.pyc get-pip.py
	$(info swept)

.PHONY: bleach
bleach:
	@rm -rf rancher-installer.tar.gz
	$(info bleached)


## FETCH DEPENDANCIES ##
.PHONY: fetch_dependancies
fetch_dependancies: pip future pyinstaller
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
