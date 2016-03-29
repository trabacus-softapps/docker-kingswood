# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from openerp.osv import fields, osv
from openerp import SUPERUSER_ID, api
from openerp.tools.translate import _
import math
import time
from datetime import datetime
from dateutil import parser
import re


class stock_picking(osv.osv):
    _inherit = 'stock.picking'
     
#     def _get_amount_words(self, cr, uid, ids, name, args, context=None):
#        """
#            Convert Amount to words
#        """   
#        res = {} 
#        sale_obj = self.pool.get("sale.order")
#        for case in self.browse(cr, uid, ids, context):
#            if case.id:
#                sale_ids = sale_obj.search(cr, uid, [('id','in',[case.sale_id.id])])
#                if sale_ids:
#                    sale_ids = sale_ids[0]
#                for sale in sale_obj.browse(cr, uid, sale_ids):
#                    amount_tot = sale.amount_total
#                    frac, whole = math.modf(amount_tot)
#                    currency = sale.currency_id or sale.company_id.currency_id
#                    whole_word = frac_word = ''
#                     
#                    CurrName = (currency.number_name or '')
#                    DeciName = (currency.decimal_name or '')
#                     
#                    if currency.name.upper() == 'INR':
#                        cr.execute("select amount2words_ind(%d)"%int(whole))
#                        whole_word = cr.fetchone()
#                         
#                        if frac:
#                            cr.execute("select amount2words_ind(%d)"%(frac * 100))
#                            frac_word = cr.fetchone()
#                            frac_word = (frac_word and frac_word[0] or '')
#                            frac_word = ' and ' + frac_word + ' ' + DeciName
#                         
#                        whole_word = CurrName + ' ' + (whole_word and whole_word[0] or '')
#                         
#                    else:
#                        cr.execute("select amount2words_english(%d)"%int(whole))
#                        whole_word = cr.fetchone()
#                     
#                        if frac:    
#                            cr.execute("select amount2words_english(%d)"%(frac * 100))
#                            frac_word = cr.fetchone()
#                            frac_word = (frac_word and frac_word[0] or '')
#                            frac_word += ' ' + DeciName 
#                     
#                        whole_word = (whole_word and whole_word[0] or '') + ' ' + CurrName
#                         
#                     
#                    if frac:
#                        res[case.id] = whole_word + ' ' + 'and' + ' ' + frac_word + ' ' +'Only.'
#                    else:
#                        res[case.id] = whole_word + ' ' + frac_word + ' ' +'Only.'
#        return res
   
    
    def default_user_company(self, cr, uid, context=None):
        if not context:
            context = {}
        user_obj = self.pool.get("res.users")
        user = user_obj.browse(cr, uid, uid)
        if ('mexico' in  user.company_id.name.lower()) or uid == 1:
            return True
        else:
            return False


    def _get_user_company(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        if not context:
            context = {}
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid)
        for case in self.browse(cr, uid, ids): 
            if ('mexico' in  user.company_id.name.lower()) or uid == 1:
                res[case.id] = True
            else:
                res[case.id] = False
        return res
    
    def _get_cf_price(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        if not context:
           context = {}
        for case in self.browse(cr, uid, ids):
            res[case.id] = 0
            tot_qty = sum([x.product_uos_qty for x in case.move_lines])
            print "tot_qty....", tot_qty
            try:
                res[case.id] = ((case.cf1_amount + case.cf2_amount) / tot_qty)
            except:
                pass
        return res

        
    _columns = {
                'sale_id'     : fields.many2one('sale.order','Sale Order'),
                'sale_type'   : fields.related('sale_id','type', type = 'char', size=128, store = False),
                'user_id'     : fields.many2one("res.users","Delivery Team"),
                'origin_type' : fields.selection([('sample','Sample'),('order','Order')],'Origin Type'),
                #for reporting purpose
                'invoice_id'       : fields.many2one("account.invoice",'Invoice'),
                'account_move_id'  : fields.many2one("account.move", 'Account Move'),
                'country_name'     : fields.related("company_id","country_id","name", type="char", size=64, store=False, string="Country Name"),
#                 'amount_in_words'  : fields.function(_get_amount_words, method=True, string="Amount in Words", type="text", store=True), 

              # For Mexicon Reports
              #Parameters
              'driver_name'             :   fields.char("Driver's Name", size=100),
              'garbage_unit'            :   fields.selection([('ok', 'OK'),('not_ok', 'NOT OK')],"Free Garbage unit, dust or food scraps"),
              'garbage_unit_comments'   :   fields.char("Comments", size=100),
              'aromas_odors'            :   fields.selection([('ok', 'OK'),('not_ok', 'NOT OK')],"Free Unit aromas or odors"),
              'aromas_odors_comments'   :   fields.char("Comments",size=100),
              'pest_vermin'             :   fields.selection([('ok', 'OK'),('not_ok', 'NOT OK')],"Free Unit Pest and vermin"),
              'pest_vermin_comments'    :   fields.char("Comments",size=100),
              'stains_oil'              :   fields.selection([('ok', 'OK'),('not_ok', 'NOT OK')],"Free Unit presence of stains and oils"),
              'stains_oil_comments'     :   fields.char("Comments",size=100),
              'foreign_objects'         :   fields.selection([('ok', 'OK'),('not_ok', 'NOT OK')],"They are not foreign objects unrelated to the load"),
              'foreign_objects_comments':   fields.char("Comments",size=100),
              'humidity_leaks'          :   fields.selection([('ok', 'OK'),('not_ok', 'NOT OK')],"Free Unit humidity, leaks and runoff"),
              'humidity_leaks_comments' :   fields.char("Comments",size=100),
              'product_damaged'         :   fields.selection([('ok', 'OK'),('not_ok', 'NOT OK')],"No product damaged or abused are detected."),
              'product_damaged_comments':   fields.char("Comments",size=100),
              'material_exposed'        :   fields.selection([('ok', 'OK'),('not_ok', 'NOT OK')],"No materials exposed to the environment, in open units is received ."),
              'material_exposed_comments':   fields.char("Comments",size=100),
              
              # Results
              'result'                  :   fields.selection([('approved', 'Approved'),('rejected', 'Rejected')],"RESULTADO RESULT"),
              'no_pedimiento'           :   fields.char("No Pedimiento",size=100),
              'customs'                 :   fields.char("Customs", size=100),
              
              #Documents
              'confirm_certificate'     :   fields.selection([('ok', 'OK'),('not_ok', 'NOT OK')],"Certificate o conformity"),
              'confirm_certificate_comments':   fields.char("Comments",size=100),
              
               #For Mexico Company 
              'is_mexico'               :   fields.function(_get_user_company, type="boolean", string="Is Mexico", store=False),
              'shipping_way'            :   fields.selection([('air', 'Air Way'),('sea', 'Sea Way'),('road', 'By Road')], "Mode of Transport"),
              'cf1_amount'              :   fields.float('CF1',digits=(16,2)),
              'cf2_amount'              :   fields.float('CF2',digits=(16,2),states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
              'cf_unit_price'           :   fields.function(_get_cf_price, digits=(16,2),type="float", store=False, string="CF Per Unit")
              
               
                
                }
    
    _defaults = {
                 'user_id'        :   lambda obj, cr, uid, context: uid,
                 'origin_type'    : 'order', 
                 'is_mexico'      : default_user_company,  
                 }
    
    #Inheritted to update delivery order to false in Sample
    def action_cancel(self, cr, uid, ids, context=None):
        sale_obj = self.pool.get('sale.order')
        res = super(stock_picking,self).action_cancel(cr, uid, ids, context)
        for case in self.browse(cr, uid, ids):
            if case.sale_id:
                sale_obj.write(cr, uid, case.sale_id.id, {'pick_id':False})
        return res
 
 # Inheriting Create Method to update Sale ID in DO
 
#     def create(self, cr, uid, vals, context=None):   
#         sale_obj=self.pool.get('sale.order')
#          
#         sale_ids=[]
#         ref=vals.get('origin','')
#         if ref:
#             ref=str(ref)
#             if ':' in ref:
#                 ref=ref[:ref.index(':')]
#             sale_ids=sale_obj.search(cr,uid,[('name','ilike',ref)])
# 
#         if sale_ids:
#             vals.update({'sale_id':sale_ids[0]})
#             
#         return super(stock_picking,self).create(cr, uid, vals, context)
    
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
       
        report_name = ''
        for case in self.browse(cr, uid, ids):
            if context.get('sample'):
                report_name = 'Sample Form'
                if case.sale_id and case.sale_id.type == 'sample':
                    ids = [case.sale_id.id]
                    context.update({'active_model':'sale.order'})
            else:
                if case.picking_type_id and case.picking_type_id.code == 'incoming':
                    if 'mexico' not in case.company_id.name.lower():
                        report_name = 'Raw Material Reception'
                    else:
                        report_name = 'Mexico Reception'
                    
                if case.picking_type_id and case.picking_type_id.code == 'outgoing':
                    if case.company_id.country_id and 'india' in case.company_id.country_id.name.lower():
                        report_name = 'Delivery Challan'
                    
#                     if case.company_id.country_id and 'mexico' in case.company_id.country_id.name.lower():
#                         report_name = 'Delivery Order'
                        
                    if context.get('proforma'):
                        if case.company_id.country_id and 'indonesia' in case.company_id.country_id.name.lower():
                            if case.sale_id and case.sale_id.type =='sample':
                                report_name = "Proforma Invoice - Sample"
                            else:
                                report_name = "Proforma Invoice"
                        
                        if case.company_id.country_id and 'india' in case.company_id.country_id.name.lower():
                            report_name = "Proforma Invoice India"
        
        if not report_name:
            return True
        data = {}
        data['ids'] = ids
        data['model'] = context.get('active_model', 'stock.picking')
        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'name' : report_name,
        'datas': data,
            }
    
 
    def print_delivery_order(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
       
        report_name = ''
        for case in self.browse(cr, uid, ids):
            if case.company_id.country_id and 'mexico' in case.company_id.country_id.name.lower():
                report_name = 'Delivery Order'
            
            else:
                raise osv.except_osv(_('UserError'), ('Please Print the Correct Report and the selected report is not for this Company.'))            
        
        if not report_name:
            return True
        data = {}
        data['ids'] = ids
        data['model'] = context.get('active_model', 'stock.picking')
        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'name' : report_name,
        'datas': data,
            }
 
    
    
    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, origin, context=None):
        comp_obj = self.pool.get('res.company')
        res = super(stock_picking,self)._get_invoice_vals(cr, uid, key, inv_type, journal_id, origin, context)
        if res.get('company_id'):
            currency_id = comp_obj.browse(cr, uid, res.get('company_id')).currency_id
            res.update({'currency_id': currency_id and currency_id.id or False})
        return res
    
    
    #inheritted to convert service product price to invoice line currency
    def _prepare_shipping_invoice_line(self, cr, uid, picking, invoice, context=None):
        cur_obj = self.pool.get('res.currency')
        res = super(stock_picking, self)._prepare_shipping_invoice_line(cr, uid, picking, invoice, context)
        if res and res.get('price'):
            price = cur_obj.compute(cr, uid, 
                                         invoice.partner_id.property_product_pricelist and  invoice.partner_id.property_product_pricelist.currency_id.id or invoice.currency_id.id,
                                         invoice.currency_id.id, 
                                         res.get('price',0.0), True, context)
            res.update({'price':price})
        return res
    
    def get_label(self, cr, uid, ids, context):
        pack_obj = self.pool.get('stock.pack.operation')
        label = """ 
        ^XA
        ^LL609.6
        """
        for case in self. browse(cr, uid, ids):
            for ln in case.move_lines:
                label += '^FO30,50^ACN,30,10^FD' + ln.product_id.name + ln.product_id.default_code + '^FS \n'
                #label += '^FO28,50^ACN,30,10^FD' + ln.product_id.name + ln.product_id.default_code + '^FS \n'
                #label += '^FO30,52^ACN,30,10^FD' + ln.product_id.name + ln.product_id.default_code + '^FS \n'
                #for bold
                #label += '^FO30,90^ACN,20,10^FD Net Contents :' + str(ln.product_uom_qty) + ' ' +str(ln.product_uom.name).upper() + (ln.product_packaging and (' (' + ln.product_packaging.ul.name +') '+ '^FS \n') or '^FS \n')
                #label += '^FO28,90^ACN,20,10^FD Net Contents :' + str(ln.product_uom_qty) + ' ' +str(ln.product_uom.name).upper() + (ln.product_packaging and (' (' +ln.product_packaging.ul.name +') '+ '^FS \n') or '^FS \n')
                label += '^FO30,92^ACN,20,10^FD Net Contents :' + str(ln.product_uom_qty) + ' ' +str(ln.product_uom.name).upper() + (ln.product_packaging and (' (' +ln.product_packaging.ul.name +') '+ '^FS \n') or '^FS \n')
                
                pack_ids = pack_obj.search(cr, uid, [('product_id','=',ln.product_id.id),('picking_id','=',ln.picking_id.id)], limit=1)
                for p in pack_obj.browse(cr, uid, pack_ids):
                    label += '^FO30,120^ACN,30,10^FD Batch No.' + (p.lot_id and p.lot_id.name or '^FS \n') + '^FS \n'
                    label += '^^FO375,20^BY4^BCN,100,Y,N,Y,N^FD'+(p.lot_id and str(p.lot_id.name) or '')+'^FS \n' 
                    if p.lot_id and p.lot_id.use_date:
                        use_date =(parser.parse(''.join((re.compile('\d')).findall(p.lot_id.use_date)))).strftime('%d/%m/%Y')
                        print "date", use_date
                        label += '^FO30,170^ACN,20,30^FD Best Before Date :'+ (p.lot_id and (p.lot_id.use_date and use_date or '^FS') or '^FS \n') + '^FS \n'
                
                
                # precautions
                label +="""^CF0,30,30
                            ^FO0,170
                            ^FB750,3,1,C
                            ^FDStore Away from sunlight, at an ambient temperature\&
                            in tightly closed original packing\&
                            Avoid Thermal Shocks \& ^FS \n"""
                
                # for manufacturing details
                label +="""^CF0,30,20
                            ^FO40,260
                            ^FB800,6,1,L
                            ^FDManufactured By\&"""
                label += str(ln.company_id.parent_id and ln.company_id.parent_id.name or '') + '\& \n'
                if ln.company_id.parent_id.street:
                    label += ln.company_id.parent_id.street + '\& \n'
                if ln.company_id.parent_id.street2:
                    label += ln.company_id.parent_id.street2 + '\& \n'
                if ln.company_id.parent_id.phone:
                    label += 'Phone :' + ln.company_id.parent_id.phone + '\& \n'
                if ln.company_id.parent_id.fax:
                   label += 'Fax :' + ln.company_id.parent_id.fax + '\& \n'
                   
                # for company  details
                label +="""^FS ^CF0,30,20
                            ^FO60,260
                            ^FB700,6,1,R
                            ^FDImported and Marketed By\&"""
                label += str(ln.company_id and ln.company_id.name or '') + '\& \n'
                if ln.company_id.street:
                    label += ln.company_id.street + '\& \n'
                if ln.company_id.street2:
                    label += ln.company_id.street2 + '\& \n'
                if ln.company_id.phone:
                    label += 'Phone :' + ln.company_id.phone + '\& \n'
                if ln.company_id.fax:
                   label += 'Fax :' + ln.company_id.fax + '\& \n'
             
                
                
                label +="""^CN1
                           ^PN0
                           ^XZ"""
        
        #print "Labellllll," ,label
        return label
    
    
    def do_enter_transfer_details(self, cr, uid, picking, context=None):
        """ Inherited to check whether Quality control has been conducted or not """
        
        context = dict(context or {})
        for case in self.browse(cr, uid, picking):
            if case.picking_type_code == 'internal' :
                for ln in case.move_lines:
                    if ln.location_id.name in ('Quality','quality','Quality Control') :
                        if not ln.quality_id and not ln.no_quality:
                            raise osv.except_osv(_('Warning!'), _(' Create the Quality lines for the product %s with Qty %s') % (ln.product_id.name, ln.product_qty))
                        
                        if ln.quality_id and ln.quality_id.state not in ('approved','quarantine','cancel'):
                            raise osv.except_osv(_('Warning!'), _(' Process the Quality control for %s ') % (ln.quality_id.qc_no))
        
        return super(stock_picking, self).do_enter_transfer_details(cr, uid, picking, context)
 
 
    # Inherit Creating Invoice
    
    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, origin, context=None):
        if context is None:
            context = {}
        invoice_vals = super(stock_picking, self)._get_invoice_vals(cr, uid, key, inv_type, journal_id, origin, context)
        ctx = {}
        for pick in self.browse(cr, uid, context.get('active_ids', [])):
            invoice_vals.update({
                             'mode_of_transport'     : pick.shipping_way and pick.shipping_way or False,
                             })
              
        return invoice_vals
    
    
    def create_entry(self, cr, uid, ids, context=None):
        """ TO create journal entry if there is a sevice product in lines from sale order / Purchase Order for sample"""
        
        context = dict(context or {})
        move_obj = self.pool.get('account.move')
        purchase_obj = self.pool.get('purchase.order')
        today = time.strftime('%Y-%m-%d')
        cur_obj = self.pool.get('res.currency')
        context.update({'date':today})
        journal_obj = self.pool.get('account.journal')
        
        data = []
        total = 0.0
        account_id = False
        
        for case in self.browse(cr, uid, ids):
            journal_ids = journal_obj.search(cr, uid, [('type','=','sale'),('company_id','=', case.company_id.id)], limit = 1)
            # for customer Invoice 
            for ln in case.sale_id.order_line:
                 # to create the lines if the product_type is service
                 if ln.product_id.type == 'service':
                     amount = cur_obj.compute(cr, uid, ln.currency_id.id, case.company_id.currency_id.id, ln.price_unit,True, context)
                     data.append({
                                  'uos_id' : ln.product_uos and ln.product_uos.id or False,
                                  'product_id' : ln.product_id.id,
                                  'partner_id' : case.partner_id.id,
                                  'ref' : case.name,
                                  'currency_id' : False,
                                  'account_id' : ln.product_id.property_account_income or ln.product_id.categ_id.property_account_income_categ.id,
                                  'quantity': ln.product_uom_qty, 
                                  'type': 'src', 
                                  'price': amount ,
                                  'name': ln.name,
                                  'credit' : (amount * ln.product_uom_qty)
                                  })
                     total += (amount * ln.product_uom_qty)
            
            
            # for supplier Invoice
            if not case.sale_id:
                journal_ids = journal_obj.search(cr, uid, [('type','=','purchase'),('company_id','=', case.company_id.id)], limit = 1)
                p_ids = purchase_obj.search(cr, uid, [('name','=',case.origin)])
                for p in purchase_obj.browse(cr ,uid, p_ids):
                    total = 0.0
                    for ln in p.order_line:
                        if ln.product_id.type == 'service':
                            amount = cur_obj.compute(cr, uid, ln.currency_id.id, case.company_id.currency_id.id, ln.price_unit,True, context)
                            data.append({
                                      'uos_id' :  False,
                                      'product_id' : ln.product_id.id,
                                      'partner_id' : case.partner_id.id,
                                      'ref' : case.name,
                                      'currency_id' : False,
                                      'account_id' : ln.product_id.categ_id.property_account_expense_categ and ln.product_id.categ_id.property_account_expense_categ.id or False,
                                      'quantity': ln.product_qty, 
                                      'type': 'src', 
                                      'price': amount ,
                                      'name': ln.name,
                                      'debit' : (amount * ln.product_qty)
                                      })
                            total += (amount * ln.product_qty)
                
                
            
            if data:
                # finding the account_id's based on customer and supplier
                if case.sale_id:
                    account_id = case.partner_id.property_account_receivable and case.partner_id.property_account_receivable.id or False
                else:
                    account_id = case.partner_id.property_account_receivable and case.partner_id.property_account_payable.id or False
                #Destination line
                data.append({
                             'currency_id': False, 
                             'date_maturity': case.date, 
                             'name': '/', 
                             'ref': False, 
                             'amount_currency': False, 
                             'price': total, 
                             'type': 'dest',
                             'account_id' : account_id 
                             })
               
                    
                
                line = [(0, 0, l) for l in data] # formating according to one2many options
                
                # main move vals
                move_vals = {
                    'ref': case.name,
                    'line_id': line,
                    'journal_id': journal_ids and journal_ids[0] or False,
                    'date': case.date,
                    'narration': '',
                    'company_id': case.company_id.id,
                    'name' : case.name
                }
                
                # updating the company_id to get period based on current_date 
                context.update({'company_id' : case.company_id.id})
                
                period = self.pool.get('account.period').find(cr, uid,case.date, context)[:1]
                if period:
                    move_vals['period_id'] = period[0]
                    for i in line:
                        i[2]['period_id'] = period[0]
                
                move = move_obj.create(cr, uid, move_vals, context)
                move_obj.post(cr, uid, move, context)
                self.write(cr, uid, [case.id], {'account_move_id': move}) 
            
        return True
       
    #inheritted to remove the account move associated with picking
    def action_cancel(self, cr, uid, ids, context=None):
        acc_move_obj = self.pool.get('account.move')
        res = super(stock_picking, self).action_cancel(cr, uid, ids, context)
        for case in self.browse(cr, uid, ids):
            if case.account_move_id:
                acc_move_obj.button_cancel(cr, uid, [case.account_move_id.id], context)
                acc_move_obj.unlink(cr, uid, [case.account_move_id.id], context)
        return res
    

    
    def send_mails(self, cr, uid, case, template_name, context=None):
        """ TO send mails """
        
        mail_obj = self.pool.get('mail.mail')
        partner_obj = self.pool.get('res.partner')
        
        
        template = self.pool.get('ir.model.data').get_object(cr, uid, 'prova', template_name)
        assert template._name == 'mail.template'
        
        emails = ''
        if template_name == 'perform_quality_send_mail':
                
                # to get the emails of sales manager based on company
                sql_str = """select distinct rp.email
                                    from res_groups_users_rel gu 
                                    inner join res_groups g on g.id = gu.gid
                                    inner join res_users ru on ru.id = gu.uid
                                    inner join res_partner rp on rp.id = ru.partner_id
                                    where g.name in ('Manager','User')
                                    and rp.email is not null
                                    and rp.company_id = """+ str(case.company_id.id) +"""
                                    and g.category_id = (select id from ir_module_category where name = 'Quality Control')"""
        
        if  template_name == 'create_invoice_send_mail':   
            
            # to get the emails of Accounting Manager
            sql_str = """select distinct rp.email
                                from res_groups_users_rel gu 
                                inner join res_groups g on g.id = gu.gid
                                inner join res_users ru on ru.id = gu.uid
                                inner join res_partner rp on rp.id = ru.partner_id
                                where g.name in ('Accountant','Financial Manager','Invoicing & Payments')
                                and rp.email is not null
                                and rp.company_id = """+ str(case.company_id.id) +"""
                                and g.category_id = (select id from ir_module_category where name = 'Accounting & Finance')"""
                
        cr.execute(sql_str)        
        for email in cr.fetchall():
             
            #to eliminate duplicate emails address
            if email[0] not in emails:
                emails += email[0] + ','
            
            if emails:
                vals = {
                        'email_to' : emails[:-1]
                        }
            else:
                vals.update({'email_to':case.user_id and case.user_id.email})
        
            if case.user_id and case.user_id.email:
                vals.update({'email_cc':case.user_id.email})
            self.pool.get('mail.template').write(cr, uid, template.id, vals)
        

        mail_id = self.pool.get('mail.template').send_mail(cr, uid, template.id, case.id, True, context=context)
        mail_state = mail_obj.read(cr, uid, mail_id, ['state'], context=context)
        if mail_state and mail_state['state'] == 'exception':
            raise osv.except_osv(_("Cannot send email: no outgoing email server configured.\nYou can configure it under Settings/General Settings."), partner.name)
        return True
            

