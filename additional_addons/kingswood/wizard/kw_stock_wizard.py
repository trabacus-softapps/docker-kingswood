from openerp.osv import fields,osv
from openerp.tools.translate import _
from datetime import datetime
import time
from openerp import tools
from openerp.tools.safe_eval import safe_eval as eval
import calendar
from dateutil import parser
from dateutil.relativedelta import relativedelta
from dateutil import parser
from lxml import etree
from openerp.osv.orm import setup_modifiers
from xlrd import open_workbook
import xml.etree.cElementTree as ET
import tempfile
import base64
import logging
_logger = logging.getLogger(__name__)
from xlsxwriter.workbook import Workbook


class vat_wizard(osv.osv_memory):
    _name = 'vat.wizard'


    def confirm(self, cr, uid, ids, context = None):
        if not context:
            context = {}

        pick_obj = self.pool.get('stock.picking.out')
        context.update({'state'         : 'KA',
                        "confirm_esugam" : True})
        pick_obj.kw_confirm(cr, uid, context['active_ids'],context=context)
        return True


vat_wizard()

class stock_wizard(osv.osv_memory):
    _name = 'stock.wizard'


    _columns ={
               'gross_weight'   :   fields.float("Gross Weight", digits=(16,2)),
               'tare_weight'    :   fields.float("Tare Weight", digits=(16,2)),
               'net_weight'     :   fields.float("Net Weight", digits=(16,2)),
               'loaded_qty'     :   fields.float('Loaded Quantity (MT)',digits=(0,3),track_visibility='onchange'),


               }

    def cash_voucher(self,cr,uid,ids,context=None):
        stock_obj = self.pool.get('stock.picking.out')
        stock_ids = context.get('active_ids',[])
        res = False
        if stock_ids:
            for case in self.browse(cr,uid,ids):
                if case.loaded_qty and case.loaded_qty > 0:
                    if case.loaded_qty > 40:
                        raise osv.except_osv(_('Warning'),_("Enter the Quantity in Metric Tons Eg. if the loaded quantity is 16800 kgs enter 16.800"))                
                    cr.execute("update stock_move set product_qty ="+str(case.loaded_qty)+"where picking_id = "+str(stock_ids[0]))
            res=stock_obj.freight_voucher(cr,uid,stock_ids)
        return res   
    
    def confirm(self, cr, uid, ids, context = None):
        pick_obj = self.pool.get('stock.picking.out')
        context.update({'confirm_vat':True})
        pick_obj.kw_confirm(cr, uid, context['active_ids'],context=context)
        return True
    
#     Weighment Slip Report Wizzard
    def weightment_slip(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        active_id = context.get('active_id', False)
        for case in self.browse(cr, uid, ids, context=context):
            report_name = 'Weighment Slip' 
            data = {}
            data['ids'] = [active_id]
            data['model'] = context.get('active_model', 'ir.ui.menu')
      
            data['output_type'] = 'pdf'
            data['variables'] = {
                                 'gross_weight'    : case.gross_weight,
                                 'tare_weight'     : case.tare_weight,
                                 'net_weight'      : case.net_weight,  
                                 
                                }
            return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': data,
                }
    
stock_wizard()
    

class invoice_group_report(osv.osv_memory):
    _name = "invoice.group.report"
    _description = "Group Invoice Report"


    _columns={
              'partner_id'    :     fields.many2one('res.partner','Partner'),
              'from_date'     :     fields.date('From'),
              'to_date'     :       fields.date('To'),  
              'product_id'  :       fields.many2one('product.product','Product'),
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', readonly=True, select=True, change_default=True, track_visibility='always'),     
              
              'report_type'   :   fields.selection([('xls','XLS'),('pdf','PDF')],'Report Type'),
              'summary'       :   fields.boolean('Monthly Summary'),
              'state_id'      :   fields.many2one('res.country.state','State'),
              'product_ids'   :   fields.many2many('product.product','product_cust_mis_rel', 'mis_id', 'product_id', 'Products'),
              'state_report'  :   fields.boolean('State'),
              'is_inout'      :   fields.boolean("Daily Incoming & Delivery"),       
              
              }
            
    _defaults={
               'report_type'   : 'pdf',
               'summary'       : False,
               'to_date'       :lambda *a: time.strftime('%Y-%m-%d'),
               'from_date'     :lambda *a: time.strftime('%Y-%m-%d'),
               'state_report' : False,
               }

    def default_get(self, cr, uid, fields, context=None):
        res={}
        today = time.strftime('%Y-%m-%d')
        if not context:
            context={}
        type=''
        invoice_obj = self.pool.get('account.invoice')
        type=context.get('type',False)
        if type:
            res['type']=type
        res['to_date']=today
        res['from_date']=today
        res['report_type']='pdf'
        print type
        return res
        
