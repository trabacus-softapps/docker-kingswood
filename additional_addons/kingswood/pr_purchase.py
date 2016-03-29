# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime
import openerp.addons.decimal_precision as dp
from openerp.addons.prova import pr_config as pr_gl
from lxml import etree
from openerp.osv.orm import setup_modifiers
# import datetime
import logging
import time
import math
 
class purchase_order(osv.osv):
    _inherit='purchase.order'
    
    #inheritted to change string of the button dynamically.
    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(purchase_order, self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form' and context.get('default_type') == 'sample':
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//button[@string='Confirm Order']")
            for node in nodes:
                node.set('string', 'Confirm Sample')
                     
            res['arch'] = etree.tostring(doc)
        return res
     
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
#         res=super(_amount_all,self).write(cr, uid, ids,field_name, arg, context=context)
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
               val1 += cur_obj.compute(cr, uid, line.currency_id.id, cur.id,line.price_subtotal, True, context)
               for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, order.partner_id)['taxes']:
                    val += cur_obj.compute(cr, uid, line.currency_id.id, cur.id,c.get('amount', 0.0), True, context)
       
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res
    
#    Calculating SecondaryCurrency Based on Currency Rate Defined 
    def _amt_local_curr(self, cr, uid, ids, field_name, args, context=None):
        
        
        """    Calculating SecondaryCurrency Based on Currency Rate Defined """
        
        
        if not context:
            context={}
        res={}
        prod=[]
        currency_count=[]
        currency1 = False
        currency2 = False
        cur_obj=self.pool.get('res.currency')
        line_obj = self.pool.get('purchase.order.line')
        for case in self.browse(cr, uid, ids):
            if case.currency_id:
                res[case.id] = {
                                'untaxed_amount1'   :0.00,
                                'untaxed_amount2'   :0.00,
                                'untaxed_amount3'   :0.00,
                                'amount_tax1'       :0.00,
                                'amount_tax2'       :0.00,
                                'amount_tax3'       :0.00,
                                'amount_total1'     :0.00,
                                'amount_total2'     :0.00,
                                'amount_total3'     :0.00,
                                }
                val=val1=0.0
                cur = case.pricelist_id.currency_id
                currency_count.append(case.currency_id.id)
                for line in case.order_line:
                    # Warning msgs if same producted multiple times in the line
                    if line.product_id:
                        if line.product_id.id not in prod: 
                            prod.append(line.product_id.id)
                            
                        else:
                            raise osv.except_osv(_('Warning'),_('Please Do Not Select Same Product More Than Once'))                    
                    if line.currency_id:
                        if not line.currency_id.id in currency_count:
                            currency_count.append(line.currency_id.id)
                        if currency_count:
                            if len(currency_count)>3:
                                raise osv.except_osv(_('Warning'),_('Please Do Not Select more than 3 different currencies'))    
                            if len(currency_count) == 2:
                                cr.execute("update purchase_order set currency_id3=null where id="+str(case.id)) 
                            if len(currency_count) == 1 or (len(currency_count) == 2 and line.currency_id.id != case.currency_id.id):  
                                cr.execute("update purchase_order set currency_id3=null,currency_id2=null where id="+str(case.id)) 
                            
                    if line.currency_id.id != case.currency_id.id:
                        if not currency1:
                           currency1=line.currency_id.id
                        if not currency2 and line.currency_id.id != currency1:
                           currency2=line.currency_id.id
                        if currency1:
                            if currency1 ==  line.currency_id.id:
                               res[case.id]['untaxed_amount2']+=line.price_subtotal
                               for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, case.partner_id)['taxes']:
                                    val += c.get('amount', 0.0)
                               res[case.id]['amount_tax2']=cur_obj.round(cr, uid, cur, val)    
                               res[case.id]['amount_total2']=res[case.id]['untaxed_amount2'] + res[case.id]['amount_tax2']                           
                               cr.execute("update purchase_order set currency_id2="+str(line.currency_id.id)+" where id="+str(case.id))
                          
                           
                        if currency2:
                            if currency2 ==  line.currency_id.id:
                               res[case.id]['untaxed_amount3']+=line.price_subtotal     
                               cr.execute("update purchase_order set currency_id3="+str(line.currency_id.id)+" where id="+str(case.id))  
                               for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, case.partner_id)['taxes']:
                                    val1 += c.get('amount', 0.0)
                               res[case.id]['amount_tax3']=cur_obj.round(cr, uid, cur, val1)  
                               res[case.id]['amount_total3']=res[case.id]['untaxed_amount3'] + res[case.id]['amount_tax3']
                            
                               
                    else:      
