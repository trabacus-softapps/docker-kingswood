#!/bin/bash
set -e
source /pd_build/buildconfig

header "Copying KIngswood Modules"

## Install Trabacus.
run sudo -i -u odoo
run mkdir -p /opt/odoo/additional_addons
run cp -r /pd_build/additional_addons/ /opt/odoo/
run chown -R odoo /opt/odoo/additional_addons