#     def print_daily_dispatch(self, cr, uid, ids, context=None):
#         if not context:
#             context = {}
#         for case in self.browse(cr, uid, ids, context=context):
#             report_name = 'daily_dispatch_in_out' 
#             data = {}
#             data['ids'] = ids
#             data['model'] = context.get('active_model', 'ir.ui.menu')
#       
#             data['output_type'] = 'xls'
#             data['variables'] = {
#                                  'from_date'    : '2016-06-18',
#                                  'to_date'      : '2016-06-20', 
#                                    
#                                 }
#                   
#         return {
#         'type': 'ir.actions.report.xml',
#         'report_name': report_name,
#         'name' : 'daily_dispatch_in_out',
#         'datas': data,
#             } 
        
    def print_inv_report(self,cr,uid,ids,context=None):
        rep_obj = self.pool.get('ir.actions.report.xml')
        invoice_obj = self.pool.get('account.invoice')
        stock_obj = self.pool.get('stock.picking')
        line_obj=self.pool.get('account.invoice.line')
        qty_del=0
        total_price=0
        qty_price=0
        res={}
        res1={}
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment') 
        invoice_ids=[]
        all_data={}
        fac_state = ''
        product_ids = []
        query = ''
#         pwriter = PdfFileWriter()
#         os.makedirs('/home/serveradmin/Desktop/temp')

        for case in self.browse(cr,uid,ids):
            if case.state_id:
                fac_state=str(case.state_id.name)
            if fac_state.lower() == 'karnataka':
               in_fac_state = 'KA'
            else:
               in_fac_state ='TN'     
            for prod in case.product_ids:
                product_ids.append(prod.id)          
            qty_del=0.00
            total_price=0.00
            qty_price=0.00    
            query="""select distinct(sp.id) from account_invoice ai
                            inner join supp_delivery_invoice_rel rel on rel.invoice_id=ai.id
                            inner join stock_picking sp on sp.id=rel.del_ord_id
                            inner join account_invoice_line al on al.invoice_id=ai.id
                            
                            where ai.state in ('open','paid') 
                            and sp.delivery_date_function>=%s
                            and sp.delivery_date_function<=%s and sp.partner_id=%s"""
                            
                             
            if case.product_ids and query and not case.state_id:
                context.update({'product_id':case.product_id.id})
                cr.execute(query+" and ai.state !='cancel' and sp.product_id in %s",(case.from_date,case.to_date,case.partner_id.id,tuple(product_ids)))
                invoice_ids = [x[0] for x in cr.fetchall()]
                print "multi prod", invoice_ids
                
            elif case.state_id and query and not case.product_ids:
                print in_fac_state
                cr.execute(query,(case.from_date,case.to_date,case.partner_id.id))
#                 cr.execute(query +""" and ai.state !='cancel' and sp.state_id = %s""",(case.from_date,case.to_date,case.partner_id.id,case.state_id.id))
                st_ids = cr.fetchall()
                print "Both", st_ids     
                for x in st_ids:
                    st_id = stock_obj.browse(cr,uid,x[0])
                    if str(in_fac_state) in st_id.name:
                       print "only state", st_id.name
                       invoice_ids.append(x[0])
                print "only state", invoice_ids
            
            elif case.state_id and query and case.product_ids:
                st_ids =[]
                cr.execute(query+" and ai.state !='cancel' and sp.product_id in %s",(case.from_date,case.to_date,case.partner_id.id,tuple(product_ids)))
                st_ids = cr.fetchall()
                print "Both", st_ids     
                for x in st_ids:
                    st_id = stock_obj.browse(cr,uid,x[0])
                    print "only state", st_id.name,"-",case.state_id.name
                    if str(in_fac_state) in st_id.name:
                       print "only state", st_id.name
                       invoice_ids.append(x[0])
                                     
                print "Both", invoice_ids           
            else:
                cr.execute("""select distinct(sp.id) from account_invoice ai
                            inner join supp_delivery_invoice_rel rel on rel.invoice_id=ai.id
                            inner join stock_picking sp on sp.id=rel.del_ord_id
                            inner join account_invoice_line al on al.invoice_id=ai.id
                            where ai.state in ('open','paid') 
                            and sp.delivery_date_function>=%s
                            and sp.delivery_date_function<=%s
                           
                            and sp.partner_id=%s""",(case.from_date,case.to_date,case.partner_id.id))
                invoice_ids = [x[0] for x in cr.fetchall()]
            if invoice_ids:
                print '\nInvoice Id-',invoice_ids
#                 res = rep_obj.pentaho_report_action(cr, uid, 'Invoice Report', invoice_ids,None,None)                
                context.update({'sup':False})
                res=self.invoice_print(cr, uid, invoice_ids,case,qty_del,total_price,context)
        return res
                                
