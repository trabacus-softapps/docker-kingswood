from openerp.osv import fields,osv
from openerp.osv import orm
from openerp.tools.translate import _
import amount_to_text_softapps
import openerp.addons.decimal_precision as dp
from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
import time
from lxml import etree
from datetime import datetime
import openerp.addons.decimal_precision as dp
import openerp.exceptions

from openerp import netsvc
from openerp import pooler

from openerp import tools
from openerp.tools.safe_eval import safe_eval as eval

class account_invoice(osv.osv):
    _inherit="account.invoice"
    
#     def _get_type(self, cr, uid, ids, args, field_name, context = None):
#         res = {}
#         for case in self.browse(cr, uid, ids):
#             for temp in case.incoming_shipment_ids:
#                 if case.incoming_shipment_ids:
#                     res[case.id] = {'invoice_type': " "}
#                     res[case.id]['invoice_type']  = 'Incoming Shipment'
#                     case.origin = 'Incoming Shipment'
# #                 res[case.id]['qty']  = temp.product_qty  
#         return res 

   
   #overidden 
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        res = super(account_invoice,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            if context.get('type', 'False') == 'in_refund':
                for field in res['fields']:
                    if field == 'partner_id':
                        res['fields'][field]['domain'] = [('supplier','=',True),('handling_charges','=',False)]
        return res
   
    def add_amount(self, cr, uid, ids, context=None):
        if not context:
            context={}
        result = {}
        new_price=0.0
        date_day = time.strftime('%Y-%m-%d')
        today=context.get('in_date',date_day)
        month_to=self.get_month(cr,uid,[],today,{'month':1}) 
        year_to=self.get_month(cr,uid,[],today,{'year':1})        
        partner_obj=self.pool.get('res.partner')
        line_obj=self.pool.get('account.invoice.line')
        partner_ids=partner_obj.search(cr,uid,[('handling_charges','=',True)])
        cr.execute("select id from account_invoice where state='cancel' and partner_id in (select id from res_partner where handling_charges = True) and type='in_invoice' and EXTRACT(month from date_invoice) = '" + str(month_to) + "' and EXTRACT(year from date_invoice) ='" + str(year_to) + "'")        
        other_sup=[x[0] for x in cr.fetchall()]
#         other_sup=self.search(cr,uid,[('type','=','in_invoice'),('partner_id','in',partner_ids)])
        invoice_line=line_obj.search(cr,uid,[('invoice_id','in',other_sup)])

        for line in line_obj.browse(cr,uid,invoice_line):
            new_price=0.0
            print line.invoice_id.partner_id.name
            if line.invoice_id.state=="cancel":
                
                print "previous",line.price_unit
                if line.price_unit>0:
                    new_price=line.price_unit-100
                    line_obj.write(cr,uid,[line.id],{'price_unit':new_price})
                print line.invoice_id.number
                print "price",new_price
                print "-------------"
                
        print "ids",len(other_sup)
        print "ids",other_sup
        self.action_cancel_draft(cr, uid, other_sup)  
        
        print "Done"
       
        return True
     
    def get_state(self, cr, uid, context=None):
        location_id = self.pool.get('res.country.state')
        res = False
#         country_id=location_id.search(cr,uid,[('name','=','india')])
        cr.execute("select id from res_country_state where lower(name) like 'karnataka%'")
        state_id=cr.fetchone()
       
        if state_id:
            res = state_id[0]
        return res
    
    #overidden
    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()
    
    #overidden
    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()
    
    #overidden
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += round(line.price_subtotal)
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += round(line.amount)
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
        
        return res
    
     #overidden
    def update_handling_charge(self, cr, uid, ids, context=None):
        res = {}
        cr.execute(""" select ai.id from account_invoice ai
                        inner join res_partner ru on ru.id=ai.partner_id
                        
                        where ai.type='in_invoice' and ru.handling_charges=True""" )
        
        invoice_id=cr.fetchall()   
        print 'invoice_id',invoice_id                             
        cr.execute("update account_invoice set handling_charges=True where id in %s",(tuple(invoice_id),))
        return res
       
    def _amt_in_words(self, cr, uid, ids, fields_name, args, context):
        res = {}
        txt = '' 
        qty=0
        qty_txt=''
        c_acc_id = False
        stock_obj=self.pool.get('stock.picking.out')
        for case in self.browse(cr, uid, ids):
            if case.type == 'out_invoice' and case.company_id.id == 1:
                if (case.account_id.name == "Total Sundry Creditors") or (case.account_id.name == "Sundry Creditors") or (case.account_id.name == "Total Sundry Debtors") or (case.account_id.name == "Sundry Debtors") :
                    c_acc_id = case.partner_id.property_account_receivable and case.partner_id.property_account_receivable.id or False
                    if case.partner_id.parent_id:
                        c_acc_id = case.partner_id.parent_id.property_account_receivable and case.partner_id.parent_id.property_account_receivable.id or False
                    if c_acc_id:
                        cr.execute("update account_invoice set account_id="+str(c_acc_id)+" where id=%s",(case.id,))
            else:
                c_acc_id= case.partner_id.account_rec and case.partner_id.account_rec.id or False
                if case.partner_id.parent_id:
                    c_acc_id=case.partner_id.parent_id.account_rec and case.partner_id.parent_id.account_rec.id or False  
                if c_acc_id:
                    cr.execute("update account_invoice set account_id="+str(c_acc_id)+" where id=%s",(case.id,))                    
                                  
            qty=0
            res[case.id]={
                          'amt_txt':'','product_id':False,'qty_txt':False,'handling_charges':False,'quantity':0.00
                          }
            if case.amount_total and case.amount_total>0:
                txt = amount_to_text_softapps._100000000_to_text(int(round(case.amount_total)))        
                res[case.id]['amt_txt'] = txt
            
            if case.type=='in_invoice':
                if case.partner_id.handling_charges:
                    res[case.id]['handling_charges']=case.partner_id.handling_charges
            
            for temp in case.invoice_line:
                qty +=temp.quantity
                if case.type=='out_invoice' or case.type=='in_invoice':
                    if temp.product_id.name!='Freight':
                        res[case.id]['product_id'] = temp.product_id.id
                    else:
                        if case.type=='out_invoice':
                            cr.execute("select del_ord_id from delivery_invoice_rel where invoice_id=%s",(case.id,))
                            del_id=cr.fetchone()
                        if case.type=='in_invoice':
                            cr.execute("select del_ord_id from supp_delivery_invoice_rel where invoice_id=%s",(case.id,))
                            del_id=cr.fetchone()
                        if del_id:
                            del_id=del_id[0]
                            stock_ids=stock_obj.browse(cr,uid,[del_id])
                            for i in stock_ids:
                                for temp in i.move_lines:
        #                             cr.execute("update account_invoice set product_id=%s where id=%s",(temp.product_id.id,case.id,))
                                     res[case.id]['product_id'] = temp.product_id.id
            if qty>0:
                qty_txt = amount_to_text_softapps._100000000_to_text(int(round(qty)))        
                res[case.id]['qty_txt'] = qty_txt
                res[case.id]['quantity'] = qty                 
                            
        return res

    
    _columns={
               'pa_no'                       :   fields.char('PA Number', size=60),
               'transporter'                 :   fields.char('Transporter Name', size=30),
               'payment'                     :   fields.char('Payment', size=30),
               'destination'                 :   fields.char('Destination', size=20),
               'delivery_orders_ids'         :   fields.many2many('stock.picking', 'delivery_invoice_rel', 'invoice_id', 'del_ord_id', 'Delivery Orders'),
               'supp_delivery_orders_ids'    :   fields.many2many('stock.picking', 'supp_delivery_invoice_rel', 'invoice_id', 'del_ord_id', 'Delivery Orders'),
               'incoming_shipment_ids'       :   fields.many2many('stock.picking.in', 'incoming_shipment_invoice_rel', 'invoice_id', 'in_shipment_id', 'Delivery Orders'),
               'amt_txt'                     :   fields.function(_amt_in_words, type='text', method = True,store=True, string='Total text',multi='text'),
               'amt_txt_freight'             :   fields.char("Freight Total text"),

               'agreement_date'              :   fields.date('P.A Date'),
               'reference'                   :   fields.char("Reference"),
               'product_id'                  :   fields.function(_amt_in_words, type='many2one',relation='product.product', method = True,
                                                                 store=True,string='Goods',multi='text'),
              
               'qty_txt'                     :   fields.function(_amt_in_words, type='text', method = True,store={
                                                                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                                                                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                                                                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                                                                    }, string='Quantity text',multi='text'),
              
              
               'handling_charges'            :   fields.function(_amt_in_words, type='boolean', method = True,store={
                                                                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                                                                        'account.invoice.tax': (_get_invoice_tax, None, 20),
                                                                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                                                                    }, string='Additional Freight Charges',multi='text'),
              
               'quantity'                  :   fields.function(_amt_in_words, type='float', method = True,
                                                                 store=False,string='Quantity',multi='text'),  
                          
                  
               # for Invoice number Purpose#########
                 'branch_state'        : fields.many2one('res.country.state','State'),

               # For Report purpose##########
               
               'freight'                     :  fields.boolean('Freight'),
                'back_date'  :  fields.boolean('Back Date Entry'),
               
               #inheritted
               'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
              
             #for Invoice number edit purpose   
          'inv_num'                   :   fields.char('To Change Invoice Number', size=5),   
#           'create_date'               :   fields.date('create date'),  
              
        #for ITC Invoice Report purpose 
            'report'            : fields.related('partner_id','report',type='boolean',store=False,string="Invoice Split Report"),
            'product_rate'      : fields.float('Transport Rate',digits=(0,3)),
            'freight_rate'     : fields.float('Handling Rate',digits=(0,3)),     
            
      # For Serch View Purpose
            'date_from'             :fields.function(lambda *a,**k:{}, method=True, type='date',string="From"),
            'date_to'               :fields.function(lambda *a,**k:{}, method=True, type='date',string="To"),            
            'cft'                   : fields.related('product_id','cft',type='boolean',store=False,string="CFT",readonly=True),
            
        'reference': fields.char('Invoice Reference', size=200, help="The partner reference of this invoice."),         
                'product_order'            : fields.char('Order Number'),
                'handling_order'            : fields.char('Handling charge Order Number'),  
    #for total balance
    
        # columns for ITC limited
        'other_charges'    : fields.boolean('Other Charges'),
        'transport_charges' : fields.float('Transport Charges'),
        'transport_acc_id'  : fields.many2one('account.account','Account'),
        'loading_charges' : fields.float('Loading Charges'),
        'loading_acc_id'  : fields.many2one('account.account','Account'),
        
    
              
                      
                    
            }
    _defaults={
               'inv_num':'',
               'back_date':False,
               'other_charges' : False
#                'create_date':lambda *a: time.strftime('%Y-%m-%d'),
                 
               }  

#     def onchange_cft_relate(self, cr, uid, ids, cft_relate):
#         res={}
#         if cft_relate:
#             res['cft']=cft_relate
#         else:
#             res['cft']=False
#         return res
    
    
    def onchange_company_id(self, cr, uid, ids, company_id, part_id, type, invoice_line, currency_id):
        partner_id=False
        period=False
        partner_obj=self.pool.get('res.partner')
        inv_line={}
        today = time.strftime('%Y-%m-%d')
#         for case in self.browse(cr,uid,ids):
#             if case.advance_type=='rtgs':
#                 voucher=self.search(cr,uid,[('voucher_id','=',case.id),('advance_type','=','rtgs')])
#             for i in voucher:
#                 ids.append(i) 
        if ids and company_id>1 and invoice_line:
            if invoice_line[0][2]:
                invoice_line[0][2].update({'company_id':company_id}
                                          )
    
        res=super(account_invoice,self).onchange_company_id(cr, uid, ids, company_id=company_id, part_id=part_id, type=type, invoice_line=invoice_line, currency_id=currency_id)
        res['value']['freight']=False
        if part_id:
            partner_id=partner_obj.browse(cr,uid,[part_id])
        if company_id >1:
            
            
            res['value']['freight']=True
            if partner_id:
                partner_id=partner_id[0]
                if type=='out_invoice' or type=='out_refund':
                    res['value']['account_id']=partner_id.account_rec.id
                if type=='in_invoice' or type=='in_refund':
                    res['value']['account_id']=partner_id.account_pay.id
        else:
            if partner_id:
                partner_id=partner_id[0]
                if type=='out_invoice' or type=='out_refund':
                    res['value']['account_id']=partner_id.property_account_receivable.id
                if type=='in_invoice' or type=='in_refund':
                    res['value']['account_id']=partner_id.property_account_payable.id
        
        if ids:
                for case in self.browse(cr,uid,ids):
                    if case.date_invoice:
                        today=case.date_invoice
        
        if company_id:                
            cr.execute("select id from account_period where company_id='"+ str(company_id)+"' and date_start <= '" + today + "' and date_stop >='" + today + "'")
            period = cr.fetchone()
            if period:
                res['value']['period_id']=period[0]           
      
    
                                      
        print "period",res                              
        return res
    
    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        partner_pool = self.pool.get('res.partner')
        partner=False
        c_account_id = False
        res=super(account_invoice,self).onchange_partner_id(cr, uid, ids, type=type,partner_id=partner_id, date_invoice=date_invoice, payment_term=payment_term, partner_bank_id=partner_bank_id, company_id=company_id)
        if partner_id:
            partner = partner_pool.browse(cr, uid, partner_id)
            res['value']['report']=partner.report
            if type=='in_invoice' or 'in_refund':
                
                res['value']['branch_state']=partner.state_id.id
                res['value']['handling_charges']=partner.handling_charges
            if type=='out_invoice' or 'out_refund':
                cr.execute("select id from res_country_state where lower(name) like 'karnataka%'")
                state_id=cr.fetchone()
               
                if state_id:
                    res['value']['branch_state'] = state_id[0]
                    
                if company_id:
                    if company_id>1:
                      c_account_id= partner.account_rec and partner.account_rec.id or False
                      if partner.parent_id:
                           c_account_id=partner.parent_id.account_rec and partner.parent_id.account_rec.id or False   
                      res['value']['account_id']=c_account_id                     
        return res
    
    
#     def kw_onchange_date(self, cr, uid, ids, date, partner_id):
#         """
#         @param date: latest value from user input for field date
#         @param args: other arguments
#         @param context: context arguments, like lang, time zone
#         @return: Returns a dict which contains new values, and context
#         """
#         bill_date=[]
#         warning=''
#         latest_date=False
#         patner_obj=self.pool.get('res.partner')
#         res={}     
#         
#        
#         if partner_id:
#            partner=patner_obj.browse(cr,uid,[partner_id])
#            for i in partner:
#                 print i.name
#                 for bill_cycle in i.billing_ids:
#                     print bill_cycle.end_date
#                     bill_date.append(bill_cycle.end_date)
#                     
#                 if bill_date:
#                     bill_date.sort()
#                     bill_date.reverse()
#                     latest_date=bill_date[0]
#                     
#                     if date<latest_date:
#                         warning={
#                                              'title':_('Warning!'), 
#                                                     'message':_('Entered Date "%s" Is Less Than The Last Billing Date "%s",'
#                                                                 ' If You Did Not Change This Date "%s"'
#                                                                 ',The Billing Report Balance Will Be Affected..!')% (date,latest_date,date)
#                                                  
#                                                  }
#                     
#                 
#         #set the period of the voucher
#           
#         return {'value':res ,'warning':warning}  
    

    
         
    def onchange_inv_num(self, cr, uid, ids, inv_num=False,context=None):
        res ={} 
        warning=''
        
        warning = ""
        if inv_num:
            try:
                inv_num = int(inv_num)
            except:
                res['inv_num']=False
                warning={
                                         'title':_('Warning!'), 
                                                'message':_('You Are Not Allowed To Change Invoice Number Format, You Can Only Change The Number')
                                             }

        return{'value':res ,'warning':warning}        
    
    #Inheriting For Validation based on account_id and Taxes
    

#     def action_date_assign(self, cr, uid, ids, *args):
#         re_fund=self.validate_refund(cr,uid,ids)
#         for re in re_fund:
#             if re not in ids:
#                 ids.append(re)
#          return super(account_invoice,self).action_date_assign(cr, uid, ids, *args)
#     
#     def action_move_create(self, cr, uid, ids, *args):
#         re_fund=self.validate_refund(cr,uid,ids)
#         for re in re_fund:
#             if re not in ids:
#                 ids.append(re)
# #                 
#          return super(account_invoice,self).action_move_create(cr, uid, ids, *args)
#     
#     def action_number(self, cr, uid, ids, *args):
#         re_fund=self.validate_refund(cr,uid,ids)
#         for re in re_fund:
#             if re not in ids:
#                 ids.append(re)
# #   
#          return super(account_invoice,self).action_number(cr, uid, ids, *args)
        
    def validate_refund(self,cr,uid,ids,context=None):
        if not context:
            context={}
        refund=context.get('refund',False)
        wf_service = netsvc.LocalService('workflow')
        dels_ids=[]
        if not refund:
            for case in self.browse(cr, uid, ids):
                
                for temp in case.invoice_line:
                    if case.type=='in_invoice' and temp.product_id.name!='Freight':
                        
                        cr.execute("select del_ord_id from supp_delivery_invoice_rel where invoice_id="+str(case.id))
                        sup_ids=[i[0] for i in cr.fetchall()]
                        for s in sup_ids:
                            cr.execute("select invoice_id from supp_delivery_invoice_rel where del_ord_id = "+str(s))
                            dels_id=cr.fetchall()
                            for j in dels_id:
                                if j not in dels_ids:
                                    dels_ids.append(j[0])
                                
                        if dels_ids:
                            sup_id=self.search(cr,uid,[('id','in',dels_ids),('type','=','in_refund'),('state','=','draft')])
                            self.write(cr,uid,sup_id,{'date_invoice':case.date_invoice,'date_due':case.date_due})
                            for i in sup_id:
                                ids.append(i)
                            context.update({'refund':1})
#         for j in ids:
#               wf_service.trg_validate(uid, 'account.invoice', j, 'invoice_open', cr)             
#         self.invoice_confirm(cr, uid, ids, context=None)
        return ids

    def generate_sequence(self, cr, uid, today, case, format, context):
        year=False
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        code1=case.branch_state.code
        
        if not code1:
            raise osv.except_osv(_('Warning!'), _('No State Code For Selected State "%s"')%(case.branch_state.name))
        l=0
        cr.execute("select code from account_fiscalyear where date_start <= '" + today + "' and date_stop >='" + today + "'")
        code = cr.fetchone()
        if code:
            year = code[0]
        if not year:
            raise osv.except_osv(_('Warning!'), _('Please Create Fiscal Year For "%s"')%(today))
        
        format = code1+'/'+format + year +'/'
     
        cr.execute("select number from account_invoice where number like '" + format + "'|| '%' order by to_number(substr(number,(length('" + format + "')+1)),'99999') desc limit 1")
        prev_format = cr.fetchone()
        
        if not prev_format:
            number = format + '00001'
        else:
            
            auto_gen = prev_format[0][-5:]
            number = format + str(int(auto_gen) + 1).zfill(5)
        self.write(cr, uid, [case.id], {'number':number,'internal_number':number}, context=context)
        return True

    #inheriting for generating the sequences
    def invoice_validate(self, cr, uid, ids, context=None):
        if not context:
            context={}
        stock_obj=self.pool.get('stock.picking')
        kwprod_obj=self.pool.get('kw.product.price')
        voucher_obj=self.pool.get('account.voucher')
        bill_obj = self.pool.get('billing.cycle')
        today = time.strftime('%Y-%m-%d')
        wf_service = netsvc.LocalService('workflow')
        schedular = context.get('schedular',False)
        back_date = context.get('back_date',False)
        #To validate invoice refund
#         for case in self.browse(cr, uid, ids):
#             for temp in case.invoice_line:
#                 if case.type=='in_invoice' and temp.product_id.name!='Freight':
#                     
#                     cr.execute("select del_ord_id from supp_delivery_invoice_rel where invoice_id="+str(case.id))
#                     sup_ids=[i[0] for i in cr.fetchall()]
#                     for s in sup_ids:
#                         cr.execute("select invoice_id from supp_delivery_invoice_rel where del_ord_id="+str(s))
#                         dels_ids=cr.fetchall()
#                     for rf in dels_ids:
#                         sup_id=self.search(cr,uid,[('id','=',rf[0]),('type','=','in_refund')])
#                         if sup_id:
#                             for i in sup_id:
#                                 ids.append(i)
        res = super(account_invoice,self).invoice_validate(cr, uid, ids, context = context)                        
#REFUND INVOICE
#         refund=context.get('refund',False)
#         if not refund:
#             re_fund=self.validate_refund(cr,uid,ids,context=context)
#             context.update({'refund':1})
#             ids=re_fund
# #             for re in re_fund:
# #                 if re not in ids:
# #                     ids.append(re)
#             for j in ids:
#                   wf_service.trg_validate(uid, 'account.invoice', j, 'invoice_open', cr)
#             
        
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        freight_price = 0
        data=[]
        state_code=False
        del_ids = []
        product=[]
        product_copy=[]
        bill_date=[]
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company=cr.fetchone()
        if company:
            company=company[0]
        
        for case in self.browse(cr, uid, ids):
            
            #for checking the billing cycle has generted for supplier
            if case.type in ("in_refund","in_invoice" ) and back_date:
                if not case.back_date:
                    date=case.date_invoice
                    if case.partner_id:
                       for bill_cycle in case.partner_id.billing_ids:
                           bill_date.append(bill_cycle.end_date)
                                
                       if bill_date and not case.back_date:
                            bill_date.sort()
                            bill_date.reverse()
                            latest_date=bill_date[0]
                            
                            if date<latest_date:
                                if schedular:
                                    self.write(cr,uid,[case.id],{'back_date':True})
                                else:
                                    raise osv.except_osv(_('Warning!'), _('Invoice Date "%s" Is Less Than The Last Billing Date "%s" Change The Invoice Date Otherwise Billing Report Balance Will Be Affected..! If You Still Want To Continue With Same Date Check The "Back Date Entry Field" and Click on Validate')% (date,latest_date))
                                                                     
                                                        
                
            if case.company_id.id==company:
                
                if case.type == 'out_invoice':
                    format = 'CI/KL/'
                    self.generate_sequence(cr, uid,case.date_invoice, case, format, context)
                if case.type == 'in_invoice':
                    format = 'SI/KL/'
                    self.generate_sequence(cr, uid,case.date_invoice, case, format, context)
                if case.type == 'out_refund':
                    format = 'CN/KL/'
                    self.generate_sequence(cr, uid,case.date_invoice, case, format, context)
                if case.type == 'in_refund':
                    format = 'DN/KL/'
                    self.generate_sequence(cr, uid,case.date_invoice, case, format, context)
            else:
                if case.type == 'out_invoice':
                    format = 'CI/KS/'
                    self.generate_sequence(cr, uid,case.date_invoice, case, format, context)
                if case.type == 'in_invoice':
                    format = 'SI/KS/'
                    self.generate_sequence(cr, uid,case.date_invoice, case, format, context)
                if case.type == 'out_refund':
                    format = 'CN/KS/'
                    self.generate_sequence(cr, uid,case.date_invoice, case, format, context)
                if case.type == 'in_refund':
                    format = 'DN/KS/'
                    self.generate_sequence(cr, uid,case.date_invoice, case, format, context)
            if case.type == 'out_invoice':
                for line in case.invoice_line:
                    product.append(line.product_id.id)
                   
                if len(product)>1:
                    for p in product:
                        product_copy.append(p)
                        if product[0] != product_copy[0]:
                            raise osv.except_osv(_('Warning!'), _("Cannot Validate Invoice with Different Products"))
                        product_copy.pop()
            
            
            
           #TODO :uncomment lines
            #to fetch delivery order records records for reporting purpose
#             if case.type!="in_refund" :
#                 cr.execute("select del_ord_id from supp_delivery_invoice_rel where invoice_id="+str(case.id))
#                 out_ids=cr.fetchall()
#                 if out_ids:
#                     del_ids =out_ids
#                 #to fetch incoming shipment records for reporting purpose
#                 #if not del_ids:
#                 cr.execute("select in_shipment_id from incoming_shipment_invoice_rel where invoice_id="+str(case.id))
#                 in_ids = cr.fetchall()
#                 if in_ids :
#                     for ins in in_ids:
#                         del_ids.append(ins)
#                 for temp in case.invoice_line:
#                     for x in del_ids:
#                         if len(case.invoice_line)==1:
#                             for d in stock_obj.browse(cr,uid,[x[0]]):
#                                 if d.type == "out" or "out" in d.type: #added the condition for unicode i.e type was coming as unicode
#                                     if temp.product_id.name != 'Freight':
#                                         stock_obj.write(cr,uid, [d.id],{'invoice_line_id':temp.id})
#                                     else:
#                                         if case.partner_id.id == d.paying_agent_id.id:
#                                             stock_obj.write(cr,uid, [d.id],{'finvoice_line_id':temp.id})
#                                         if case.partner_id.handling_charges:
#                                             stock_obj.write(cr,uid, [d.id],{'oinvoice_line_id':temp.id})
#                                 
#                                 #for Incoming Shipments
#                                 else:
#                                     stock_obj.write(cr,uid, [d.id],{'invoice_line_id':temp.id})
#                         else:
#                             for d in stock_obj.browse(cr,uid,[x[0]]):
#                                 price1 =0
#                                 other_price = 0
#                                 freight_price = 0
#                                 for ln in d.move_lines:
#                                     if d.type =='out' or "out" in d.type:
#                                         for i in ln.product_id.seller_ids:
#                                             #to fetch goods price for delivery order and map respective invoice lines to delivery orders
#                                             if d.paying_agent_id.id == i.name.id:
#                                                 prod_ids=kwprod_obj.search(cr, uid, [('ef_date','<=',ln.delivery_date),('supp_info_id','=',i.id)],limit=1, order='ef_date desc')
#                                                 for j in kwprod_obj.browse(cr,uid,prod_ids):
#                                                     if i.customer_id and i.customer_id.id == d.partner_id.id:
#                                                         if d.partner_id.freight or d.gen_freight:
#                                                             price1=j.product_price
#                                                         else:
#                                                             price1 = j.sub_total
#                                                         
#                                                         #to check the handling charge
#                                                         if case.partner_id.handling_charges and j.partner_id:
#                                                             other_price = j.handling_charge or 0.0
#                                                         
#                                                         freight_price = j.transport_price
#                                                         key = (price1,temp.product_id.id,temp.price_unit,d.id)
#                                         #check for key, if already lines updated
#                                         if key not in data:
#                                             if temp.product_id.id == ln.product_id.id and temp.price_unit == price1 and temp.product_id.name !='Freight':
#                                                 stock_obj.write(cr,uid, [d.id],{'invoice_line_id':temp.id})
#                                                 data.append(key)
#                                             else :
#                                                 if case.partner_id.id == d.paying_agent_id.id and temp.price_unit == freight_price:
#                                                     stock_obj.write(cr,uid, [d.id],{'finvoice_line_id':temp.id})
#                                                     data.append(key)
#                                                 
#                                                 if case.partner_id.handling_charges and temp.price_unit == other_price:
#                                                     stock_obj.write(cr,uid, [d.id],{'oinvoice_line_id':temp.id})
#                                     else:
#                                         for sp_line in d.move_lines:
#                                             location = sp_line.location_dest_id.id
#                                         for ship in ln.product_id.seller_ids:
#                                             if d.partner_id.id == ship.name.id:
#                                                 prod_ids=kwprod_obj.search(cr, uid, [('ef_date','<=',d.date),('supp_info_id','=',ship.id)],limit=1, order='ef_date desc')
#                                                 for js in kwprod_obj.browse(cr,uid,prod_ids):
#                                                     if ship.depot and ship.depot.id == location:
#                                                         price1 = js.product_price + js.transport_price
#                                                         freight_price = js.transport_price
#                                                         key = (price1,temp.product_id.id,temp.price_unit,d.id)
#                                         if key not in data:
#                                             if temp.product_id.id == ln.product_id.id and temp.price_unit == price1 and temp.product_id.name !='Freight':
#                                                 stock_obj.write(cr,uid, [d.id],{'invoice_line_id':temp.id})
#                                                 data.append(key)
#                                             else :
#                                                 if case.partner_id.id == d.partner_id.id and temp.price_unit == freight_price:
#                                                     stock_obj.write(cr,uid, [d.id],{'finvoice_line_id':temp.id})
#                                                     data.append(key)
#                 
#                 
# #                                 super(account_invoice,self).invoice_validate(cr, uid, sup_id, context = context)
#                 #To post draft vouchers which are created from pay freight
#                 for pick in case.supp_delivery_orders_ids:
#                     for case in self.browse(cr,uid, ids):
#                         vid = voucher_obj.search(cr,uid,[('reference','=',pick.name)])
#                         if vid:
#                             if context==None:
#                                 context={}
#                             context.update({'freight_paid':True})
#                             voucher_obj.proforma_voucher(cr, uid,vid,context=context)
                            
                       
        return res
    
    def action_update_del_orders(self, cr, uid, ids, context = None):
        stock_obj=self.pool.get('stock.picking')
        kwprod_obj=self.pool.get('kw.product.price')
        voucher_obj=self.pool.get('account.voucher')
        bill_obj = self.pool.get('billing.cycle')
        today = time.strftime('%Y-%m-%d')
        wf_service = netsvc.LocalService('workflow')
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        freight_price = 0
        data=[]
        state_code=False
        del_ids = []
        product=[]
        product_copy=[]
        bill_date=[]
        key = False
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company=cr.fetchone()
        if company:
            company=company[0]
        
         #to fetch delivery order records records for reporting purpose
        for case in self.browse(cr, uid, ids):
            if case.type!="in_refund" :
                cr.execute("select del_ord_id from supp_delivery_invoice_rel where invoice_id="+str(case.id))
                out_ids=cr.fetchall()
                if out_ids:
                    del_ids =out_ids
                #to fetch incoming shipment records for reporting purpose
                #if not del_ids:
                cr.execute("select in_shipment_id from incoming_shipment_invoice_rel where invoice_id="+str(case.id))
                in_ids = cr.fetchall()
                if in_ids :
                    for ins in in_ids:
                        del_ids.append(ins)
                for temp in case.invoice_line:
                    for x in del_ids:
                        if len(case.invoice_line)==1:
                            for d in stock_obj.browse(cr,uid,[x[0]]):
                                if d.type == "out" or "out" in d.type: #added the condition for unicode i.e type was coming as unicode
                                    if temp.product_id.name != 'Freight':
                                        stock_obj.write(cr,uid, [d.id],{'invoice_line_id':temp.id})
                                    else:
                                        if case.partner_id.id == d.paying_agent_id.id:
                                            stock_obj.write(cr,uid, [d.id],{'finvoice_line_id':temp.id})
                                        if case.partner_id.handling_charges:
                                            stock_obj.write(cr,uid, [d.id],{'oinvoice_line_id':temp.id})
                                
                                #for Incoming Shipments
                                else:
                                    if not case.partner_id.handling_charges:
                                        stock_obj.write(cr,uid, [d.id],{'invoice_line_id':temp.id})
                                    else:
                                        stock_obj.write(cr,uid, [d.id],{'oinvoice_line_id':temp.id})
                        else:
                            for d in stock_obj.browse(cr,uid,[x[0]]):
                                price1 =0
                                other_price = 0
                                freight_price = 0
                                for ln in d.move_lines:
                                    if d.type =='out' or "out" in d.type:
#                                         for i in ln.product_id.seller_ids:
#                                             #to fetch goods price for delivery order and map respective invoice lines to delivery orders
#                                             if d.paying_agent_id.id == i.name.id:
#                                                 prod_ids=kwprod_obj.search(cr, uid, [('ef_date','<=',ln.delivery_date),('supp_info_id','=',i.id)],limit=1, order='ef_date desc')
                                        cr.execute(""" 
                                        select 
                                                kw.id,
                                                kw.product_price,
                                                kw.sub_total,
                                                kw.handling_charge,
                                                kw.transport_price 
                                            from product_supplierinfo ps
                                            inner join kw_product_price kw on ps.id = kw.supp_info_id
                                            and ps.product_id = %s
                                            and ps.customer_id = %s
                                            and ef_date <='%s'
                                            and ps.name = %s
                                            order by ef_date desc limit 1
                                        """ % (ln.product_id.id, d.partner_id.id, ln.delivery_date,d.paying_agent_id.id ))
                                        prod_ids = [x[0] for x in cr.fetchall()]
                                        
                                        for j in kwprod_obj.browse(cr,uid,prod_ids):
                                            if d.partner_id.freight or d.gen_freight:
                                                price1=j.product_price
                                            else:
                                                price1 = j.sub_total
                                            
                                            #to check the handling charge
                                            if case.partner_id.handling_charges and j.partner_id:
                                                other_price = j.handling_charge or 0.0
                                            
                                            freight_price = j.transport_price
                                            key = (price1,temp.product_id.id,temp.price_unit,d.id)
                                        #check for key, if already lines updated
                                        if key not in data:
                                            if temp.product_id.id == ln.product_id.id and temp.price_unit == price1 and temp.product_id.name !='Freight':
                                                stock_obj.write(cr,uid, [d.id],{'invoice_line_id':temp.id})
                                                data.append(key)
                                            else :
                                                if case.partner_id.id == d.paying_agent_id.id and temp.price_unit == freight_price:
                                                    stock_obj.write(cr,uid, [d.id],{'finvoice_line_id':temp.id})
                                                    data.append(key)
                                                
                                                if case.partner_id.handling_charges and temp.price_unit == other_price:
                                                    stock_obj.write(cr,uid, [d.id],{'oinvoice_line_id':temp.id})
                                    else:
                                        for sp_line in d.move_lines:
                                            location = sp_line.location_dest_id.id
#                                         for ship in ln.product_id.seller_ids:
#                                             if d.partner_id.id == ship.name.id:
#                                                 prod_ids=kwprod_obj.search(cr, uid, [('ef_date','<=',d.date),('supp_info_id','=',ship.id)],limit=1, order='ef_date desc')
                                        cr.execute("""select 
                                                kw.id,
                                                kw.product_price,
                                                kw.sub_total,
                                                kw.handling_charge,
                                                kw.transport_price 
                                            from product_supplierinfo ps
                                            inner join kw_product_price kw on ps.id = kw.supp_info_id
                                            and ps.product_id = %s
                                            and ps.depot = %s
                                            and ef_date <='%s'
                                            and ps.name = %s
                                            order by ef_date desc limit 1""" % (ln.product_id.id, location, d.date,d.partner_id.id ))
                                        
                                        prod_ids = [x[0] for x in cr.fetchall()]
                                        
                                        
                                        
                                        for js in kwprod_obj.browse(cr,uid,prod_ids):
#                                             if ship.depot and ship.depot.id == location:
                                            price1 = js.product_price + js.transport_price
                                            freight_price = js.transport_price
                                            key = (price1,temp.product_id.id,temp.price_unit,d.id)
                                        if key not in data:
                                            if temp.product_id.id == ln.product_id.id and temp.price_unit == price1 and temp.product_id.name !='Freight':
                                                stock_obj.write(cr,uid, [d.id],{'invoice_line_id':temp.id})
                                                data.append(key)
                                            else :
                                                if case.partner_id.id == d.partner_id.id and temp.price_unit == freight_price:
                                                    stock_obj.write(cr,uid, [d.id],{'finvoice_line_id':temp.id})
                                                    data.append(key)
                
                
#                                 super(account_invoice,self).invoice_validate(cr, uid, sup_id, context = context)
                #To post draft vouchers which are created from pay freight(Delivery Orders)
                for pick in case.supp_delivery_orders_ids:
                    vid = voucher_obj.search(cr,uid,[('reference','=',pick.name),('partner_id','=',pick.paying_agent_id.id)])
                    if vid:
                        if context==None:
                            context={}
                        context.update({'freight_paid':True})
                        voucher_obj.proforma_voucher(cr, uid,vid,context=context)
                        
             #To post draft vouchers which are created from pay freight(Incoming Shipments)
                for pick in case.incoming_shipment_ids:
                    vid = voucher_obj.search(cr,uid,[('reference','=',pick.name),('partner_id','=',pick.partner_id.id)])
                    if vid:
                        if context==None:
                            context={}
                        context.update({'freight_paid':True})
                        voucher_obj.proforma_voucher(cr, uid,vid,context=context)
                            
        return True
    
    def action_validate_refund(self,cr,uid,ids,context=None):
        i = 0
        print i+1
        if not context:
            context={}
        refund=context.get('refund',False)
        wf_service = netsvc.LocalService('workflow')
        refund_ids = []
        dels_ids=[]
        if not refund:
            for case in self.browse(cr, uid, ids):
                for temp in case.invoice_line:
                    if case.type=='in_invoice' and temp.product_id.name!='Freight':
                         
                        cr.execute("select del_ord_id from supp_delivery_invoice_rel where invoice_id="+str(case.id))
                        sup_ids=[i[0] for i in cr.fetchall()]
                        for s in sup_ids:
                            cr.execute("select invoice_id from supp_delivery_invoice_rel where del_ord_id = "+str(s))
                            dels_id=cr.fetchall()
                            for j in dels_id:
                                if j not in dels_ids:
                                    dels_ids.append(j[0])
                                 
                        if dels_ids:
                            sup_id=self.search(cr,uid,[('id','in',dels_ids),('type','=','in_refund'),('state','=','draft')])
                            self.write(cr,uid,sup_id,{'date_invoice':case.date_invoice,'date_due':case.date_due})
                            for i in sup_id:
                                refund_ids.append(i)
                            context.update({'refund':1})
        for j in refund_ids:
              wf_service.trg_validate(uid, 'account.invoice', j, 'invoice_open', cr)
        return True

    def action_validate_number(self,cr,uid,ids,context=None):
        if not context:
            context={}

        wf_service = netsvc.LocalService('workflow')
#         cr.execute("select id from account_invoice where state='open' and number is null")
#         reval_ids=[x[0] for x in cr.fetchall()] 
#         self.action_cancel(cr,uid,ids)
#         self.action_cancel_draft(cr, uid, ids)
        for j in ids:
            print "cancel......", j
            wf_service.trg_validate(uid, 'account.invoice', j, 'invoice_cancel', cr)
               
        self.action_cancel_draft(cr, uid, ids)
#         self.unlink(cr,uid,ids)
#         for i in ids:
#                print "open......", i
#                wf_service.trg_validate(uid, 'account.invoice', i, 'invoice_open', cr)

             
        return True



    def do_merge_old_inv(self, cr, uid, ids, context=None):
        if not context:
            context={}
        wf_service = netsvc.LocalService('workflow')
        date_day = time.strftime('%Y-%m-%d')
        day_to=self.get_month(cr,uid,[],date_day,{'day':1})        
        today=context.get('in_date',date_day)
        supplier_id=context.get('supplier_id',False)
        partner_obj=self.pool.get('res.partner')
        del_ord_out_ids=[]
        del_ord_in_ids=[]
        shipment_ids=[]
        res={}
        res1={}
        partner_company=[]
        partner=[]
        inv_m=False
        inv_month=[]
        company=[]
        partner_ids=partner_obj.search(cr,uid,[('handling_charges','=',True)])
         

        year_to=self.get_month(cr,uid,[],today,{'year':1})         
        for case in self.browse(cr, uid, ids):
            month_to=self.get_month(cr,uid,[],case.date_invoice,{'month':1})
            day_to=self.get_month(cr,uid,[],case.date_invoice,{'day':1}) 
            
            shedular_date = datetime.strptime(case.date_invoice, '%Y-%m-%d') - relativedelta(days=int(day_to))
            shedular_date = shedular_date.strftime('%Y-%m-%d')         
            cr.execute("select id from account_invoice where state='draft' and handling_charges = True and company_id = "+str(case.company_id.id)+" and partner_id= '" + str(case.partner_id.id) + "'and partner_id in (select id from res_partner where handling_charges = True) and type='in_invoice' and EXTRACT(month from date_invoice) = '" + str(month_to) + "' and EXTRACT(year from date_invoice) ='" + str(year_to) + "'")
            other_sup=[x[0] for x in cr.fetchall()]  
                       
            
            del_ord_in_ids=[]
            incoming_in_ids=[]
            in_ship_ids=[]
            in_ids=[]
            print 'other_sup',case.id
            print "no-",len(other_sup)
            print "name-",case.partner_id.name
            group_ids=self.search(cr,uid,[('partner_id','=',case.partner_id.id),('handling_charges','=', True),('company_id','=',case.company_id.id),('state','=','draft'),('id','in',other_sup)],order='partner_id',)
            group_in_ids=self.search(cr,uid,[('origin','=','IN'),('handling_charges','=', True),('partner_id','=',case.partner_id.id),('company_id','=',case.company_id.id),('state','=','draft'),('id','in',other_sup)],order='origin',)
            
            if group_in_ids:
                for in_ship in group_in_ids:
                    if in_ship not in other_sup:
                        group_in_ids.remove(in_ship)
                    if in_ship in group_ids:
                        group_ids.remove(in_ship)
                                  
            if group_ids:
                for dc_in in group_ids:
                    if dc_in not in other_sup:
                        group_ids.remove(dc_in)
                                    
            if len(group_ids)>1:
                
            
                if case.type=='in_invoice' or case.partner_id.handling_charges:
                    if case.state=='draft' and case.origin!='Handling Charges' and case.origin!='IN':
                        res = super(account_invoice,self).do_merge(cr, uid, group_ids, context= context)
                        for temp in self.browse(cr,uid,group_ids):   
                                 
        #                         cr.execute("select del_ord_id from supp_delivery_invoice_rel where invoice_id in %s ",(tuple(group_ids),))
                                    cr.execute("select del_ord_id from supp_delivery_invoice_rel where invoice_id =%s",(temp.id,))
                                    in_ids=cr.fetchall()
                                    for i in in_ids:
                                        if i[0] not in del_ord_in_ids:
                                            del_ord_in_ids.append(i[0])
                    

                            
                    
                                             
                    if del_ord_in_ids:
                        print "state",case.branch_state.id
                        self.write(cr,uid,res.keys(),{'date_invoice': shedular_date,'freight':case.freight,'origin':'DC-Handling Charges',
                                                      'branch_state':case.branch_state.id,'supp_delivery_orders_ids': [(6,0,del_ord_in_ids)],
                                                      },context=context)
                        if res:
#                             self.invoice_validate(cr, uid, res.keys(), context)
                            inv_validate1=res.keys()
                            for j in inv_validate1:
                                wf_service.trg_validate(uid, 'account.invoice', j, 'invoice_open', cr) 
                             
                        
                        for dc in group_ids:
                            if dc in other_sup:
                                other_sup.remove(dc)                         
            elif len(group_ids)==1:
#                 self.invoice_validate(cr, uid, group_ids, context)
                wf_service.trg_validate(uid, 'account.invoice', group_ids[0], 'invoice_open', cr)  
                self.write(cr, uid, group_ids, {'date_invoice':shedular_date}, context)            
            print "name-",case.partner_id.name,"no-"  
            print "Incoming no-",len(group_in_ids),"-",group_in_ids
            
            if len(group_in_ids)>1:
                if case.type=='in_invoice' or case.partner_id.handling_charges:
                    if case.state=='draft' and case.origin!='Handling Charges': 
                        context.update({'other':1})                       
                        res1 = self.do_merge(cr, uid, group_in_ids, context= context)
                        for temp in self.browse(cr,uid,group_in_ids): 
                            cr.execute("select in_shipment_id from incoming_shipment_invoice_rel where invoice_id =%s",(temp.id,))
                            in_ship_ids=cr.fetchall()
                            for j in in_ship_ids:
                                if j[0] not in incoming_in_ids:
                                    incoming_in_ids.append(j[0])
                                    
                    if incoming_in_ids:
                        self.write(cr,uid,res1.keys(),{'date_invoice': shedular_date,'freight':case.freight,'origin':'IN-Handling Charges','branch_state':False,
                                                   'incoming_shipment_ids':[(6,0,incoming_in_ids)]},context=context)
                        if case.branch_state:
                            self.write(cr,uid,res1.keys(),{'branch_state':case.branch_state.id},context=context) 
                        if res1:                                                       
#                             self.invoice_validate(cr, uid, res1.keys(), context)
                            inv_validate=res1.keys()
                            for i in inv_validate:
                                wf_service.trg_validate(uid, 'account.invoice', i, 'invoice_open', cr)    
           
                        for k in group_in_ids:
                            if k in other_sup:
                                other_sup.remove(k) 
            elif len(group_in_ids)==1:
#                 self.invoice_validate(cr, uid, group_in_ids, context)
                wf_service.trg_validate(uid, 'account.invoice', group_in_ids[0], 'invoice_open', cr) 
                self.write(cr, uid, group_in_ids, {'date_invoice':shedular_date}, context)                                            
        return True
    
    
    def do_merge_old_invoice(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        if not context:
            context={}
        
        date_day = time.strftime('%Y-%m-%d')
        day_to=self.get_month(cr,uid,[],date_day,{'day':1}) 
        wf_service = netsvc.LocalService('workflow')
        shedular_date = datetime.strptime(date_day, '%Y-%m-%d') - relativedelta(days=int(day_to))
        shedular_date = shedular_date.strftime('%Y-%m-%d')        
        print shedular_date
        today=context.get('in_date',shedular_date)
        supplier_id=context.get('supplier_id',False)
        partner_obj=self.pool.get('res.partner')
        del_ord_out_ids=[]
        del_ord_in_ids=[]
        shipment_ids=[]
        res={}
        res1={}
        partner_company=[]
        partner=[]
        inv_m=False
        inv_month=[]
        company=[]
        partner_ids=partner_obj.search(cr,uid,[('handling_charges','=',True)])
        month_to=self.get_month(cr,uid,[],today,{'month':1}) 
        print 'month_to',month_to
        year_to=self.get_month(cr,uid,[],today,{'year':1}) 
        
        sup_comp = 1
        inv_comp=context.get('inv',False)
        
        if inv_comp:
           if inv_comp == 'sup':
                cr.execute("select id from res_company where lower(name) like '%supplier%'")
                sup_comp=cr.fetchone()
           elif inv_comp == 'logistic':
                cr.execute("select id from res_company where lower(name) like '%logistic%'")
                sup_comp=cr.fetchone()     
        if sup_comp: 
            sup_comp=sup_comp[0]  
                       
        if supplier_id:
            cr.execute("select id from account_invoice where state='draft' and handling_charges = True and company_id ="+str(sup_comp)+" and partner_id= '" + str(supplier_id) + "' and partner_id in (select id from res_partner where handling_charges = True) and type='in_invoice' and EXTRACT(month from date_invoice) < '" + str(month_to) + "' and EXTRACT(year from date_invoice) ='" + str(year_to) + "'")
        else:
            cr.execute("select id from account_invoice where state='draft' and handling_charges = True and company_id ="+str(sup_comp)+" and partner_id in (select id from res_partner where handling_charges = True) and type='in_invoice' and EXTRACT(month from date_invoice) < '" + str(month_to) + "' and EXTRACT(year from date_invoice) ='" + str(year_to) + "'")
        old_inv=[x[0] for x in cr.fetchall()] 
        if old_inv:
             res = self.do_merge_old_inv(cr,uid,old_inv,context)         
        
        
        return res
        
    #Schedular for merging Facilitator Invoices
    def do_merge_facilitator(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        if not context:
            context={}
        
        date_day = time.strftime('%Y-%m-%d')
        day_to=self.get_month(cr,uid,[],date_day,{'day':1}) 
        wf_service = netsvc.LocalService('workflow')
        shedular_date = datetime.strptime(date_day, '%Y-%m-%d') - relativedelta(days=int(day_to))
        shedular_date = shedular_date.strftime('%Y-%m-%d')        
        print shedular_date
        today=context.get('in_date',shedular_date)
        supplier_id=context.get('supplier_id',False)
        
        partner_obj=self.pool.get('res.partner')
        del_ord_out_ids=[]
        del_ord_in_ids=[]
        shipment_ids=[]
        res={}
        res1={}
        partner_company=[]
        partner=[]
        inv_m=False
        p_id = False
        inv_month=[]
        company=[]
        partners=[]
        partner_ids=partner_obj.search(cr,uid,[('handling_charges','=',True)])
        month_to=self.get_month(cr,uid,[],today,{'month':1}) 
        year_to=self.get_month(cr,uid,[],today,{'year':1}) 
        print 'month_to',month_to
        sup_comp = 1
        inv_comp=context.get('inv',False)
        s_comp = context.get('comp_id',False) 
        if inv_comp:
           if inv_comp == 'sup':
                cr.execute("select id from res_company where lower(name) like '%supplier%'")
                sup_comp=cr.fetchone()
           elif inv_comp == 'logistic':
                cr.execute("select id from res_company where lower(name) like '%logistic%'")
                sup_comp=cr.fetchone()     
        if sup_comp: 
            sup_comp= s_comp or sup_comp[0] 
        
        
                                
        if int(month_to)<8 and int(year_to)==2014:
            if supplier_id:
                cr.execute("select id from account_invoice where state='draft' and handling_charges = True and company_id ="+str(sup_comp)+" and partner_id= '" + str(supplier_id) + "'and partner_id in (select id from res_partner where handling_charges = True) and type='in_invoice' and EXTRACT(month from date_invoice) < '" + str(8) + "' and EXTRACT(year from date_invoice) ='" + str(year_to) + "'")
            else:
                cr.execute("select id from account_invoice where state='draft' and handling_charges = True and company_id ="+str(sup_comp)+" and partner_id in (select id from res_partner where handling_charges = True) and type='in_invoice' and EXTRACT(month from date_invoice) < '" + str(8) + "' and EXTRACT(year from date_invoice) ='" + str(year_to) + "'")
            other_sup=[x[0] for x in cr.fetchall()] 
        else:     
            if supplier_id:
                cr.execute("select id from account_invoice where state='draft'  and handling_charges = True and company_id ="+str(sup_comp)+" and partner_id= '" + str(supplier_id) + "' and partner_id in (select id from res_partner where handling_charges = True) and type='in_invoice' and EXTRACT(month from date_invoice) = '" + str(month_to) + "' and EXTRACT(year from date_invoice) ='" + str(year_to) + "'")
            else:
                cr.execute("select id from account_invoice where state='draft' and handling_charges = True and company_id ="+str(sup_comp)+" and partner_id in (select id from res_partner where handling_charges = True) and type='in_invoice' and EXTRACT(month from date_invoice) = '" + str(month_to) + "' and EXTRACT(year from date_invoice) ='" + str(year_to) + "'")
            other_sup=[x[0] for x in cr.fetchall()] 
                       
#             if supplier_id:
#                 cr.execute("select id from account_invoice where state='draft' and partner_id= '" + str(supplier_id) + "' and partner_id in (select id from res_partner where handling_charges = True) and type='in_invoice' and EXTRACT(month from date_invoice) < '" + str(month_to) + "' and EXTRACT(year from date_invoice) ='" + str(year_to) + "'")
#             else:
#                 cr.execute("select id from account_invoice where state='draft' and partner_id in (select id from res_partner where handling_charges = True) and type='in_invoice' and EXTRACT(month from date_invoice) < '" + str(month_to) + "' and EXTRACT(year from date_invoice) ='" + str(year_to) + "'")
#             old_inv=[x[0] for x in cr.fetchall()] 
#             if old_inv:
#                  self.do_merge_old_inv(cr,uid,old_inv,context)                    
#         other_sup=self.search(cr,uid,[('id','in',partner_ids),('type','=','in_invoice'),('partner_id','in',partner_ids),('state','=','draft'),('origin','=',False)],order='partner_id desc')
#         context.update({'other':1})
        print "no-other_sup-",len(other_sup)
        
        for case in self.browse(cr, uid, other_sup):
            del_ord_in_ids=[]
            incoming_in_ids=[]
            in_ship_ids=[]
            in_ids=[]
            print 'other_sup',case.id
            print "no-",len(other_sup)
            print "name-",case.partner_id.name
            
            group_ids=self.search(cr,uid,[('partner_id','=',case.partner_id.id),('handling_charges','=', True),('company_id','=',case.company_id.id),('state','=','draft'),('id','in',other_sup)],order='partner_id',)
            group_in_ids=self.search(cr,uid,[('origin','=','IN'),('handling_charges','=', True),('partner_id','=',case.partner_id.id),('company_id','=',case.company_id.id),('state','=','draft'),('id','in',other_sup)],order='origin',)
            
            print 'group_ids',group_ids
            cr.execute("select id from account_period where company_id='"+ str(case.company_id.id) +"'and date_start <= '" + shedular_date + "' and date_stop >='" + shedular_date + "'")
            p_ids = cr.fetchone()   
            if p_ids:
                p_id=p_ids[0]
#                 p_id = period_obj.browse(cr, uid, p_ids)      
                      
            if case.type=='in_invoice':
                    
                cr.execute('select EXTRACT(month from date_invoice) from account_invoice where id=%s',(case.id,))
                inv_m=cr.fetchone()
                
#                 if inv_month:
#                     if inv_m not in inv_month:
#                         raise osv.except_osv(_('Warning!'), _("Cannot Merge Invoices of Different month"))   
                                    
                if inv_m:
                    inv_month.append(inv_m[0])
                    inv_m=inv_m[0]            
                        
            if group_in_ids:
                for in_ship in group_in_ids:
                    if in_ship not in other_sup:
                        group_in_ids.remove(in_ship)
                    if in_ship in group_ids:
                        group_ids.remove(in_ship)
                                  
            if group_ids:
                for dc_in in group_ids:
                    if dc_in not in other_sup:
                        group_ids.remove(dc_in)
                                           
                print "group_ids no-",len(group_ids) 
                print "other_sup no-",len(other_sup) 
                
            if len(group_ids)>1:
                
            
                if case.type=='in_invoice' or case.partner_id.handling_charges:
                    if case.state=='draft' and case.origin!='Handling Charges' and case.origin!='IN':
                        res = super(account_invoice,self).do_merge(cr, uid, group_ids, context= context)
                        for temp in self.browse(cr,uid,group_ids):   
                                 
        #                         cr.execute("select del_ord_id from supp_delivery_invoice_rel where invoice_id in %s ",(tuple(group_ids),))
                                    cr.execute("select del_ord_id from supp_delivery_invoice_rel where invoice_id =%s",(temp.id,))
                                    in_ids=cr.fetchall()
                                    for i in in_ids:
                                        if i[0] not in del_ord_in_ids:
                                            del_ord_in_ids.append(i[0])
                    

                            
                    
                                             
                    if del_ord_in_ids:
                        print "state",case.branch_state.id
                        self.write(cr,uid,res.keys(),{'date_invoice': shedular_date,'period_id':p_id,'freight':case.freight,'origin':'DC-Handling Charges',
                                                      'branch_state':case.branch_state.id,'supp_delivery_orders_ids': [(6,0,del_ord_in_ids)],
                                                      },context=context)
#                         self.invoice_validate(cr, uid, res.keys(), context)
                        if res:
                            inv_validate1=res.keys()
                            for j in inv_validate1:
                                wf_service.trg_validate(uid, 'account.invoice', j, 'invoice_open', cr)
                       
                        
                        for dc in group_ids:
                            if dc in other_sup:
                                other_sup.remove(dc)  
            elif len(group_ids)==1:
#                 self.invoice_validate(cr, uid, group_ids, context)
                wf_service.trg_validate(uid, 'account.invoice', group_ids[0], 'invoice_open', cr)                                                                   
                self.write(cr, uid, group_ids, {'date_invoice':shedular_date}, context)
            
            print "name-",case.partner_id.name,"no-"  
            print "Incoming no-",len(group_in_ids),"-",group_in_ids
            print "other_sup no-",len(other_sup),"-",other_sup
            if len(group_in_ids)>1:
                if case.type=='in_invoice' or case.partner_id.handling_charges:
                    if case.state=='draft' and case.origin!='Handling Charges': 
                                 
                        res1 = self.do_merge(cr, uid, group_in_ids, context= context)
                        for temp in self.browse(cr,uid,group_in_ids): 
                            cr.execute("select in_shipment_id from incoming_shipment_invoice_rel where invoice_id =%s",(temp.id,))
                            in_ship_ids=cr.fetchall()
                            for j in in_ship_ids:
                                if j[0] not in incoming_in_ids:
                                    incoming_in_ids.append(j[0])
                                    
                    if incoming_in_ids:
                        self.write(cr,uid,res1.keys(),{'date_invoice': shedular_date,'period_id':p_id,'freight':case.freight,'origin':'IN-Handling Charges','branch_state':False,
                                                   'incoming_shipment_ids':[(6,0,incoming_in_ids)]},context=context)
                        if case.branch_state:
                            self.write(cr,uid,res1.keys(),{'branch_state':case.branch_state.id},context=context)                                                        
#                         self.invoice_validate(cr, uid, res1.keys(), context)
                        if res1:
                            inv_validate=res1.keys()
                            for i in inv_validate:
                                wf_service.trg_validate(uid, 'account.invoice', i, 'invoice_open', cr)   
           
                        for k in group_in_ids:
                            if k in other_sup:
                                other_sup.remove(k)                    
                    
            elif len(group_in_ids)==1:
#                 self.invoice_validate(cr, uid, group_in_ids, context)
                self.write(cr, uid, group_in_ids, {'period_id':p_id,'date_invoice':shedular_date}, context)
                wf_service.trg_validate(uid, 'account.invoice', group_in_ids[0], 'invoice_open', cr)   
            context.update({'other':1})               
            partners.append([case.partner_id.name,case.company_id.name])
            print [case.partner_id.name,case.company_id.name]
        print res  
        print "============"                    
        return res,res1





    def print_inv_lr(self,cr,uid,ids,context=None):
        rep_obj = self.pool.get('ir.actions.report.xml')
        res={}
        res1={}
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment') 
#         pwriter = PdfFileWriter()
#         os.makedirs('/home/serveradmin/Desktop/temp')

        for case in self.browse(cr,uid,ids):
            cr.execute("select id,name from res_partner where upper(name) like 'I.T.C%'")
            partner=cr.fetchall()
            if partner and case.type=='out_invoice':
                self.write(cr, uid, ids, {'origin':False}, context)
                if not case.freight:
                    partner=[d[0] for d in partner]
                    if (case.partner_id.id in partner) and case.report:
                        res = rep_obj.pentaho_report_action(cr, uid, 'Invoice For ITC', ids,None,None)
                    else:   
    #                     raise osv.except_osv(_('Warning'),_('Report Is Specifically For The Customer I.T.C Limited')% (case.partner_id.name,))
                        res = rep_obj.pentaho_report_action(cr, uid, 'Customer Invoice', ids,None,None)
                if case.cft:
                    res = rep_obj.pentaho_report_action(cr, uid, 'Invoice For CFT', ids,None,None)

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

    def account_update(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        del_ord_out_ids=[]
        del_ord_in_ids=[]
        shipment_ids=[]
        origin=''
        product=[]
        product_copy=[]
        product1=[]
        product2=[]
        user=[]
        inv_ids = []
        inv_month=[]
        inv_m=False
        temp_id = []
        today = time.strftime('%Y-%m-%d %H:%M:%S')
        schedular = context.get('schedular',False)
        res = super(account_invoice,self).do_merge(cr, uid, ids, context= context)
        s_parent_id = False
        cr.execute("""select id from account_invoice where handling_charges=True and state!='cancel'
                        and company_id = 3 and date_invoice::date>='2015-02-01'::date
                        and account_id in (
                        select id from account_account where company_id=1
                        )
                        order by date_invoice""")
        temp_id=cr.fetchall()
        for temp in temp_id:
            for case in self.browse(cr, uid, [temp[0]]):
                if case.company_id.id >1 :
                    s_parent_id = case.partner_id.account_pay and case.partner_id.account_pay.id or False
                else:
                    s_parent_id = case.partner_id.property_account_payable and case.partner_id.property_account_payable.id or False
                self.write(cr,uid,[case.id],{'account_id':s_parent_id}) 
        
    
                
        return True
    
    
    def do_merge(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        del_ord_out_ids=[]
        del_ord_in_ids=[]
        shipment_ids=[]
        origin=''
        product=[]
        product_copy=[]
        product1=[]
        product2=[]
        user=[]
        inv_ids = []
        inv_month=[]
        inv_m=False
        today = time.strftime('%Y-%m-%d %H:%M:%S')
        schedular = context.get('schedular',False)
        res = super(account_invoice,self).do_merge(cr, uid, ids, context= context)
        s_parent_id = False
        if context.get('other','')!=1:
            for case in self.browse(cr, uid, ids):
                cr.execute("update account_invoice set user_id ="+str(uid)+" where id = "+str(case.id))
#                 if case.type == 'in_invoice':
#                     if case.company_id.id >1 :
#                         s_parent_id = case.partner_id.account_pay and case.partner_id.account_pay.id or False
#                     else:
#                         s_parent_id = case.partner_id.property_account_payable and case.partner_id.property_account_payable.id or False
              
                cr.execute("select id from account_period where company_id='"+ str(case.company_id.id) +"'and date_start <= '" + str(case.date_invoice) + "' and date_stop >='" + str(case.date_invoice) + "'")
                p_ids = cr.fetchone()   
                if p_ids:
                    p_id = p_ids[0]  
                
                if case.type=='in_invoice':
                    cr.execute('select EXTRACT(month from date_invoice) from account_invoice where id=%s',(case.id,))
                    inv_m=cr.fetchone()
                    
                    if inv_month and inv_m: 
                        if inv_m[0] not in inv_month:
                            if not schedular:
                                raise osv.except_osv(_('Warning!'), _("Cannot Merge Invoices of Different month"))                
               
                    if inv_m:
                        inv_month.append(inv_m[0])
                        inv_m=inv_m[0]
                    
                   
                   
             
                
                if user:
                    if case.user_id.id not in user:
                        cr.execute("update account_invoice set user_id = "+str(user[0])+" where id = "+str(case.id))
                        self.write(cr,uid,[case.id],{'user_id':user[0]})
                        self.write(cr,uid,res.keys(),{'user_id':user[0]})
                else:
                    user.append(case.user_id.id)
                    
                origin=''
                if case.partner_id.handling_charges:
                    origin='Handling Charges'
                    self.write(cr,uid,res.keys(),{'date':today,'origin':'Handling Charges','period_id':p_id, },context=context)
                if case.type=='in_invoice' or case.type=='in_refund':

#                     if product2:
#                         if case.product_id.id not in product2:
#                             raise osv.except_osv(_('Warning!'), _("Cannot Merge Invoices with Different Products"))
#                     if not product2:
#                         product2.append(case.product_id.id)
                                            
                    if case.origin != 'IN':
                        cr.execute("select del_ord_id from supp_delivery_invoice_rel where invoice_id="+str(case.id))
                        in_ids=cr.fetchall()
                        for i in in_ids:
                            del_ord_in_ids.append(i[0])
                    
                elif case.type=='out_invoice':
                    
                    if product1:
                        if case.product_id.id not in product1:
                            raise osv.except_osv(_('Warning!'), _("Cannot Merge Invoices with Different Products"))
                    if not product1:
                        product1.append(case.product_id.id)                    
                       
                    cr.execute("select del_ord_id from delivery_invoice_rel where invoice_id="+str(case.id))
                    del_ids=cr.fetchall()
                    for j in del_ids:
                        del_ord_out_ids.append(j[0])
        #                 inv_ids.append(case.id)
                
                
                if case.type == 'in_invoice' and case.origin:
                    cr.execute("select in_shipment_id from incoming_shipment_invoice_rel where invoice_id="+str(case.id))
                    sh_ids=cr.fetchall()
                    for temp in case.invoice_line:
                        if temp.product_id.name=='Freight':
                            product.append(temp.product_id.name)
                        else:
                            product_copy.append(temp.product_id.name)
                            
                    for k in sh_ids:
                        if k[0] not in shipment_ids:
                            shipment_ids.append(k[0])
                        
                        
                if shipment_ids and del_ord_in_ids:
                    raise osv.except_osv(_('Warning!'), _("Select Same Type Of Invoices"))
                        
                    
      
            if del_ord_out_ids:
                self.write(cr,uid,res.keys(),{'date':today,'freight':case.freight,'branch_state':case.branch_state.id,'delivery_orders_ids': [(6,0,del_ord_out_ids)],'period_id':p_id, },context=context) 
                                                           
            if del_ord_in_ids:
                self.write(cr,uid,res.keys(),{'date':today,'freight':case.freight,'branch_state':case.branch_state.id,'supp_delivery_orders_ids': [(6,0,del_ord_in_ids)],'period_id':p_id, },context=context)  
                 
            if product and product_copy:
                raise osv.except_osv(_('Warning!'), _("Cannot Merge Goods Invoice And Freight Invoice"))
            if shipment_ids:
                if not origin:
                    origin='IN'
                self.write(cr,uid,res.keys(),{'date':today,'incoming_shipment_ids': [(6,0,shipment_ids)],'origin':origin,'branch_state':case.branch_state.id,'period_id':p_id, },context=context)
            if res:
                inv_ids =res.keys()   
            context.update({'inv_ids':inv_ids})                       
#         if res:
#             self.unlink(cr,uid,ids)    
        return res
    
    
    
    
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        if context is None:
            context = {}
        user_id = self.pool.get('res.users').browse(cr, uid,[uid])[0]
#         if user_id:
#             raise osv.except_osv(_('Warning!'), _("You Cannot Duplicate the record, You can only Create New Record "))
        return super(account_invoice, self).copy(cr, uid, id, default, context=context)
    
    def write_sequence(self, cr, uid, today, case, num,form,company,context):
        number=''
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        code1=case.partner_id.state_id.code
        
        l=0
        num_len=0
        num_len=len(num)
        cr.execute("select code from account_fiscalyear where date_start < '" + today + "' and date_stop >'" + today + "'")
        code = cr.fetchone()
        if code:
            year = code[0]
        format = form + year +'/'
        if num_len >= 12:
            if num[:12]==format:
                if len(form)==len(num[0:6]):
                     if form!=num[0:6]:
                         raise osv.except_osv(_('Warning!'), _("You Can only change the number "))
                num_len=12-num_len
                if len(num[num_len:])==5:
                    number=num
                if len(num[num_len:])>5:
                    number=format+num[-5:]
                else:
                    number = format+str(num[12:]).zfill(5)
            else:
                if len(form)==len(num[0:6]):
                     if form!=num[0:6]:
                         raise osv.except_osv(_('Warning!'), _("You Can only change the number "))
                try:
                    num = int(num)
                except ValueError:
                    raise osv.except_osv(_('Warning!'), _("You Can only change the number "))
                    number = False 
                num_len=12-num_len
                num=num[num_len:]
                number= format + str(num).zfill(5)
        else:
            
            try:
                num = int(num)
            except ValueError:
                 if len(form)==len(num[0:6]):
                     if form==num[0:6]:
                         raise osv.except_osv(_('Warning!'), _("You Can only change the number "))
                 raise osv.except_osv(_('Warning!'), _("You Can only change the number "))
                 number = False 
            number= format + str(num).zfill(5)
#         cr.execute("update account_invoice set number=%s where id=%s",(number,case.id,))     

        return number
    
    def write(self, cr, uid, ids,vals, context=None):
        today = time.strftime('%Y-%m-%d')
        code=False
        report=False
        number=''
        if context is None:
            context = {}
        stock_out=[]
        stock_in = []  
        invoice_in = []
        
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company=cr.fetchone()
        if company:
            company=company[0]    
        
        for case in self.browse(cr,uid,ids):
            if 'back_date' in vals:
                cr.execute("""select rel.del_ord_id from supp_delivery_invoice_rel rel
                                inner join account_invoice ai on ai.id = rel.invoice_id
                                where ai.state != 'cancel' and rel.invoice_id = """+str(case.id))
                
                stock_out = [x for x in cr.fetchall()]
                cr.execute("""select rel.in_shipment_id from incoming_shipment_invoice_rel rel
                                inner join account_invoice ai on ai.id = rel.invoice_id
                                where ai.state != 'cancel' and rel.invoice_id = """+str(case.id))
                
                stock_in = [x for x in cr.fetchall()]
                
                if stock_in:
                    cr.execute("""select distinct invoice_id from incoming_shipment_invoice_rel rel
                                inner join account_invoice ai on ai.id = rel.invoice_id
                                where ai.state != 'cancel' and in_shipment_id in %s""",(tuple(stock_in),))
                    invoice_in = [x for x in cr.fetchall()]

                if stock_out:
                    cr.execute("""select distinct invoice_id from supp_delivery_invoice_rel rel
                                inner join account_invoice ai on ai.id = rel.invoice_id
                                where ai.state != 'cancel' and del_ord_id in %s""",(tuple(stock_out),))
                    invoice_in = [x for x in cr.fetchall()]                    
                
                if invoice_in:
                    print 'invoice_in',invoice_in
                    cr.execute("""update account_invoice set back_date = """+str(vals['back_date'])+""" where id in %s""",(tuple(invoice_in),))
                         
            if case.type=='in_invoice':
                vals.update({'handling_charges':case.partner_id.handling_charges})
            
            if not case.freight:
                for temp in case.invoice_line:
                   if temp.product_id.cft:
                        vals.update({'cft':True})
            if 'type' in context:
               
               type=context['type']
               
               if type =='out_invoice':
                               
                   report=case.partner_id.split_invoice 
                   vals.update({'report':report})
                   
                   if 'inv_num' in vals:
                       if vals['inv_num']:
                           try:
                                number = int(vals['inv_num'])
                           except:
                                raise osv.except_osv(_('Warning!'), _("You Can only change the number "))
                           number = False 
                           cr.execute("update account_invoice set number='' where id=%s",(case.id,))
                           number=vals['inv_num']
                           code1=case.branch_state.code
                           if not code1:
                               raise osv.except_osv(_('Warning!'), _('No State Code For Selected State "%s"')%(case.branch_state.name))
                           
                           if case.company_id.id==company:
                                if case.type == 'out_invoice':
                                    format = 'CI/KL/'
                            
                                if case.type == 'out_refund':
                                    format = 'CN/KL/'
                            
                           else:
                                if case.type == 'out_invoice':
                                    format = 'CI/KS/'
                                                           
                                if case.type == 'out_refund':
                                    format = 'CN/KS/'
                           if case.date_invoice:
                               today=case.date_invoice
                           cr.execute("select code from account_fiscalyear where date_start <= '" + today + "' and date_stop >='" + today + "'")
                           code = cr.fetchone()
                           if code:
                                year = code[0]
                                    
                           format = code1+'/'+format + year +'/'
                           number= format + str(number).zfill(5)
                           vals['inv_num']=''
                           vals.update({'number':number})
            if case.company_id:
                cr.execute("update account_invoice_line set company_id=%s where invoice_id=%s",(case.company_id.id,case.id,))       
        res=super(account_invoice, self).write(cr, uid, ids,vals, context=context)
        return res
    
    
#TODO : unlink for invoices
#     def unlink(self, cr, uid, ids, context = None):
#         data = []
#         pick_obj = self.pool.get('stock.picking.out')
#         for case in self.browse(cr,uid,ids):
#             if case.type == 'out_invoice':
#                 cr.execute("select _del_ord_id from delivery_invoice_rel where invoice_id ="+str(case.id))
#                 data = [x for x in cr.fetchall()]
#                 pick_obj.write(cr, uid, data,{'cust_invoice':False})
#         return super(account_invoice,self).unlink(cr, uid, ids,context)
    

    #Inheritted
    def action_cancel_draft(self, cr, uid, ids, *args):
        voucher_obj = self.pool.get('account.voucher')
        res = super(account_invoice,self).action_cancel_draft(cr, uid, ids, *args)
        for case in self.browse(cr, uid, ids):
            #To set posted vouchers to draft which are created from pay freight
            for pick in case.supp_delivery_orders_ids:
                vid = voucher_obj.search(cr,uid,[('reference','=',pick.name)])
                if vid:
                    voucher_obj.cancel_voucher(cr, uid, vid,context=None)
                    voucher_obj.action_cancel_draft(cr,uid,vid,context=None)
        
        return res
    
    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        account_move_obj = self.pool.get('account.move')
        res=super(account_invoice, self).action_cancel(cr,uid,ids,context)

        self.write(cr, uid, ids, {'internal_number':''})

        return res
    
    def server_action_validate(self, cr, uid, ids, context):
        """ Select only Open Records """
        open_ids = self.search(cr, uid,[('state','=','paid'),('id','in',ids)])
        if open_ids:
            raise osv.except_osv(_('Warning!'), _('You Need to select only Open records'))
        self.action_cancel(cr, uid, ids,context=context)
        self.action_cancel_draft(cr, uid,ids,{})
        self.write(cr, uid,ids,{'back_date':True})
        wf_service = netsvc.LocalService('workflow')
        for i in self.browse(cr, uid, ids):
            wf_service.trg_validate(uid, 'account.invoice', i.id, 'invoice_open', cr)  

    def create_facilitator_inv(self, cr, uid, ids, context=None):
        print "context-",context
        if not context:
            context={}
            
        if context.get('state','Karnataka'):
            fac_state =  context.get('state','Karnataka')
        in_fac_state = ''
        partner_ids = []
        date_day = time.strftime('%Y-%m-%d')
        context.update({'schedular':True})
        today = context.get('shedular_date',date_day)
        state = context.get('state',False)
        stock_p = self.pool.get('stock.picking')
        wf_service = netsvc.LocalService('workflow')
        invoices_ids = []
        invoice_id = []
        inv_ids = []
        merged_invoice_id = []
        res={}
        st={}
        st_ids = []
        invoices = {}
        out_shedular_month_ids = {}
        billing = {}
        invoice_create = False
        merged = False
        merged_ids = []
        month_to = 0
        stock_obj = self.pool.get('stock.picking.out')
        stock_in_obj = self.pool.get('stock.picking.in')
        billing_obj = self.pool.get('billing.cycle') 
        partner_obj = self.pool.get('res.partner') 
        stock_ids = []
        in_shipment_ids = []
        invoice_create_out = True
        invoice_create_in = True
        invoice_created_in = []
        invoice_created_out = []
        if not today:        
            today = time.strftime('%Y-%m-%d')
        
        # Added to cond to subtract the 2 days only if it comes from schedular
        shedular_date = datetime.strptime(today, '%Y-%m-%d')
        if not context.get('facilitator'):
            shedular_date =  shedular_date - relativedelta(days=int(2))
        shedular_date = shedular_date.strftime('%Y-%m-%d')
        
        day_to = self.get_month(cr,uid,[],date_day,{'day':1}) 
        last_date = datetime.strptime(date_day, '%Y-%m-%d') - relativedelta(days=int(day_to))
        last_date = last_date.strftime('%Y-%m-%d')   
        last_date_from = self.get_month(cr,uid,[],shedular_date,{'month':1})  
        last_date_to = self.get_month(cr,uid,[],last_date,{'month':1})    
        
        cr.execute("select id from res_partner where lower(name) like 'dummy%'")
        dummy_ids=[y[0] for y in cr.fetchall()]
        # removing the S-Ramakrishnappa - T
        dummy_ids.append(2054)
#         print "Date-",shedular_date
        stock_ids_in = []
        stock_ids_out = []
        more_inv = []
        invoice_rate_out = False
        invoice_rate_in = False
        shedular_month = self.get_month(cr,uid,[],shedular_date,{'month':1})   
        in_shedular_month_ids = {}
        order_id = []
        merged_invoice = []
        sch_partner_id = self.pool.get('res.users').browse(cr, uid, uid).partner_id.id
#         if state:

        query_out = """select distinct sp.id from stock_picking sp 
                        left outer join res_country_state rs on rs.id = sp.state_id
                        where sp.date::date >= '2016-02-01' and type = 'out' 
                        and sp.date::date <= '"""+str(shedular_date)+"""'::date and sup_invoice = False                        
                        and sp.state in ('done','freight_paid') and sp.del_quantity>0
                        and lower(rs.name) ilike '%"""+fac_state+"""%'"""
                        
        if context.get('facilitator'):
            query_out += ' and sp.paying_agent_id ='+str(context.get('facilitator'))
            
        
        cr.execute(query_out) 
 
#                         and sp.id not in 
#                         (SELECT dr.del_ord_id FROM supp_delivery_invoice_rel dr inner 
#                         join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id  IN %s and ac.state <>'cancel')""",(tuple(dummy_ids),tuple(dummy_ids),))
          
#         cr.execute("""select id from stock_picking where type='out' and 
#         date::date >= %s::date and state in ('done','freight_paid') and sup_invoice=False""",(str(shedular_date),)) 
        stock_ids_out=cr.fetchall()
        if stock_ids_out:
            stock_ids_out=zip(*stock_ids_out)[0]
            if isinstance(stock_ids_out, tuple):
                stock_ids_out = list(stock_ids_out)
            #stock_obj.write(cr,uid,stock_ids_out,{'user_id':1})
            #cr.execute("""update stock_picking set user_id = 1 where id in %s""",(tuple(stock_ids_out),))  
#         stock_ids_out = [x[0] for x in cr.fetchall()]
#         stock_ids_out = stock_obj.search(cr,uid,[('id','in',stock_ids_out),('paying_agent_id','not in',dummy_ids)])
        

        if fac_state.lower() == 'karnataka':
           in_fac_state = 'KA'
        else:
           in_fac_state ='TN'
           
        
        query_in = """select distinct sp.id from stock_picking sp 
                        left outer join res_country_state rs on rs.id = sp.state_id
                        where sp.date::date >= '2016-02-01' and type = 'in' 
                        and sp.date::date <= '"""+str(shedular_date)+"""'::date and sup_invoice = False                        
                        and sp.state in ('done','freight_paid') and lower(sp.name) ilike '%"""+in_fac_state+"""%'"""
        
        if context.get('facilitator'):
            query_in += ' and sp.partner_id ='+str(context.get('facilitator'))
        
        cr.execute(query_in)
 
        stock_ids_in=cr.fetchall()
        if stock_ids_in:
            stock_ids_in=zip(*stock_ids_in)[0] 
            
            if isinstance(stock_ids_in, tuple):
                stock_ids_in = list(stock_ids_in) 
                         
            #stock_obj.write(cr,uid,stock_ids_in,{'user_id':1})
            #cr.execute("""update stock_picking set user_id = 1 where id in %s""",(tuple(stock_ids_in),))  
        if stock_ids_out or stock_ids_in:
            if stock_ids_out:
                cr.execute("""select sp.id from stock_picking sp where sp.date::date >= '2016-02-01'::date and sp.id not in (SELECT dr.del_ord_id FROM supp_delivery_invoice_rel dr inner 
                join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id  IN %s and ac.state <>'cancel') and sp.id in %s""",(tuple(stock_ids_out),tuple(stock_ids_out)))    
#                 order_id = cr.fetchall()
                order_id=cr.fetchall()
                if order_id:
                    order_id=zip(*order_id)[0]
            
                 

            if stock_ids_in:
                cr.execute("""select sp.id from stock_picking sp where sp.date::date >= '2016-02-01'::date and sp.id not in 
                (SELECT dr.in_shipment_id FROM incoming_shipment_invoice_rel dr inner
                join account_invoice ac on ac.id=dr.invoice_id WHERE dr.in_shipment_id  IN  %s and ac.state <>'cancel')and sp.id in %s""",(tuple(stock_ids_in),tuple(stock_ids_in)))    
                in_shipment_ids = cr.fetchall()
                if in_shipment_ids:
                    in_shipment_ids=zip(*in_shipment_ids)[0]                   

            stock_ids_out = stock_obj.search(cr,uid,[('id','in',order_id),('paying_agent_id','not in',dummy_ids),('type','=','out')])

            stock_ids_in = stock_in_obj.search(cr,uid,[('id','in',in_shipment_ids),('partner_id','not in',dummy_ids),('type','=','in')]) 
            
            invoice_rate_out = stock_obj.get_supplier_rate(cr,uid,stock_ids_out,False,context=context)
            
            invoice_rate_in = stock_in_obj.get_supplier_rate(cr,uid,stock_ids_in,False,context=context)
            
            
            if stock_ids_out:
                if not invoice_rate_out:
                    return False    
            if stock_ids_in:
                if not invoice_rate_in:
                    return False     
            if stock_ids_out: 
                cr.execute("""select id from stock_picking where EXTRACT(month from date)= '""" + str(shedular_month) + """'and id in %s""",(tuple(stock_ids_out),))
                out_shedular_month = [x[0] for x in cr.fetchall()] 
                out_shedular_month_ids[shedular_month] = out_shedular_month
                print "out_shedular_month",out_shedular_month
                
                
                if out_shedular_month: 
                    cr.execute("""select id from stock_picking where id not in %s and id in %s""",(tuple(out_shedular_month),tuple(stock_ids_out)))
                # checking for old records
                else:
                    cr.execute("""select id from stock_picking where id in %s""",(tuple(stock_ids_out),))
                
                out_old_month = [y[0] for y in cr.fetchall()]
                if out_old_month:
                    old_month = int(shedular_month) - 1
                    out_shedular_month_ids[old_month] = out_old_month  
                         

                
                for sh_month in out_shedular_month_ids:
                    invoice_create_out = stock_obj.get_supplier_invoice(cr,uid,out_shedular_month_ids[sh_month],False,context=context) 
                    if context.get('invoices',[]) not in invoice_created_out:
                        invoice_created_out.append(context.get('invoices',[]))
                        
            if stock_ids_in:               
                cr.execute("""select id from stock_picking where EXTRACT(month from date)= '""" + str(shedular_month) + """'and id in %s""",(tuple(stock_ids_in),))
                shedular_in = [x[0] for x in cr.fetchall()] 
 
                in_shedular_month_ids[shedular_month] = shedular_in
                
                if shedular_in:
                    cr.execute("""select id from stock_picking where id not in %s and id in %s""",(tuple(shedular_in),tuple(stock_ids_in)))
                    in_old_month = [x[0] for x in cr.fetchall()] 
                
                    old_month = int(shedular_month) - 1
                    in_shedular_month_ids[old_month] = in_old_month  
                       
#             stock_ids_in = []

#             print len(out_shedular_month_ids['shedular_month']),'-shedular_month',
#             print len(out_shedular_month_ids['old_month']),'-old_month',  
            
            for in_month in in_shedular_month_ids:
                invoice_create_in = stock_in_obj.get_invoice(cr,uid,in_shedular_month_ids[in_month],False,context=context)
                if context.get('in_invoices',[]) not in invoice_created_in:
                    invoice_created_in.append(context.get('in_invoices',[]))
                                                       
#             invoice_create_in = stock_in_obj.get_invoice(cr,uid,stock_ids_in,False,context=context)
                
            #print 'context created',context
            invoice = invoice_created_out
            in_invoice = invoice_created_in
                       
            #print 'no. in_invoice to merge', len(in_invoice)
            for out in invoice:
                if out and out not in invoice_id:
                    invoice_id.append(out)
#             print 'out_invoices',invoice_id
#             print 'no. invoice to merge', len(invoice_id)
            
            for in_id in in_invoice:
                 if in_id and in_id not in invoice_id:
                     invoice_id.append(in_id) 
                  
#             print 'invoices',invoice_id
#             print 'no. invoice to merge', len(invoice_id)   
            
            
            for i_id in invoice_id:
#                 print 'i_id',i_id
                cr.execute("""update account_invoice set back_date=True where id in %s """,(tuple(i_id),))
#                 self.write(cr,uid,i_id,{'back_date':True})
                for case in self.browse(cr,uid,i_id):
                    inv_date = shedular_date
#                     print 'case',case
                    if case.date_invoice:
                        month_to=self.get_month(cr,uid,[],case.date_invoice,{'month':1})
                        
                    if last_date_to != month_to:
                        inv_date = last_date
                    self.write(cr,uid,[case.id],{'date_invoice':inv_date})
                    if case.partner_id.id not in partner_ids:
                        partner_ids.append(case.partner_id.id)
                    
                    key = (case.partner_id, case.company_id, case.type, case.origin, month_to)
                    if key not in invoices :
                        invoices[key] = [case.id]
                    else:
                        invoices[key].append(case.id)   
           
            for merge_inv in invoices:
                inv_date = shedular_date
                invoices_ids = invoices[merge_inv]
                if invoices_ids and len(invoices_ids)==1:
#                     print "validate single",invoices_ids
                    cr.execute("""update account_invoice set back_date=True,user_id=1 where id = %s """,(invoices_ids[0],))   
                    inv_done = self.browse(cr,uid,invoices_ids[0])
                    inv_done_to=self.get_month(cr,uid,[],inv_done.date_invoice,{'month':1})
                    if last_date_to != inv_done_to:
                        inv_date = last_date
                    self.write(cr,uid,[invoices_ids[0]],{'date_invoice':inv_date,'back_date':True})
                    wf_service.trg_validate(uid, 'account.invoice', invoices_ids[0], 'invoice_open', cr) 
                    merged_invoice.append(invoices_ids[0])
                else:
                    inv_done_m = self.browse(cr,uid,invoices_ids[0])
                    inv_done_to=self.get_month(cr,uid,[],inv_done_m.date_invoice,{'month':1}) #inv_done
                    if last_date_to != inv_done_to:
                        inv_date = last_date                    
                    self.do_merge(cr, uid, invoices_ids, context)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
                    merged_ids=context.get('inv_ids',[])
                    for merged_inv in merged_ids:
#                         print 'before merged',merged_ids
                        cr.execute("""update account_invoice set back_date=True where id = %s """,(merged_inv,))                        
                        self.write(cr,uid,[merged_inv],{'date_invoice':inv_date,'back_date':True})
                        wf_service.trg_validate(uid, 'account.invoice', merged_inv, 'invoice_open', cr)
                        merged_invoice.append(merged_inv)
#                         
                 
#             print "Date-",shedular_date  
            for partner_id in partner_ids:
#                 print 'Facilitator', partner_id.name
    #             context.update({'billing_ids':[{'partner_id':partner_id.id}]})
                billing_list = billing_obj.search(cr,uid,[('partner_id','=',partner_id)],order='end_date desc',limit=1)
                for i in billing_obj.browse(cr,uid,billing_list,context):
                    end_date = datetime.strptime(i.end_date, '%Y-%m-%d') + relativedelta(days=int(1))
                    
                    st_date = str(end_date)
                    end_date = end_date.strftime('%Y-%m-%d')
                    
                    if end_date < today:
                        try:                                
                                        
                                     
                            billing.update({'st_date':st_date,
                                            'end_date':today,
                                            'partner_id':partner_id,
                                             
                                            })
                            billing_cycle=billing_obj.create(cr,uid,billing,context)
                            billing_obj.generate_report(cr,uid,[billing_cycle],context)
                        except:
                             pass
                    else:
                         billing_obj.generate_report(cr,uid,billing_list,context)  
           
                if not billing_list:
                        year_to=self.get_month(cr,uid,[],shedular_date,{'year':1})
                        cr.execute("select date_start from account_fiscalyear where date_start <= '" + str(today) + "' and date_stop >='" + str(today) + "'")
                        date_start = cr.fetchone()
                        date_start = date_start and date_start[0] or ''                        
                        billing.update({'st_date': date_start,
                                        'end_date':today,
                                        'partner_id':partner_id,
                                         
                                        })
                        billing_cycle=billing_obj.create(cr,uid,billing,context)
                        billing_obj.generate_report(cr,uid,[billing_cycle],context)
            if stock_ids_out:
                cr.execute("""update stock_picking set sup_invoice=True where state = 'out' and id in
                (SELECT dr.del_ord_id FROM supp_delivery_invoice_rel dr inner 
                join account_invoice ac on ac.id=dr.invoice_id WHERE ac.state <>'cancel' and ac.type ='in_invoice') and id in %s """,(tuple(stock_ids_out),))

            if stock_ids_in:    
                cr.execute("""update stock_picking set sup_invoice=True where state = 'in' and id in 
                (SELECT dr.del_ord_id FROM supp_delivery_invoice_rel dr inner 
                join account_invoice ac on ac.id=dr.invoice_id WHERE ac.state <>'cancel' and ac.type ='in_invoice' )and id in %s """,(tuple(stock_ids_in),))
                    
            
            
            merged_ids=self.search(cr,uid,[('state','=','draft'),('id','in',merged_invoice)]) 
            for not_done in merged_ids:
                wf_service.trg_validate(uid, 'account.invoice', not_done, 'invoice_open', cr)
#                 print 'not-done',not_done
                
            # for sending mails
            if partner_ids:
                partner_obj.write(cr, uid, [sch_partner_id], {'list_of_cust' : partner_ids}, context)
                self.send_billing_cycle_mail(cr, uid, [], context)
            return res

      
    #Schedular for Create Facilitator Invoices
    def create_facilitator_invoice(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        if not context:
            context={}
        state_id1 = context.get(1,False) 
        state_id2 = context.get(2,False)
        
        context.update({'shedular_date':'2016-04-13'})

#         print "Schedular",context
        res = self.create_facilitator_inv(cr,uid,[uid],context)
        
        return res
    
    
    #Schedular for Create Facilitator Invoices
    def update_invoice(self, cr, uid, ids, context=None):
        if not context:
            context={}
        stock_ids_out = []
        stock_obj = self.pool.get('stock.picking.out')
        today = time.strftime('%Y-%m-%d')
        cr.execute("""select distinct sp.id from stock_picking sp 
                        left outer join res_country_state rs on rs.id = sp.state_id
                        where sp.date::date >= '2014-12-01'
                        and sp.date::date <= '"""+str(today)+"""'::date                           
                        and sp.state in ('done','freight_paid') and sp.sup_invoice=True
                        and lower(rs.name) like 'karnataka%'""")
          
        stock_ids_out=cr.fetchall()
        if stock_ids_out:
            stock_ids_out=zip(*stock_ids_out)[0] 
        stock_ids_out = stock_obj.search(cr,uid,[('id','in',stock_ids_out)])
        for case in stock_obj.browse(cr,uid,stock_ids_out):
            cr.execute("""SELECT ai.date_invoice from supp_delivery_invoice_rel dr inner join account_invoice ai on ai.id = dr.invoice_id where 
                            ai.type = 'in_invoice' and ai.state = 'open' and ai.company_id = 1 and dr.del_ord_id = """+str(case.id))
            date_invoice = cr.fetchone()
            if date_invoice:
                date_invoice = date_invoice[0]
                cr.execute("""SELECT ai.id from supp_delivery_invoice_rel dr inner join account_invoice ai on ai.id = dr.invoice_id where 
                                dr.del_ord_id = """+str(case.id))
                invoice_ids = cr.fetchall() 
                if invoice_ids: 
#                     print  'invoice_ids',invoice_ids                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                    invoice_ids=zip(*invoice_ids)[0]  
                    cr.execute("""update account_invoice set date_invoice = '"""+str(date_invoice)+"""' where id in %s""",(tuple(invoice_ids),))
            invoice_ids = []
            date_invoice = False   
            
        print date_invoice
         
                    
        return True
        
       

    # Mail,after successful completion of facilitator invoice by schedular
    def send_billing_cycle_mail(self,cr,uid,ids,context=None):
        res={}
        if not context:
            context = {}
        partners = ''
        mail_obj = self.pool.get('mail.mail')
        partner_obj = self.pool.get('res.partner')
        email_obj = self.pool.get('email.template')
        prod_obj = self.pool.get('product.product')
        user_obj = self.pool.get('res.users')
       
        template = self.pool.get('ir.model.data').get_object(cr, uid,'kingswood', 'billing_cycle_send_mail')
        assert template._name == 'email.template'
        
        for case in user_obj.browse(cr,uid,[uid]):
            
            cr.execute(""" select distinct rp.email 
                            from res_groups_users_rel gu 
                            inner join res_groups g on g.id = gu.gid
                            inner join res_users ru on ru.id = gu.uid
                            inner join res_partner rp on rp.id = ru.partner_id  
                            where g.name = 'KW_Admin' and rp.email is not null""")
            for p in cr.fetchall():
#                 p = partner_obj.browse(cr, uid,p[0])
                partners += (p and p[0] or "") + ","
            if partners:
                email_obj.write(cr, uid, [template.id], {'email_to':partners[0:-1]})
                        
            mail_id = self.pool.get('email.template').send_mail(cr, uid, template.id, case.partner_id.id, True, context=context)
            mail_state = mail_obj.read(cr, uid, mail_id, ['state'], context=context)
            if mail_state and mail_state['state'] == 'exception':
                raise osv.except_osv(_("Cannot send email(date): no outgoing email server configured.\nYou can configure it under Settings/General Settings."), case.partner_id.name)
        return True 
           
account_invoice()


class account_invoice_line(osv.osv):
    _inherit="account.invoice.line"
    def _qty_in_words(self, cr, uid, ids, fields_name, args, context):
        res = {}
        txt = '' 
        for case in self.browse(cr, uid, ids):
            if case.quantity:
                txt += amount_to_text_softapps._100000000_to_text(int(round(case.quantity)))        
                res[case.id] = txt     
        return res
    _columns={
                'name': fields.text('Description', required=True),
               'rejected_qty'    :   fields.float('Rejected Quantity',digits=(0,3)),
               'qty_txt'         :   fields.function(_qty_in_words, type='text', method = True,store=True, string='Total text'),
               'state'           :   fields.selection([('done','Delivered'),('draft','Draft')], 'Status'),
               #for reporting purposes
               'move_line_id'                :  fields.many2one('stock.move','Move Line Id'),
#                'price_unit'      : fields.float('Unit Price', digits_compute= dp.get_precision('Product Price'), readonly=True, states={'draft': [('readonly', False)]} ),
     
             }

    def _default_account_id(self, cr, uid, context=None):
        # XXX this gets the default account for the user's company,
        # it should get the default account for the invoice's company
        # however, the invoice's company does not reach this point
        prop=False
        if context is None:
            context = {}
            
        if context.get('type') in ('in_refund','in_invoice'):
            cr.execute("select id from account_account where lower(name) ilike 'purchase of wood' and company_id = 1")
            prop = [x[0] for x in cr.fetchall()]
            if prop:
                return prop[0]
        elif 'acc_id' in context:
            return context['acc_id']
        else:
            return super(account_invoice_line, self)._default_account_id(cr,uid,context)
        
    _defaults={
               'name':"Invoice Refund",
                'state': 'draft',
                 'account_id': _default_account_id,
               }
   
#     def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):
#         res=super(account_invoice_line, self).product_id_change( cr, uid, ids, product=product, uom_id=uom_id, qty=qty, name=name, type=type, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id, context=context, company_id=company_id)
#         if context is None:
#             context = {}
#         if company_id>1:
#             prod_obj = self.pool.get('product.product')
# #             prod_id=prod_obj.search(cr,uid,[('name','=','Freight')])
# #             if prod_id[0]!=product:
# #                raise osv.except_osv(_('Warning!'), _('You Can only Select Freight For Kingswood Logistics'))
# #             else:
#             res['value']['company_id']=company_id 
#          
#         print res
#         return res 

    #overidden to achieve multiple account for move line for I.T.C Limited
    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = []
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        if context is None:
            context = {}
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
        for line in inv.invoice_line:
            #context.update({'line1':{'account_id':2248,'price_unit':1,'price':line.quantity * 1},'line2':{'account_id':2248,'price_unit':1,'price':line.quantity * 1}})
            
            if inv.other_charges:
                context.update({'line':{'account_id':inv.transport_acc_id.id,'price_unit':inv.transport_charges,'price_subtotal':line.quantity * inv.transport_charges}})
                mres = self.move_line_get_item(cr, uid, line, context)
                if not mres:
                    continue
                res.append(mres)
                
                context.update({'line':{'account_id':inv.loading_acc_id.id,'price_unit':inv.loading_charges,'price_subtotal':line.quantity * inv.loading_charges}})
                mres = self.move_line_get_item(cr, uid, line, context)
                if not mres:
                    continue
                res.append(mres)
            
            else:
                mres = self.move_line_get_item(cr, uid, line, context)
                if not mres:
                    continue
                res.append(mres)
                
            tax_code_found= False
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id,
                    (line.price_unit * (1.0 - (line['discount'] or 0.0) / 100.0)),
                    line.quantity, line.product_id,
                    inv.partner_id)['taxes']:

                if inv.type in ('out_invoice', 'in_invoice'):
                    tax_code_id = tax['base_code_id']
                    tax_amount = line.price_subtotal * tax['base_sign']
                else:
                    tax_code_id = tax['ref_base_code_id']
                    tax_amount = line.price_subtotal * tax['ref_base_sign']

                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(self.move_line_get_item(cr, uid, line, context))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, tax_amount, context={'date': inv.date_invoice})
        return res

    
    #overidden to achieve multiple account for move line for I.T.C Limited
    def move_line_get_item(self, cr, uid, line, context=None):
        if context.get('line'):
            return {
                    'type':'src',
                    'name': line.name.split('\n')[0][:64],
                    'price_unit':context.get('line')['price_unit'],
                    'quantity':line.quantity,
                    'price':context.get('line')['price_subtotal'],
                    'account_id':context.get('line')['account_id'],
                    'product_id':line.product_id.id,
                    'uos_id':line.uos_id.id,
                    'account_analytic_id':line.account_analytic_id.id,
                    'taxes':line.invoice_line_tax_id,
                    }
        return {
            'type':'src',
            'name': line.name.split('\n')[0][:64],
            'price_unit':line.price_unit,
            'quantity':line.quantity,
            'price':line.price_subtotal,
            'account_id':line.account_id.id,
            'product_id':line.product_id.id,
            'uos_id':line.uos_id.id,
            'account_analytic_id':line.account_analytic_id.id,
            'taxes':line.invoice_line_tax_id,
        } 
       
account_invoice_line()

class account_invoice_tax(osv.osv):
    _inherit="account.invoice.tax"
    _columns={
              }

account_invoice_tax()

class account_voucher(osv.osv):
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        result=super(account_voucher,self).name_get(cr, uid, ids)
        
        if context.get('rtgs','')==True:
            result = []
            for voucher in self.browse(cr, uid, ids, context=context):
                result.append((voucher.id, (voucher.partner_id.name or '')+'/ ('+str(voucher.id)+')'))
      
            
        return result    
    
    def _get_customer(self, cr, uid, ids, fields_name, args, context):
        res = {} 
        stock_obj=self.pool.get('stock.picking.out')
        voucher_line = self.pool.get('account.voucher.line')
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'customer_id':False,'owner_name':''}
            if case.reference:
                stock_id=stock_obj.search(cr,uid,[('name','=',case.reference)])
                stock_ids=stock_obj.browse(cr,uid,stock_id)
                for i in stock_ids:
                   res[case.id]['customer_id'] = i.partner_id.id  
            if case.account_owner:
                 res[case.id]['owner_name'] = case.account_owner
            else:
                res[case.id]['owner_name']=case.partner_id.name
#             for line in case.line_dr_ids:
#                 cr.execute("update account_voucher_line set company_id="+str(case.company_id.id)+" where id="+str(line.id)) 
               
            cr.execute("select id from account_account where lower(name) like 'miscellaneous%'")
            acc_no=[x[0] for x in cr.fetchall()] 
            j_id=self.search(cr,uid,[('journal_id','in',acc_no),('mis_journal','=',False)])
            self.write(cr,uid,j_id,{'mis_journal':True})
               
        return res
    
   
    _inherit="account.voucher"
    _columns={
              'advance'   :   fields.boolean('advance'),
              'customer_id':  fields.function(_get_customer,type='many2one',relation='res.partner',store=True, string='Customer',multi='names'),
              'back_date'  :  fields.boolean('Back Date Entry'),
              'advance_type': fields.selection([('advance','Advance'),('rtgs','RTGS'),('b2b','B2B Transfer')], 'Type'),
              'bank_id'     : fields.many2one('res.bank','Bank'),
              'bank_address' : fields.text('Bank Address'),
              'ifsc'        : fields.char('IFSC',size=20),
              'bank_name'   : fields.char('Bank Name', size=100),
              'acc_number'  : fields.many2one('res.partner.bank','Account Number'),
              'address'     : fields.text('Address'),
              'charges'     : fields.boolean('Charges'),
              'voucher_id'     : fields.many2one('account.voucher','Voucher'),
              'account_owner'  : fields.char('Account Owner Name',size=100),
              'owner_name'  : fields.function(_get_customer,type='char',size=100,store=True, string='Account Owner/Facilitator',multi='names'),
#               'company_change' : fields.function(_get_customer,type='many2one',relation='res.company',store=True,multi='names'),
              'bank'        :   fields.many2one('account.journal',"Bank Name"),
              'mis_journal' :   fields.boolean('Miscellaneous Journal'),
            'date_from'             :fields.function(lambda *a,**k:{}, method=True, type='date',string="From"),
            'date_to'               :fields.function(lambda *a,**k:{}, method=True, type='date',string="To"), 
            'customer'    : fields.boolean('Customer'),
            'bank_charge'   : fields.float('Bank Charges',digits=(0,2)),
            'reject'        : fields.float('Rejected',digits=(0,2)),   
             'prod_sale'        : fields.float('Product Sale',digits=(0,2)), 
          'reference': fields.char('Ref #', readonly=True, states={'draft':[('readonly',False)]},
                 help="Transaction reference number.", copy=False,size=200),
              }
    _defaults={
               'advance'   : False,
               'back_date' : False,
               'mis_journal': False,
               'advance_type':'rtgs',
               }
    
    
    #To adjust the payment entries
    def compute_adjustment(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        inv_obj = self.pool.get('account.invoice')
        pick_obj = self.pool.get('stock.picking.out')
        vline_obj = self.pool.get('account.voucher.line')
        mvln_obj = self.pool.get('account.move.line')
        company_ids = []
        supplier_ids = {}
        today = time.strftime('%Y-%m-%d')
        cr.execute("select id from account_invoice where create_date::date = '"+today+"'::date and state = 'open' and type= 'in_invoice' order by id asc")
        #inv_ids = acc_obj.search(cr, uid, [('create_date','=',today),('state','=','open'),('type','=','in_invoice')])
        inv_ids = [x[0] for x in cr.fetchall() ]
        
        
        for inv in inv_obj.browse(cr, uid, inv_ids):
            data = self.onchange_company_id(cr, uid, ids, inv.company_id.id,inv.partner_id.id,False,'payment',context=context)['value']
            acc_details = self.onchange_payment(cr, uid, ids, inv.partner_id.id, data['journal_id'], 0.0, False, 'payment',today,inv.company_id.id,context=context)['value']
           
            vals = {
                    'partner_id'  : inv.partner_id.id,
                    'company_id'  : inv.company_id.id,
                    'pre_line'    : acc_details['pre_line'],
                    'account_id'  : acc_details['account_id'],
                    'period_id'   :  data['period_id'],
                    'journal_id'  :  data['journal_id'],
                    'date'        :  inv.date_invoice and inv.date_invoice or today,
                    }
            context.update({'company':inv.company_id.id,'type':'payment'})
            mv_ln_ids = vline_obj.search(cr, uid, [('move_line_id.invoice','=',inv.id)])
            for ln in vline_obj.browse(cr, uid, mv_ln_ids):
                if ln.voucher_id.state == 'draft':
                    self.write(cr, uid, [ln.voucher_id.id] ,{'state':'cancel'})
            v_id = self.create(cr, uid, vals, context=context)
            self.get_lines(cr, uid, [v_id], context)
            self.proforma_voucher(cr, uid, [v_id], context)
                
        return True
    
    #schedular for Creating Invoices
    def do_adjustment(self, cr, uid, automatic = False, use_new_cursor = False,context = None ):
        print "inside payment"
        self.compute_adjustment(cr, uid, [], context)
        return True
    
    def onchange_company_id(self, cr, uid, ids, company_id,partner_id,journal_id,type,context=None):
        if context is None: 
            context = {}
        voucher_line=self.pool.get('account.voucher.line')
        res = {}
        dom = {}
        ctx={}
        voucher=[]
        line_dr_ids = {}
        line_cr_ids = {}
        j_ids=False
        line_acc1=[]
        line_acc = []
# print 'type',type 
        account_obj = self.pool.get('account.account') 
        acc_type = self.pool.get('account.account.type')
#                      
#         if partner_id:
#             partner = self.pool.get('res.partner').browse(cr,uid,partner_id)
#         company = self.pool.get('res.company').browse(cr, uid, company_id)
#         
#         journal_obj = self.pool.get('account.journal')
#         if company_id:
#             dom = {'journal_id':  [('company_id', '=', company_id)]}
#         
#         #for updating default journal for purchases based on company
#         if company_id and type == 'purchase':
#             if ids:
#                 if company_id >1:
#                     line_dr_ids.update({'company_id':company_id})
#                     
#                     type_id = acc_type.search(cr,uid,[('report_type','=','expense')])
#                     if type_id:
#                        line_acc=account_obj.search(cr,uid,[('user_type','in',type_id),('company_id','=',company_id)])
#                     if line_acc:
#                        line_acc = line_acc[0] 
# #                        line_dr_ids.update({'account_id':line_acc})   
#                     res.update({'line_dr_ids':line_dr_ids})                
        print 'type',type  
                     
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr,uid,partner_id)
        company = self.pool.get('res.company').browse(cr, uid, company_id)
        
        journal_obj = self.pool.get('account.journal')
        if company_id:
            dom = {'journal_id':  [('company_id', '=', company_id)]}
            line_dr_ids.update({'company_id':company_id})
        
        if company_id and type == 'sale':
            for case1 in self.browse(cr,uid,ids):
                for line1 in case1.line_cr_ids:
                    if company_id:
                        type_id1 = acc_type.search(cr,uid,[('report_type','=','income')])
                        if type_id1:
                           line_acc1=account_obj.search(cr,uid,[('user_type','in',type_id1),('company_id','=',company_id),('note','like','Sales')])
                        if line_acc1:
                           line_acc1 = line_acc1[0] 
#                        line_dr_ids.update({'account_id':line_acc})                         
                        line_cr_ids.update({'company_id':company_id,'account_id':line_acc1})
                        voucher_line.write(cr,uid,[line1.id],line_cr_ids)        
        
        
        
        #for updating default journal for purchases based on company
        if company_id and type == 'purchase':
            for case in self.browse(cr,uid,ids):
                for line in case.line_dr_ids:
                    if company_id:
                        type_id = acc_type.search(cr,uid,[('report_type','=','expense')])
                        if type_id:
                           line_acc=account_obj.search(cr,uid,[('user_type','in',type_id),('company_id','=',company_id),('note','like','Cost of supplies')])
                        if line_acc:
                           line_acc = line_acc[0] 
#                        line_dr_ids.update({'account_id':line_acc})                         
                        line_dr_ids.update({'company_id':company_id,'account_id':line_acc})
                        voucher_line.write(cr,uid,[line.id],line_dr_ids)
                        
                        
                        
#                     cr.execute("update account_voucher_line set company_id")
#                     res.update({'line_dr_ids':line_dr_ids})
            p_ids = journal_obj.search(cr,uid,[('company_id','=',company_id),('type','in',('purchase','purchase_journal'))])
            res.update({'journal_id':p_ids[0]})
            
            
        if company_id and type == 'receipt':
            res['advance_type']='advance'
        if company_id:
            #domain['journal_id'] = [('company_id','=',company_id)]
            dom = {'journal_id':  [('company_id', '=', company_id)]}
            ctx = dict(context, account_period_prefer_normal=True)
            ctx.update({'company_id':company_id})
            periods = self.pool.get('account.period').find(cr, uid, context=ctx)
            res.update({'period_id':periods[0]})
            j_ids = journal_obj.search(cr,uid,[('company_id','=',company_id),('name','like','CANARA')])
            if not j_ids:
                j_ids = journal_obj.search(cr,uid,[('company_id','=',company_id),('name','like','Cash')])
                
            if type == 'payment':
                if j_ids:
                    res['journal_id']=j_ids[0]
                    
            if type == 'sale':    
                js_ids = journal_obj.search(cr,uid,[('company_id','=',company_id),('type','=','sale')])
                if js_ids:
                    res['journal_id']=js_ids[0]
                dom = {'journal_id':  [('company_id', '=', company_id),('type','=','sale')]}
                if partner_id:
                    if 'Logistics' in company.name:
                        account_id = partner.account_rec.id
                    else:
                        account_id = partner.property_account_receivable.id
                    
            if type == 'purchase' and partner_id:
                p_ids = journal_obj.search(cr,uid,[('company_id','=',company_id),('type','in',('purchase','purchase_journal'))])
                dom = {'journal_id':  [('company_id', '=', company_id),('type','in',('purchase','purchase_journal'))]}
                
                if 'Logistics' in company.name :
                    account_id = partner.account_pay.id
                else:
                    account_id = partner.property_account_payable.id
               
                res.update({'account_id':account_id})
                
        return {'value':res, 'domain':dom}
   
#     def kw_onchange_date(self, cr, uid, ids, date, currency_id, payment_rate_currency_id, amount, company_id,partner_id, context=None):
#         """
#         @param date: latest value from user input for field date
#         @param args: other arguments
#         @param context: context arguments, like lang, time zone
#         @return: Returns a dict which contains new values, and context
#         """
#         bill_date=[]
#         warning=''
#         latest_date=False
#         patner_obj=self.pool.get('res.partner')
#         if context is None:
#             context ={}         
#         res=super(account_voucher,self).onchange_date(cr, uid, ids, date=date, currency_id=currency_id, payment_rate_currency_id=payment_rate_currency_id, amount=amount, company_id=company_id,)
#         print partner_id
#         if partner_id:
#            partner=patner_obj.browse(cr,uid,[partner_id])
#            for i in partner:
#                 print i.name
#                 for bill_cycle in i.billing_ids:
#                     print bill_cycle.end_date
#                     bill_date.append(bill_cycle.end_date)
#                     
#                 if bill_date:
#                     bill_date.sort()
#                     bill_date.reverse()
#                     latest_date=bill_date[0]
#                     
#                     if date<latest_date:
#                         warning={
#                                              'title':_('Warning!'), 
#                                                     'message':_('Entered Date "%s" Is Less Than The Last Billing Date "%s",'
#                                                                 ' If You Did Not Change This Date "%s"'
#                                                                 ',The Billing Report Balance Will Be Affected..!')% (date,latest_date,date)
#                                                  
#                                                  }
#                     
#                 
#         #set the period of the voucher
#           
#         return {'value':res ,'warning':warning}
    
    
    
    def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
        res=super(account_voucher,self).writeoff_move_line_get(cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency)
        company = False
        if res:
            cr.execute("select id from res_company where lower(name) like '%logistics%'")
            company=cr.fetchone()
            if company:
                company=company[0]
            partner_id=res['partner_id']
            prtner_obj = self.pool.get('res.partner')
            partner_ids = prtner_obj.search(cr,uid,[('id','=',partner_id)])
            p_id = prtner_obj.browse(cr,uid,partner_ids)
            if p_id:
                p_id=p_id[0]
            
                if p_id.supplier :
                    acc_id = p_id.account_pay and p_id.account_pay.id or False
                else :# for customer 
                    acc_id = p_id.account_rec and p_id.account_rec.id or False
                if context.get('freight',False):
                    res.update({
                             'account_id':acc_id,
                             })
        
        return res
    
    def get_lines(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for case in self.browse(cr, uid, ids):
            
            context.update({'company':case.company_id.id})
            res=self.onchange_partner_id(cr, uid, ids, case.partner_id.id, case.journal_id.id, case.amount, case.currency_id.id, case.type, case.date, context=context)
           
            for i in res['value']['line_cr_ids']:
                self.write(cr, uid,ids,{
                                        'line_cr_ids':[(0,0,i)],
                                        'currency_id': res['value']['currency_id'],
                                        'pre_line ': res['value']['pre_line'],
                                        'account_id':res['value']['account_id'],
                                        'paid_amount_in_company_currency':res['value']['paid_amount_in_company_currency'],
                                        'writeoff_amount':res['value']['writeoff_amount'],
                                        'currency_help_label':res['value']['currency_help_label'],
                                        'payment_rate':res['value']['payment_rate'],
                                        'payment_rate_currency_id':res['value']['payment_rate_currency_id'],
                                        })
            for d in res['value']['line_dr_ids']:
                self.write(cr, uid,ids,{
                                        'line_dr_ids':[(0,0,d)],
                                        'currency_id': res['value']['currency_id'],
                                        'pre_line ': res['value']['pre_line'],
                                        'account_id':res['value']['account_id'],
                                        'paid_amount_in_company_currency':res['value']['paid_amount_in_company_currency'],
                                        'writeoff_amount':res['value']['writeoff_amount'],
                                        'currency_help_label':res['value']['currency_help_label'],
                                        'payment_rate':res['value']['payment_rate'],
                                        'payment_rate_currency_id':res['value']['payment_rate_currency_id'],
                                        })
        return True
    
    
    
    
    
#     def onchange_payment(self,cr, uid, ids,advance_type,partner_id, journal_id, amount, currency_id, type,date,company_id,context=None):
#         bill_date=[]
#         warning=''
#         latest_date=False
#         if context is None:
#             context ={} 
#         res = {} 
#         account_id = False
#         partner_pool = self.pool.get('res.partner')
#         journal_pool = self.pool.get('account.journal')
#         cmp_obj = self.pool.get('res.company')
#         bank_obj = self.pool.get('res.partner.bank')
#         partner_bank=bank_obj.search(cr,uid,[('journal_id','=',journal_id),('company_id','=',company_id)])
#         
#         company = cmp_obj.browse(cr, uid, company_id)
#         j_ids = journal_pool.search(cr,uid,[('company_id','=',company.id)])
# 
# #         for case in self.browse(cr,uid,ids):
# #             if case.advance_type=='rtgs':
# #                 voucher=self.search(cr,uid,[('voucher_id','=',case.id),('advance_type','=','rtgs')])
# #             for i in voucher:
# #                 #ids.append(i)
# #                 self.cancel_voucher(cr, uid, [i],context=None)
# #                 self.action_cancel_draft(cr,uid,[i],context=None)
# #             self.unlink(cr, uid, voucher)         
#         
#         
#         res['bank_id'] = False
#         res['ifsc'] =  False
#         res['bank_name'] = False
#         res['acc_number'] = False
#         res['amount'] = 0 
#         res['bank_address'] =  False
# #        res['address'] =  False       
# #         if journal_id:      
# #                 
# #            vals = self.onchange_journal(cr, uid, ids, journal_id, [], False, partner_id, context)
# #            vals = vals.get('value')
# #            currency_id = vals.get('currency_id', currency_id)
# #            res['currency_id'] = currency_id 
# 
# #             
#         vals = self.recompute_voucher_lines(cr, uid, ids,partner_id, journal_id, amount, currency_id, type, date, context=context)['value']
#         res.update({'pre_line':vals['pre_line'],
#                     'line_dr_ids':[],
#                     'line_cr_ids':[],
#                     })
#         dom = {'journal_id':  [('id', 'in', j_ids)]}
#         if partner_id and journal_id:  
#                      
#             journal = journal_pool.browse(cr, uid, journal_id)
#             partner = partner_pool.browse(cr, uid, partner_id)
#             if journal.type in ('sale','sale_refund'):
#                 if 'Logistics' in company.name :
#                     account_id = partner.account_rec.id
#                 else:
#                     account_id = partner.property_account_receivable.id
#             elif journal.type in ('purchase', 'purchase_refund','expense'):
#                 if 'Logistics' in company.name :
#                     account_id = partner.account_pay.id
#                 else:
#                     account_id = partner.property_account_payable.id
#             else:
#                 account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
#             if partner_bank:
#                 bank=bank_obj.browse(cr,uid,partner_bank[0])
#                 res['address'] = bank.bank_address or False
#             res['account_id'] = account_id
#             
#             res['amount']=0
#             if customer:
#                 res['amount'] = partner.credit or 0
#                 res['advance_type'] = 'advance'
#                 
#                 res['type']='receipt'
#             elif advance_type!='advance':
#                 res['amount'] = partner.debit or 0
#                 
#             for bank_info in partner.bank_ids:
# #                     if company_id== bank_info.company_id.id:
#                     res['acc_number']= bank_info.id or False
# #                         res['bank_id'] = bank_info.bank.id or False
#                     res['ifsc'] = bank_info.bank_bic or False
#                     res['bank_name'] = bank_info.bank_name or False
#                     res['bank_address'] = bank_info.bank_address or False
#                         
#         #set the period of the voucher
#    
#         return {'value':res,'domain':dom}
    
    
    def onchange_partner(self,cr, uid, ids,advance_type,partner_id, journal_id, amount, currency_id, type,date,company_id,customer,context=None):
        bill_date=[]
        warning=''
        latest_date=False
        if context is None:
            context ={} 
        res = {} 
        account_id = False
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        cmp_obj = self.pool.get('res.company')
        bank_obj = self.pool.get('res.partner.bank')
        partner_bank=bank_obj.search(cr,uid,[('journal_id','=',journal_id),('company_id','=',company_id)])
        
        company = cmp_obj.browse(cr, uid, company_id)
        j_ids = journal_pool.search(cr,uid,[('company_id','=',company.id)])

#         for case in self.browse(cr,uid,ids):
#             if case.advance_type=='rtgs':
#                 voucher=self.search(cr,uid,[('voucher_id','=',case.id),('advance_type','=','rtgs')])
#             for i in voucher:
#                 #ids.append(i)
#                 self.cancel_voucher(cr, uid, [i],context=None)
#                 self.action_cancel_draft(cr,uid,[i],context=None)
#             self.unlink(cr, uid, voucher)         
        
        
        res['bank_id'] = False
        res['ifsc'] =  False
        res['bank_name'] = False
        res['acc_number'] = False
        res['amount'] = 0 
        res['bank_address'] =  False
#        res['address'] =  False       
#         if journal_id:      
#                 
#            vals = self.onchange_journal(cr, uid, ids, journal_id, [], False, partner_id, context)
#            vals = vals.get('value')
#            currency_id = vals.get('currency_id', currency_id)
#            res['currency_id'] = currency_id 

#             
#         vals = self.recompute_voucher_lines(cr, uid, ids,partner_id, journal_id, amount, currency_id, type, date, context=context)['value']
        res.update({
#                     'pre_line':vals['pre_line'],
                    'line_dr_ids':[],
                    'line_cr_ids':[],
                    })
        dom = {'journal_id':  [('id', 'in', j_ids)]}
        if partner_id and journal_id:  
                     
            journal = journal_pool.browse(cr, uid, journal_id)
            partner = partner_pool.browse(cr, uid, partner_id)
            if journal.type in ('sale','sale_refund'):
                if 'Logistics' in company.name :
                    account_id = partner.account_rec.id
                else:
                    account_id = partner.property_account_receivable.id
            elif journal.type in ('purchase', 'purchase_refund','expense'):
                if 'Logistics' in company.name :
                    account_id = partner.account_pay.id
                else:
                    account_id = partner.property_account_payable.id
            else:
                account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
            if partner_bank:
                bank=bank_obj.browse(cr,uid,partner_bank[0])
                res['address'] = bank.bank_address or False
            res['account_id'] = account_id
            
            res['amount']=0
            if customer:
                res['amount'] = partner.credit or 0
                res['advance_type'] = 'advance'
                
                res['type']='receipt'
            elif advance_type!='advance':
                res['amount'] = partner.debit or 0
                
            for bank_info in partner.bank_ids:
#                     if company_id== bank_info.company_id.id:
                    res['acc_number']= bank_info.id or False
#                         res['bank_id'] = bank_info.bank.id or False
                    res['ifsc'] = bank_info.bank_bic or False
                    res['bank_name'] = bank_info.bank_name or False
                    res['bank_address'] = bank_info.bank_address or False
                        
        #set the period of the voucher
   
        return {'value':res,'domain':dom}
    
    
    def onchange_acc_num(self, cr, uid, ids, acc_number,context=None):
        res={}
        account_id = False
        partner_bank_pool = self.pool.get('res.partner.bank')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        cmp_obj = self.pool.get('res.company')

        res['bank_id'] = False
        res['ifsc'] =  ''
        res['bank_name'] = ''
        res['amount'] = 0 
        res['bank_address'] =  ''
        res['account_owner'] =  '' 
        if acc_number:
            bank_ids = partner_bank_pool.search(cr,uid,[('id','=',acc_number)])  
                           
            for bank_info in partner_bank_pool.browse(cr,uid,bank_ids):
                print bank_info.partner_id
                res['bank_id'] = bank_info.bank.id or False
                res['ifsc'] = bank_info.bank_bic or ''
                res['bank_name'] = bank_info.bank_name or ''
                res['bank_address'] = bank_info.bank_address or ''
                res['account_owner'] = bank_info.account_owner or bank_info.partner_id.name or ''
                
        return {'value':res}
  
    
    



    def onchange_company(self, cr, uid, ids, partner_id,company_id,journal_id,context=None):
        res={}
        account_id = False
        partner_pool = self.pool.get('res.partner')
        journal_pool =   self.pool.get('account.journal')
        cmp_obj = self.pool.get('res.company')
        company = cmp_obj.browse(cr, uid, company_id)
        j_ids = journal_pool.search(cr,uid,[('company_id','=',company.id)])
        
        dom = {'journal_id':  [('id', 'in', j_ids)]}
        if partner_id and journal_id:  
                     
            journal = journal_pool.browse(cr, uid, journal_id)
            partner = partner_pool.browse(cr, uid, partner_id)
            if journal.type in ('sale','sale_refund'):
                if 'Logistics' in company.name :
                    account_id = partner.account_rec.id
                else:
                    account_id = partner.property_account_receivable.id
            elif journal.type in ('purchase', 'purchase_refund','expense'):
                if 'Logistics' in company.name :
                    account_id = partner.account_pay.id
                else:
                    account_id = partner.property_account_payable.id
            else:
                account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
                    
            res['account_id'] = account_id
        for case in self.browse(cr,uid,ids):
            voucher=self.search(cr,uid,[('voucher_id','=',case.id),('advance_type','=','rtgs')])
            for i in voucher:
                ids.append(i)
        return {'value':res,'domain':dom}
    
    def cancel_voucher_all(self, cr, uid, ids, context=None):
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        stock_obj=self.pool.get('stock.picking.out')
        invoice_obj=self.pool.get('account.invoice')
        move_line_obj=self.pool.get('account.move.line')
        ids=[]
        ref=[]
        del_ord=[]
        del_ids=[]
        del_id=[]
        v_id=[]
        
#to Fetch all ids based on delivery order reference
#         cr.execute(""" 
#                         select 
#                              a.id
#                         from account_voucher a
#                         inner join res_partner rp on rp.id = a.partner_id 
#                         and rp.customer = true
#                         and a.partner_id not in (1429,1447) 
#                         and a.state = 'draft'
#         """)
#         d_ids = [x[0] for x in cr.fetchall()]
#         self.unlink(cr, uid, d_ids)
#         
#         cr.execute(""" 
#                         select 
#                              a.id
#                         from account_voucher a
#                         inner join res_partner rp on rp.id = a.partner_id 
#                         and rp.customer = true
#                         and a.partner_id not in (1429,1447) 
#                         and a.state = 'posted'
#         """)
#         inv_name=[]
#         v_ids=[]
#         del_name=[3400, 3414, 3430, 3438, 3462]
#         for i in del_name:
#             d_name='DC/14-15/KA/0'+str(i)
#             del_ord.append(d_name)
#             del_id=stock_obj.search(cr,uid,[('name','=',d_name)])
#             if del_id:
#                 del_ids.append(del_id[0])
#                 
#             v_id=self.search(cr,uid,[('reference','=',d_name)])
#             if v_id:
#                 v_ids.append(v_id[0])  
#         cr.execute("delete from account_invoice where state='cancel'")  
#         
#         cr.execute("SELECT invoice_id FROM delivery_invoice_rel WHERE del_ord_id IN %s ",(tuple(del_ids),))
#         out_invoice_id = cr.fetchall()
#         cr.execute("SELECT invoice_id FROM supp_delivery_invoice_rel WHERE del_ord_id IN %s ",(tuple(del_ids),))
#         in_invoice_id = cr.fetchall()
#         in_p=0
#         for in_id in out_invoice_id:
#             inv=invoice_obj.browse(cr,uid,in_id[0])
# #             if inv.state=='cancel':
# #                 cr.execute("delete from account_invoice where id="+str(inv.id))
#             if inv.state not in ('draft','cancel'):
#                 inv_name.append(inv.number)
#                 invoice_obj.action_cancel(cr,uid,[in_id[0]],context=None)
#                 invoice_obj.action_cancel_draft(cr,uid,[in_id[0]])
# 
#        
#         for inv_id in in_invoice_id:
#             inv=invoice_obj.browse(cr,uid,inv_id[0])
# #             if inv.state=='cancel':
# #                 cr.execute("delete from account_invoice where id="+str(inv.id))            
#             if inv.state not in ('draft','cancel'):
#                 inv_name.append(inv.number)
#                 invoice_obj.action_cancel(cr,uid,[inv.id],context=None)
#                 invoice_obj.action_cancel_draft(cr,uid,[inv.id])
# #             if inv.state=='cancel':
# #                 invoice_obj.unlink(cr,uid,[inv_id[0]])        
#        
#        
# #         v_ids = [x[0] for x in cr.fetchall()]
#         print "inv_name",inv_name
#         for v in v_ids:
#             self.cancel_voucher(cr, uid, [v],context=None)
#             self.action_cancel_draft(cr,uid,[v],context=None)
#         self.unlink(cr, uid, v_ids)
#         for del_ord in stock_obj.browse(cr,uid,del_ids):
#             if del_ord.state=='freight_paid':
#                 stock_obj.write(cr,uid,del_ord.id,{'state':'done'})
#             cr.execute("update stock_picking state 'done' where id="+)
#                 
#             stock_obj.write(cr,uid,del_ord.id,{'sup_invoice':False,'cust_invoice':False})

        p=1
        d=1
        cr.execute("SELECT id FROM account_voucher WHERE customer_id is not null")
        v_ids = [x[0] for x in cr.fetchall()]
        for case in self.browse(cr,uid,v_ids):
#             if case.type=="payment" and case.reference:
#                 stock_id=stock_obj.search(cr,uid,[('name','=',case.reference)])
            if case.customer_id:  
                if not case.customer_id.pay_freight:
                    for line in case.move_ids:
                        
                        if case.company_id.id==1 and line.account_id.name!='Cash':
                            if line.partner_id.property_account_payable.id!=line.account_id.id and line.credit>0:
                                try:
                                    move_line_obj.write(cr,uid,[line.id],{'partner_id':case.customer_id.representative_id.id})
                                except:
                                    pass 
#                                 self.cancel_voucher(cr, uid, [case.id],context=None)
#                                 self.action_cancel_draft(cr,uid,[case.id],context=None) 
#                                
#                                 p= p+1
#                                 self.proforma_voucher1(cr, uid, [case.id], context=None)
#                                 print p
#                                 
#                                 print case.customer_id.name
                        else:
                            if line.account_id.name!='CashKL':
                                
                                if line.partner_id.account_pay.id!=line.account_id.id and line.credit>0:    
                                    try:
                                        move_line_obj.write(cr,uid,[line.id],{'partner_id':case.customer_id.representative_id.id})  
                                    except:
                                        pass
#                                     self.cancel_voucher(cr, uid, [case.id],context=None)
#                                     self.action_cancel_draft(cr,uid,[case.id],context=None) 
#                                     
#                                     p= p+1
#                                     self.proforma_voucher1(cr, uid, [case.id], context=None)
#                                     print p
#                                                                    
#                                     print case.customer_id.name
           
        return True
    
    
    
    def proforma_voucher1(self, cr, uid, ids, context=None):
        move_line_obj=self.pool.get('account.move.line')
        acc_obj=self.pool.get('account.account')
        stock_obj=self.pool.get('stock.picking.out')
        bill_date=[]
        latest_date=False
        credit_total=0
        debit_total=0
        if context is None:
            context={}            
                    
        for case in self.browse(cr,uid,ids):
            

                            
            cr.execute("select id from res_company where lower(name) like '%logistics%'")
            company=cr.fetchone()
            if company and company[0]==case.company_id.id:
                context.update({'freight':True})
            else:
                context.update({'freight':False})                        

         
        t=self.action_move_line_create(cr, uid, ids, context=context)
        for case in self.browse(cr,uid,ids):
            company=str(case.company_id.id)
            
            if case.type=="payment" and case.customer_id and case.reference:
                stock_id=stock_obj.search(cr,uid,[('name','=',case.reference)])
                for pick in stock_obj.browse(cr,uid,stock_id):
                    if not pick.partner_id.pay_freight:
                        for line in case.move_ids:
                            print case.partner_id.name
                            if line.company_id==1:
                                if line.partner_id.property_account_payable.id!=line.account_id.id and line.credit>0:
                                    move_line_obj.write(cr,uid,[line.id],{'partner_id':pick.partner_id.representative_id.id})
                                    cr.execute("update account_move_line set partner_id=%s where id=%s",(str(pick.partner_id.representative_id.id),str(line.id),)) 
                            else:
                                if line.partner_id.account_pay.id!=line.account_id.id and line.credit>0:        
                                    move_line_obj.write(cr,uid,[line.id],{'partner_id':pick.partner_id.representative_id.id})
                                    cr.execute("update account_move_line set partner_id=%s where id=%s",(str(pick.partner_id.representative_id.id),str(line.id),))            

               
        
        print 'ids',ids
        return True
    
    def cancel_voucher(self, cr, uid, ids, context=None):
        voucher=[]
        for case in self.browse(cr,uid,ids):
            voucher=self.search(cr,uid,[('voucher_id','=',case.id),('advance_type','=','rtgs')])
        for i in voucher:
            ids.append(i) 
        res=super(account_voucher,self).cancel_voucher(cr, uid, ids)
        return res 
    
    def action_cancel_draft(self, cr, uid, ids, context=None):
        voucher=[]
        for case in self.browse(cr,uid,ids):
            voucher=self.search(cr,uid,[('voucher_id','=',case.id),('advance_type','=','rtgs')])
        for i in voucher:
            ids.append(i) 
        res=super(account_voucher,self).action_cancel_draft(cr, uid, ids)
        return res
    
    def update_partner(self, cr, uid, ids, context=None): 
        voucher_cust=[]
        inv_prod=[]
        prods=[]
        prod_obj=self.pool.get('product.template')
        cr.execute("select id from account_voucher where customer_id is null")
        cust=cr.fetchall()
        for i in cust:
            voucher_cust.append(i[0])
        stock_obj=self.pool.get('stock.picking.out')
        ac_inv_obj=self.pool.get('account.invoice')
        for case in self.browse(cr, uid, voucher_cust):
            if case.reference:
                stock_id=stock_obj.search(cr,uid,[('name','=',case.reference)])
                stock_ids=stock_obj.browse(cr,uid,stock_id)
                for i in stock_ids:
                   cr.execute("update account_voucher set customer_id=%s where id=%s",(i.partner_id.id,i.id)) 
        
        cr.execute("select id from account_invoice where product_id is null or company_id=3")
        prod=cr.fetchall()         
        for j in prod:
            inv_prod.append(j[0])
            cr.execute("select product_id from account_invoice_line where invoice_id=%s",(j[0],))
            product=cr.fetchone()
            if product:
                product=product[0]
#                 cr.execute("update account_invoice set product_id=%s where id=%s",(product,j[0],))
                prods=prod_obj.search(cr,uid,[('id','=',product)])
                
                if not prods:
                    cr.execute("update account_invoice set product_id=%s where id=%s",(product,j[0],)) 
                else:
                    cr.execute("select del_ord_id from delivery_invoice_rel where invoice_id=%s",(j[0],))
                    del_id=cr.fetchone()
                    if del_id:
                        del_id=del_id[0]
                    stock_ids=stock_obj.browse(cr,uid,[del_id])
                    for i in stock_ids:
                        for temp in i.move_lines:
                            cr.execute("update account_invoice set product_id=%s where id=%s",(temp.product_id.id,j[0],))
                            
        return True
    
    
    def update_period(self, cr, uid, ids, context=None): 
        voucher_ids=[]
        inv_prod=[]
        prods=[]
        prod_obj=self.pool.get('product.template')
        today=False
        cr.execute("select id from account_voucher where reference is not null")
        cust=cr.fetchall()
        for i in cust:
            voucher_ids.append(i[0])
        print 'voucher_ids',len(voucher_ids)
        for case in self.browse(cr,uid,voucher_ids):
            today=case.date
            cr.execute("select id from account_period where company_id='"+ str(case.company_id.id) +"'and date_start <= '" + today + "' and date_stop >='" + today + "'")
            period = cr.fetchone()   
            if period:
                period_id=period[0]
        
            cr.execute("update account_voucher set period_id=%s where id=%s",(period_id,case.id,))
                            
        return True
    
    
    def update_all(self, cr, uid, ids, context=None): 
        self.cancel_voucher_all(cr, uid, ids, context)
#         self.update_partner(cr, uid, ids, context)
#         self.update_period(cr, uid, ids, context)
        return True
    #overridden
    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """
        Returns a dict that contains new values and context
 
        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone
 
        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False
 
        if context is None:
            context = {}
        context_multi_currency = context.copy()
         
        #added new line for company
        company = context.get('company',False)
        if ids:
            voucher = self.browse(cr, uid, ids[0])
            company = voucher.company_id.id
#        company = False #voucher.company_id.id
        
        advances = {}
        temp = [] 
        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')
 
        #set default values
        default = {
            'value': {'line_dr_ids': [] ,'line_cr_ids': [] ,'pre_line': False,},
        }
 
        #drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)
 
        if not partner_id or not journal_id:
            return default
 
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id
 
        total_credit = 0.0
        total_debit = 0.0
        account_type = 'receivable'
        if ttype == 'payment':
            account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            account_type = 'receivable'
 
        if not context.get('move_line_ids', False):
            #based on company_id Retrieving the Records
            if company:
                ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id),('company_id','=',company)], context=context)
            else:
                ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_line_found = False
 
        #order the lines by most old first
        ids.reverse()
        temp_ids = ids
        print "ids",ids,len(ids)
        #for grouping the ids based on dc_no -for adjusting the freight entries
        move_ids = move_line_pool.browse(cr, uid, ids, context=context)
        for ln in move_line_pool.browse(cr, uid, ids, context=context):
            if ln.invoice:
                for pick in ln.invoice.supp_delivery_orders_ids:
                    for mv in move_ids:
                        if mv.ref == pick.name:
                            temp.append(mv.id)
                            if mv.id in temp_ids:
                                temp_ids.remove(mv.id)
        
        del ids
        
        ids = list(set(temp)) + list(set(temp_ids)) #to remove duplicate entries
        print "ids",ids,len(ids)
        #print "len_ids",ids
                
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)
 
        #compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue
 
            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_line_found = line.id
                    break
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if line.amount_residual == price:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_line_found = line.id
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_line_found = line.id
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0
 
        #voucher line creation
        for line in account_move_lines:
 
            if _remove_noise_in_o2m():
                continue
 
            if line.currency_id and currency_id == line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)
            else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency)
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rs = {
                'name':line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': amount_original,
                'amount': (move_line_found == line.id) and min(abs(price), amount_unreconciled) or 0.0,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
            if not move_line_found:
                if currency_id == line_currency_id:
                    if line.credit:
                        amount = min(amount_unreconciled, abs(total_debit))
                        rs['amount'] = amount_original #instead of amount field , Added the amount_original field
                        total_debit -= amount
                    else:
                        amount = min(amount_unreconciled, abs(total_credit))
                        rs['amount'] = amount
                        total_credit -= amount
 
            if rs['amount_unreconciled'] == rs['amount']:
                rs['reconcile'] = True
 
            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)
 
            if ttype == 'payment' and len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif ttype == 'receipt' and len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
 
        return default
   
       #Post Method For Miscellaneous Journal
    
    def button_post(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('account.move')
        journal_obj = self.pool.get('account.journal')
        period_obj=self.pool.get('account.period')
        
        data = move_obj.default_get(cr, uid, ['period_id'], context)
        period_id=data.get('period_id', False)
#         today = datetime.today() 
        today = time.strftime('%Y-%m-%d')
        cr.execute("select code from account_fiscalyear where date_start <= '" + str(today) + "' and date_stop >='" + str(today) + "'")
        code = cr.fetchone()
        year = code and code[0] or ''
        
        payable_id=False
        if not year:
            raise osv.except_osv(_('Warning!'), _('Fiscal Year does not exist'))
        
        
        
        for case in self.browse(cr, uid, ids):
            format='MISC/'
            company_id=int(case.company_id.id)

#             period_id = journal_obj.search(cr, uid, [('company_id', '=', case.company_id.id), ('date_start','<=', today),('date_stop','>=', today)], limit=1)   
            cr.execute("select id from account_period where company_id='"+ str(company_id) +"'and date_start <= '" + today + "' and date_stop >='" + today + "'")
            p_ids = cr.fetchone()   
            if p_ids:
                period_id=p_ids[0]           
            Num = ''
            journal_ids = journal_obj.search(cr, uid, [('company_id', '=', case.company_id.id), ('type','=', 'general'),('name','like','Miscellaneous')], limit=1)

            if case.partner_id.customer:
                if company_id>1:
                    payable_id = case.partner_id.account_rec.id
                    format=format+'KL/'                    
                else:
                    payable_id = case.partner_id.property_account_receivable.id  
                    format=format+'KS/'
                    
            if case.partner_id.supplier:                    
                if case.company_id.id>1:
                        payable_id = case.partner_id.account_pay.id
                        format=format+'KL/'
                else:
                        format=format+'KS/'
                        payable_id = case.partner_id.property_account_payable.id            
#             payable_id = case.partner_id.property_account_payable.id
                 
                          
            if journal_ids:
                for journal in journal_obj.browse(cr,uid,journal_ids):
                    if case.type == 'sale' or case.type == 'receipt':
                        miscellaneous_acc=journal.default_debit_account_id.id
                    if case.type == 'payment'  or case.type == 'purchase':
                        miscellaneous_acc=journal.default_credit_account_id.id
          

            
            format = format + year +'/'
         
            cr.execute("select number from account_voucher where number like '" + format + "'|| '%' order by to_number(substr(number,(length('" + format + "')+1)),'99999') desc limit 1")
            prev_format = cr.fetchone()
            
            
            if not prev_format:
                number = format+ '00001'
            else:
                
                auto_gen = prev_format[0][-5:]
                number = format + str(int(auto_gen) + 1).zfill(5)

                     
            line = {
                   'name'   : number, 
                   'credit' : (case.type == 'sale' or case.type == 'receipt')  and case.amount or 0,
                   'debit'  : (case.type == 'payment'  or case.type == 'purchase') and case.amount or 0,
                   
                   'partner_id' : case.partner_id.id,
                   'account_id' : payable_id
                   }
             
            adjust_line = {
                    'name'   : number,
                    'credit' : (case.type == 'payment'  or case.type == 'purchase' )and case.amount or 0,
                    'debit'  : (case.type == 'sale' or case.type == 'receipt')  and case.amount or 0,
                    
                    'partner_id' : case.partner_id.id,
                    'account_id' : miscellaneous_acc
                   }
            
            move = {
                'ref': number or '/',
                'line_id': [[0, False, line], [0, False, adjust_line]],
                'journal_id': journal_ids and journal_ids[0] or False,
                'date': case.date,
                'narration' : case.narration,
                'company_id': case.company_id.id,
                'period_id' : period_id
            }
             
              
            move_id = move_obj.create(cr, uid, move)
            move_obj.post(cr, uid, [move_id], context={})
            self.write(cr, uid, ids, {'state':'posted', 'move_id': move_id, 'name': number,'number':number})
        return True    
    
    
    
    
    #overridden to update the context values for freight
    def proforma_voucher(self, cr, uid, ids, context=None):
        move_line_obj=self.pool.get('account.move.line')
        acc_obj=self.pool.get('account.account')
        stock_obj=self.pool.get('stock.picking.out')
        bank_obj=self.pool.get('res.partner.bank')
        bill_date=[]
        latest_date=False
        credit_total=0
        debit_total=0
        c=False
        c1=False
        if context is None:
            context={}
        schedular = context.get('schedular',False)
        freight_advance = context.get('freight_advance',False)
        dc_reference = context.get('dc_reference',False)
        freight_account=0
        refund = context.get('refund',False)
        refereance = ''
        cr.execute("select id from res_partner where lower(name) like 'kingswood supp%'")
        paying_agent=[x[0] for x in cr.fetchall()]     
        if not refund:  
            for av in self.browse(cr,uid,ids):
                            
                voucher_id=self.search(cr,uid,[('voucher_id','=',av.id),('advance_type','=','rtgs')])                        
                for i in self.browse(cr,uid,voucher_id):
                    if i.advance_type=='rtgs':
                        ids.append(i.id)
                    
        for case in self.browse(cr,uid,ids):
            customer=context.get('customer',case.customer)
            freight_account=acc_obj.search(cr, uid, [('name','like','Freight'),('company_id','=',case.company_id.id)])
            if freight_account:
                freight_account=freight_account[0] 
                            
            cr.execute("select id from res_company where lower(name) like '%logistics%'")
            company=cr.fetchone()
            if company and company[0]==case.company_id.id:
                context.update({'freight':True})
            else:
                context.update({'freight':False})
            
            if 'freight_paid' not in context:
                    
                if case.type in ('payment','purchase') and not case.back_date:
                   if not case.back_date:
                       date=case.date 
                       if case.partner_id:
                           for bill_cycle in case.partner_id.billing_ids:
                               bill_date.append(bill_cycle.end_date)
                                    
                           if bill_date:
                                bill_date.sort()    
                                bill_date.reverse()
                                latest_date=bill_date[0]
                                
                                if date<latest_date:
                                    if schedular:
                                        self.write(cr,uid,[case.id],{'back_date':True})
                                    else:
                                        raise osv.except_osv(_('Warning!'), _('Date Entered "%s" Is Less Than The Last Billing Date "%s" Change The Date Otherwise Billing Report Balance Will Be Affected..! If You Still Want To Continue With Same Date Check The "Back Date Entry Field" and Click on Validate')% (date,latest_date))
            
            if not case.account_id:            
                if case.type in ('sale','sale_refund'):
                    if 'Logistics' in case.company_id.name :
                        account_id = case.partner_id.account_rec.id
                    else:
                        account_id = case.partner_id.property_account_receivable.id
                elif case.type in ('purchase', 'purchase_refund','expense'):
                    if 'Logistics' in case.company_id.name :
                        account_id = case.partner_id.account_pay.id
                    else:
                        account_id = case.partner_id.property_account_payable.id
                else:
                    account_id = case.journal_id.default_credit_account_id.id or case.journal_id.default_debit_account_id.id                            
#                             raise osv.except_osv(_('Warning!'), _('Invoice Date "%s" Is Less Than The Last Billing Date "%s",'
#                                                             ' If You Did Not Change This Date "%s"'
#                                                             ',The Billing Report Balance Will Be Affected..!'
#                                                             ' Mark Back Date Entry')% (date,latest_date,date))
#             if case.type=='payment'and not case.advance:
#                 if case.line_dr_ids:
#                     for debit_line in case.line_dr_ids:
#                         if debit_line.type=='dr':
#                             debit_total += debit_line.amount
#                             if debit_line.amount_original != debit_line.amount:
#                                 raise osv.except_osv(_('Warning!'), _('You Cannot Partially Reconcile, Delete The line ,Journal Item "%s" or Pay The Advance and Adjust')% (debit_line.name))
#                 if case.line_cr_ids:
#                     for credit_line in case.line_cr_ids:
#                         if credit_line.type=='cr':
#                             credit_total += credit_line.amount
#                  
#                 if debit_total!=credit_total:
#                     raise osv.except_osv(_('Warning!'), _("Credit and Debit Total Amount Must Be Same"))
        
         
        t=self.action_move_line_create(cr, uid, ids, context=context)
        
        if not refund:
            for case in self.browse(cr,uid,ids):
                company=str(case.company_id.id)
#                 if case.charges and case.advance_type=='rtgs':
#                     cr.execute("select id from account_account where lower(name) like '%bank charges%' and company_id="+ company)
#                     acc=cr.fetchone()                
#                     for j in case.move_ids:
#         #                 acc_id=acc_obj.search(cr,uid,[('company_id','=',case.company_id.id),('name','like','bank')])
#                             if 'Logistics' in case.company_id.name :
#                                 if not acc:
#                                    if j.account_id == case.partner_id.account_pay.id:
#                                     move_line_obj.write(cr,uid,[j.id],{'debit':0,'credit':case.amount}) 
#                                 if acc: 
#                                     if j.account_id.id == acc[0]:
#                                         move_line_obj.write(cr,uid,[j.id],{'credit':0,'debit':case.amount})
#                                     else:
#                                         move_line_obj.write(cr,uid,[j.id],{'debit':0,'credit':case.amount})                                   
#                             else:
#                                 if not acc:
#                                     if j.account_id == case.partner_id.property_account_payable.id:
#                                         move_line_obj.write(cr,uid,[j.id],{'debit':0,'credit':case.amount})
#                                 if acc: 
#                                     if j.account_id.id == acc[0]:
#                                         move_line_obj.write(cr,uid,[j.id],{'credit':0,'debit':case.amount})                              
#                                     else:
#                                         move_line_obj.write(cr,uid,[j.id],{'debit':0,'credit':case.amount})
                
                freight_advance=context.get('freight_advance',False)
                                    
                if case.type=="payment" and case.customer_id and case.reference:
                    stock_id=stock_obj.search(cr,uid,[('name','=',case.reference)])
                                     
                    for pick in stock_obj.browse(cr,uid,stock_id):
                        if not pick.partner_id.pay_freight:
                            for line in case.move_ids:
                                if freight_advance or (pick.transporter_id and pick.paying_agent_id.id in paying_agent):
                                    if line.credit>0:
                                        ac=acc_obj.search(cr, uid, [('name','like','Cash'),('company_id','=',case.company_id.id)])
                                        if ac and pick.transporter_id:
                                            if pick.transporter_id.id==case.partner_id.id:
                                                cr.execute("update account_move_line set partner_id=%s where id=%s",(str(pick.paying_agent_id.id),str(line.id),))                                    
                                                cr.execute("update account_move_line set account_id=%s where id=%s",(str(ac[0]),str(line.id),))
                                
                                else:   
                                    if line.account_id.id != freight_account:
                                        print case.partner_id.name
                                        if line.company_id==1:
                                            if line.partner_id.property_account_payable.id!=line.account_id.id and line.credit>0:
                                                move_line_obj.write(cr,uid,[line.id],{'partner_id':pick.partner_id.representative_id.id})
                                                cr.execute("update account_move_line set partner_id=%s where id=%s",(str(pick.partner_id.representative_id.id),str(line.id),)) 
                                        else:
                                            if line.partner_id.account_pay.id!=line.account_id.id and line.credit>0:        
                                                move_line_obj.write(cr,uid,[line.id],{'partner_id':pick.partner_id.representative_id.id})
                                                cr.execute("update account_move_line set partner_id=%s where id=%s",(str(pick.partner_id.representative_id.id),str(line.id),))
                if case.advance_type=='rtgs':
                    banks=[]
                    account_owner=''
                    banks=bank_obj.search(cr,uid,[('partner_id','=',case.partner_id.id)])
                    for bank_info in bank_obj.browse(cr,uid,banks):
                        account_owner=bank_info.account_owner or bank_info.partner_id.name or ''
                        
                    self.write(cr, uid, ids, {'account_owner':account_owner}, context)            
#                 v_id=self.search(cr,uid,[('voucher_id','=',case.id),('advance_type','<>','rtgs')])        
#                 self.cancel_voucher(cr, uid, v_id,context=None)
#                 self.action_cancel_draft(cr,uid,v_id,context=None)
#                 self.unlink(cr,uid,v_id)
        
        if customer:
            for case in self.browse(cr,uid,ids):
                bank_charge=case.bank_charge   
                reject=case.reject       
                prod_sale=case.prod_sale  
                total=case.amount                  
                 
                if not bank_charge: bank_charge=0
                if not reject: reject=0
                if not prod_sale: prod_sale=0
                if bank_charge or reject or prod_sale:            
                    ac_total=bank_charge+reject+prod_sale 
                    if ac_total==total:
                        for line in case.move_ids:             
                            if line.debit>0:
                                if line.debit==total:
                                    
                                    cr.execute("select id from account_account where lower(name) like '%product sale%' and company_id="+(str(line.company_id.id)))
                                    prod_sale_account_id=cr.fetchone()  
                                    if (reject and prod_sale) or (bank_charge and prod_sale):
                                                                        
                                        move_line_obj.write(cr,uid,[line.id],{'debit':prod_sale})
                                                                            
                                    cr.execute("select id from account_account where lower(name) like '%bank charges%' and company_id="+(str(line.company_id.id)))
                                    account_id=cr.fetchone()    
                                    if (bank_charge and prod_sale) or (bank_charge and reject): 
                                        if account_id and bank_charge:  
                                            c1=move_line_obj.copy(cr,uid,line.id,{})                               
                                            move_line_obj.write(cr,uid,[c1],{'account_id':account_id[0],'debit':bank_charge})
                                        
                                            
                                        
                                    cr.execute("select id from account_account where lower(name) like 'rejection' and company_id="+(str(line.company_id.id)))
                                    reject_account_id=cr.fetchone()
                                    if (reject and prod_sale) or (bank_charge and reject):
                                        if reject_account_id:  
                                            c=move_line_obj.copy(cr,uid,line.id,{})                                      
                                            move_line_obj.write(cr,uid,[c],{'debit':reject})
                                                                                    
        if dc_reference and case.reference:
            reference = 'Freight Advance ' + case.reference
            self.write(cr, uid, ids, {'reference':reference}, context)
        print 'ids',ids
        return True


    def onchange_bank(self, cr, uid, ids, partner_id=False, bank = False, context=None):
        res ={} 
        warning=''
        res['partner_id']=partner_id
        res['bank']= bank
        acc_obj=self.pool.get('account.journal')
        
        if bank:
            bank_id=acc_obj.browse(cr,uid,bank)

            res['account_id'] = bank_id.default_debit_account_id.id
  
                          
#         if partner_id != False:
#             res['partner_id']=False
#             res['bank']= False
#             
#             warning={
#                                          'title':_('Warning!'), 
#                                                 'message':_('Select Either Bank or Partner....! You Cannot Select Both.')
#                                              }
            
            
                
        
        return{'value':res ,'warning':warning}


    def onchange_journal_voucher(self, cr, uid, ids, price=0.0, partner_id=False, journal_id=False, ttype=False, company_id=False, context=None):
        account_id=False    
#         res=super(account_voucher,self).onchange_journal_voucher(cr,uid,ids,line_ids=line_ids, tax_id=tax_id, price=price, partner_id=partner_id, journal_id=journal_id, ttype=ttype, company_id=company_id,context=context)
        res={}
        partner_obj=self.pool.get('res.partner')
        if partner_id:
            partner=partner_obj.browse(cr,uid,partner_id)
            if partner.supplier:
                if company_id>1:
                        account_id = partner.account_pay.id
                else:
                        account_id = partner.property_account_payable.id
                        
            if partner.customer:
                if company_id>1:
                    account_id = partner.account_rec.id
                else:
                    account_id = partner.property_account_receivable.id
                    
        res['account_id']=account_id
            
        line=[]
        dom=''
        if company_id:
            cr.execute("select id from account_account where lower(name) like 'miscellaneous%' and company_id="+(str(company_id)))
            acc_no=cr.fetchone()
            if acc_no:
                acc_no=acc_no[0]
#                 line.append({'account_id':acc_no})
#                 
            res['line_ids']=line
            dom={'company_id':company_id}
            
        return {'value':res,'domain':dom}
    
    def onchange_mis_com(self, cr, uid, ids, journal_id,company_id,context=None):
        journal_pool=self.pool.get('account.journal')
        account_pool=self.pool.get('account.account')
        today = time.strftime('%Y-%m-%d')
        res={}
        print "res",res
#         acc_no=False
#         voucher_no=False
        line=[]
        bank_id=False
        dom=''
        cr.execute("select id from res_company where lower(name) like '%logistic%'")
        company=cr.fetchone()
        res['mis_journal']=True
        if company:
            company=company[0]
        if company_id:
            cr.execute("select id from account_period where company_id='"+ str(company_id) +"'and date_start <= '" + today + "' and date_stop >='" + today + "'")
            p_ids = cr.fetchone()   
            if p_ids:
                p_ids=p_ids[0]
                res['period_id']=p_ids
            cr.execute("select id from account_account_type where lower(name) like 'bank%'")
            bank_id=cr.fetchone()
            if bank_id:
                bank_id=bank_id[0]
            dom = {'journal_id':  [('company_id','=', company_id)],'bank':[('type','=','bank'),('company_id','=',company_id)]}
            
            cr.execute("select id from account_account where lower(name) like 'miscellaneous%' and company_id="+(str(company_id)))
            acc_no=cr.fetchall()
            cr.execute("select id from account_journal where lower(name) like 'miscellaneous%' and company_id="+(str(company_id)))
            journal_no=cr.fetchone()            
            if acc_no:
                acc_no=acc_no[0]
#                 line.append({'account_id':acc_no})
#                 res['account_id']=acc_no
            res['line_ids']=line
            if journal_no:
                journal_no=journal_no[0]
                res['journal_id']=journal_no
                
        return {'value':res,'domain':dom} 
    
    #overidden
    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        bank_obj = self.pool.get('res.partner.bank')
        partner_bank=bank_obj.search(cr,uid,[('journal_id','=',journal_id),('company_id','=',company_id)])        
        if context is None:
            context = {}
        if not journal_id:
            return False
        journal_pool = self.pool.get('account.journal')
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        account_id = journal.default_credit_account_id or journal.default_debit_account_id
        tax_id = False
        if account_id and account_id.tax_ids:
            tax_id = account_id.tax_ids[0].id

        vals = {'value':{} }
        vals['value'].update({'account_id':account_id.id})
        if ttype in ('sale', 'purchase'):
            if amount>0:
                print "amount",amount
                vals = self.onchange_price(cr, uid, ids, line_ids, tax_id, partner_id, context)
                vals['value'].update({'tax_id':tax_id,'amount': amount})
        currency_id = False
        if journal.currency:
            currency_id = journal.currency.id
        else:
            currency_id = journal.company_id.currency_id.id
        vals['value'].update({'currency_id': currency_id})
        #in case we want to register the payment directly from an invoice, it's confusing to allow to switch the journal 
        #without seeing that the amount is expressed in the journal currency, and not in the invoice currency. So to avoid
        #this common mistake, we simply reset the amount to 0 if the currency is not the invoice currency.
        if context.get('payment_expected_currency') and currency_id != context.get('payment_expected_currency'):
            vals['value']['amount'] = 0
            amount = 0
        vals['value']['address'] =  False     
        if partner_bank:
            bank=bank_obj.browse(cr,uid,partner_bank[0])
            vals['value']['address'] = bank.bank_address or False        
#         res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context)
#         for key in res.keys():
#             vals[key].update(res[key])
        return vals

#inheriteed
    def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
        if context is None:
            context = {}
        context.update({'company':company_id})
        return super(account_voucher,self).onchange_amount(cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context)
    
    #to change company_id for voucher
    def change_company(self, cr, uid, ids, context = None):
        journal_obj = self.pool.get('account.journal')
        acc_obj=self.pool.get('account.account')
        if context is None: context = {}
        ctx = {}
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company=cr.fetchone()
        if company:
            company=company[0]
        j_ids = journal_obj.search(cr, uid, [('name','like','Cash'),('company_id','=',company)])
        j_id = journal_obj.browse(cr, uid, j_ids[0])
        ctx = dict(context, account_period_prefer_normal=True)
        ctx.update({'company_id':company})
        p_ids= self.pool.get('account.period').find(cr, uid, context=ctx)
        
        freight_journal=journal_obj.search(cr, uid, [('name','like','Freight'),('company_id','=',company)])
        if freight_journal:
            freight_journal=freight_journal[0]     
        else:
            raise osv.except_osv(_('Warning'),_('Freight Journal Not Found, Cannot Pay Freight')) 
        
        freight_account=acc_obj.search(cr, uid, [('name','like','Freight'),('company_id','=',company)])
        if freight_account:
            freight_account=freight_account[0]  
        
        #SESH, CWWB, TN 
        cr.execute(""" 
                    select 
                        id
                        from account_voucher 
                        where company_id = 1
                        and reference in 
                        (select 
                          name
                        from stock_picking 
                        where partner_id = 1442 and product_id = 75
                        and state_id = 58
                        and gen_freight = true
                        and state='freight_paid')""")
        v_ids = [x[0] for x in cr.fetchall()]
        print len(v_ids)
        for case in self.browse(cr,uid, ids):
            voucher_vals = {  
                              'account_id'       : freight_account,
                              'journal_id'       : freight_journal,
                              'type'             : 'payment',
                              'company_id'       : company,
                              'period_id'        : p_ids and p_ids[0] or False
                            }
        self.write(cr, uid, v_ids, voucher_vals, context = context)
        
        #TNPL, CWWB.EHWB,TN
        

        cr.execute("""
                select 
                    id, state
                    from account_voucher
                    where 
                    company_id = 1  
                    and reference in
                        (     select 
                            name 
                        from stock_picking 
                        where partner_id = 1443
                        and state_id = 58
                        and product_id in (76,75)
                        and gen_freight = true )
        """)
        tv_ids = [x[0] for x in cr.fetchall()]
        print len(tv_ids)
        for case in self.browse(cr,uid, ids):
            voucher_vals = {  
                              'account_id'       : freight_account,
                              'journal_id'       : freight_journal,
                              'type'             : 'payment',
                              'company_id'       : company,
                              'period_id'        : p_ids and p_ids[0] or False
                            }
        self.write(cr, uid, tv_ids, voucher_vals, context = context)
            
        return True
    
    
    
    def create(self,cr,uid,vals,context=None):
      bank_type_obj = self.pool.get('res.partner.bank')
      fiscal_obj=self.pool.get('account.fiscalyear')
      today = time.strftime('%Y-%m-%d')
      account_owner=''
      vals1={}
      customer=context.get('customer',False)
      if customer:
          vals.update({'advance_type':'advance','type':"receipt",'customer':True})
         
      vals.update({'customer':customer})
      if 'account_id' in vals:
          acc_id=vals['account_id']
      else:
          acc_id=False
      if context and 'advance' in context:
          if context['advance']:
              vals.update({
                           'advance':True,
                           
                           })
              if 'amount' in vals:
                 if vals['amount']<1:
                    raise osv.except_osv(_('Warning!'), _("Amount Should Not Be Zero or Less Than Zero"))
      
      if context.get('type','')=='mis_journal':
          vals.update({'mis_journal':True})

      if vals.get('advance_type','')=='rtgs' or vals.get('customer',False):
        if 'partner_id' in vals:
          if vals['partner_id']:
              banks=[]
              account_owner=''
              banks=bank_type_obj.search(cr,uid,[('partner_id','=',vals['partner_id'])])
              for bank_info in bank_type_obj.browse(cr,uid,banks):
                  account_owner=bank_info.account_owner or bank_info.partner_id.name or ''
                  account_owner=str(account_owner)
                     
              vals.update({'account_owner':account_owner})         
          
          
                
      res=super(account_voucher,self).create(cr, uid, vals, context)
                
      if 'advance_type' in vals:
          if vals['advance_type']!='advance' or vals.get('customer',False):
              if 'acc_number' in vals:
                  if vals['acc_number']:
                      account_id=bank_type_obj.browse(cr,uid,[vals['acc_number']])
                      for a_name in account_id:
                        if vals['advance_type']=='rtgs' or vals.get('customer',False):
                            account_owner=a_name.account_owner or a_name.partner_id.name or ''
                        else:
                            account_owner=a_name.account_owner
                            
                        vals.update({'account_owner':a_name.account_owner})
          
          if 'charges' in vals:            
              if not vals['charges']:
                  company=str(vals['company_id'])
                  print company
                  cr.execute("select id from account_account where lower(name) like '%bank charges%' and company_id="+ company)
                  acc=cr.fetchone()
                  
                  amount=vals['amount']
                  if vals['advance_type']=='rtgs':
                    vals1=vals.copy()
                    if vals['amount'] <= 500000.00:
                        vals1['amount']=50.00
                    if vals['amount'] > 500000.00:
                        vals1['amount']=100.00
                    if acc:
                        vals1['account_id']=acc[0]
                        vals1['debit']=vals1['amount']
                    vals1.update({'reference':'Bank Comission/charges'})
                    context.update({'charges':True})
                    vals1.update({'charges':True,'voucher_id':res})
                    if vals['type']=='payment':
                        vals1['type']='payment'
                        super(account_voucher,self).create(cr, uid, vals1, context)
                    vals['amount']=amount  
#       
      if 'advance_type' in vals:
          if vals['advance_type']=='rtgs':
             vals.update({'account_owner':account_owner})  
      print "account_owner",account_owner      
      vals.update({'charges':False})
      vals.update({'charges':False})
      vals['account_id']=acc_id
      print vals
      print "vals1",vals1

      return res 


        
      
    def write(self,cr,uid,ids,vals,context=None):
      bank_type_obj = self.pool.get('res.partner.bank')
      advance_type=''
      if not context:
          context={}
      amount=0.00
      vals1={}
      voucher=[]
      acc_name=''
      account_id=False
      customer=context.get('customer',False)
      
      if context:
          if 'advance' in context:
              if context['advance']:
                  vals.update({
                               'advance':True,
                               
                               })
                  if 'amount' in vals:
                     if vals['amount']<1:
                         raise osv.except_osv(_('Warning!'), _("Amount Should Not Be Zero or Less Than Zero"))
                     
      
          
      for case in self.browse(cr,uid,ids):
          if 'back_date' in vals:
              voucher_id = self.search(cr,uid,[('voucher_id','=',case.id)])
              for voucher in voucher_id:
                  cr.execute("update account_voucher set back_date = "+str(vals['back_date'])+" where id = "+str(voucher))
              if case.voucher_id:
                  voucher_id = self.search(cr,uid,[('id','=',case.voucher_id.id)])
              for voucher in voucher_id:
                  cr.execute("update account_voucher set back_date = "+str(vals['back_date'])+" where id = "+str(voucher))
                               
          if customer:
             bank_charge=vals.get('bank_charge',case.bank_charge)   
             reject=vals.get('reject',case.reject)       
             prod_sale=vals.get('prod_sale',case.prod_sale)  
             total=vals.get('amount',case.amount)       
             if not bank_charge: bank_charge=0
             if not reject: reject=0
             if not prod_sale: prod_sale=0
             if bank_charge or reject or prod_sale:
                 ac_total=bank_charge+reject+prod_sale
                 if ac_total!=total:
                   raise osv.except_osv(_('Warning!'), _("Bank Charges+Rejected+Product Sale Should Be same as Total"))    
          if 'acc_number' in vals or case.acc_number:
#           acc_name=case.acc_number.account_owner
              acc_no=case.acc_number.id or False
              if 'advance_type' in vals:
                  if vals['advance_type'] !='advance' or case.advance_type!='advance':
                      if 'acc_number' in vals:
                          if vals['acc_number']:
                              acc_no=vals['acc_number']
              if acc_no:                
                  account_id=bank_type_obj.browse(cr,uid,acc_no)
              if account_id and account_id>0:
                  acc_name=account_id.account_owner
          if 'account_owner' not in vals:                  
              vals.update({'account_owner':acc_name})
          voucher=self.search(cr,uid,[('voucher_id','=',case.id),('advance_type','=','rtgs')])
          if 'advance_type' in vals:
              if vals['advance_type'] != 'rtgs':
                  for vcr in voucher:
                        self.cancel_voucher(cr, uid, [vcr],context=None)
                        self.action_cancel_draft(cr,uid,[vcr],context=None)
                  self.unlink(cr, uid, voucher)
                     
          journal=case.journal_id.id
          if 'journal_id' in vals:
              journal=vals['journal_id']
            

          acc_id=case.account_id.id
          company=str(case.company_id.id)
          cr.execute("select id from account_account where lower(name) like '%bank charges%' and company_id="+ company)
          v_acc=cr.fetchone()
          if v_acc:
              v_acc=v_acc[0]
          else:
              v_acc=case.account_id.id              
          vals1.update({'partner_id':case.partner_id.id,
                        'company_id':case.company_id.id,
                        'journal_id':case.journal_id.id,
                        'period_id':case.period_id.id,
                        'advance_type':case.advance_type,
                        'account_id':v_acc,
                        'reference':'Bank Comission/charges',
                        
              })


          amount=case.amount
          if 'account_id' in vals:
              acc_id=vals1['account_id'] or case.account_id.id
          if not case.charges:
            if 'advance_type' in vals:
                if vals['advance_type']=='rtgs':
                    advance_type=vals['advance_type']
                  
            if case.advance_type=='rtgs'or advance_type=='rtgs':
                if 'amount' in vals:
                    amount=vals['amount']
                if amount <= 500000.00:
                    vals1.update({'amount':50.00
                                  })
                    rs=50.00
                if amount > 500000.00:
                    vals1.update({'amount':100.00})
                    rs=100
                if acc_id:
                    vals1['account_id']=acc_id
                context.update({'charges':True})
                vals1.update({'charges':True,'voucher_id':case.id})
                
                for i in voucher: 
                    cr.execute("update account_voucher set amount="+str(rs)+" where id="+str(i))
                    p=case.partner_id.id
                    if 'partner_id' in vals:
                        p=vals['partner_id']  
                        cr.execute("update account_voucher set account_id="+str(v_acc)+ " where id="+ str(i))                       
                        cr.execute("update account_voucher set partner_id="+str(p)+ " where id="+ str(i) )
                    if 'company_id' in vals:
                        c=vals['company_id'] or case.company_id.id
                        ac=self.onchange_company_id(cr, uid,i, c,case.partner_id.id,journal,case.type,context=None)
                        cr.execute("update account_voucher set company_id="+str(c)+ " where id="+ str(i))
                        
                    if 'journal_id' in vals:
                        j=vals['journal_id']
                        cr.execute("update account_voucher set journal_id="+str(j)+ " where id="+ str(i))
                        
                    if 'voucher_id' in vals:
                        v=vals['voucher_id']
                        
                        cr.execute("update account_voucher set voucher_id="+str(v)+ " where id="+ str(i))
                        
                    if 'period_id' in vals:
                        period=vals['period_id'] or case.period_id.id
                        cr.execute("update account_voucher set period_id="+str(period)+ " where id="+ str(i))
                        
                    if 'account_id' in vals:
                        a=v_acc
                        if not v_acc:
                           a=vals['account_id']                         
                        
                        cr.execute("update account_voucher set account_id="+str(a)+ " where id="+ str(i))
                        
                    if 'account_owner' in vals:
                        a_w=vals['account_owner']
                        cr.execute("update account_voucher set account_owner='"+str(a_w)+ "' where id='"+ str(i)+"'")                            
                   
                                            
                         
                    cr.execute("update account_voucher set reference ='Bank Comission/charges' where id="+ str(i))   
                        
#                     if 'state' in vals:
#                         s=vals['state']
#                         cr.execute("update account_voucher set state="+s+ " where id="+ str(i))                                                                                              
#                     if 'journal_id' in vals:
#                         cr.execute("update account_voucher set journal_id=%s where id=%s"(vals['journal_id'],str(i),))
 
                if not voucher and ids:
                    if 'type' in vals1:
                        if vals1['type']=='payment':
                            self.create(cr, uid, vals1, context)   
      if customer:
           vals.update({'advance_type':'advance','customer':True,'type':"receipt"})     
      res=super(account_voucher,self).write(cr, uid,ids, vals, context)                        
      return res
   
account_voucher()


class account_voucher_line(osv.osv):
    _inherit="account.voucher.line"
    _columns={
              'product_id'      :   fields.many2one('product.product',"Goods Details"),
              'name':fields.char('Description',),
              
              }
    _defaults = {
        'name': '.',
    }    
    def onchange_account_id(self, cr, uid, ids, account_id,name,parent_company,context=None):
        if context is None: 
            context = {}
        voucher_line=self.pool.get('account.voucher.line')
        res = {}
        dom = {}
        ctx={}
        voucher=[]
        line_dr_ids = {}
        j_ids=False
# print 'type',type 
        account_obj = self.pool.get('account.account') 
        acc_type = self.pool.get('account.account.type')
        if parent_company:
            res['company_id'] = parent_company
        
            dom = {'account_id':  [('company_id','=',parent_company),('type','!=','view')]}
            
        return {'value':res,'domain':dom}
    
account_voucher_line()


class account_account(osv.osv):
    _inherit="account.account"
    
    
    _columns={
  
              }
    _defaults={


               }
    def onchange_parent_id(self, cr, uid, ids, parent_id=False,context=None):
        res={}
        codes=[]
        m=0
        l=0
        length=0
        parent_ids = self.search(cr,uid,[('parent_id', '=',parent_id)])
        if parent_ids:
            for j in self.browse(cr,uid,parent_ids):
                 m=int(j.code)
                 codes.append(m)
    
            if codes:
                codes.sort()
                length=len(codes)
                l=length-1
                code=codes[l]
                res['code']=code+1
        else:
            res['code']=False
        return{'value' : res}

    def action_journal(self, cr, uid, ids, context=None):
        if not context:
            context={}
        journal_ids = []
        result = []
        journal_obj = self.pool.get('account.move.line')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        search_disable_custom_filters=context.update({'search_disable_custom_filters':False})   
        journal_ids = journal_obj.search(cr,uid,[('account_id','in',ids)]) 
        context.update({'move_ids':journal_ids})    
        move_ids = context.get('move_ids',[])
        xml_id = 'account_payable_action_bank_form' or False
        result = mod_obj.get_object_reference(cr, uid, 'kingswood', xml_id)              
        id = result and result[1] or False     
        result = act_obj.read(cr, uid, id, context=context)
        if result:
            result['domain'] = []
            account_domain = result['domain']
            account_domain.append(('id', 'in', move_ids))        
            result['domain'] = account_domain
        return result        
#         if journal_ids:
#             res_v = model_obj.get_object_reference(cr, uid, 'account', 'view_move_line_tree')
#             res_vid = res_v and res_v[1] or False
#             if res_vid:
#                 res.update({'view_id': res_vid})           
#  
#             res.update({
#                         'name': _('Incoming Shipments-Returns'),
#                         'res_model': 'account.journal',
#                         'view_type': 'tree',
#                         'view_mode': 'tree', 
#                         'type': 'ir.actions.act_window',
#                         'target': 'current',
#                         'nodestroy': True,
#                         'target': 'current',
#              
#                         })
           
           
             
#         result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)           
#         context.update({'move_ids':journal_ids})
#         model_data_ids = mod_obj.search(cr, uid,[('model','=','ir.ui.view'),('name','=','view_move_line_bank_tree')], context=context)
#         resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
#         model_data_search_ids = mod_obj.search(cr, uid,[('model','=','ir.ui.view'),('name','=','view_account_move_line_filter')], context=context)
#         resource_id_search = mod_obj.read(cr, uid, model_data_search_ids, fields=['res_id'], context=context)[0]['res_id']
#         return {
#             'domain': "[('id','in', ["+','.join(map(str,context['move_ids']))+"])]",
#             'name': 'Entries',
#             'view_type': 'tree',
#             'view_mode': 'tree',
#             'res_model': 'account.move.line',
#             'views': [(resource_id,'tree')],
#            
#             'type': 'ir.actions.act_window',
#         }    
account_account()


class account_tax(osv.osv):
     _inherit="account.tax"
     _columns={
                'state_id'        : fields.many2one('res.country.state','State'),
               
              }
account_tax()

class account_move(osv.osv):
    _inherit = "account.move"
    _description = "Account Entry"
    _order = 'id desc'
    _columns = {
                }

    def onchange_journal_comp(self, cr, uid, ids, journal_id, context=None):
        journal_obj = self.pool.get('account.journal')
        today = time.strftime('%Y-%m-%d')
        p=[]
        period={}
        if not context:
            context = {}
        res = {}
        journal = journal_obj.browse(cr, uid, [journal_id] )
        if journal:
            journal = journal[0]
            company =journal.company_id.id
            cr.execute("select id from account_period where company_id='"+ str(company) +"'and date_start <= '" + today + "' and date_stop >='" + today + "'")
            p_ids = cr.fetchone()   
            if p_ids:
                p_ids=p_ids[0]
                res.update({'period_id':p_ids})

            res.update({'company_id' : journal.company_id.id})
                    
                    
                    
        return {'value': res}
    
    def create(self, cr, uid, vals, context=None):
        journal_obj = self.pool.get('account.journal')
        today = time.strftime('%Y-%m-%d')
        if not context:
            context = {}
        j_id = vals.get('journal_id',False)
        journal = journal_obj.browse(cr, uid, [j_id] )
        if journal:
            journal = journal[0]
        vals.update({
                    'company_id' : journal.company_id.id or False,
                    })
        return super(account_move,self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        journal_obj = self.pool.get('account.journal')
        move_line=self.pool.get('account.move.line')
        case = self.browse(cr, uid, ids)
        if case:
            case = case[0]
        if not context:
            context = {}
        j_id = vals.get('journal_id',False)
        if j_id:
            journal = journal_obj.browse(cr, uid, [j_id] )
            if journal:
                journal = journal[0]
                company=journal.company_id.id
                vals.update({
                        'company_id' : journal.company_id.id or False,
                        })  

        return super(account_move,self).write(cr, uid, ids, vals, context=context)
    
account_move()


class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    
    def get_balance(self, cr, uid, ids, field_name, args, context = None):
        res = {}
        
        for case in self.browse(cr, uid, ids):
            total_balance = 0.00
            line_id = []
            res[case.id]={
                          'balance':0.00,'total_balance':0.00
                          } 
            res[case.id]['balance'] = case.debit - case.credit
            
            if case.partner_id.id:
                cr.execute("""select id from account_move_line where partner_id ="""+str(case.partner_id.id)+"""and company_id =
                           """+str(case.company_id.id)+"""and account_id="""+str(case.account_id.id))
                line_id=cr.fetchall()
            if line_id:
                line_id=zip(*line_id)[0]             
#             line_id = self.search(cr,uid,[('partner_id','=',case.partner_id.id),('company_id','=',case.company_id.id),('account_id','=',case.account_id.id)])    
            print 'line',len(line_id)
            
            if line_id:
                cr.execute("""select sum(debit - credit) from account_move_line where id in %s""",(tuple(line_id),))      
                total_balance = cr.fetchone() 
                if total_balance:
                   total_balance = total_balance[0]               
            
            res[case.id]['total_balance'] = total_balance
            
        return res
    
    _columns = {
                'balance'  : fields.function(get_balance, type="float",store=False, string="Balance",multi = 'balance'),
                'total_balance' : fields.function(get_balance, type='float', method = True, multi = 'balance',
                                                                 store=False,string='Total Balance'),                  
                }
    
    #overridden to add the customer name based on delivery order
    def name_get(self, cr, uid, ids, context=None):
        pick_obj = self.pool.get('stock.picking.out')
        if not ids:
            return []
        result = []
        for line in self.browse(cr, uid, ids, context=context):
            if line.ref:
                pick_ids = pick_obj.search(cr,uid, [('name','=',line.ref)])
                if pick_ids:
                    for p in pick_obj.browse(cr, uid, pick_ids):
                        result.append((line.id, (line.move_id.name or '')+' ('+line.ref+')'+' / ('+p.partner_id.name+')'))
                else:
                    result.append((line.id, (line.move_id.name or '')+' ('+line.ref+')'))
            else:
                result.append((line.id, line.move_id.name))
        return result
    

    
account_move_line()

# class res_partner_bank(osv.osv):
#     _inherit = 'res.partner.bank'
#     # name '_bank_type_get' is not defined error occurs if not defined here
# 
#      
#     _columns={
#                
#            'name': fields.char('Bank Account', size=100), # to be removed in v6.2 ?
#             'bank_name': fields.char('Bank Name', size=100),
#             'owner_name': fields.char('Owner Name', size=100),
#               }
#     
# res_partner_bank()
# hh
#     def name_get(self, cr, uid, ids, context=None):
#         if not ids:
#             return []
#         result = []
#         acc=self.search(cr,uid,[('id','=',ids[0])])
#         if acc:
#             if 'acc_num' in context :
#                 if context['acc_num'] :
# #                    partner= context['partner']
# #                    acc_ids=self.search(cr,uid,[('partner_id','=',partner)])
#                    for i in self.browse(cr,uid,ids):
#                         number=i.acc_number
#                         result.append((i.id, number))
#         return result
        
# 

    