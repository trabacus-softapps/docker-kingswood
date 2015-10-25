from openerp.osv import fields,osv
from openerp.tools.translate import _
from lxml import etree
from openerp import tools
import math
import time
from datetime import datetime

import amount_to_text_softapps
import random
from openerp.report import report_sxw
from openerp import pooler


class kw_refund(osv.osv_memory):
    _name = 'kw.refund'
    _columns = {
                'pdb_rejection_qty'        : fields.float('Pdb Rejection Quantity',digits=(0,3)),
                'normal_rejection_qty'     : fields.float('Normal Rejection Quantity',digits=(0,3)),
                'amount'                   : fields.float('Amount'),

                }
    def refund_save(self, cr, uid, ids, context =None ):
        inv_vals = {}
        inv_line_vals = {}
        
        picking_obj = self.pool.get('stock.picking.out')
        mv_obj = self.pool.get('stock.move')
        inv_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.journal')
        inv_ln_obj = self.pool.get('account.invoice.line')
        
        qty = 0
        for case in self.browse(cr, uid, ids):
            
            journal_id = journal_obj.search(cr, uid, [('type','=','purchase_refund')])[0]
            if (case.pdb_rejection_qty and case.normal_rejection_qty) or (not case.pdb_rejection_qty and not case.normal_rejection_qty):
                raise osv.except_osv(_('Warning'),_('You Should Either Enter PDB or Normal Quantity'))
            if not case.amount:
                raise osv.except_osv(_('Warning'),_('Enter the Amount'))
            
            
            for do in picking_obj.browse(cr, uid, context.get('active_ids',False)):
                # for creating Paying Agents Refund
                for ln in do.move_lines:
                    qty = case.pdb_rejection_qty and case.pdb_rejection_qty or case.normal_rejection_qty
                    inv_vals={'partner_id' : ln.supplier_id.partner_id.id,
                              'type'       : 'in_refund',
                              'journal_id' : journal_id,
                              'date_invoice':datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                              'date_due':datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                              'origin':do.name,
                    }
                    inv_vals.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_refund',ln.supplier_id.partner_id.id)['value'])
                    inv_line_vals.update(inv_ln_obj.product_id_change( cr, uid, ids, ln.product_id.id, ln.product_uom, qty=0, name='', type='in_refund', partner_id=ln.supplier_id.partner_id.id, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None))
                    inv_line_vals = {'product_id' : ln.product_id.id,
                                     'name'       : ln.name,
                                     'quantity'   : qty,
                                     'price_unit' : (case.amount / qty),
                                     'uos_id'     : ln.product_uom.id, 
                                     }
                    inv_vals.update({
                                                   
                                                  'invoice_line': [(0,0, inv_line_vals)],
                                    }) 
                    inv_obj.create(cr, uid, inv_vals)
                    mv_obj.write(cr, uid, [ln.id],{'pdb_qty':case.pdb_rejection_qty and case.pdb_rejection_qty or ln.pdb_qty,
                                                   'rejected_qty':case.normal_rejection_qty and case.normal_rejection_qty or ln.rejected_qty
                                                   },context = context)
                    
                    
                    # for creating customer Refund
                    inv_vals1 = {}
                    inv_line_vals1 = {}
                    journal_id1 = journal_obj.search(cr, uid, [('type','=','sale_refund')])[0]
                    inv_vals1={'partner_id' : do.partner_id.id,
                              'type'       : 'out_refund',
                              'journal_id' : journal_id1,
                              'date_invoice':datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                              'date_due':datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                              'origin':do.name,
                    }
                    inv_vals1.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_refund',do.partner_id.id)['value'])
                    inv_line_vals1.update(inv_ln_obj.product_id_change( cr, uid, ids, ln.product_id.id, ln.product_uom, qty=0, name='', type='out_refund', partner_id=do.partner_id.id, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None))
                    inv_line_vals1 = {'product_id' : ln.product_id.id,
                                     'name'       : ln.name,
                                     'quantity'   : qty,
                                     'price_unit' : (case.amount / qty),
                                     'uos_id'     : ln.product_uom.id, 
                                     }
                    inv_vals1.update({
                                                   
                                                  'invoice_line': [(0,0, inv_line_vals1)],
                                    }) 
                    inv_obj.create(cr, uid, inv_vals1)
                     
                    
        return True
kw_refund()

