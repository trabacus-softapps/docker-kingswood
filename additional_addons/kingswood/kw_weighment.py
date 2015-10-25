from openerp.osv import fields,osv
from openerp.tools.translate import _
import time
from tools import config

class kw_weigh_brigde(osv.osv):
    _name = 'kw.weigh.bridge'
    _columns = {
                'name'       : fields.char('Code', size=10),
                'partner_id' : fields.many2one('res.partner','Address'),
                }
kw_weigh_brigde()

class kw_weighment(osv.osv):
    _name = 'kw.weighment'
    
    def _get_weight(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for case in self.browse(cr, uid, ids):
            if case.first_weight and case.second_weight:
                res[case.id] = (case.second_weight - case.first_weight)
        return res
    
    _columns = {
                'name'          : fields.char('Ticket No.',size=20),
                'type'          : fields.selection([('general','General'),('stock','Stock')],'Type'),
                'weigh_date'    : fields.datetime('Weigh DateTime'),
                'partner_id'    : fields.many2one('res.partner','Party'),
                'party_name'    : fields.char('Party Name', size=100),
                'material_id'   : fields.many2one('product.product','Material'),
                'material_desc' : fields.char('Material Description',size=100),
                'vehicle_reg_no': fields.char('Vechile Register Number',size=10,required=True),
                'first_weight'  : fields.float('First Weight',digits=(6,3)),
                'second_weight' : fields.float('Second Weight',digits=(6,3)),
                'net_weight'    : fields.function(_get_weight,type='float',method=True,store=True,string='Net Weight'),
                'account_id'    : fields.many2one('account.account','Account'),
                'service_charge': fields.float('Service Charge', digits=(3,2)),
                'user_id'       : fields.many2one('res.users','User'),
                'weighbridge_id': fields.many2one('kw.weigh.bridge','Weigh Bridge'),
                'state'         : fields.selection([('draft','Draft'),('pending','Pending'),('done','Done')],'State'),
                'weight_dummy'  : fields.float('Weighing Scale',digits=(6,3)),
                #for testing
                'weight_dummy1' : fields.char('Weight',size=200)
                }
    _defaults = {
                 'user_id'    : lambda self,cr,uid,c: uid,
                 'weigh_date' : time.strftime('%Y-%m-%d %H:%M:%S'),
                 'state'      : 'draft',
                 }
    def onchange_partner_id(self, cr, uid, ids, partner_id):
        res ={'party_name':''}
        if partner_id:
            for p in self.pool.get('res.partner').browse(cr, uid, [partner_id]):
                res['party_name'] = p.name or ''
        return {'value':res}
    
    def onchange_material_id(self, cr, uid, ids, material_id):
        res ={'material_desc':''}
        if material_id:
            for p in self.pool.get('product.product').browse(cr, uid, [material_id]):
                res['material_desc'] = p.description or ''
        return {'value':res}
    
    def first_weight(self, cr, uid, ids, context=None):
        for case in self.browse(cr, uid, ids):
            self.write(cr, uid, ids, {'state':'pending','first_weight':case.weight_dummy},context)
        return True
    
    def second_weight(self, cr, uid, ids, context=None):
        for case in self.browse(cr, uid, ids):
            vals = {'state':'done',
                    'second_weight':case.weight_dummy,
                    'net_weight':case.first_weight - case.second_weight}
            self.write(cr, uid, ids, vals,context)
        return True
    
    def print_report(self, cr, uid, ids, context = None):
        return True
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(kw_weighment, self).default_get(cr, uid, fields, context=context)
        config_obj = self.pool.get('ir.config_parameter')
        weigh_bridge_id = int(config["kw_weigh_bridge"])
        
        #Account ID
        acc_ids = self.pool.get('account.account').search(cr, uid, [('code','=','302010')])
        if acc_ids:
            res.update({'account_id' :acc_ids[0]})
        #to generate the ticket number based on Weigh bridge Code
        for wb in self.pool.get('kw.weigh.bridge').browse(cr,uid,[weigh_bridge_id]):
            cr.execute('select name from kw_weighment order by id desc limit 1')
            seq = cr.fetchone()
            if seq == None:
                seq_no = '0000000'
            else:
                seq_no = seq[0][-7:]
            print wb.name
            ticket_no = str(wb.name) + "/" + str(int(seq_no)+1).zfill(7)
            res.update({'weighbridge_id' : wb.id,'name':ticket_no})
        return res
kw_weighment()