#             for i in in_ids:
#             
#                 invoice_ids.append(i[0])   
#                 inv=invoice_obj.browse(cr,uid,i[0])
#                 line_id=line_obj.search(cr,uid,[('invoice_id','=',i[0])])
#                 pick_line=[]
#     #                 invoice_ids = [x[0] for x in cr.fetchall()]
#                 for j in line_id:
#                     
#                         
#                     print qty_del
#                     inv_line=line_obj.browse(cr,uid,j)
#                     prod=inv_line.product_id.id
#                     if prod not in pick_line:
#                         pick_line.append(prod)
#                         cr.execute("""select sum(sp.del_quantity) as del_quantity,
#                         (select max(price_unit) from account_invoice_line al where al.invoice_id = %s and al.product_id=%s) as price_unit 
# 
#                         from stock_picking sp
#                         inner join supp_delivery_invoice_rel dl on sp.id = dl.del_ord_id
#                         
#                         where sp.product_id =%s
#                         and sp.partner_id =%s 
#                         and dl.invoice_id =%s """,(i[0],prod,prod,case.partner_id.id,i[0],))
#                         data1 = cr.fetchall()
#                         data=data1[0]
#                         qty_data=data[0]
#                         if qty_data:
#                             qty_del=qty_del+data[0]
#                             qty_price=data[0]*data[1]
#                             total_price=total_price+qty_price
#                             all_data.update({data[0]:data[1]})
#                             print i,'-',j,'-''data[0]',qty_price,'price-',data[0],'qty-',data[1]                    
# 
#             print 'all_data ',all_data
#             print 'qty_del ',qty_del
#             print 'total_price ',total_price    
#             print 'invoice_ids ',case.from_date,case.to_date,'-',len(invoice_ids),'-',invoice_ids
#             
#             if invoice_ids:
#                 print '\nInvoice Id-',invoice_ids
# #                 res = rep_obj.pentaho_report_action(cr, uid, 'Invoice Report', invoice_ids,None,None)                
#                 context.update({'sup':False})
#                 res=self.invoice_print(cr, uid, invoice_ids,case,qty_del,total_price,context)
# #             if case.product_id:
# #                 invoice_ids=invoice_obj.search(cr,uid,[('product_id','=',case.product_id.id),('date_invoice','>=',case.from_date),('date_invoice','<=',case.to_date)])
# #             else:
# #                 invoice_ids=invoice_obj.search(cr,uid,[('date_invoice','>=',case.from_date),('date_invoice','<=',case.to_date)])            
# # #             if case.product_id:
# # #                 stock_ids=stock_obj.search(cr,uid,[('partner_id','=',case.partner_id.id),('product_id','=',case.product_id.id),('delivery_date_function','>=',case.from_date),('delivery_date_function','<=',case.to_date)])
# # #             else:
# # #                 stock_ids=stock_obj.search(cr,uid,[('partner_id','=',case.partner_id.id),('delivery_date_function','>=',case.from_date),('delivery_date_function','<=',case.to_date)])
# #             
# #             if stock_ids:
# #                 cr.execute("select invoice_id from supp_delivery_invoice_rel where del_ord_id in %s",(tuple(stock_ids),))
# #                 invoice_ids = [x[0] for x in cr.fetchall()]
# #                 print 'All-',len(invoice_ids),'inv_ids-',invoice_ids,
# #                 inv_ids=invoice_obj.search(cr,uid,[('id','in',invoice_ids),('state','in',('open','paid'))])
# #                 length=len(inv_ids)
# #                 print '\nlenght of Invoice Id-',length
# #                 if inv_ids:
# #                     print '\nInvoice Id-',inv_ids
# #                     res = rep_obj.pentaho_report_action(cr, uid, 'Invoice Report', inv_ids,None,None)
#             
#             
#         return res


    def print_facilitator_inv_report(self,cr,uid,ids,context=None):
        if not context:
            context={}
        rep_obj = self.pool.get('ir.actions.report.xml')
        invoice_obj = self.pool.get('account.invoice')
        stock_obj = self.pool.get('stock.picking')
        line_obj=self.pool.get('account.invoice.line')
        all_data={}
        res={}
        res1={}
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment') 
        
