ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
STAGE			:= ${STAGE}
STAGE	:= $(if $(STAGE),$(STAGE),dev)
CLUSTER_NAME := $(if $(CLUSTER_NAME),$(CLUSTER_NAME),kubernetes-prod-us-west-2)

DOCKER_REPO := 320464205386.dkr.ecr.us-west-2.amazonaws.com/sso-dashboard
COMMIT_SHA := $(shell git rev-parse --short HEAD)

all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]^\.PHONY.*].*:' Makefile

.PHONY: setup-codebuild
setup-codebuild:
	apt update && apt install -y apt-transport-https curl
	curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
	echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list
	apt update && apt install -y kubectl
	curl -O https://storage.googleapis.com/kubernetes-helm/helm-v2.11.0-linux-amd64.tar.gz
	tar zxf helm-v2.11.0-linux-amd64.tar.gz
	mv linux-amd64/helm /usr/local/bin/
	curl -O https://amazon-eks.s3-us-west-2.amazonaws.com/1.10.3/2018-07-26/bin/linux/amd64/aws-iam-authenticator
	chmod +x aws-iam-authenticator
	mv aws-iam-authenticator /usr/local/bin/
	apt update && apt install -y python3-pip
	pip3 install awscli

.PHONY: login
login:
	aws eks update-kubeconfig --name $(CLUSTER_NAME)
	aws ecr get-login --region us-west-2 --no-include-email | bash

.PHONY: build
build:
	docker build -t $(DOCKER_REPO):$(COMMIT_SHA) .

.PHONY: push
push:
	docker push $(DOCKER_REPO):$(COMMIT_SHA)

.PHONY: release
release:
	$(eval ASSUME_ROLE_ARN := $(shell aws ssm get-parameter --name "/iam/sso-dashboard/$(STAGE)/assum_role_arn" --query 'Parameter.Value' --output text))
	helm template -f k8s/values.yaml -f k8s/values/$(STAGE).yaml --set registry=$(DOCKER_REPO),namespace=sso-dashboard-$(STAGE),rev=$(COMMIT_SHA),assume_role=$(ASSUME_ROLE_ARN) k8s/ | kubectl apply -f -
