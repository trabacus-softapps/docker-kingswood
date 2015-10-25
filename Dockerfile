FROM softapps/docker-openerpbase-kings
MAINTAINER Arun T K <arun.kalikeri@xxxxxxxx.com>
ADD additional_addons/pentaho_reports /opt/odoo/additional_addons/pentaho_reports
ADD additional_addons/account_financial_report_webkit /opt/odoo/additional_addons/account_financial_report_webkit
ADD additional_addons/report_xls /opt/odoo/additional_addons/report_xls
ADD additional_addons/account_financial_report_webkit_xls /opt/odoo/additional_addons/account_financial_report_webkit_xls
ADD additional_addons/web_m2x_options /opt/odoo/additional_addons/web_m2x_options
ADD additional_addons/report_webkit /opt/odoo/additional_addons/report_webkit
ADD additional_addons/account_invoice_merge /opt/odoo/additional_addons/account_invoice_merge
ADD additional_addons/kingswood /opt/odoo/additional_addons/kingswood

RUN chown -R odoo:odoo /opt/odoo/additional_addons/