#                         line_obj.write(cr,uid,[line.id],{'secondary_unit_price':0.001})
                        
                        res[case.id]['untaxed_amount1']+=line.price_subtotal
                        for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, case.partner_id)['taxes']:
                            val1 += c.get('amount', 0.0)
                        res[case.id]['amount_tax1']=cur_obj.round(cr, uid, cur, val1)  
                        res[case.id]['amount_total1']=res[case.id]['untaxed_amount1'] + res[case.id]['amount_tax1']
                           
                          
            if case.currency_id.id not in currency_count:
                  cr.execute("update purchase_order set amount_untaxed=0,amount_tax=0,amount_total=0 where id="+str(case.id))
#                 for j in case.order_line:
#                     line_obj.write(cr,uid,[j.id],{'currency_id':case.currency_id2.id})
                
#                 from_currency = case.currency_id2.id
#                 to_currency = case.currency_id.id
#                 
#                 sec_total = curr_obline.compute(cr,uid,to_currency,from_currency,case.amount_total,True,context)
#                 res[case.id]['secondary_currency'] = sec_total
#                 sec_total = curr_obj.compute(cr,uid,to_currency,from_currency,case.amount_tax,True,context)
#                 res[case.id]['secondary_tax'] = sec_total                 
            return res 

    # Overriden
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
        

    # Overriden:
    def _get_picking_in(self, cr, uid, context=None):
        res = super(purchase_order, self)._get_picking_in(cr, uid, context=context)
        company = []
        spt_ids = []
        picking_company=False
        pickingtype_obj = self.pool.get('stock.picking.type')
        user_obj = self.pool.get('res.users').browse(cr,uid,uid)
        
        for x in user_obj.company_ids:
            company.append(x.id)        
        if res:
            picking_type = pickingtype_obj.browse(cr,uid,res)
            try:
                picking_company = picking_type.warehouse_id.company_id.id
                return res
            except:
                cr.execute("select spt.id from stock_picking_type spt inner join stock_warehouse sw on sw.id = spt.warehouse_id where sw.company_id in %s",(tuple(company),))
                spt_ids = [x[0] for x in cr.fetchall()]
                spt_id = pickingtype_obj.search(cr,uid,[('id','in',spt_ids)])
                if spt_id:
                    print spt_id
                    return spt_id[0]
                else:
                    return []
        else:
            return res

       
    
      
    def _get_amount_words(self, cr, uid, ids, name, args, context=None):
        
        """
      Convert Amount to words
     """  
        res = {} 
       
        def _get_words(case, amount,currency):
            whole_word = frac_word = amt_word = ''
            frac, whole = math.modf(amount)
            currency_pool = self.pool.get("res.currency")
        
            if currency:
                currency_obj = currency_pool.browse(cr, uid, currency)
                
                
                CurrName = (currency_obj.number_name or '')
                DeciName = (currency_obj.decimal_name or '')
                
                if currency_obj.name.upper() == 'INR':
                    cr.execute("select amount2words_ind(%d)"%int(whole))
                    whole_word = cr.fetchone()
                    
                    if frac:
                        cr.execute("select amount2words_ind(%d)"%(frac * 100))
                        frac_word = cr.fetchone()
                        frac_word = (frac_word and frac_word[0] or '')
                        frac_word = ' and ' + frac_word + ' ' + DeciName
                    
                    whole_word = CurrName + ' ' + (whole_word and whole_word[0] or '')
                    
                else:
                    cr.execute("select amount2words_english(%d)"%int(whole))
                    whole_word = cr.fetchone()
                
                    if frac:   
                        cr.execute("select amount2words_english(%d)"%(frac * 100))
                        frac_word = cr.fetchone()
                        frac_word = (frac_word and frac_word[0] or '')
                        frac_word += ' ' + DeciName 
                
                    whole_word = (whole_word and whole_word[0] or '') + ' ' + CurrName 
                    
                if frac:
                    amt_word = whole_word + ' ' + 'and' + ' ' + frac_word + ' ' +'Only.'
                else:
                    amt_word = whole_word + ' ' + frac_word + ' ' +'Only.'
                    
            return amt_word
            
        for case in self.browse(cr, uid, ids, context):
            res[case.id] = {
                            'amount_in_words': _get_words(case,case.amount_total,case.pricelist_id.currency_id.id),
                            'amount_in_words2': _get_words(case,case.amount_total2,case.currency_id2.id),
                            'amount_in_words3': _get_words(case,case.amount_total3,case.currency_id3.id),
                            }
        return res
        
        
    def default_get(self, cr, uid, fields, context=None):
        res = self._get_picking_in(cr, uid, context)
        result = super(purchase_order, self).default_get(cr, uid, fields, context)
        # to update default picking type id
        if res:
            result.update({'picking_type_id':res})
        if context.get('default_type'):
            result['type'] = 'sample'
        else:
            result['type'] = 'purchase'
        return result
    
    def _get_partner_ref(self, cr, uid, ids, field_name, args, context=None):
        """ TO return true or false based on conditons. Used to hide the button """
        res = {}
        ref = ''
        for case in self.browse(cr, uid, ids):
            
            if case.partner_id:
                ref = str(case.partner_id.ref or "")
            if ref:
                cr.execute("update purchase_order set partner_reference ='"+str(ref)+ "' where id = "+ str(case.id))

            res[case.id] = ref

        return res    

    def _get_in_records(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        pick_obj = self.pool.get("stock.picking")
        for case in self.browse(cr, uid, ids):
            pick_ids = pick_obj.search(cr, uid, [('origin','=',case.name)])
            if pick_ids:
                res[case.id] = pick_ids
            else:
                 res[case.id] = []
        return res
    
#     def fields_get(self, cr, uid, fields=None, context=None, write_access=True, attributes=None):
#         res = super(purchase_order, self).fields_get(cr, uid, fields, context, write_access, attributes)
#         print "res..",res
#         return res
            
    _columns={
              'courier'             : fields.char('Courier',size=200),
              'ship_via'            : fields.char('Port of Destination',size=200),
              'user_id'             : fields.many2one('res.users','User'),
              'ship_term'           : fields.char('Shipping Terms',size=200),
              'currency_id2'        : fields.many2one('res.currency','Secondary Currency'),
              'currency_id3'        : fields.many2one('res.currency','Secondary Currency'),
              'untaxed_amount1'     : fields.function(_amt_local_curr,  type='float',digits=(0,2),string='Untaxed Amount',store=True,multi='currency'),
              'untaxed_amount2'     : fields.function(_amt_local_curr,  type='float',digits=(0,2),string='Untaxed Amount',store=True,multi='currency'),
              'untaxed_amount3'     : fields.function(_amt_local_curr,  type='float',digits=(0,2),string='Untaxed Amount',store=True,multi='currency'),
              'amount_tax1'         : fields.function(_amt_local_curr,  type='float',digits=(0,2),string='Taxes',store=True,multi='currency'),
              'amount_tax2'         : fields.function(_amt_local_curr,  type='float',digits=(0,2),string='Taxes',store=True,multi='currency'),
              'amount_tax3'         : fields.function(_amt_local_curr,  type='float',digits=(0,2),string='Taxes',store=True,multi='currency'),
              'amount_total1'        : fields.function(_amt_local_curr,  type='float',digits=(0,2),string='Total',store=True,multi='currency'),
              'amount_total2'        : fields.function(_amt_local_curr,  type='float',digits=(0,2),string='Total',store=True,multi='currency'),
              'amount_total3'        : fields.function(_amt_local_curr,  type='float',digits=(0,2),string='Total',store=True,multi='currency'),
              'email_send_date'     : fields.datetime("Email Sent Date"),
              'ref'                 :    fields.char('Code',size=200),   
              
              'amount_in_words'     :   fields.function(_get_amount_words, method=True, string="Amount in Words", type="text",
                    store={
                    'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 20),
                    'purchase.order.line': (_get_order, ['order_id'], 20), # To Update the Lines Changes.
                },multi="Words" ),
              
              'amount_in_words2'     :   fields.function(_get_amount_words, method=True, string="Amount in Words", type="text",
                    store={
                    'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 20),
                    'purchase.order.line': (_get_order, ['order_id'], 20), # To Update the Lines Changes.
                },multi="Words" ),
              
              'amount_in_words3'     :   fields.function(_get_amount_words, method=True, string="Amount in Words", type="text",
                    store={
                    'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 20),
                    'purchase.order.line': (_get_order, ['order_id'], 20) # To Update the Lines Changes.
                },multi="Words" ),
              
              
                'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
                    store=True, multi="sums", help="The amount without tax", track_visibility='always'),
                'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
                    store={
                        'purchase.order.line': (_get_order, None, 10),
                    }, multi="sums", help="The tax amount"),
                'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
                    store=True, multi="sums", help="The total amount"),         
              
              # overidden to add track visibility  
              'company_id': fields.many2one('res.company', 'Company', required=True, track_visibility='onchange',select=1, states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)]}),
              
              'picking_type_id': fields.many2one('stock.picking.type', 'Deliver To', help="This will determine picking type of incoming shipment", required=True,
                                           states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)], 'done': [('readonly', True)]}),
              
              'type' : fields.selection([('sample', 'Sample'), ('purchase', 'Purchase')], 'Type', copy=True),
              'related_usage': fields.related('location_id', 'usage', type='char'),
            # Partner Reference from Graph view                  
              'partner_id_ref': fields.function(_get_partner_ref, type='char',string='Reference', store=False),
              'partner_reference': fields.related('partner_id','ref',type='char',string = "Reference",store=True),
              
              # for Mexico Report
              'shipping_way'            :   fields.selection([('air', 'Air Way'),('sea', 'Sea Way')], "Ship Via"), 
              
              # for Email Template