#         pwriter = PdfFileWriter()
#         os.makedirs('/home/serveradmin/Desktop/temp')
        invoice_ids=[]
        for case in self.browse(cr,uid,ids):
            qty_del=0.00
            total_price=0.00
            qty_price=0.00              
            param_values={'partner_id':case.partner_id.id}
            print 'Sup-',case.partner_id.id,'-',case.partner_id.name
            if case.product_id:
                context.update({'product_id':case.product_id.id})
                cr.execute("""select distinct(ai.id) from account_invoice ai
                            inner join delivery_invoice_rel rel on rel.invoice_id=ai.id
                            inner join stock_picking sp on sp.id=rel.del_ord_id
                            where ai.state in ('open','paid') 
                            and sp.product_id=%s
                            and sp.delivery_date_function>=%s
                            and sp.delivery_date_function<=%s
                            and ai.type='out_invoice'
                            and sp.paying_agent_id=%s""",(case.product_id.id,case.from_date,case.to_date,case.partner_id.id))
                invoice_ids = [x[0] for x in cr.fetchall()]
            else:
                cr.execute("""select distinct(ai.id) from account_invoice ai
                            inner join delivery_invoice_rel rel on rel.invoice_id=ai.id
                            inner join stock_picking sp on sp.id=rel.del_ord_id
                            where ai.state in ('open','paid') 
                            and sp.delivery_date_function>=%s
                            and sp.delivery_date_function<=%s
                            and ai.type='out_invoice'
                            and sp.paying_agent_id=%s""",(case.from_date,case.to_date,case.partner_id.id))
                
                invoice_ids = [x[0] for x in cr.fetchall()]
                
            if invoice_ids:
                print '\nInvoice Id-',invoice_ids
    #                 res = rep_obj.pentaho_report_action(cr, uid, 'Invoice Report', invoice_ids,None,None)                
                context.update({'sup':True})
                res=self.invoice_print(cr, uid, invoice_ids,case,qty_del,total_price,context)
                            
        return res  
    
    
    def print_cust_facilitator_inv_report(self,cr,uid,ids,context=None):
        if not context:
            context={}
        rep_obj = self.pool.get('ir.actions.report.xml')
        invoice_obj = self.pool.get('account.invoice')
        stock_obj = self.pool.get('stock.picking')
        line_obj=self.pool.get('account.invoice.line')
        all_data={}
        res={}
        res1={}
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment') 
        
#         pwriter = PdfFileWriter()
#         os.makedirs('/home/serveradmin/Desktop/temp')
        invoice_ids=[]
        for case in self.browse(cr,uid,ids):
            qty_del=0.00
            total_price=0.00
            qty_price=0.00              
            param_values={'partner_id':case.partner_id.id}
            print 'Sup-',case.partner_id.id,'-',case.partner_id.name
            if case.product_id:
                context.update({'product_id':case.product_id.id})
                cr.execute("""select distinct(ai.id) from account_invoice ai
                            inner join supp_delivery_invoice_rel rel on rel.invoice_id=ai.id
                            inner join stock_picking sp on sp.id=rel.del_ord_id
                            where ai.state in ('open','paid') 
                            and sp.product_id=%s
                            and sp.delivery_date_function>=%s
                            and sp.delivery_date_function<=%s
                            and ai.type='in_invoice'
                            and sp.paying_agent_id=%s""",(case.product_id.id,case.from_date,case.to_date,case.partner_id.id))
                invoice_ids = [x[0] for x in cr.fetchall()]
            else:
                cr.execute("""select distinct(ai.id) from account_invoice ai
                            inner join supp_delivery_invoice_rel rel on rel.invoice_id=ai.id
                            inner join stock_picking sp on sp.id=rel.del_ord_id
                            where ai.state in ('open','paid') 
                            and sp.delivery_date_function>=%s
                            and sp.delivery_date_function<=%s
                            and ai.type='in_invoice'
                            and sp.paying_agent_id=%s""",(case.from_date,case.to_date,case.partner_id.id))
                
                invoice_ids = [x[0] for x in cr.fetchall()]
                
            if invoice_ids:
                print '\nInvoice Id-',invoice_ids
    #                 res = rep_obj.pentaho_report_action(cr, uid, 'Invoice Report', invoice_ids,None,None)                
                context.update({'facilitator':True})
                res=self.invoice_print(cr, uid, invoice_ids,case,qty_del,total_price,context)
                            
        return res    

    def get_month(self,cr,uid,ids,from_date,context):
        res=''
        f_month='' 
        f_month = datetime.fromtimestamp(time.mktime(time.strptime(from_date, "%Y-%m-%d")))
        res = tools.ustr(f_month.strftime('%B-%Y'))
        if context.get('month','')==1:
            res = tools.ustr(f_month.strftime('%m'))
        if context.get('year','')==1:
            res = tools.ustr(f_month.strftime('%Y'))
        if context.get('day','')==1:
            res = tools.ustr(f_month.strftime('%d'))            
        return res
        
    def print_monthly_dispatch_report(self,cr,uid,ids,context=None):
        if not context:
            context={}
        rep_obj = self.pool.get('ir.actions.report.xml')
        invoice_obj = self.pool.get('account.invoice')
        stock_obj = self.pool.get('stock.picking')
        line_obj=self.pool.get('account.invoice.line')
        all_data={}
        res={}
        res1={}
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment') 
        pick_ids=[]