stock_picking()

class stock_move(osv.osv):
    _inherit = 'stock.move'
     #_order = 'date_expected desc, id' Standard
    _order = 'id asc'
    
    def _get_location_status(self, cr, uid, ids, field_name, args, context=None):
        """ To get the status of source location to control button visibility """
        
        res = {}
        count = 0
        for case in self.browse(cr, uid, ids):
            if case.location_id.name in ('Quality','quality','Quality Control') :
                res[case.id] = True
                if case.picking_type_id and case.picking_type_id.code == 'incoming':
                    if case.quality_id :
                        res[case.id] = False
                    else:
                        res[case.id] = True
                
# TODO : Uncomment if it is required for Delivery order 
#                 if case.picking_type_id and case.picking_type_id.code == 'outgoing':
#                     if case.quality_ids:
#                         count = self.pool.get('quality.control').search_count(cr, uid, [('move_id','=',case.id)], context=context)
#                         if count <3:
#                             res[case.id] = True
#                         else:
#                             res[case.id] = False
                
            else:
                res[case.id] = False
        print "res..............", res, case.location_id.name 
        return res
    
    def get_visibility(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for case in self.browse(cr, uid, ids):
            res[case.id] = False
            if case.company_id and 'india' in case.company_id.name.lower() and case.picking_type_id.code == 'incoming':
                res[case.id] = True
        return res 
    
    def _get_cf_price(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        context = dict(context or {})
        for case in self.browse(cr, uid, ids):
            res[case.id] = {
                            'cf_unit_price'  : 0,
                            'cf_total_amount' :0
                            }
            if case.picking_id:
                res[case.id].update({
                                     'cf_unit_price' : case.picking_id.cf_unit_price,
                                     'cf_total_amount' : round(case.picking_id.cf_unit_price * case.product_uos_qty),
                                     })
        return res
        
    _columns = {
                'quality_id'   : fields.many2one('quality.control','Quality Control'),
                'quality_ids'  : fields.one2many('quality.control','move_id','Quality Lines'),
                
                #to control visibility of Quality Control Button for incoming / delivery
                'quality_visible' : fields.function(_get_location_status, type="boolean", string='Visible', store=False),
                
                'dilution_id'         : fields.many2one('mrp.bom.dilution','Dilution'),
                'product_qty_kg'      : fields.float('Product Quantity / Kg ',digits=(16,3)),
               # 'production_line_id'  : fields.many2one('mrp.production.product.line','Line Id'),
                
                # To save BARCODE
                'code'              : fields.char('Code'),
                
                'tariff_no'         : fields.char('Tariff No', size=32), 
                'tot_excise'        : fields.float('Total assessable value',digits=(16,2)),
                'duty_per'          : fields.float('Duty (%)',digits=(16,2)),
                'duty_amount'       : fields.float('Duty Amount',digits=(16,2)),
                'eduty_per_unit'     : fields.float('Excise Duty Per Unit',digits=(16,2)), 
                'excise_per'        : fields.float('Excise (%)',digits=(16,2)),
                'excise_amount'     : fields.float('Excise Amount',digits=(16,2)),
                'cess_per'          : fields.float('Cess (%)',digits=(16,2)),
                'cess_amount'       : fields.float('Cess Amount',digits=(16,2)),
                'hcess_per'         : fields.float('Hcess (%)',digits=(16,2)),
                'hcess_amount'      : fields.float('Hcess Amount',digits=(16,2)),
                'aed_per'           : fields.float('AED (%)',digits=(16,2)),
                'aed_amount'        : fields.float('AED Amount',digits=(16,2)),
                'aduty_per_unit'     : fields.float('AED Duty Per Unit',digits=(16,2)), 
                
                'excise_visible'    : fields.function(get_visibility, type="boolean", store=False, string = 'Visible'),
                'no_quality'        : fields.boolean('Without Quality'),
                'total_amount'      : fields.float('Total Excise Amount',digits=(16,2)), 
                
                'cf_unit_price'     : fields.function(_get_cf_price, digits=(16,2),type="float", store=False, string="CF Per Unit", multi="all"),
                'cf_total_amount'   : fields.function(_get_cf_price, digits=(16,2),type="float", store=False, string="Total CF Amount", multi="all"),
                
                
                # For RMC report
                'sup_weight'        : fields.float("Gross Weight", digits=(16,2)),
                'sup_net_weight'    : fields.float("Net Weight", digits=(16,2)),

                'cmp_weight'        : fields.float("Gross Weight", digits=(16,2)),
                'cmp_net_weight'    : fields.float("Net Weight", digits=(16,2)),
                
                
 
 
                }
    _defaults = {
                 'duty_per'    :  10.0,
                 'excise_per'  :  12.5,
                 'cess_per'    :  2.0,
                 'hcess_per'   :  1.0,
                 'aed_per'     :  4.0,
                 'excise_visible' : True
                 }
    
    def onchange_company_id(self, cr, uid, ids, company_id):
        res = {}
        comp_obj = self.pool.get('res.company')
        if company_id:
            comp = comp_obj.browse(cr, uid, company_id)
            if 'india' in comp.name.lower():
                res['excise_visible'] = True
            else:
                res['excise_visible'] = False
    
    def onchange_excise(self, cr, uid, ids, qty, tot_excise, duty_per = 0.0, excise_per = 0.0, cess_per = 0.0, hcess_per = 0.0, aed_per = 0.0 , context = None):
        res = {}
        
        # to convert the amount to percentage
        duty_per = duty_per and (duty_per / 100.0) or 0.0
        excise_per = excise_per and (excise_per / 100.0) or 0.0
        cess_per = cess_per and (cess_per / 100.0) or 0.0
        hcess_per = hcess_per and (hcess_per / 100.0) or 0.0
        aed_per = aed_per and (aed_per / 100.0) or 0.0
        
        
        if duty_per and tot_excise:
            res['duty_amount'] = round((tot_excise * duty_per),2)
            
        
        if not duty_per:
            res['duty_amount'] = 0.0
            
                        
        
        if excise_per and tot_excise :
            res['excise_amount'] = round((res.get('duty_amount', 0.0) + tot_excise) * excise_per, 2)  or 0.0
            res['eduty_per_unit'] = (qty and (res['excise_amount'] / qty) or 0 )
            
        if not excise_per:
            res.update({'excise_amount': 0.0 , 'duty_per_unit' :0.0 })
        
        if cess_per and tot_excise :
            res['cess_amount'] = round((res.get('excise_amount',0.0) + res.get('duty_amount',0.0)) * cess_per, 2)
        
        if not cess_per:
            res['cess_amount'] = 0.0
        
        if hcess_per and tot_excise :
            res['hcess_amount'] = round((res.get('excise_amount', 0.0) + res.get('duty_amount', 0.0)) * hcess_per , 2)
        
        if not hcess_per:
            res['hcess_amount'] = 0.0
        
        if aed_per and tot_excise :
            res['aed_amount'] = round(((res.get('duty_amount', 0.0) + tot_excise) + res.get('excise_amount', 0.0) 
                                       + res.get('cess_amount',0.0) + res.get('hcess_amount',0.0)) * aed_per , 2)
            
            res['aduty_per_unit'] = qty and res['aed_amount'] / qty or 0
        
        if not aed_per:
            res['aed_amount'] = 0.0 
            res['aduty_per_unit'] = 0.0                  
        
        res.update({
                    'total_amount'   :  res.get('duty_amount', 0.0) +  res.get('excise_amount', 0.0) 
                                        + res.get('cess_amount', 0.0) + res.get('hcess_amount', 0.0) + res.get('aed_amount', 0.0)
                    })
          
            
        return {'value' :res}
    
    def but_create_quality(self, cr, uid, ids, context=None):
        """ TO Create the Quality Control Record from Incoming shipment / Delivery Order 
        @returns : wizard to Fill the quality ccontrol data
        """
        
        ir_model_data = self.pool.get('ir.model.data')
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'prova', 'qc_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        for case in self.browse(cr, uid, ids):
            ctx.update({'default_move_id':case.id})
            if case.picking_id:
                ctx.update({'default_partner_id' : case.picking_id.partner_id and case.picking_id.partner_id.id or False })
            if case.product_id:
                ctx.update({'default_product_id': case.product_id and case.product_id.id or False})
        
        
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'quality.control',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target'   : 'new',
            'context'  : ctx,
            'flags': {'form': {'action_buttons': True}},
          }
    
    #overidden to show the warning
    def action_assign(self, cr, uid, ids, context=None):
        """ Checks the product type and accordingly writes the state.
        """
        warn_obj = self.pool.get('warning')
        context = context or {}
        products = " "
        quant_obj = self.pool.get("stock.quant")
        to_assign_moves = []
        main_domain = {}
        todo_moves = []
        operations = set()
        for move in self.browse(cr, uid, ids, context=context):
            
            # to update the locations when check availability is called
            if move.raw_material_production_id and move.location_id.id != move.raw_material_production_id.location_src_id.id:
                self.write(cr, uid, [move.id], {'location_id' : move.raw_material_production_id.location_src_id.id})
                
            if move.state not in ('confirmed', 'waiting', 'assigned'):
                continue
            if move.location_id.usage in ('supplier', 'inventory', 'production'):
                to_assign_moves.append(move.id)
                #in case the move is returned, we want to try to find quants before forcing the assignment
                if not move.origin_returned_move_id:
                    continue
            if move.product_id.type == 'consu':
                to_assign_moves.append(move.id)
                continue
            else:
                todo_moves.append(move)

                #we always keep the quants already assigned and try to find the remaining quantity on quants not assigned only
                main_domain[move.id] = [('reservation_id', '=', False), ('qty', '>', 0)]

                #if the move is preceeded, restrict the choice of quants in the ones moved previously in original move
                ancestors = self.find_move_ancestors(cr, uid, move, context=context)
                if move.state == 'waiting' and not ancestors:
                    #if the waiting move hasn't yet any ancestor (PO/MO not confirmed yet), don't find any quant available in stock
                    main_domain[move.id] += [('id', '=', False)]
                elif ancestors:
                    main_domain[move.id] += [('history_ids', 'in', ancestors)]

                #if the move is returned from another, restrict the choice of quants to the ones that follow the returned move
                if move.origin_returned_move_id:
                    main_domain[move.id] += [('history_ids', 'in', move.origin_returned_move_id.id)]
                for link in move.linked_move_operation_ids:
                    operations.add(link.operation_id)
        # Check all ops and sort them: we want to process first the packages, then operations with lot then the rest
        operations = list(operations)
        operations.sort(key=lambda x: ((x.package_id and not x.product_id) and -4 or 0) + (x.package_id and -2 or 0) + (x.lot_id and -1 or 0))
        for ops in operations:
            #first try to find quants based on specific domains given by linked operations
            for record in ops.linked_move_operation_ids:
                move = record.move_id
                if move.id in main_domain:
                    domain = main_domain[move.id] + self.pool.get('stock.move.operation.link').get_specific_domain(cr, uid, record, context=context)
                    qty = record.qty
                    if qty:
                        quants = quant_obj.quants_get_prefered_domain(cr, uid, ops.location_id, move.product_id, qty, domain=domain, prefered_domain_list=[], restrict_lot_id=move.restrict_lot_id.id, restrict_partner_id=move.restrict_partner_id.id, context=context)
                        quant_obj.quants_reserve(cr, uid, quants, move, record, context=context)
        for move in todo_moves:
            if move.linked_move_operation_ids:
                continue
            move.refresh()
            #then if the move isn't totally assigned, try to find quants without any specific domain
            if move.state != 'assigned':
                print "domain............", main_domain[move.id]
                qty_already_assigned = move.reserved_availability
                qty = move.product_qty - qty_already_assigned
                quants = quant_obj.quants_get_prefered_domain(cr, uid, move.location_id, move.product_id, qty, domain=main_domain[move.id], prefered_domain_list=[], restrict_lot_id=move.restrict_lot_id.id, restrict_partner_id=move.restrict_partner_id.id, context=context)
                quant_obj.quants_reserve(cr, uid, quants, move, context=context)
                
                
                # to show the warning
#                 if context.get('manufacture'):
                # to show warning when product not in the stock.
                #Added to check qty only for individual moves and not for linked moves
                if not ancestors:
                    for q in quants:
                        print "Qaunts.........", q
                        if not q[0]:
                            #products += move.product_id.name + " \n "
                            raise osv.except_osv(_('Warning!'), _(' Quantity "%s" : for Product  "%s". is not in stock') % (move.product_qty, move.product_id.name))
                     

        #force assignation of consumable products and incoming from supplier/inventory/production
        if to_assign_moves:
            self.force_assign(cr, uid, to_assign_moves, context=context)
        
      
    #inheritted
    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        pick_obj = self.pool.get("stock.picking")
        pack_obj = self.pool.get("stock.pack_operation")
        
        currency_id = move.company_id.currency_id.id 
        res = super(stock_move, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context)
        
        if move.purchase_line_id:
            currency_id = move.purchase_line_id.currency_id.id
        elif move.procurement_id.sale_line_id:
            currency_id = move.procurement_id.sale_line_id.currency_id.id
            
        
        res.update({
                    'currency_id' : currency_id, 
                    'custom_duty' : move.total_amount or False,
                    })
        return res
    
    
    # overidden to control creating of MO based on user configuration
    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        @return: List of ids.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        states = {
            'confirmed': [],
            'waiting': []
        }
        to_assign = {}
        for move in self.browse(cr, uid, ids, context=context):
            self.attribute_price(cr, uid, move, context=context)
            state = 'confirmed'
            #if the move is preceeded, then it's waiting (if preceeding move is done, then action_assign has been called already and its state is already available)
            if move.move_orig_ids:
                state = 'waiting'
            #if the move is split and some of the ancestor was preceeded, then it's waiting as well
            elif move.split_from:
                move2 = move.split_from
                while move2 and state != 'waiting':
                    if move2.move_orig_ids:
                        state = 'waiting'
                    move2 = move2.split_from
            states[state].append(move.id)

            if not move.picking_id and move.picking_type_id:
                key = (move.group_id.id, move.location_id.id, move.location_dest_id.id)
                if key not in to_assign:
                    to_assign[key] = []
                to_assign[key].append(move.id)

        for move in self.browse(cr, uid, states['confirmed'], context=context):
            if move.procure_method == 'make_to_order':
                self._create_procurement(cr, uid, move, context=context)
                print "line_id and move",move.procurement_id.sale_line_id , move.id
                states['waiting'].append(move.id)
                states['confirmed'].remove(move.id)
                    
#                     if move.procurement_id.sale_line_id.create_mo :
#                         self._create_procurement(cr, uid, move, context=context)
#                         states['waiting'].append(move.id)
#                         states['confirmed'].remove(move.id)
#                 else:
#                     self._create_procurement(cr, uid, move, context=context)
#                     states['waiting'].append(move.id)
#                     states['confirmed'].remove(move.id)

        for state, write_ids in states.items():
            if len(write_ids):
                self.write(cr, uid, write_ids, {'state': state})
        #assign picking in batch for all confirmed move that share the same details
        for key, move_ids in to_assign.items():
            procurement_group, location_from, location_to = key
            self._picking_assign(cr, uid, move_ids, procurement_group, location_from, location_to, context=context)
        moves = self.browse(cr, uid, ids, context=context)
        self._push_apply(cr, uid, moves, context=context)
        return ids
    
    
    def _prepare_procurement_from_move(self, cr, uid, move, context=None):
        res = super(stock_move, self)._prepare_procurement_from_move(cr, uid, move, context=context)
        if move.procurement_id and move.procurement_id.sale_line_id:
            res['sale_line_id'] = move.procurement_id.sale_line_id.id
        return res
    
    
    def create(self, cr, uid, vals, context=None):
        vals.update(self.onchange_excise(cr, uid, [],vals.get('product_uos_qty',0) ,vals.get('tot_excise',0), vals.get('duty_per',0.0), 
                             vals.get('excise_per', 0.0), vals.get('cess_per', 0.0), vals.get('hcess_per', 0.0), 
                             vals.get('aed_per', 0.0) , context)['value'])
        return super(stock_move,self).create(cr, uid, vals, context)
    
    def write(self, cr, uid, ids, vals, context=None):
        for case in self.browse(cr, uid, ids):
            vals.update(self.onchange_excise(cr, uid, [], vals.get('product_uos_qty',case.product_uos_qty), vals.get('tot_excise',case.tot_excise), vals.get('duty_per',case.duty_per), 
                             vals.get('excise_per', case.excise_per), vals.get('cess_per', case.cess_per), vals.get('hcess_per', case.hcess_per), 
                             vals.get('aed_per', case.aed_per) , context)['value'])
        
        return super(stock_move,self).write(cr, uid, ids, vals, context) 

 
stock_move()

class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'
    
    def _get_sequence(self, cr, uid, ids, context=None):
        """ To give the current year,month and date as sequence"""
        data = str(time.strftime('%y')) + str(time.strftime('%m')) + str(time.strftime('%d'))
        return data
    
    _columns = {
                'name': fields.char('Serial Number', required=True, help="Unique Lot / Serial Number, format : yymmdd \n for ex : if the date is 2015-05-01 then the number will be \n 150501",track_visibility='onchange'),
                'ref': fields.char('Internal Reference', help="Internal reference number in case it differs from the manufacturer's serial number",track_visibility='onchange'),
                'product_id': fields.many2one('product.product', 'Product', required=True, domain=[('type', '<>', 'service')],track_visibility='onchange'),
                'quant_ids': fields.one2many('stock.quant', 'lot_id', 'Quants', readonly=True,track_visibility='onchange'),
                'create_date': fields.datetime('Creation Date',track_visibility='onchange'),                
                }
    
    _defaults = {
        'name': _get_sequence,
        }
    
    def onchange_name(self, cr, uid, ids, name, context=None):
        res = {}
        warning = {}
        
        if name:
            if len(name) > 6:
                warning = {
                           'title': ('Warning'),
                           'message' : 'Invalid lot / serial number ! Please enter less then 9 numbers'
                        }
                res['name'] = ''
        return {'value':res , 'warning': warning }
    

stock_production_lot()

class stock_quant(osv.osv):
    _inherit = "stock.quant"
    
    _columns = {
                # to update the unit cost price in quants for valuation
                'cost_price'  : fields.related('product_id','standard_price', type='float', string='Cost Price')
                }
stock_quant()

class stock_inventory_line(osv.osv):
    _inherit = "stock.inventory.line"
    
    _columns = {
                'barcode'    : fields.char('Barcode', size=16),
                'prod_db_id' : fields.related('product_id','id', type='integer', store=False, string="Product Id"),
                }
stock_inventory_line()
    
    
    


        