#             ''      :   fields.function(, type='one2many', relation="stock.picking", string="Incoming Records",store=True),    
            
            'in_records'    : fields.function(_get_in_records, method=True, type='one2many', relation='stock.picking', string='Incoming Records'),
            
            #For Indian Purchase Order Report
            'invoice'       :   fields.boolean("Invoice"),
            'analysis'      :   fields.boolean("Certificate of Analysis"),
            'packing_list'  :   fields.boolean("Packing List"),
            'msds'          :   fields.boolean("MSDS"),
            'iso'           :   fields.boolean("Invoice"),
            'halal_kosher'  :   fields.boolean("Halal/Kosher Certificate"),
            'conformity'    :   fields.boolean("Certificate of Conformity"),
            'brc'           :   fields.boolean("Copy of BRC Certificate"),
            'others'        :   fields.boolean("Others"),
            'food_laws'     :   fields.boolean("Labeling Instruction as per indian food laws"),
            'cf1_amount'    :   fields.float('CF1',states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)], 'done': [('readonly', True)]},digits=(16,2))
            
            
            
              
              }
    _defaults={
                       'user_id': lambda obj, cr, uid, context: uid,
                        'picking_type_id': _get_picking_in,  
                        'shipping_way'  :   'air',
                        'invoice'       :   False,
                        'analysis'      :   False,
                        'packing_list'  :   False,
                        'msds'          :   False,
                        'iso'           :   False,
                        'halal_kosher'  :   False,
                        'conformity'    :   False,
                        'brc'           :   False,
                        'others'        :   False,
                        'food_laws'     :   False,
                        
               }
    
    
    
  # Print reports  
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        multi=False
        currency_count=[]
        report_name = ''
        for case in self.browse(cr, uid, ids):
            if not case.order_line:
                raise osv.except_osv(_('Warning'),_('You cannot Print a purchase order without any purchase order line.'))   
            for line in case.order_line:
                if line.currency_id:
                    if not line.currency_id.id in currency_count:
                        currency_count.append(line.currency_id.id)
                    if currency_count:
                        if len(currency_count)>1:
                            multi=True
                        
            if not multi:
                if case.company_id.country_id and 'indonesia' in case.company_id.country_id.name.lower():            
                    if case.company_id.partner_id and 'pt prova' in case.company_id.partner_id.name.lower():
                        report_name = 'Purchase Order'
                    if case.company_id.partner_id and 'pt projava' in case.company_id.partner_id.name.lower():
                        report_name = 'purchase order import'

            else:
                
                if case.company_id.country_id and 'indonesia' in case.company_id.country_id.name.lower(): 
                    if case.company_id.partner_id and 'pt projava' in case.company_id.partner_id.name.lower():