#         pwriter = PdfFileWriter()
#         os.makedirs('/home/serveradmin/Desktop/temp')
        invoice_ids=[]
        for case in self.browse(cr,uid,ids):
            month_to=self.get_month(cr,uid,[],case.from_date,{'month':1}) 
            month_to=int(month_to)
            year_to=self.get_month(cr,uid,[],case.from_date,{'year':1})
            year_to=int(year_to)   

                                
            qty_del=0.00
            total_price=0.00
            qty_price=0.00              
            param_values={'partner_id':case.partner_id.id}
            print 'Sup-',case.partner_id.id,'-',case.partner_id.name
            context.update({'monthly_dispatch':True}) 
            if not case.summary:
                if case.partner_id:
                    cr.execute("select id from stock_picking where type='out' and state not in ('cancel') and partner_id= '" + str(case.partner_id.id) + "'and date::date = '" + str(case.from_date) + "'order by paying_agent_id desc")
                if not case.partner_id:
                    cr.execute("""
                      select sp.id

                      from stock_picking sp
                      inner join res_partner rp on rp.id = sp.partner_id
                      where sp.type='out' and sp.state not in ('cancel')
                      and sp.date::date= '""" + str(case.from_date) +"""'
                      order by sp.paying_agent_id desc""")

                # if context.get('adl'):
                #     cr.execute("""
                #       select sp.id
                #
                #       from stock_picking sp
                #       inner join res_partner rp on rp.id = sp.partner_id
                #       where sp.type='out' and sp.state not in ('cancel')
                #       and sp.date::date= '""" + str(case.from_date) +"""'
                #       and rp.ref ='ADL'
                #       order by sp.paying_agent_id desc""")

                pick_ids = [x[0] for x in cr.fetchall()]
                print "pick=",len(pick_ids)
                print "pick=",pick_ids
            if case.is_inout:
                context.update({'daily_dispatch':1, 'ddio_wiz':1})
            
            res=self.invoice_print(cr, uid, pick_ids,case,False,False,context)
                    
        return res    
                                
#             for i in in_ids:
#             
#                 invoice_ids.append(i[0])   
#                 inv=invoice_obj.browse(cr,uid,i[0])
#                 line_id=line_obj.search(cr,uid,[('invoice_id','=',i[0])])
#                 pick_line=[]
#     #                 invoice_ids = [x[0] for x in cr.fetchall()]
#                 for j in line_id:
#                     
#                         
#                     print qty_del
#                     inv_line=line_obj.browse(cr,uid,j)
#                     prod=inv_line.product_id.id
#                     if prod not in pick_line:
#                         pick_line.append(prod)
#                         cr.execute("""select sum(sp.del_quantity) as del_quantity,
#                         (select max(price_unit) from account_invoice_line al where al.invoice_id = %s and al.product_id=%s) as price_unit 
#                         
#                         
#                         
#                         from stock_picking sp
#                         inner join delivery_invoice_rel dl on sp.id = dl.del_ord_id
#                         
#                         where sp.product_id =%s
#                         and sp.paying_agent_id =%s 
#                         and dl.invoice_id =%s """,(i[0],prod,prod,case.partner_id.id,i[0],))
#                         data1 = cr.fetchall()
#                         data=data1[0]
#                         qty_data=data[0]
#                         if qty_data:
#                             qty_del=qty_del+data[0]
#                             qty_price=data[0]*data[1]
#                             total_price=total_price+qty_price
#                             all_data.update({data[0]:data[1]})
#                             print i,'-',j,'-''data[0]',qty_price,'price-',data[0],'qty-',data[1]                    
# 
#             print 'all_data ',all_data
#             print 'qty_del ',qty_del
#             print 'total_price ',total_price    
#             print 'invoice_ids ',case.from_date,case.to_date,'-',len(invoice_ids),'-',invoice_ids
#             
# #             if invoice_ids:
# #                 print '\nInvoice Id-',invoice_ids
# # #                 res = rep_obj.pentaho_report_action(cr, uid, 'Invoice Report', invoice_ids,None,None)                
# #                 context.update({'sup':True})
# #                 res=self.invoice_print(cr, uid, invoice_ids,case,qty_del,total_price,context)                
# #                 invoice_ids = [x[0] for x in cr.fetchall()]
# #                 
# #             print 'invoice_ids',len(invoice_ids),'-',invoice_ids
# #             
# #             if invoice_ids:
# #                 print '\nInvoice Id-',invoice_ids
# # #                 res = rep_obj.pentaho_report_action(cr, uid, 'MIS Facilitator Report', invoice_ids,None,None)
# #                 context.update({'sup':True})
# #                 res=self.invoice_print(cr, uid, invoice_ids,case,qty_del,total_price,context)            
#             
#             
#         return res


     #To Print Invoice Group Report
    def invoice_print(self, cr, uid, ids, case,qty_del,total_price,context=None):
        if not context:
            context={}
        start_date=False
        data = {}
        data['ids'] = ids
        id=0
        if ids:
            id=ids[0]
        data['model'] = context.get('active_model', 'ir.ui.menu')            
        rep_obj = self.pool.get('ir.actions.report.xml')
        datas={}
        month_to=self.get_month(cr,uid,[],case.from_date,{'month':1}) 
        month_to=int(month_to)
        year_to=self.get_month(cr,uid,[],case.from_date,{'year':1})
        year_to=int(year_to)  
        product_id = context.get('product_id',False)    
        partner=context.get('sup',False)
        facilitator=context.get('facilitator',False)
        monthly_dispatch=context.get('monthly_dispatch',False)
