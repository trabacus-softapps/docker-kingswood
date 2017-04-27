from openerp.osv import fields,osv
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from openerp.tools.translate import _
import base64
import netsvc
from openerp import netsvc
import pytz
import logging
_logger = logging.getLogger(__name__)
import re

# from PyPDF import PdfFileReader, PdfFileWriter

class kw_freight(osv.osv_memory):
    _name="kw.freight"
    _columns={
              'no_freight'        :   fields.boolean('With Freight'),
              'loaded_qty'        :   fields.float('Loaded Quantity (MT)',digits=(0,3),track_visibility='onchange'),
              'facilitator_id'    :   fields.many2one('res.partner','Facilitator'),
              'customer_id'       :   fields.many2one('res.partner','Customer'),
              'from_date'         :   fields.date('From'),
              'to_date'           :   fields.date('To'),   
              'pick_type'         :   fields.selection([('in','Incoming Shipment'),('out','DC')],'Type', select=True,track_visibility='onchange',),
              'company_id'        :   fields.many2one('res.company','Company'),
              'state_id'          :   fields.many2one('res.country.state','State'),  
              'product_id'        :   fields.many2one('product.product','Product'),        
              
              }
    _defaults={
                'no_freight' : False,
                'from_date': lambda *a: time.strftime('%Y-%m-%d'),
                 'to_date': lambda *a: time.strftime('%Y-%m-%d'),
                 'pick_type' : 'out',
              }
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
    
    def get_freight(self,cr,uid,ids,context=None):
        stock_pick_obj=self.pool.get("stock.picking.out")
        for case in self.browse(cr, uid, ids):
            stock_pick_obj.get_invoice(cr,uid,context['active_ids'],case.no_freight,context=None)
        
        return True
    
    def freight_report(self,cr,uid,ids,context=None):
        if not context: context={}
        state_id = 0
        purchase_report = context.get('purchase_report',False)
        freight_report = context.get('freight_report',False)
        hc_report = context.get('hc',False)
        rep_obj = self.pool.get('ir.actions.report.xml')
        stock_obj=self.pool.get("stock.picking.out")
        from_date = time.strftime('%Y-%m-%d')  
        to_date = time.strftime('%Y-%m-%d')   
        stock_ids =[]
        company_id = 0
        query =" " 
        facilitator_id = 0
        customer_id = 0
        product_id = 0
        data = {}
        for case in self.browse(cr, uid, ids):
            from_date = datetime.strptime(case.from_date, '%Y-%m-%d').strftime('%Y-%m-%d')
            to_date = datetime.strptime(case.to_date, '%Y-%m-%d').strftime('%Y-%m-%d') 
                
            if case.facilitator_id:
                facilitator_id = case.facilitator_id.id
                
            if case.customer_id:
                customer_id = case.customer_id.id
                
            if case.product_id:
               product_id =  case.product_id.id                  
            if case.state_id:
                state_id = case.state_id.id 
#                     query = query + " and sp.state_id = "+str(case.state_id.id)       
            if case.company_id: 
                company_id = case.company_id.id  
            if case.pick_type:
                pick_type = str(case.pick_type)                              
            if freight_report:
                report_name = "Freight Report"

            if purchase_report:
                report_name = "Purchase Report"  
            
            if hc_report:    
                report_name = 'HC Purchase Report'
            
            if context.get('purchase_recon_report'):
                report_name = "Purchase Reconciliation Report"
                  
            print 'stock_ids',len(stock_ids),"stocks",stock_ids 
            print 'From',from_date          
#             if stock_ids:
#                 res = rep_obj.pentaho_report_action(cr, uid, 'Freight Charge Details', stock_ids,None,None)
        
        data['variables'] = { 'from_date' : from_date , 
                             'to_date' : to_date,
                             'inv_company': company_id,
                             'state_id':state_id,
                             'customer_id':customer_id,
                             'facilitator_id':facilitator_id,
                             'product_id' : product_id,
                              #'pick_type' : pick_type
                             }
        print "date",data['variables']
        data['ids'] = stock_ids
        data['output_type'] = 'xls'
        data['model'] = context.get('active_model', 'ir.ui.menu')
        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'name' : report_name,
        'datas': data,
            }
                
  
    
 
    
