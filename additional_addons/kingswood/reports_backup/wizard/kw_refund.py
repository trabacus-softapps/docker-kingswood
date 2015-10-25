from openerp.osv import fields,osv
from openerp.tools.translate import _
import time
from datetime import datetime

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