#         context.update({'xls_export': 1,'width':'0.67"','height':'0.21"'}) 
        data['context']=context
        end_date='' 
        today = time.strftime('%Y-%m-%d')
        
        summary = context.get('summary',case.summary)
        if partner:
            report_name = 'MIS Facilitator Report' 
            if product_id:
               report_name = 'Sup Invoice Report With Product'  
        elif facilitator:
            report_name = 'MIS Facilitator Invoice'
            if product_id:
                report_name = 'Sup_cust Invoice report with product'
        elif monthly_dispatch:
            data['output_type'] = 'xls' 
            if context.get('pdf',False):
                data['output_type'] = 'pdf'             
            if summary:
#                 data['output_type'] = 'pdf' 
                report_name = 'monthly_dispatch'
                st_date = datetime.strptime(case.from_date, '%Y-%m-%d').strftime('%Y-%m-%d')
                cr.execute("select cast(date_trunc('month', '"+ str(st_date) +"'::date) as date)")
                start_date=cr.fetchone()
                if start_date:start_date=start_date[0]
                 
                cr.execute("SELECT (date_trunc('MONTH', '"+ str(st_date) +"'::date) + INTERVAL '1 MONTH - 1 day')::date;")
                end_date=cr.fetchone()  
                if end_date:end_date=end_date[0]              
#                 day_to1=self.get_month(cr,uid,[],case.from_date,{'day':1}) 
#                 day_to=int(day_to1)-1
#                 start_date = datetime.strptime(case.from_date, '%Y-%m-%d') - relativedelta(days=int(day_to))
#                  
#                 end_d=calendar.monthrange(year_to,month_to)[1]   
#                 end_d=int(end_d)  
                 
#                 end_date = datetime.strptime(case.from_date, '%Y-%m-end_d')
#                 end_date=str(year_to)+'-'+str(month_to)+'-'+str(end_d)
            else:
                report_name=  'dispatches'    
#                 data['output_type'] = 'pdf'                  
        
        else:
            report_name=  'MIS Invoice Report'
            if product_id:
                report_name=  'Cust Invoice Report With Product'
            
#         print "ids",ids
#         print "report_name",report_name,".",data['output_type']
        from_date = datetime.strptime(case.from_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        if case.report_type and not monthly_dispatch:
            if case.report_type=='pdf':
                data['output_type'] = 'pdf'
            elif case.report_type=='xls':
                data['output_type'] = 'xls'
        total=total_price
        print "Total Quantity",qty_del
        print "Total Amount",total_price
        
        
        data['variables'] = {
                             'partner_id': case.partner_id.id,
                             'from_date':from_date,
                             'to_date':case.to_date,
                             'qty_del':qty_del,
                             'total':total_price,
                             'start_date':start_date,
                             'end_date':from_date,
                             'month':month_to,
                             'year':year_to,
                             'product_id':product_id,
                             'id':id,
                            }

        if context.get('daily_dispatch') and not context.get('ddio_wiz'):
            report_name = 'daily_dispatch_in_out'
            data['output_type'] = 'xls'
            prev_date = (datetime.strptime(today, '%Y-%m-%d') - relativedelta(days=int(1))).strftime('%Y-%m-%d')
            print "prev_date...........",prev_date
            data['ids'] = []
            data['variables'] = {
                                 'from_date':   prev_date,
                                }
             
        if context.get('ddio_wiz'):

            report_name = 'daily_dispatch_in_out'
            data['output_type'] = 'xls'
            data['ids'] = []
            data['variables'] = {
                                 'from_date':   case.from_date,
                                }
                 
        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'name' : report_name,
        'datas': data,
            }
    
   
    
    def onchange_type(self, cr, uid, ids, type = False, context=None):
        res ={} 
        dom=''
        
        if  type:
            if type=='in_invoice' or type=='in_refund':
                dom = {'partner_id':  [('supplier','=', True)]}
            elif type=='out_invoice' or type=='out_refund':
                dom = {'partner_id':  [('customer','=', True)]}
        return{'value':res ,'domain':dom}    
invoice_group_report()

