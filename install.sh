#!/bin/bash
set -e
source /pd_build/buildconfig

run /pd_build/prepare.sh

run /pd_build/finalize.sh
