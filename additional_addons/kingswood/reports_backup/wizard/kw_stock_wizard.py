from openerp.osv import fields,osv
from openerp.tools.translate import _


class stock_wizard(osv.osv_memory):
    _name = 'stock.wizard'
    _columns ={
               }
    
    def confirm(self, cr, uid, ids, context = None):
        pick_obj = self.pool.get('stock.picking.out')
        pick_obj.kw_confirm(cr, uid, context['active_ids'],context=context)
        return True
    
stock_wizard()
    