kw_freight()

  
   


class delivery_summary(osv.osv_memory):
    _name = "del.sumwiz"
    
    def get_partner_id(self, cr, uid, context=None):
        user_id = self.pool.get('res.users').browse(cr,uid, [uid])[0]
        if user_id.role == 'supplier':
            return user_id.partner_id.id
        return False
    
    def get_invoice_date(self, cr, uid, context =None):
        inv_obj = self.pool.get('account.invoice')
        user_id = self.pool.get('res.users').browse(cr,uid, uid)
        date = False
        if user_id.role == 'supplier':
            inv_ids = inv_obj.search(cr, uid, [('partner_id','=',user_id.partner_id.id),('date_invoice','!=',False)],order="date_invoice desc", limit=1)
            for i in inv_obj.browse(cr, uid,inv_ids ):
                date = i.date_invoice
        return date
    
    _columns = {
                'st_date'         : fields.date('Start Date'),
                'end_date'        : fields.date('End Date'),
                'invoice_date'    : fields.date('Last Invoice Date'),
                'partner_id'      : fields.many2one('res.partner','Supplier'),
                'unpaid_inv'      : fields.boolean('Detailed Summary'),
                  
                
                }
    _defaults = {
                 'partner_id'    : get_partner_id,
                 'invoice_date'  : get_invoice_date,
                 'unpaid_inv'    : True
                 }
    
    def onchange_partner_id(self, cr, uid, ids,partner_id):
        inv_obj = self.pool.get('account.invoice')
        res = {}
        if partner_id:
            inv_ids = inv_obj.search(cr, uid, [('partner_id','=',partner_id),('date_invoice','!=',False)],order="date_invoice desc", limit=1)
            for i in inv_obj.browse(cr, uid,inv_ids ):
                res.update({'invoice_date' :i.date_invoice})
        return {'value':res}
    
    def print_report(self, cr, uid, ids, context = None):
        inv_obj = self.pool.get('account.invoice')
        freight = False
        for case in self.browse(cr, uid, ids):
            if case.st_date > case.end_date:
                raise osv.except_osv(_('Warning'),_('Please enter valid Start and End dates'))
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
    
            data['output_type'] = 'pdf'
            
#             st_date = (parser.parse(''.join((re.compile('\d')).findall(case.st_date)))).strftime('%d/%m/%Y 00:00:00')
#             end_date = (parser.parse(''.join((re.compile('\d')).findall(case.end_date)))).strftime('%d/%m/%Y 12:00:00')
            
            #to check whether all invoices are validated
            
            #to fetch the latest invoice creation_date from invoice table
            st_date = case.st_date
            if case.unpaid_inv:
                cr.execute("select date::date from account_voucher where partner_id = "+ str(case.partner_id.id)+" and date <= '"+case.end_date+"' and state = 'posted' and amount = 0 order by date::date desc limit 1")
                #cr.execute("select date_invoice::date from account_invoice where partner_id = "+ str(case.partner_id.id)+" and date_invoice <= '"+case.end_date+"' and state = 'paid' order by date_invoice::date desc limit 1")

                inv_date = cr.fetchone()
                print "inv_date",inv_date
                
                #to check whether to display the freight paid amount in report or not 
                in_ids = inv_obj.search(cr, uid, [('date_invoice','<=',case.end_date),('state','=','open'),('partner_id','=',case.partner_id.id)])
                for invoice in inv_obj.browse(cr, uid, in_ids):
                    if invoice.origin == 'IN':
                        freight = True
                        break
                
                if inv_date:
                    st_date = inv_date and inv_date[0] or case.st_date
            
            # to get the financial year start date
            cr.execute("select date_start from account_fiscalyear where date_start <= '" + case.st_date + "' and date_stop >='" + case.st_date + "' limit 1")
            fydate = cr.fetchone()
            if not fydate:
                raise osv.except_osv(_('Warning'),_('There is No valid FiscalYear Defined in the System'))
            else:
                fy_st_date = fydate[0]
                
            data['variables'] = {
                                 'st_date'           : case.st_date,
                                 'end_date'          :case.end_date,
                                 'supplier'          :case.partner_id.id,
                                 'unpaid'            :case.unpaid_inv and "True" or '',
                                 'unpaid_st_date'    : case.st_date,
                                 'supplier_name'     : case.partner_id.name or '',
                                 'freight'           : freight,
                                 'fy_st_date'        : fy_st_date,
                                 }
            print "data",data['variables']
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'delivery_summary',
            'datas': data,
                }
    
