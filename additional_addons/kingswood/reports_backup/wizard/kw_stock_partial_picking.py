from openerp.osv import osv, fields

class stock_partial_picking(osv.osv_memory):
    _name = "stock.partial.picking"
    _inherit = "stock.partial.picking"
    _rec_name = 'picking_id'
    _description = "Partial Picking Processing Wizard"
    
    _columns = {
                'picking_id': fields.many2one('stock.picking', 'Picking', required=True, ondelete='CASCADE'),
                }
    
    def _partial_move_for(self, cr, uid, move):
       res = super(stock_partial_picking, self)._partial_move_for(cr, uid, move)
       res['quantity'] = move.product_qty
       return res
   
stock_partial_picking()
