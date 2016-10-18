from openerp.osv import fields,osv
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from openerp.tools.translate import _
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
                }


    def gp_report(self, cr, uid, ids, context=None):
        if not context:
            cntext={}
        report_data = []
        partner_obj = self.pool.get("res.partner")
        prod_obj = self.pool.get("product.product")
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
            data['variables'] = {
                                 'from_date'    : case.from_date,
                                 'to_date'      : case.to_date,
                                 'partner_id'   : partner_id,
                                 'product_id'   : product_id,

                                 }

        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'datas': data,
            }

gross_profit_wiz()