delivery_summary()

class account_voucher(osv.osv):
    _name = 'account.voucher'
    _inherit = 'account.voucher'
    _columns = {
                #to check whether voucher has been created from freight
                'freight'    :  fields.boolean('Is Freight')
                }
    _defaults={
               'freight' : False
               }
account_voucher()



# class delivery_challan(osv.osv_memory):
#      _name = "del.challan"
#      
#      def print_report(self, cr, uid, ids, context = None):
#         res = rep_obj.pentaho_report_action(cr, uid, 'Delivery_Challan', [active_id],None,None)
#         
#         
#         return res  
    
# delivery_challan()

# class stock_return_picking(osv.osv_memory):
#     _inherit = 'stock.return.picking'
#     
#     def create_returns(self, cr, uid, ids, context=None):
#         res=super(stock_return_picking,self).create_returns(self, cr, uid, ids)
#         return res
    

class invoice_merge_wiz(osv.osv_memory):
    _name = 'invoice.merge.wiz'
    _columns = {
                #to check whether voucher has been created from freight
                'date'        :  fields.date('Date'),
                'supplier_id' :  fields.many2one('res.partner','Facilitator'),
                'state_id'  :   fields.many2one('res.country.state','State'),
                'company_id' :  fields.many2one('res.company','Company'),
                }
    _defaults={
               'date' : False
               }
    
    def invoice_merge(self, cr, uid, ids, context = None):
       inv_obj=self.pool.get('account.invoice')
       comp_obj = self.pool.get('res.company')
       company=[]
       if not context:
           context={}
       for case in self.browse(cr,uid,ids):
           if case.company_id:
               company.append(case.company_id.id)
           
           if not company:
               company = comp_obj.search(cr,uid,[])
               
           context.update({'in_date':case.date})
           if case.supplier_id:
               context.update({'supplier_id':case.supplier_id.id})
           for comp in company:
               context.update({'comp_id':comp})
               res=inv_obj.do_merge_facilitator(cr,uid,False,False,context=context)
       return res 
   
    def invoice_amount(self, cr, uid, ids, context = None):
       inv_obj=self.pool.get('account.invoice')
       if not context:
           context={}
       for case in self.browse(cr,uid,ids):
           context.update({'in_date':case.date})
           res=inv_obj.add_amount(cr,uid,ids,context=context)
       return res   

    def invoice_create(self, cr, uid, ids, context = None):
       inv_obj=self.pool.get('account.invoice')
       if not context:
           context={}
       for case in self.browse(cr,uid,ids):
           context.update({'shedular_date':case.date,'state':str(case.state_id.name).lower()})
           inv_obj.create_facilitator_inv(cr,uid,ids,context=context)
#            inv_obj.create_facilitator_inv_in(cr,uid,ids,context=context)
       return True

    
invoice_merge_wiz()