class facilitator_report(osv.osv_memory):
    _name = 'facilitator.report'
    _columns = {
                'state_id'     : fields.many2one('res.country.state','State'),
                 'partner_id'  : fields.many2one('res.partner',"Facilitator"),
                'report_type'  : fields.selection([('balance','Facilitator Outstanding Balance'),('estimate','Facilitator Estimate Balance')],'Report Type'),
                }
    def print_report(self, cr, uid, ids, context = None):
        part_obj = self.pool.get('res.partner')
        partner_ids =[]
        today = time.strftime('%Y-%m-%d')
        cr.execute("select date_start from account_fiscalyear where date_start <= '" + str(today) + "' and date_stop >='" + str(today) + "' limit 1" )
        st_date = cr.fetchall()[0]
        
        for case in self.browse(cr, uid, ids):
            report_name = 'Facilitator Estimate'
            if case.report_type == 'balance':
                report_name = 'Facilitator Balance'
            
#             if case.state_id and not case.partner_id:
#                 partner_ids = part_obj.search(cr, uid, [('name','not ilike','%Kingswood%'),('state_id','=',case.state_id.id),('supplier','=',True),('handling_charges','!=',True)])
#             elif case.partner_id:
#                 partner_ids.append(case.partner_id.id)
#             else:
#                 partner_ids = part_obj.search(cr, uid, [('name','not ilike','%Kingswood%'),('supplier','=',True),('handling_charges','!=',True)])
        
        data = {}
        data['variables'] = {
                             'st_id'  : case.state_id and case.state_id.id or 0,
                             'p_id'   : case.partner_id and case.partner_id.id or 0,
                             'st_date': st_date and st_date[0] or False
                             }
        print "variables", data['variables']
        data['ids'] = ids
        data['output_type'] = 'pdf'
        data['model'] = context.get('active_model', 'ir.ui.menu')
        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'name' : report_name,
        'datas': data,
            }
facilitator_report()

class fac_billing_cyle(osv.osv_memory):
    _name = 'fac.billing.cycle'
    _columns = {
                'partner_id'  : fields.many2one('res.partner','Facilitator'),
                'date_to'     : fields.date('Date'),
                
                }
    
    def generate_invoice(self, cr, uid, ids, context=None):
        context = dict(context or {})
        invObj = self.pool.get('account.invoice')
        billObj = self.pool.get('billing.cycle')
        
        for case in self.browse(cr, uid, ids):
            context.update({
                           'shedular_date' : case.date_to,
                           'facilitator'   : case.partner_id.id,
                           'state'         : case.partner_id.state_id and  case.partner_id.state_id.name or ''
                           })
            # need to check the cilling cycle already created for this date
            billing_list = billObj.search(cr,uid,[('partner_id','=',case.partner_id.id),('end_date','=',case.date_to)],order='end_date desc',limit=1)
            if billing_list:
                raise osv.except_osv(_('Warning'),_("Billing Cycle already exists!. Please delete the billing cycle and generate again"))
            
            invObj.create_facilitator_inv(cr, uid, ids, context)
            


fac_billing_cyle()