class kw_invoice(osv.osv_memory):
    _name = 'kw.invoice'
    _columns = {
                'product_rate'      : fields.float('Transport Rate',digits=(0,3)),
                'freight_rate'      : fields.float('Handling Rate',digits=(0,3)),
                'unit_price'        : fields.float('Unit Price',digits=(0,3)),
                'qty_txt'           :   fields.char('Quantity text'),
                'amt_txt'           :   fields.char('Total text'),
                'product_order'            : fields.char('TRANSPORTATION BILL No.'),
                'handling_order'            : fields.char('HANDLING & OTHER CHARGES BILL No.'),                
                }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        cust=False
        sup=False
        inv_obj = self.pool.get('account.invoice')
        move=self.pool.get('stock.move')
        res = super(kw_invoice, self).default_get(cr, uid, fields, context=context)
        move_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
        prod = self.pool.get('account.invoice')
        for inv in inv_obj.browse(cr, uid, move_ids, context=context):
            if inv.type=='out_invoice':
                res.update(freight_rate=inv.freight_rate)
                res.update(product_rate=inv.product_rate)
                if inv.product_order:
                    res.update(product_order=inv.product_order)
                if inv.handling_order:
                    res.update(handling_order=inv.handling_order)                    
                for lines in inv.invoice_line: 
                    res.update(unit_price=lines.price_unit)
  
        return res
    
    def print_invoice(self, cr, uid, ids, context =None ):
        inv_vals = {}
        inv_line_vals = {}
        if not context:
            context={}
        rep_obj = self.pool.get('ir.actions.report.xml')
        picking_obj = self.pool.get('stock.picking.out')
        mv_obj = self.pool.get('stock.move')
        inv_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.journal')
        inv_ln_obj = self.pool.get('account.invoice.line')
        qty = 0
        unit_price=0
        line_price=0
        list={}
        inv_ids=context.get('active_ids',[])

        res={}
        res1={}
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment') 

#         os.makedirs('/home/serveradmin/Desktop/temp')
        for case in self.browse(cr, uid, ids):
             
            for inv in inv_obj.browse(cr,uid,inv_ids):
                unit_price=case.product_rate+case.freight_rate
                if inv.product_rate and case.freight_rate:
                    unit_price=inv.product_rate+case.freight_rate
                if inv.freight_rate and case.product_rate:
                    unit_price=inv.freight_rate+case. product_rate                
                if unit_price>0:
                    for line in inv.invoice_line:
                        line_price=line.price_unit
            
                if not unit_price>line_price:
    #                 inv_obj.write(cr,uid,[inv.id],{'product_rate':case.product_rate,'freight_rate' :case.freight_rate})
                    cr.execute("update account_invoice set product_rate=%s where id=%s",(case.product_rate,inv.id,))
                    cr.execute("update account_invoice set freight_rate=%s where id=%s",(case.freight_rate,inv.id,))
                    if case.product_order:
                        cr.execute("update account_invoice set product_order=%s where id=%s",(case.product_order,inv.id,))
                    if case.handling_order:
                        cr.execute("update account_invoice set handling_order=%s where id=%s",(case.handling_order,inv.id,))                        
                    print "product_rate",inv.product_rate
                    print "freight_rate",inv.freight_rate
                    context.update({'product_rate':case.product_rate,'freight_rate' :case.freight_rate})
                    
                    
                    
                    res = rep_obj.pentaho_report_action(cr, uid, 'Transport Invoice For ITC', inv_ids,None,None)
                    res2 = rep_obj.pentaho_report_action(cr, uid, 'Handling Invoice For ITC', inv_ids,None,None)
#                     return inv_obj.print_inv_lr(cr,uid,[inv.id])
#                     self.print_Transport(cr, uid, ids, context)
#                     self.print_Transport(cr, uid, ids, context)
                    list.update({'res':res.values(),
                                 'res1':res2.values()
                                 
                                 })
        
                    
        return res2 and res

    def print_Transport(self, cr, uid, ids, context =None ):
        inv_vals = {}
        inv_line_vals = {}
        if not context:
            context={}
        rep_obj = self.pool.get('ir.actions.report.xml')
        picking_obj = self.pool.get('stock.picking.out')
        mv_obj = self.pool.get('stock.move')
        inv_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.journal')
        inv_ln_obj = self.pool.get('account.invoice.line')
        qty = 0
        unit_price=0
        line_price=0
        list={}
        inv_ids=context.get('active_ids',[])
        qty_txt=''
        res={}
        res1={}
        data = {}
        data2 ={}
        cur_qtxt=''
        cur_txt=''
        amt=''
        amt_txt=''
        attachment_obj = self.pool.get('ir.attachment') 
       
        for case in self.browse(cr, uid, ids):

            for inv in inv_obj.browse(cr,uid,inv_ids):
                cur_qtxt=case.qty_txt
                cur_txt=case.amt_txt
                unit_price=case.product_rate+case.freight_rate
                if inv.product_rate and case.freight_rate:
                    unit_price=inv.product_rate+case.freight_rate
                if inv.freight_rate and case.product_rate:
                    unit_price=inv.freight_rate+case. product_rate                
                if unit_price>0:
                    for line in inv.invoice_line:
                        line_price=line.price_unit
                        qty=+(line.quantity)
                        
                if qty>0:
                    qty_txt = amount_to_text_softapps._100000000_to_text(int(round(qty)))    
                    amt=qty*case.product_rate 
                if amt>0:       
                    amt_txt = amount_to_text_softapps._100000000_to_text(int(round(amt)))          
                               
                if not unit_price>line_price:
    #                 inv_obj.write(cr,uid,[inv.id],{'product_rate':case.product_rate,'freight_rate' :case.freight_rate})
                    cr.execute("update account_invoice set product_rate=%s where id=%s",(case.product_rate,inv.id,))
                    cr.execute("update account_invoice set freight_rate=%s where id=%s",(case.freight_rate,inv.id,))
