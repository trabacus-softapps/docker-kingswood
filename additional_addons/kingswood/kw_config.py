from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
class kw_city(osv.osv):
    """  FOr city master for delivery orders"""
    _name = 'kw.city'
    _columns = {
                'name'     : fields.char('City', size=64),
                'state_id' : fields.many2one('res.country.state','State'),
                'pincode'  : fields.char("Pincode", size=15),
                }
    
    def unlink(self, cr, uid, ids, context=None):
        stock_obj = self.pool.get('stock.picking')
        city_ids = stock_obj.search(cr, uid, [('city_id','=',ids[0])])

        if city_ids:
            raise osv.except_osv(_('Warning'),_('You Cannot Delete the City which is used in Delivery Order'))

        res = super(kw_city,self).unlink(cr,uid,ids,context=None)
        return res
    
kw_city()


class res_company(osv.osv):
    _inherit = "res.company"
    _description = 'Companies'
    _columns = {
                'commodity'     : fields.char("Commodity Code",size=8),
                'esugam_ids'    : fields.one2many('esugam.master','company_id','E-Sugam')
                }
    _defaults = {
                 'commodity'   : '99.99'
                 } 
    
res_company()

class esugam_master(osv.osv):
    _name = 'esugam.master'
    _columns = {
                    'username'        : fields.char("UserName",size=64),
                    'password'        : fields.char("Password",size=64),
                    'url1'            : fields.char("Url",size=64),
                    'url2'            : fields.char("Alternate Url1",size=64),
                    'url3'            : fields.char("Alternate Url2",size=64),
                    'state_id'        : fields.many2one('res.country.state','State'),
                    'company_id'      : fields.many2one('res.company','Company')
                }
esugam_master()


# class ir_rule(osv.osv):
#     _inherit= 'ir.rule'
#        
# #     ********* Overridden Rule For Facilitator**********
#     def domain_get(self, cr, uid, model_name, mode='read', context=None):
#         # _where_calc is called as superuser. This means that rules can
#         # involve objects on which the real uid has no acces rights.
#         # This means also there is no implicit restriction (e.g. an object
#         # references another object the user can't see).
#         " This function is to set the rule domain for product_product object based on the user permissions"
# #         print "Model Name", model_name
#         dom = self._compute_domain(cr, uid, model_name, mode)
#         
#         cr.execute("select uid from res_groups_users_rel where gid in (select id  from res_groups where name in ('KW_Supplier'))")
#         supgrp_ids = [x[0] for x in cr.fetchall()]
#         if uid in supgrp_ids:
#              if dom:
#                  dom = ['&'] + dom + [('user_id', 'in', supgrp_ids)]
#              else:
#                  dom = [('user_id', 'in', supgrp_ids)]
#             
#              query = self.pool[model_name]._where_calc(cr, SUPERUSER_ID, dom, active_test=False)
#              return query.where_clause, query.where_clause_params, query.tables
#         return [], [], ['"' + self.pool[model_name]._table + '"']         
#   
#          
# ir_rule()   


# class ir_needaction_mixin(osv.AbstractModel):
#     """Mixin class for objects using the need action feature.
# 
#     Need action feature can be used by models that have to be able to
#     signal that an action is required on a particular record. If in
#     the business logic an action must be performed by somebody, for
#     instance validation by a manager, this mechanism allows to set a
#     list of users asked to perform an action.
# 
#     Models using the 'need_action' feature should override the
#     ``_needaction_domain_get`` method. This method returns a
#     domain to filter records requiring an action for a specific user.
# 
#     This class also offers several global services:
#     - ``_needaction_count``: returns the number of actions uid has to perform
#     """
# 
#     _inherit = 'ir.needaction_mixin'
#     _needaction = True
# 
#     #------------------------------------------------------
#     # Addons API
#     #------------------------------------------------------
# 
#     def _needaction_domain_get(self, cr, uid, context=None):
#         """ Returns the domain to filter records that require an action
#             :return: domain or False is no action
#         """
#         return False
# 
#     #------------------------------------------------------
#     # "Need action" API
#     #------------------------------------------------------
# 
#     def _needaction_count(self, cr, uid, domain=None, context=None):
#         """ Get the number of actions uid has to perform. """
#         dom = self._needaction_domain_get(cr, uid, context=context)
#         if not dom:
#             return 0
#         cr.execute("select uid from res_groups_users_rel where gid in (select id  from res_groups where name in ('KW_Supplier'))")
#         supgrp_ids = [x[0] for x in cr.fetchall()]
#         if uid in supgrp_ids:
#              if dom:
#                  dom = ['&'] + dom + [('user_id', 'in', supgrp_ids)]
#              else:
#                  dom = [('user_id', 'in', supgrp_ids)]
#              
#              query = self.pool[model_name]._where_calc(cr, SUPERUSER_ID, dom, active_test=False)
#           
#         res = self.search(cr, uid, (domain or []) + dom, limit=100, order='id DESC', context=context)
#         return len(res)  