class delivery_import(osv.osv_memory):
    _name = 'delivery.import'

    _columns= {
            'dc_file'       :   fields.binary("DC File")
            }


    def confirm(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        pick_obj = self.pool.get("stock.picking.out")
        mail_obj = self.pool.get('mail.mail')
        email_obj = self.pool.get('email.template')
        temp_obj = self.pool.get('email.template')
        partner_obj = self.pool.get('res.partner')
        partners = ''

        today = time.strftime('%Y/%m/%d')
        print "today............",today
        datafile = 'DC_FILE.xlsx'
        p_id = 0
        workbook1 = Workbook(datafile)
        sheet1 = workbook1.add_worksheet()

        left_size = workbook1.add_format({'align': 'left', 'bold': False})
        left_size.set_font_name('Serif')
        left_size.set_font_size(10)

        bold_left = workbook1.add_format({'align': 'left', 'bold': True})
        bold_left.set_font_name('Serif')
        bold_left.set_font_size(12)


        for case in self.browse(cr, uid, ids):
            if case.dc_file:
                out_filename = tempfile.mktemp(suffix=".xls", prefix="webkit.tmp.")
                fp = open(out_filename, 'wb+')
                fp.write((base64.b64decode(case.dc_file)))
                fp.close()

                book = open_workbook(out_filename)
                print "book",book
                sheet = book.sheet_by_index(0)

                # read header values into the list
                keys = [sheet.cell(0, col_index).value for col_index in xrange(sheet.ncols)]

                dict_list = []
                for row_index in xrange(1, sheet.nrows):
                    d = {keys[col_index]: sheet.cell(row_index, col_index).value
                         for col_index in xrange(sheet.ncols)}
                    dict_list.append(d)

                print "dict_list..............", dict_list
                r = 2
                cl = 0
                sheet1.write(r-2, cl, 'DC Number', bold_left)
                sheet1.write(r-2, cl+1, 'Error', bold_left)

                for dc in dict_list:
                    cr.execute("select id from stock_picking where name='"+str(dc.get('DC Number'))+"' ")
                    pick_id = [x[0] for x in cr.fetchall()]
                    if pick_id:
                        pick_id = pick_id[0]
                        pick = pick_obj.browse(cr, uid, pick_id)
                        if pick.state != 'in_transit':
                            raise osv.except_osv(_('Warning'),_('Delivery Order "%s" Should Be In Transit State')% (pick.name,))
                        if dc.get('Delivery Date') > today:
                            raise osv.except_osv(_('Warning'),_('Please enter the Valid Delivery Date for Delivery Order "%s", ')% (pick.name,))

                        if (dc.get('Delivered Qty')>0 and dc.get('Rejected Qty')>0) and  dc.get("Deduction Amount") <=0 :
                            raise osv.except_osv(_('Warning'),_('Enter Deduction Amount for "%s", ')% (pick.name,))

                        cr.execute(""" update stock_move set unloaded_qty="""+str(dc.get('Delivered Qty'))+""",
                                        rejected_qty ="""+str(dc.get('Rejected Qty'))+""",
                                        delivery_date = '""" +str(dc.get('Delivery Date'))+ """',
                                        deduction_amt = """+str(dc.get('Deduction Amount'))+"""
                                        where picking_id ="""+str(pick_id)+"""

                                  """)
                        try:
                            pick_obj.deliver(cr, uid, [pick_id], context=context)
                            print "=============>",pick_id
                        except Exception as e:
                            _logger.info('Error reason %s',e,pick.name)
                            sheet1.write(r,cl, pick.name, left_size)
                            sheet1.write(r,cl+1, e.value, left_size)
                            p_id = pick.id
                            r += 1

                if p_id > 0:
                    workbook1.close()
                    fp = open(datafile, 'rb')
                    contents = fp.read()
                    result = base64.b64encode(contents)
                    template = self.pool.get('ir.model.data').get_object(cr, uid, 'kingswood', 'kw_dc_file')
                    file_name = 'DC_FILES.xls'

                    cr.execute(""" select ru.partner_id
                                    from res_groups_users_rel gu
                                    inner join res_groups g on g.id = gu.gid
                                    inner join res_users ru on ru.id = gu.uid
                                    where g.name = 'KW_Admin'""")

                    for p in cr.fetchall():
                        p = partner_obj.browse(cr, uid,p[0])
                        if p.email and p.email not in partners:
                            partners += (p.email and p.email or "") + ","



                    _logger.info('DC Mail Before==========================> %s',partners[0:-1])
                    if partners:
                        email_obj.write(cr, uid, [template.id], {'email_to':partners[0:-1]})


                    attach_ids = self.pool.get('ir.attachment').create(cr, uid,
                                                              {
                                                               'name': file_name,
                                                               'datas': result,
                                                               'datas_fname': file_name,
                                                               'res_model': 'stock.picking.out',
                                                               'res_id': p_id,
                                                               'type': 'binary'
                                                              },
                                                              context=context)


                    temp_obj.dispatch_mail(cr,uid,[template.id],attach_ids,context)
                    print "template ......",template.id
                    mail_id = self.pool.get('email.template').send_mail(cr, uid, template.id, p_id, True, context=context)
                    cr.execute("delete from email_template_attachment_rel where email_template_id="+str(template.id))
                    cr.execute("delete from ir_attachment where lower(datas_fname) like '%DC_FILES%'")

        res = {}

        return res



delivery_import()


    
# class stock_partial_picking(osv.osv):
#     _inherit = 'stock.partial.picking'
#     
#     def do_partial(self, cr, uid, ids, context=None):
#         if not context:
#             context={}
#         stock_obj=self.pool.get('stock.picking.out')
#         pick_ids=context.get('active_ids',[])
#         type=context.get( 'default_type','')
#         res= {}
#         res=super(stock_partial_picking,self).do_partial(cr, uid, ids,context)
#         
#         for pick in stock_obj.browse(cr, uid, pick_ids):
#             if pick.partner_id.contract_ids:
#                 qty_pending = 0.00
#                 from_date = False
#                 to_date = False
#                 pick_date = False
#                 for cntrt in pick.partner_id.contract_ids:
#                     from_date = cntrt.from_date + ' 00:00:00'
#                     from_date = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S')
#                     to_date = cntrt.to_date + ' 23:59:59'
#                     to_date = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S')
#                     pick_date = datetime.strptime(pick.date, '%Y-%m-%d %H:%M:%S')
#                     if pick.product_id.id == cntrt.product_id.id and pick_date >= from_date and pick_date <= to_date:
#                         qty_pending = cntrt.qty_pending
# #                         cr.execute("update customer_contracts set qty_pending ="+str(qty_pending)+" where partner_id="+str(pick.partner_id.id))
#     
#         return res
# stock_partial_picking()
    
    