#                     cr.execute("update account_invoice set qty_txt=%s where id=%s",(qty_txt,inv.id,))
                    cr.execute("update account_invoice set amt_txt=%s where id=%s",(amt_txt,inv.id,))
                    print "product_rate",inv.product_rate
                    print "freight_rate",inv.freight_rate
                    context.update({'product_rate':case.product_rate,'freight_rate' :case.freight_rate})
                    
                    res = rep_obj.pentaho_report_action(cr, uid, 'Transport Invoice For ITC', inv_ids,None,None)
                else:
                    raise osv.except_osv(_('Warning'),_('Enter the Valid Amount'))
        

#             cr.execute("update account_invoice set qty_txt=%s where id=%s",(cur_qtxt,inv.id,))
#             cr.execute("update account_invoice set amt_txt=%s where id=%s",(cur_txt,inv.id,))
        return res
    
    def print_Handling(self, cr, uid, ids, context =None ):
        inv_vals = {}
        inv_line_vals = {}
        if not context:
            context={}
        rep_obj = self.pool.get('ir.actions.report.xml')
        picking_obj = self.pool.get('stock.picking.out')
        mv_obj = self.pool.get('stock.move')
        inv_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.journal')
        inv_ln_obj = self.pool.get('account.invoice.line')
        qty = 0
        unit_price = freight_amt =0
        line_price=0
        list={}
        inv_ids=context.get('active_ids',[])
        qty_txt=''
        res={}
        res1={}
        data = {}
        data2 ={}
        cur_qtxt=''
        cur_txt=''
        amt=''
        amt_txt=''
        attachment_obj = self.pool.get('ir.attachment') 
        cust=[]
        freight_amt_txt = ''
        for case in self.browse(cr, uid, ids):
             
            for inv in inv_obj.browse(cr,uid,inv_ids):
                unit_price=case.product_rate+case.freight_rate
#                 if inv.product_rate and case.freight_rate:
#                     unit_price=inv.product_rate+case.freight_rate
#                 if inv.freight_rate and case.product_rate:
#                     unit_price=inv.freight_rate+case. product_rate 

                cr.execute("select id from res_partner where lower(name) like 'i.t.c%'")
                cust=[x[0] for x in cr.fetchall()]  
                for line in inv.invoice_line:
                    line_price=line.price_unit
                    if not unit_price>line_price:
        #                 inv_obj.write(cr,uid,[inv.id],{'product_rate':case.product_rate,'freight_rate' :case.freight_rate})
                        cr.execute("update account_invoice set product_rate=%s where id=%s",(case.product_rate,inv.id,))
                        cr.execute("update account_invoice set freight_rate=%s where id=%s",(case.freight_rate,inv.id,))                    
                    else:
                        raise osv.except_osv(_('Warning'),_('Enter the Valid Amount'))    
                    if case.product_order:
                        cr.execute("update account_invoice set product_order=%s where id=%s",(case.product_order,inv.id,))
                    if case.handling_order:
                        cr.execute("update account_invoice set handling_order=%s where id=%s",(case.handling_order,inv.id,))                     
                                   
                    if inv.partner_id.id in cust:             
                        if unit_price>0:
                            qty=+(line.quantity)
                                
                        if qty>0:
                            qty_txt = amount_to_text_softapps._100000000_to_text(int(round(qty)))    
                            freight_amt=qty*case.freight_rate 
                            amt = qty*case.product_rate
                        if amt>0:       
                            freight_amt_txt = amount_to_text_softapps._100000000_to_text(int(round(freight_amt)))    
                            amt_txt = amount_to_text_softapps._100000000_to_text(int(round(amt)))                                     
                    
                        if not unit_price>line_price:
            #                 inv_obj.write(cr,uid,[inv.id],{'product_rate':case.product_rate,'freight_rate' :case.freight_rate})
                            cr.execute("update account_invoice set product_rate=%s where id=%s",(case.product_rate,inv.id,))
                            cr.execute("update account_invoice set freight_rate=%s where id=%s",(case.freight_rate,inv.id,))
                            cr.execute("update account_invoice set amt_txt=%s where id=%s",(amt_txt,inv.id,))
                            cr.execute("update account_invoice set amt_txt_freight=%s where id=%s",(freight_amt_txt,inv.id,))
                            
                            print "product_rate",inv.product_rate
                            print "freight_rate",inv.freight_rate
                            context.update({'product_rate':case.product_rate,'freight_rate' :case.freight_rate})
                            
                            res = rep_obj.pentaho_report_action(cr, uid, 'Handling Invoice For ITC', inv_ids,None,None)

                    else:
                        res = rep_obj.pentaho_report_action(cr, uid, 'Transport Invoice', inv_ids,None,None)
        
        return res
kw_invoice()