class gross_profit_wiz(osv.osv):
    _name = 'gross.profit.wiz'

    _columns = {
                'from_date'     :   fields.date("From Date"),
                'to_date'       :   fields.date("To Date"),
                'partner_id'    :   fields.many2one("res.partner", "Customer"),
                'product_id'    :   fields.many2one("product.product", "Product"),
                'state_id'      :   fields.many2one("res.country.state", "State"),
                }


    def gp_report(self, cr, uid, ids, context=None):
        if not context:
            cntext={}
        report_data = []
        partner_obj = self.pool.get("res.partner")
        prod_obj = self.pool.get("product.product")
        state_obj = self.pool.get("res.country.state")
        for case in self.browse(cr, uid, ids):
            report_name = 'Gross Profit Report'
            data={}
            data['ids'] = ids
            data['model'] = context.get('active_model','ir.ui.menu')
            data['output_type'] = 'pdf'
            if not case.partner_id:
                partner_id = partner_obj.search(cr, uid, [('customer','=',True)])
            else:
                partner_id = case.partner_id.id
            if not case.product_id:
                product_id = prod_obj.search(cr, uid, [])
            else:
                product_id = case.product_id.id
            if case.state_id:
                state_id = case.state_id.id
            if not case.state_id:
                state_id = state_obj.search(cr, uid, [])

            data['variables'] = {
                                 'from_date'    : case.from_date,
                                 'to_date'      : case.to_date,
                                 'partner_id'   : partner_id,
                                 'product_id'   : product_id,
                                 'state_id'     : state_id,

                                 }

        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'datas': data,
            }

gross_profit_wiz()


