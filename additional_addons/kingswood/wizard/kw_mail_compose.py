import datetime
from lxml import etree
import math
import pytz
import re
import time
from dateutil import parser
from lxml import etree
from dateutil import parser
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import openerp
from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime
from openerp.tools import html2plaintext
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
import base64
import xmlrpclib
from tools import config
host = str(config["xmlrpc_interface"])  or str("localhost"),
port = str(config["xmlrpc_port"])
sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (host[0], port))

class email_template(osv.osv):
    _name = 'email.template'
    _inherit = 'email.template'
    _description = 'Email composition wizard'
    
    def dispatch_mail(self, cr, uid, ids,attach_ids,context=None):
        if not context:
            context = {}        
        today = time.strftime('%Y-%m-%d %H:%M:%S')      
        wzd_obj = self.pool.get('invoice.group.report')
        mail_obj = self.pool.get('mail.mail')
        user_obj = self.pool.get('res.users')
        mail_compose = self.pool.get('mail.compose.message')
        print_report = True
        attach_obj = self.pool.get('ir.attachment')
        model_obj = 'stock.picking.out'
        data = context.get('active_res_id', False)
                
        if uid:
            user_id = user_obj.browse(cr,uid,uid)
        context.update({'date':today})
               
                             
        
        attachment_ids = [(4, attach_ids)]
        self.write(cr,uid,ids,{'attachment_ids':attachment_ids})
        
        return True   
        
        
email_template() 