#                         if len(currency_count)>2:
#                             report_name = 'Purchase Order 3 currency' 
                        if len(currency_count) == 2 :
                            report_name = 'Purchase Order Local - PT Projava'   
                                               
            if case.company_id.country_id and 'india' in case.company_id.country_id.name.lower():
                report_name = 'Purchase Order – India'
        
        if not report_name:
            return True
        data = {}
        data['ids'] = ids
        data['model'] = context.get('active_model', 'purchase.order')
        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'name' : report_name,
        'datas': data,
        }
           
# Overriding to add the warning if no product in lines
    def wkf_confirm_order(self, cr, uid, ids, context=None):
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
            for line in po.order_line:
                if not line.product_id:
                   raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without product in purchase order line.')) 
                if line.state=='draft':
                    todo.append(line.id) 
                    
        self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
        
#         for case in self.browse(cr, uid, ids, context=context):
#             # to send the confirmation message for Delivery Manager
#             print"in_records" ,case.in_records
#             self.send_sample_mails(cr, uid, case, 'purchase_order_receive_send_mail', context)
            
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid})
        return True
    
    def send_sample_mails(self, cr, uid, case, template_name, context=None):
        mail_obj = self.pool.get('mail.mail')
        partner_obj = self.pool.get('res.partner')
        
        
        template = self.pool.get('ir.model.data').get_object(cr, uid, 'prova', template_name)
        assert template._name == 'mail.template'
        
        for partner in partner_obj.browse(cr, uid, [case.user_id.partner_id.id], context):
            if template_name == 'purchase_order_receive_send_mail':
                emails = ''
                
                # to get the emails of Purchase and Qality manager based on company
                cr.execute("""select distinct rp.email
                                    from res_groups_users_rel gu 
                                    inner join res_groups g on g.id = gu.gid
                                    inner join res_users ru on ru.id = gu.uid
                                    inner join res_partner rp on rp.id = ru.partner_id
                                    where g.name = 'Manager'
                                    and rp.email is not null
                                    and rp.company_id = """+ str(case.company_id.id) +"""
                                    and g.category_id in (select id from ir_module_category where name in ('Purchases','Quality Control'))""")
                for email in cr.fetchall():
                    #to eliminate duplicate emails address
                    if email[0] not in emails:
                        emails += email[0] + ','
                
                self.pool.get('mail.template').write(cr, uid, template.id, {'email_to':emails[:-1],'email_cc':case.user_id.partner_id.email})
            
            
            if not partner.email:
                raise osv.except_osv(_("Cannot send email: user has no email address."), partner.name)
            mail_id = self.pool.get('mail.template').send_mail(cr, uid, template.id, case.id, True, context=context)
            mail_state = mail_obj.read(cr, uid, mail_id, ['state'], context=context)
            if mail_state and mail_state['state'] == 'exception':
                raise osv.except_osv(_("Cannot send email: no outgoing email server configured.\nYou can configure it under Settings/General Settings."), partner.name)
        return True
    
    #overidden to update the Origin Type of the picking
    def action_picking_create(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids):
            picking_vals = {
                'picking_type_id': order.picking_type_id.id,
                'partner_id': order.partner_id.id,
                'date': max([l.date_planned for l in order.order_line]),
                'origin': order.name,
                'shipping_way' : order.shipping_way,
                'cf1_amount'   : order.cf1_amount or 0,
            }
            if order.type == 'sample':
                picking_vals.update({'origin_type':'sample'})
            else:
                picking_vals.update({'origin_type':'order'})
            picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
            self._create_stock_moves(cr, uid, order, order.order_line, picking_id, context=context)
            
            for case in self.browse(cr, uid, ids, context=context):
                print "Incoming Recotds", case.in_records
                # to send the confirmation message for Delivery Manager
                self.send_sample_mails(cr, uid, case, 'purchase_order_receive_send_mail', context)

    
   
    
    #Warning msgs if same product selected multiple times in the line