class bank_details_wiz(osv.osv):
    _name = 'bank.details.wiz'

    _columns = {
                'from_date'     :   fields.date("From Date"),
                'to_date'       :   fields.date("To Date"),
                'partner_id'    :   fields.many2one("res.partner", "Customer"),
                'state_id'      :   fields.many2one("res.country.state", "State"),
                'picking_id'    :   fields.many2one("stock.picking", "DC Number")
                }


    _defaults = {
                'from_date' : lambda *a: time.strftime('%Y-%m-%d'),
                'to_date'   : lambda *a: time.strftime('%Y-%m-%d'),
                }

    def bank_details_report(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        rep_obj = self.pool.get('ir.actions.report.xml')
        today = time.strftime('%Y-%m-%d')
        mail_obj = self.pool.get('mail.mail')
        email_obj = self.pool.get('email.template')
        user_obj = self.pool.get('res.users')
        mail_compose = self.pool.get('mail.compose.message')
        print_report = True
        partner_obj = self.pool.get('res.partner')
        model_obj = 'stock.picking.out'
        temp_obj = self.pool.get('email.template')
        file_name = "bank_acc_details.xls"
        variables = {}
        partners = ''
        pick_obj = self.pool.get('stock.picking.out')

        template = self.pool.get('ir.model.data').get_object(cr, uid, 'kingswood', 'kw_bank_details_mail')

        cr.execute(""" select ru.partner_id
                        from res_groups_users_rel gu
                        inner join res_groups g on g.id = gu.gid
                        inner join res_users ru on ru.id = gu.uid
                        where g.name = 'KW_Admin'""")
        # By Praveen
        # if context.get('adl'):
        #     cr.execute("select id from res_partner where ref ='ADL'")

        for p in cr.fetchall():
            p = partner_obj.browse(cr, uid,p[0])
            if p.email and p.email not in partners:
                partners += (p.email and p.email or "") + ","
        if partners:
            email_obj.write(cr, uid, [template.id], {'email_to':partners[0:-1]})

        print_report = self.print_bank_report(cr, uid, ids, context)


        report = print_report['datas']
        if report:
            variables = report['variables']
        report_service = "report." + 'Bank Details'

        service = netsvc.LocalService(report_service)
        (result, format) = service.create(cr, uid, ids, {'model': 'bank.details.wiz','variables':variables}, context)
        result = base64.b64encode(result)

        if ids:
            for case in self.browse(cr, uid, ids):
    #                 (result, format) = service.create(cr, uid, ids, {'model': 'stock.picking.out'}, context)
    #                 result = base64.b64encode(result)
                attach_ids = self.pool.get('ir.attachment').create(cr, uid,
                                                          {
                                                           'name': file_name,
                                                           'datas': result,
                                                           'datas_fname': file_name,
                                                           'res_model': 'bank.details.wiz',
                                                           'res_id': case.id,
                                                           'type': 'binary'
                                                          },
                                                          context=context)

                temp_obj.write(cr, uid, [template.id], {'attachment_ids' : [(6, 0, [attach_ids])]}, context)
                temp_obj.dispatch_mail(cr,uid,[template.id],attach_ids,context)


            pick_ids = print_report['datas']['variables'].get('pick_ids')
            if pick_ids:
                # Calling Pay Freight Function
                for pick in pick_obj.browse(cr, uid, pick_ids):
                    cust_uid = user_obj.search(cr, uid, [('partner_id','=',pick.partner_id.id)])
                    if cust_uid and pick.freight_charge > 0:
                        pick_obj.kw_pay_freight(cr, cust_uid[0], [pick.id], context)

            # Send Email to Admin
            mail_id = self.pool.get('email.template').send_mail(cr, uid, template.id, case.id, True, context=context)
            mail_state = mail_obj.read(cr, uid, mail_id, ['state'], context=context)
            try:
                if mail_state and mail_state['state'] == 'exception':
                    mail_state=mail_state
            except:
                pass

            cr.execute("""update stock_picking set is_bank_submit = true where id in %s""",(tuple(pick_ids),))



        return print_report


    def print_bank_report(self, cr, uid, ids, context=None):
        if not context:
            cntext={}
        report_data = []
        partner_id = []
        state_id = []
        part_obj = self.pool.get("res.partner")
        state_obj = self.pool.get("res.country.state")

        for case in self.browse(cr, uid, ids):
            report_name = 'Bank Details'
            data={}
            data['ids'] = ids
            data['model'] = context.get('active_model','ir.ui.menu')
            data['output_type'] = 'xls'

            if case.partner_id:
                partner_ids = case.partner_id.id
                partner_ids = "(" + str(partner_ids) +")"
            else:
                partner_ids = part_obj.search(cr, uid, [('customer','=', True)])
                partner_ids = tuple(partner_ids)
            if case.state_id:
                state_ids = case.state_id.id
                state_ids = "(" + str(state_ids) +")"
            else:
                state_ids = state_obj.search(cr, uid, [])
                state_ids = tuple(state_ids)

            cr.execute("""
                select

                distinct(sp.id) as pick_id

                from stock_picking sp
                where sp.state = 'done'
                and sp.delivery_date_function::date >= '"""+str(case.from_date)+"""' and sp.delivery_date_function::date <= '"""+str(case.to_date)+"""'
                and sp.is_bank_submit != True and sp.frieght_paid != True and sp.freight_balance > 0
                and sp.partner_id  in """+str(partner_ids)+"""
                and sp.state_id in """+str(state_ids)+"""

            """)
            pick_ids = [x[0] for x in cr.fetchall()]
            _logger.info('Picking IDs ==============> %s',pick_ids)
            if pick_ids:
                data['variables'] = {
                                     'pick_ids' : pick_ids
                                     }
            else:
                raise osv.except_osv(_('Warning'),_('There are no Delivery Challan for the Date Range.'))
        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'datas': data,
            }

    def print_dc_bank(self, cr, uid, ids, context=None):
        if not context:
            cntext={}
        report_data = []

        for case in self.browse(cr, uid, ids):
            report_name = 'Individual DC Bank Details'
            data={}
            data['ids'] = ids
            data['model'] = context.get('active_model','ir.ui.menu')
            data['output_type'] = 'xls'

            if case.picking_id:
                data['variables'] = {
                                     'picking_id'   : case.picking_id and case.picking_id.id or False,
                                     }
        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'datas': data,
            }



bank_details_wiz()