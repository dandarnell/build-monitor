#!/usr/bin/bash

tc-signin() { eval `./taskcluster signin "${@}"`; }

export TASKCLUSTER_ROOT_URL='https://firefox-ci-tc.services.mozilla.com/'

curl -L 'https://github.com/taskcluster/taskcluster/releases/latest/download/taskcluster-linux-amd64.tar.gz' --output taskcluster.tar.gz && \
tar -xvf taskcluster.tar.gz && \
rm taskcluster.tar.gz && \
chmod +x taskcluster

tc-signin

./build_monitor.py
