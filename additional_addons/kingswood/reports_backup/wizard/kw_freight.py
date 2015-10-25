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
              'no_freight'    :   fields.boolean('With Freight')
              
              }
    _defaults={
                'no_freight' : False
              }
    
    def get_freight(self,cr,uid,ids,context=None):
        stock_pick_obj=self.pool.get("stock.picking.out")
        for case in self.browse(cr, uid, ids):
            stock_pick_obj.get_invoice(cr,uid,context['active_ids'],case.no_freight,context=None)
        
        return True
    
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
    