#     def onchange_order_line(self, cr, uid, ids, order_line, context=None):
#         values = {}
#         prod=[]
#         for ln in self.resolve_o2m_commands_to_record_dicts(cr, uid, 'order_line', order_line, ["product_id"]):
#             product_id = ln.get('product_id', False)
#             print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", product_id
#             if ln.get('id', False): 
#                 if product_id[0] not in prod:
#                     prod.append(product_id[0])
#                 else:
#                     raise osv.except_osv(_('Warning'),_('Please Select different product'))
#             else:
#                  if product_id not in prod:
#                      prod.append(product_id)    
#                  else:
#                    raise osv.except_osv(_('Warning'),_('Please Select different product'))                
#         print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", prod                
#         return {'value':values}  


    def onchange_pricelist(self, cr, uid, ids, pricelist_id, context=None):
        res=super(purchase_order, self).onchange_pricelist(cr, uid, ids,pricelist_id, context=context)
        if ids:
            order_line=self.pool.get('purchase.order.line')
            for order in self.browse(cr,uid,ids):
                for line in order.order_line:
                    order_line.write(cr,uid,[line.id],{'secondary_unit_price':0.001})
                    
        return res
    
    #inheritted to update currency from purchase to invoice
    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        res = super(purchase_order, self)._prepare_inv_line(cr, uid, account_id, order_line, context)
        res.update({'currency_id':order_line.currency_id and order_line.currency_id.id or False})
        return res
    
    
    def view_picking(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''        
            
        if not context:
            context={}
        journal_ids = []
        result = []
        pick_ids = []
        pick_obj = self.pool.get('stock.picking')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        search_disable_custom_filters=context.update({'search_disable_custom_filters':False})   
        for so in self.browse(cr, uid, ids, context=context):
            pick_ids += [picking.id for picking in so.picking_ids]
        print 'pick_ids',pick_ids 
        for case in self.browse(cr,uid,ids):
            pick_ids = pick_obj.search(cr,uid,[('origin','=',case.name)])
            pick_ids = [x for x in pick_ids]
        print 'pick_ids1',pick_ids 
        context.update({'pick_ids':pick_ids})    
        move_ids = context.get('pick_ids',[])
        xml_id = 'action_picking_tree_all' or False
        result = mod_obj.get_object_reference(cr, uid, 'stock', xml_id)              
        id = result and result[1] or False     
        result = act_obj.read(cr, uid, id, context=context)
        if result:
            result['domain'] = []
            account_domain = result['domain']
            account_domain.append(('id', 'in', move_ids))        
            result['domain'] = account_domain
                    
        return result 
    
     # Overriding to add the email_send_date whete PO state changed to sent
    def write(self,cr,uid,ids,vals,context=None): 
        today = time.strftime('%Y-%m-%d %H:%M:%S') 
        if not context:
            context={}  
        currency=[]    
        pricelist_id = vals.get('pricelist_id',False)    
        state=vals.get('state',False)
        if state=='sent':
            vals.update({'email_send_date':today})

        if pricelist_id:
            vals.update({'currency_id': self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id.id})
                                       
        res=super(purchase_order,self).write(cr, uid, ids,vals, context=context)
        # to check the currency conversion rate as per record date or current date
        for case in self.browse(cr, uid, ids):
            pr_gl.chk_currencyConversion(self, cr, uid,vals.get('company_id',case.company_id.id) , vals.get('date_order',case.date_order),context)
        return res
    
    # Overriding to Change  the PO number/name according to company
    def create(self, cr, uid, vals, context=None):
        msg_obj = self.pool.get('mail.message')
        msg_ids = []
        if context is None:
            context = {}
        lead_obj = self.pool.get('crm.lead')
        pricelist_id = vals.get('pricelist_id',False)
        context.update({'force_company':vals.get('company_id', False)})
        
        if vals.get('company_id',False):
            pr_gl.chk_currencyConversion(self, cr, uid,vals.get('company_id',False) , vals.get('date_order',False),context)
        
        if context.get('default_type') == 'sample':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase.sample', context) or '/'
        else:
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order', context) or '/'
        if pricelist_id:
            vals.update({'currency_id': self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id.id})
            
        res=super(purchase_order, self).create(cr, uid, vals, context=context)
        return res
    
    #inheritted to update the location id for specific suppliers
    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        context = dict(context or {})
        partner = self.pool.get('res.partner')
        res = super(purchase_order,self).onchange_partner_id(cr, uid, ids, partner_id, context=context)
        if partner_id:
            supplier = partner.browse(cr, uid, partner_id, context=context)
            if res['value'] and supplier.property_location_id:
                res['value'].update({
                                     'location_id': supplier.property_location_id.id or False,
                                     })
        return res
            
purchase_order()
 
 
 
class purchase_order_line(osv.osv):
    _inherit='purchase.order.line'
     
    def _get_uom_id(self, cr, uid, *args):
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_gram')
            return result[1]
        except Exception, ex:
            return False
        
#    Calculating SecondaryCurrency Based on Currency Rate Defined
    def _amt_sec_curr(self, cr, uid, ids, field_name, args, context=None):
        res={}
        curr_obj = self.pool.get("res.currency")
        prod=[]
        for case in self.browse(cr, uid, ids):
             
            res[case.id] = {'secondary_currency':0.00,'secondary_unit_price' :0.00}

            return res 
             
    _columns={
              'currency_id'         : fields.many2one('res.currency','Currency'),
              'secondary_currency'  : fields.function(_amt_sec_curr,  type='float', digits=(0,2),string='Secondary Subtotal',store=True,multi='currency'),
              'secondary_unit_price': fields.function(_amt_sec_curr,  type='float', digits=(0,2),string='Secondary Price Unit',store=True,multi='currency'),
              'packing_id'          : fields.many2one('product.packing','Packing'),
               'date_planned': fields.date('Scheduled Date', required=True, select=True),
                'product_uom': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
                
              # For PT PROVA Company Report
              'ref_code'    :   fields.char("Ref Code"),
              'tariff_code' :   fields.char("Tariff Code"),
              'size'        :   fields.char("Size", size=50),
              
              }
    
    _defaults={
                'currency_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id,
                'secondary_currency'  : 0.00,
                'date_planned'  :    lambda *a: time.strftime('%Y-%m-%d'),
                'product_uom' : _get_uom_id,
                'price_unit' : 0.0,
                
               }
    
    def onchange_secondary_currency(self, cr, uid, ids, secondary_currency, currency_id,context=None):
        values = {}
        today = time.strftime('%Y-%m-%d')
        prod=[]
        if currency_id:
            values['currency_id']=currency_id
        return {'value':values} 
    
    #Inheritted
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', replace=True, context=None):
        """
    
        onchange handler of product_id.
        """

        
        context = dict(context or  {})
        context.update({'date':date_order})
        company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        
        print "context1,...........", context
        
         # to check the conversion rate for given date_order
        pr_gl.chk_currencyConversion(self, cr, uid, company_id , date_order, context)
        
        from_currency_id = self.pool.get('product.pricelist').browse(cr, uid, pricelist_id).currency_id.id
        cur_obj = self.pool.get('res.currency')
         
        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id, 
                                                                   partner_id, date_order, fiscal_position_id, date_planned,
                                                                   name, price_unit, state, replace, context)
        if context.get('currency_id') and 'price_unit' in res['value']:
            res['value']['price_unit'] = cur_obj.compute(cr, uid, from_currency_id, context.get('currency_id'), res['value']['price_unit'],True, context)
        return res
     
    #product_id_change = onchange_product_id
    
    def currency_id_change(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', from_currency_id =False, to_currency_id =False, context=None):
        
        """ Line Level Currency Conversion """
        
        context = dict(context or  {})
        context.update({'date':date_order})
        print "context2,...........", context 
        res = {}
        cur_obj = self.pool.get('res.currency')
        res = self.product_id_change(cr, uid, ids, pricelist_id, product_id, qty, uom_id, 
                                                                   partner_id, date_order, fiscal_position_id, date_planned,
                                                                   name, price_unit, state, context)
       
        if res.get('value') and 'price_unit' in res['value']:
            res['value']['price_unit'] = cur_obj.compute(cr, uid, from_currency_id, to_currency_id, res['value']['price_unit'],True, context)
        return res

purchase_order_line() 


class purchase_requisition(osv.osv):
    _inherit = "purchase.requisition"
    
    def _get_picking_in(self, cr, uid, context=None):
        obj_data = self.pool.get('ir.model.data')
        type_obj = self.pool.get('stock.picking.type')
        user_obj = self.pool.get('res.users')
        company_id = user_obj.browse(cr, uid, uid, context=context).company_id.id
        types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)], context=context)
        if not types:
            types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id', '=', False)], context=context)
            if not types:
                raise osv.except_osv(_('Error!'), _("Make sure you have at least an incoming picking type defined"))
        return types[0]
    
    
    _defaults = {
                'picking_type_id': _get_picking_in
                }

purchase_requisition()

