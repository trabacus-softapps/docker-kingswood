#!/bin/bash

# this is what starts your ERP server with odoo version 8.0
docker run -d -p 8069:8069 -p 8072:8072 --name="odoo.kingswooddemo" docker/kingswooddemo start
