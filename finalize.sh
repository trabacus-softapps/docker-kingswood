#!/bin/bash
set -e
source /pd_build/buildconfig

header "Finalizing..."

run apt-get autoremove
run apt-get clean
run rm -rf /pd_build
