from openerp.osv import fields,osv
from openerp.tools.translate import _
from lxml import etree
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re


class kw_farmers(osv.osv):
    _name = "kw.farmers"
    _columns={
                'name'      :   fields.char("Name", size=30,required=True),
                'survey_no' :   fields.char("Survey no", size=20,required=True),
                'village'   :   fields.char("Village", size=30),
                'hobli'     :   fields.char("Hobli", size=30),
                'taluk'     :   fields.char("Taluk", size=30),
                'district'  :   fields.char("District", size=30),
#                 'state'     :   fields.char("State")
              }
kw_farmers()

class kw_facilitator(osv.osv): 
    
    _name ='kw.facilitator'
    _columns={
                'partner_id'           :  fields.many2one('res.partner',"Partner"),
                'facilitator_id'       :  fields.many2one('res.partner',"Faciltator"),
                'date'                 :  fields.date("Date"),
                'active_sup'           :  fields.boolean('Active'),
                }
    _defaults={

                'date'     : lambda *a: time.strftime('%Y-%m-%d'),             
               }    
kw_facilitator()    
class res_partner(osv.osv): 
    
    _inherit = 'res.partner'


    def _get_user(self, cr, uid, ids, args, field_name, context = None):
        if not context:
            context={}
        res ={}
        g_ids = []
        user_obj = self.pool.get('res.users')
        user_id=user_obj.browse(cr,uid,uid)        
        u_id=context.get('uid')
        if u_id:
            uid=u_id
        for case in self.browse(cr, uid, ids):
                res[case.id] = {'user_log':'','partner_state':False}
                
                user_id=user_obj.browse(cr,uid,uid)
                res[case.id]['partner_state']=user_id.partner_id.state_id.id
                cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
                gid = cr.dictfetchall()
                for x in gid:
                    g_ids.append(x['gid'])
                for g in self.pool.get('res.groups').browse(cr, uid, g_ids):

                    if g.name == 'KW_Supplier':
                        res[case.id]['user_log'] = 'KW_Supplier'

                         
                    if g.name == 'KW_Customer':
                        res[case.id]['user_log'] = 'KW_Customer'
                    if g.name == 'KW_Depot':
                        res[case.id]['user_log'] = 'KW_Depot'   
                    if g.name == 'KW_Admin':
                        res[case.id]['user_log'] = 'KW_Admin'

                    if g.name == 'KW_Freight':
                        res[case.id]['user_log'] = 'kw_freight'
                        
                    if g.name == 'KW_Supplier' and user_id.partner_id.billing_cycle:
                        res[case.id]['user_log'] = 'KW_Supplier_billing'                        
                       
         
        return res
    
    def _get_default_user(self, cr, uid, context=None):
        if not context:
            context={}        
        res ={}
        g_ids = []
        user_obj = self.pool.get('res.users')
        user_id=user_obj.browse(cr,uid,uid)
        
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
            if g.name == 'KW_Supplier':
                res = 'KW_Supplier'
                
            if g.name == 'KW_Customer':
                res = 'KW_Customer'
            if g.name == 'KW_Depot':
                res = 'KW_Depot'
            if g.name == 'KW_Admin':
                res = 'KW_Admin'
            if g.name == 'KW_Freight':
                res = 'kw_freight'   
                
            if g.name == 'KW_Supplier' and user_id.partner_id.billing_cycle:
                res = 'KW_Supplier_billing'                 
                 
                           
        return res    
    
    def get_customers(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        for case in self.browse(cr, uid, ids):
            res[case.id] = []
            if case.list_of_cust:
                res[case.id] = eval(case.list_of_cust or '[]' )
        return res
    
    def get_billing(self, cr, uid, ids, field_name, args,context =None):
        res = {}
        bill_ids = []
        lines = []
        bill_obj = self.pool.get('billing.cycle')
        for case in self.browse(cr, uid, ids):
            res[case.id] = []
            bill_ids = bill_obj.search(cr, uid, [('partner_id','=',case.id)], limit=1, order="st_date desc")
            if bill_ids:
                res[case.id] = bill_ids
        return res
    
    
    _columns={
                'tin_no'                :   fields.char("Tin Number",size=15),
                'pan_no'                :   fields.char("Pan Number",size=10),
                'sup_num'               :   fields.char("Supplier Reference",readonly='True'),
                'tol_rate'              :   fields.float("Rate/Kg"),
                'tol_qty'               :   fields.float("Tolerance Qty/MT in Kgs"),
                'freight'               :   fields.boolean('Generate Freight Invoice'),  
                'customer_ids'          :   fields.many2many('res.partner','customer_list_rel','supplier_id','customer_id','Customers'),
                'customer'              :   fields.boolean('Customer', help="Check this box if this contact is a customer."),  
                'gen_esugam'            :   fields.boolean('Generate ESugam No.',track_visibility='onchange'),
                'farmers_ids'           :   fields.many2many('kw.farmers','farmers_list_rel','supplier_id','farmers_id','Farmers'),
                'es_active'             :   fields.boolean("Active"),
                'es_username'           :   fields.char("UserName",size=64),
                'es_password'           :   fields.char("Password",size=64),
                'es_url1'               :   fields.char("Url",size=64),
                'es_url2'               :   fields.char("Alternate Url",size=64),
                'handling_charges'      :   fields.boolean('Additional Freight Charges'),  
                'product_change'        :   fields.boolean('Allow Product Change'),
                'cst'                   :   fields.char('CST',size=64),
                'account_rec'           :   fields.many2one('account.account','Account Receivable-Sub Company'),
                'account_pay'           :   fields.many2one('account.account','Account Payable-Sub Company'),
                'work_order'            :   fields.char('Work Order Number',size=20),
                'show_esugam'           :   fields.boolean('Show Esugam',track_visibility='onchange'),
                'show_freight'          :   fields.boolean('Show Freight',track_visibility='onchange'),
                'billing_ids'           :   fields.one2many('billing.cycle','partner_id','Billing Cycle'),
                'dealers_ids'           :   fields.one2many('goods.dealers','partner_id','Dealer'),
#                 'dealers'               :   fields.many2many('goods.dealers','dealers_list_rel','dealers_id','partner_id','Dealers'),
                'pay_freight'           :   fields.boolean('Pay Freight By Customer'),
                'representative_id'     :   fields.many2one('res.partner','Pay Freight Representative'),
                'representative'        :   fields.boolean("Is a Representative"),
                'city_id'               :   fields.many2one('kw.city','City'),
                'report'                :   fields.boolean('DC-LR Report'),
                'split_invoice'         :   fields.boolean('Customised Split Invoice'),
                'amc_attachment'        :   fields.boolean('AMC Attachment'),
                'billing_cycle'         :   fields.boolean('Facilitator Tab'),
                'billing_cycle_tab'     :   fields.boolean('Billing Cycle Tab'),
                 'user_log'             :   fields.function(_get_user,type='char',method=True,string="Permission", store=False,multi='state'),  
                 'wc_num'               :   fields.boolean('WC Number/GP Number'),    
                 'partner_state'        :   fields.function(_get_user,type='many2one',relation='res.country.state',method=True,string="State", store=True,multi='state'),
                 
                 # This field for Weighment Slip Report 
                 'w_report'             :   fields.boolean('Weighment Slip Report'),   
                'dc_report'            :  fields.boolean("DC Report"),
                
                #for templating 
                'list_of_cust'         : fields.text('Customer'),
                'billing_partners'     :  fields.function(get_customers, method=True, type='one2many',string="Billing Customers", relation="res.partner"),
                'current_bill'         :  fields.function(get_billing, method=True, type="one2many", string="Current Bill", relation="billing.cycle"), 

                'facilitator_ids'      :  fields.one2many('kw.facilitator','partner_id',"Faciltator"),
                'is_farm_decl'         : fields.boolean('Farmer Declaration') ,
                
                # For AP Tax Link
                'transit_pass'         : fields.boolean("Transit Pass"), 
                'tax_link'             : fields.char("Tax Link", size=500),
                
                # Daily Dispatch Report IN and OUT
                'contract_ids'         :   fields.one2many("customer.contracts", 'partner_id', "Customer Contracts"),

                'show_jjform'          :   fields.boolean('Show JJform',track_visibility='onchange'),
                'gen_jjform'           :   fields.boolean('Generate JJform.',track_visibility='onchange'),
                'ftbal_deduct'         :   fields.float("Freiht Balance Deduct", digits=(16,2)),

                'gstin_code'            :   fields.char("GST IN Code", size=20),
                'un_reged_vendor'       :   fields.boolean("Un Reged Vendor"),

                # GST Purchase
                'sub_facilitator_ids'   :   fields.one2many("sub.facilitator", 'main_facilitator_id', "Sub Facilitators"),
                'sub_facilitator'       :   fields.boolean("Is Sub Facilitator"),
              }
    _defaults={
               'customer':True,
               'country_id' : 105,
               'gen_esugam':False,
               'product_change':False,
               'show_esugam' : False,
               'show_freight':False,
               'handling_charges':False,
                'user_log'     :_get_default_user,

               }

    def onchange_country_id(self, cr, uid, ids, country_id, context=None):
        if not context:
            context = {}
        res = {}
        country_obj = self.pool.get("res.country")
        if country_id:
            cntry = country_obj.browse(cr, uid, country_id)
            if cntry.code != 'IN':
                res.update({'is_india' : False})
            else:
                res.update({'is_india' : True})

        return {'value' : res}

    def onchange_gstin_code(self, cr, uid, ids, gstin_code, context=None):
        if not context:
            context = {}
        warning = {}
        res = {}
        if gstin_code:
            if not re.match('^[a-z_A-Z0-9]+$',gstin_code):
                warning = {
                    'title': _('Warning!'),
                    'message': _('Special Charecters not allowed in GST Code.')
                      }
                res.update({'gstin_code':False})
            else:
                res.update({'gstin_code':gstin_code})

        return {'value':res, 'warning' : warning}

    def onchange_pay_freight(self, cr, uid, ids, pay_freight=False,context=None):
        res ={}
        stock_obj=self.pool.get('stock.picking.out')
        if pay_freight and ids:
            pick=stock_obj.search(cr,uid,[('partner_id','=',ids[0])])
            stock_obj.write(cr,uid,pick,{'pay_freight':pay_freight})
       
        return{'value':res}
    #to update logistics account_id for facilitator
    
    def onchange_billing_cycle(self, cr, uid, ids, address_type, parent_id, name,context=None):
        res={}
        cr.execute("select id from res_country where lower(name) like 'india%'")
        country_id=cr.fetchone()        
        if address_type and parent_id:
            partner_ids=self.search(cr,uid,[('id','=',parent_id)])
            partner_id=self.browse(cr,uid,partner_ids)
            if partner_id:
                partner_id=partner_id[0]
                
                res['name']=partner_id.name
            
        else:
            res['name']=False
        if name:
           res['name']=name  
#         if country_id:
#             res['country_id']=country_id[0]
            
        return {'value':res}    
    
    def update_account(self, cr, uid, ids, context = None):
        acc_obj = self.pool.get('account.account')
        supp_ids = self.search(cr, uid,[('account_pay','=',False),('supplier','=',True)])
        for s in self.browse(cr, uid, supp_ids):
            acc_ids = acc_obj.search(cr, uid,[('code','=','KL'+s.property_account_payable.code)])
            if acc_ids:
                self.write(cr, uid, [s.id],{'account_pay':acc_ids[0]})
        return True
    
    
    #to update logistics account_id for facilitator
    def update_city(self, cr, uid, ids, context = None):
        city_obj = self.pool.get('kw.city')
        billing_cycle=self.pool.get('billing.cycle')
        supp_ids = self.search(cr, uid,[])
        print "supp_ids",len(supp_ids),"ids",supp_ids
        for s in self.browse(cr, uid, supp_ids):
            city_ids = city_obj.search(cr, uid,[('name','like',s.city)])
            if city_ids:
                self.write(cr, uid, [s.id],{'city_id':city_ids[0]})
        billing_cycle.update(cr,uid,ids)
        return True
    
    
    def unlink(self, cr, uid, ids, context=None):
        stock_obj = self.pool.get('stock.picking')
        supplier_ids = stock_obj.search(cr, uid, [('paying_agent_id','=',ids[0])])
        customer_ids = stock_obj.search(cr, uid, [('partner_id','=',ids[0])])
        if supplier_ids:
            raise osv.except_osv(_('Warning'),_('You Cannot Delete the Facilitator which is used in Delivery Order'))
        if customer_ids:
            raise osv.except_osv(_('Warning'),_('You Cannot Delete the Customer which is used in Delivery Order'))
        res = super(res_partner,self).unlink(cr,uid,ids,context=None)
        return res
    
    def create(self,cr,uid,vals,context=None):
        kw_ac=self.pool.get('account.account')
        c_parent_id=False
        s_parent_id=False
        supplier=context.get('default_supplier',0)
        customer=context.get('default_customer',0)
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company=cr.fetchone()
        if company:
            company=company[0]
#         cr.execute("select id from res_company where lower(name) like '%Supplier%'")
#         company1=cr.fetchone()
        if context.get("sub_facilitator"):
            vals["sub_facilitator"] = True
        if supplier>0:  
            
            
            if vals.get('name') and vals.get('mobile'):
                res = self.search(cr, uid, [('name','=',vals['name']),('mobile','=',vals['mobile'])])
                if res:
                    raise osv.except_osv(_('warning'),_('Name and mobile number already exist'))
                
# ******************************* cutomer Receivable*****************************                
            s_sequence=self.pool.get('ir.sequence').get(cr, uid,'kw.supplier')
       
            if s_sequence:
                account_pool = self.pool.get('account.account.type')
                account_ids = account_pool.search(cr, uid, [('name','=','Payable')])
                if account_ids:
                    type_account = account_pool.browse(cr, uid, account_ids[0])
                   
                s_account_parent=self.pool.get('account.account')
                s_parent_ids=s_account_parent.search(cr,uid,[('name','=','Sundry Creditors'),('company_id','<>',company)])
                ls_parent_ids=s_account_parent.search(cr,uid,[('name','=','Sundry Creditors'),('company_id','=',company)])
                if s_parent_ids:
                    s_parent_id=s_account_parent.browse(cr,uid,s_parent_ids[0])
                  
                ac_sval={ 
                        "code" : "KS"+s_sequence,
                        'name':vals['name'],
                        'type':'payable',
                        'user_type':type_account.id, 
                        'parent_id':s_parent_id and s_parent_id.id or False,
                        }
                
                if ls_parent_ids:
                    ls_parent_id=s_account_parent.browse(cr,uid,ls_parent_ids[0])
                kl_val={ 
                        "code" : "KL"+s_sequence,
                        'name':vals['name'],
                        'type':'payable',
                        'user_type':type_account.id,
                        'parent_id':ls_parent_id.id or False,
                        'company_id':company,
                        }
                
                kw_ac_sid=kw_ac.create(cr,uid,ac_sval,context)
                kwl_sid=kw_ac.create(cr,uid,kl_val,context)
                vals['property_account_payable']= kw_ac_sid
                vals['account_pay']=kwl_sid
                vals['sup_num']=s_sequence
                
        # ********************* cutomer payable*****************************
        if customer>0:
            c_sequence=self.pool.get('ir.sequence').get(cr, uid,'kw.customer')
            if c_sequence:
                c_account_pool = self.pool.get('account.account.type')
                c_account_ids = c_account_pool.search(cr, uid, [('name','=','Receivable')])
                
                if c_account_ids:
                    c_type_account = c_account_pool.browse(cr, uid, c_account_ids[0])
                    
                c_account_parent=self.pool.get('account.account')
                c_parent_ids=c_account_parent.search(cr,uid,[('name','=','Sundry Debtors'),('company_id','<>',company)])
                l_parent_ids=c_account_parent.search(cr,uid,[('name','=','Sundry Debtors'),('company_id','=',company)])
                
                if c_parent_ids:
                    c_parent_id=c_account_parent.browse(cr,uid,c_parent_ids[0])
               
                ac_cval={ 
                        "code" : "KS"+c_sequence,
                        'name':vals['name'],
                        'type':'receivable',
                        'user_type':c_type_account.id,
                        'parent_id':c_parent_id.id or False,
                        }
                
                if l_parent_ids:
                    l_parent_id=c_account_parent.browse(cr,uid,l_parent_ids[0])
                ac_clval={ 
                        "code" : "KL"+c_sequence,
                        'name':vals['name'],
                        'type':'receivable',
                        'user_type':c_type_account.id,
                        'parent_id':l_parent_id.id or False,
                        'company_id':company,
                        }
                
                
                kw_ac_cid=kw_ac.create(cr,uid,ac_cval,context)
                kwl_cid=kw_ac.create(cr,uid,ac_clval,context)
                vals['property_account_receivable']= kw_ac_cid 
                vals['account_rec']=kwl_cid
                vals['sup_num']=c_sequence

                    

        return super(res_partner,self).create(cr, uid, vals, context)
  
    def write(self, cr, uid, ids, vals, context=None):
        if context.get("report"):
            cr.execute("select id from res_users where login='Admin'")
            uid = cr.fetchone()
            if uid:
                uid = uid[0]
        res = super(res_partner,self).write(cr, uid, ids, vals, context=None)
         
        return res
res_partner()

class sub_facilitator(osv.osv):
    _name = "sub.facilitator"

    def _get_total_purchase(self, cr, uid, ids, field_name, args, context=None):
        context = dict(context or {})
        res = {}
        for case in self.browse(cr, uid, ids):
            total_purchase = 0.00
            if case.from_date and case.to_date and case.sub_part_id.id:
                cr.execute("""
                    select
                        sum(purchase_amount)

                    from stock_picking sp
                    where sp.date::date >='"""+str(case.from_date)+"""' and sp.date::date <= '"""+str(case.to_date)+"""'
                        and sp.sub_facilitator_id=""" +str(case.sub_part_id.id))
                total_purchase = [x[0] for x in cr.fetchall()]
                if total_purchase:
                    total_purchase = total_purchase[0]
                    if total_purchase is None:
                       total_purchase = 0.00
            res[case.id] = total_purchase
        return res

    _columns = {
        'sub_part_id'           :   fields.many2one("res.partner", "Sub Facilitator"),
        'main_facilitator_id'   :   fields.many2one("res.partner", "Main Facilitator"),
        'from_date'             :   fields.date("From Date"),
        'to_date'               :   fields.date("To Date"),
        'total_purchase'        :   fields.function(_get_total_purchase, type="float", store=False, string="Total Purchase")


    }

    def create(self, cr, uid, vals, context=None):
        if not context:
            context = {}
        res = super(sub_facilitator, self).create(cr, uid, vals, context)
        if res:
            for case in self.browse(cr, uid, [res]):
                cr.execute("update res_partner set parent_id = "+str(case.main_facilitator_id and case.main_facilitator_id.id or False)+" where id="+str(case.sub_part_id and case.sub_part_id.id or False))
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context = {}
        res = super(sub_facilitator, self).write(cr, uid, ids, vals, context)
        if res:
            for case in self.browse(cr, uid, ids):
                cr.execute("update res_partner set parent_id = "+str(case.main_facilitator_id and case.main_facilitator_id.id or False)+" where id="+str(case.sub_part_id and case.sub_part_id.id or False))
        return res

sub_facilitator()

class customer_contracts(osv.osv):
    _name = "customer.contracts"
    
    def _get_pending_qty(self, cr, uid, ids, field_name, args, context=None):
        context = dict(context or {})
        res = {}
        qty_pending = 0.00
        
        for case in self.browse(cr, uid, ids):
            sold_qty = 0.00
            cr.execute(""" 
                    select sum(sp.del_quantity) 
    
                    from stock_picking sp
                    where sp.product_id ="""+str(case.product_id.id)+""" and sp.partner_id = """+str(case.partner_id.id)+"""
                    and sp.date >='"""+str(case.from_date)+"""' and sp.date <= '"""+str(case.to_date)+"""' 
                    and sp.state in ('done','freight_paid')           
                    """)
            sold_qty = [x[0] for x in cr.fetchall()]
            if sold_qty:
                sold_qty = sold_qty[0]
                if sold_qty is None:
                   sold_qty = 0.00
        res[case.id] = case.qty_ordered - sold_qty
        return res
    
    _columns={
              'name'        :   fields.char("Customer Contracts"),
              'partner_id'  :   fields.many2one("res.partner", "Partner"),
              'from_date'   :   fields.date("From Date"),
              'to_date'     :   fields.date("To Date"),
              'product_id'  :   fields.many2one('product.product', "Specie"),
              'qty_ordered' :   fields.float("Qty Ordered", digits=(16,2)),
              'qty_pending' :   fields.function(_get_pending_qty, string="Qty Pending", type='float', store=True),
              'is_active'   :   fields.boolean("Active"),
              
              }
    _defaults ={
                'is_active' : False
                }

customer_contracts()

class res_company(osv.osv):
    _inherit='res.company'
    _columns={
                'tin'               :   fields.char('Tin Number',size=20),
                'toll_free'         :   fields.char("Toll Free No.",size=15),
                'attachment'        :   fields.binary("APMC Attachment"),
                'farmer_declaration':   fields.binary("Farmer Declaration"),
                'gstin_code'        :   fields.char("GST IN Code", size=20),
             }
    _defaults={
               
               'country_id' : 105,
               
               }
    def onchange_gstin_code(self, cr, uid, ids, gstin_code, context=None):
        if not context:
            context = {}
        warning = {}
        res = {}
        if gstin_code:
            if not re.match('^[a-z_A-Z0-9]+$',gstin_code):
                warning = {
                    'title': _('Warning!'),
                    'message': _('Special Charecters not allowed in GST Code.')
                      }
                res.update({'gstin_code':False})
            else:
                res.update({'gstin_code':gstin_code})

        return {'value':res, 'warning' : warning}

res_company()


class res_users(osv.osv):
    _name='res.users'
    _inherit=['res.users','mail.thread','ir.needaction_mixin']
    
    def _get_belongingGroups(self, cr, uid, belongto, context=None):
       data_obj = self.pool.get('ir.model.data') 
       result = super(res_users, self)._get_group(cr, uid, context)
       try:  
           if belongto == 'KW_Supplier':
               dummy, groupid = data_obj.get_object_reference(cr, 1, 'Kingswood', 'KW_Supplier')
               result.append(groupid)
               result.append(3)
           elif belongto == 'KW_Depot':
               dummy, groupid = data_obj.get_object_reference(cr, 1, 'Kingswood', 'KW_Depot')
               result.append(groupid)
               result.append(3)
               
           elif belongto == 'KW_Customer':
               dummy, groupid = data_obj.get_object_reference(cr, 1, 'Kingswood', 'KW_Customer')
               result.append(groupid)
               result.append(3)
           elif belongto == 'KW_Freight':
               dummy, groupid = data_obj.get_object_reference(cr, 1, 'Kingswood', 'KW_Freight')
               result.append(groupid)
               result.append(3)
           
             
       except ValueError:
           # If these groups does not exists anymore
           pass
       return result
     
    _columns={
              
                'role'       : fields.selection([('admin','Admin'),('customer','Customer'),('supplier','Supplier'),('depot','Depot'),('freight','Freight'),('representative','Representative')],'Role'),
                'location_id': fields.many2one('stock.location', 'Location'),
                 'password'  : fields.char('Password',size=64),
                'customer_id': fields.many2one('res.partner',"Customer"), 
              }
    
    _defaults={
               
               'customer':False,
              
               
               }
    def create(self, cr, uid, values, context=None):
        res = {}
        group_obj = self.pool.get('res.groups')
        billing_obj = self.pool.get('billing.cycle')
        billing_cycle=values.get('billing_cycle',False)
        billing_cycle_tab=values.get('billing_cycle_tab',False)
        partner_id = values.get('partner_id',False)  
        billing_id = []        
        if partner_id:
            billing_id = billing_obj.search(cr,uid,[('partner_id','=',partner_id)]) 
            
        print billing_cycle
        if 'role' in values and values['role']:
            if values['role'] == 'admin':
                groupids = self._get_belongingGroups(cr, uid, values['role'], context)
                group_obj = self.pool.get('res.groups')
                group_ids = group_obj.search(cr,uid,[('name','=','KW_Admin')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = True
                group_ids = group_obj.search(cr,uid,[('name','=','Access Rights')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = True
                group_ids = group_obj.search(cr,uid,[('name','=','Technical Features')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = False
             
            if 'role' in values and values['role'] != 'KW_Admin':
                groupids = self._get_belongingGroups(cr, uid, 'technical_features', context)
                for tf in groupids:
                    values['in_group_' + str(tf)] = False
                group_ids = group_obj.search(cr,uid,[('name','=','KW_Freight')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = False
                    
                        
            if values['role'] == 'customer':
                group_obj = self.pool.get('res.groups')
                group_ids = group_obj.search(cr,uid,[('name','=','KW_Customer')]) 
                for fl in group_ids:
                    values['in_group_'+str(fl)] = True
                group_ids = group_obj.search(cr,uid,[('name','=','KW_Freight')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = False    
                    
                    
            if values['role'] == 'supplier':
                group_obj = self.pool.get('res.groups')
                group_ids = group_obj.search(cr,uid,[('name','=','KW_Supplier')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = True
                group_ids = group_obj.search(cr,uid,[('name','=','KW_Freight')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = False    
                
#                 group_ids = group_obj.search(cr,uid,[('name','=','KW_billing_cycle')])  
#                 for fl in group_ids:
#                     values['in_group_'+str(fl)] = billing_cycle 
#                     
#                 group_ids = group_obj.search(cr,uid,[('name','=','kw_facilitor_billing_service_tab')])  
#                 for fl in group_ids:
#                     values['in_group_'+str(fl)] = billing_cycle_tab                                              
                    
            if values['role'] == 'depot':
                group_obj = self.pool.get('res.groups')
                group_ids = group_obj.search(cr,uid,[('name','=','KW_Depot')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = True
                group_ids = group_obj.search(cr,uid,[('name','=','KW_Freight')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = False
                    
                        
            if values['role'] == 'freight':
                group_obj = self.pool.get('res.groups')
                group_ids = group_obj.search(cr,uid,[('name','=','KW_Freight')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = True

            # For Billing Cycle Tab         
            if billing_cycle_tab:   
                group_ids = group_obj.search(cr,uid,[('name','=','KW_billing_cycle')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = billing_cycle_tab
            # For Facilitator Tab
            if billing_cycle:
                group_ids = group_obj.search(cr,uid,[('name','=','KW_facilitor_billing_cycle_tab')])
                for fl in group_ids:
                    values['in_group_'+str(fl)] = billing_cycle                     
        
        res = super(res_users, self).create(cr, uid, values, context=context)    
        if res and billing_id:
            billing_obj.write(cr,uid,billing_id,{'user_partner':res})            
        return res

    def write(self, cr, uid, ids, vals, context=None):
        group_obj = self.pool.get('res.groups')
        billing_cycle=False

                                
        if ids and isinstance(ids, int):    
           ids = [ids] 
        if hasattr(ids, '__iter__'):
            for case in self.browse(cr, uid, ids, context=context):
                billing_cycle=vals.get('billing_cycle',case.billing_cycle) 
                billing_cycle_tab=vals.get('billing_cycle_tab',case.billing_cycle_tab) 
                if case.id > 1:
                    
                    if 'role' in vals and vals['role']:
                        groupids = self._get_belongingGroups(cr, uid, case.role, context)
                        for fl in groupids:
                            vals['in_group_' + str(fl)] = False
                    if 'role' in vals and vals['role']:
                        groupids = self._get_belongingGroups(cr, uid, vals['role'], context)
                        for fl in groupids:
                            vals['in_group_' + str(fl)] = True
                    
                    if 'role' in vals and vals['role']:
                        cr.execute("delete from res_groups_users_rel where uid ="+str(ids[0]))
                        
                        
                    if 'role' in vals and vals['role']:
                        if vals['role'] == 'admin':
                            groupids = self._get_belongingGroups(cr, uid, vals['role'], context)
                            group_obj = self.pool.get('res.groups')
                            group_ids = group_obj.search(cr,uid,[('name','=','KW_Admin')])
                            for fl in group_ids:
                                vals['in_group_'+str(fl)] = True
                            group_ids = group_obj.search(cr,uid,[('name','=','Access Rights')])
                            for fl in group_ids:
                                vals['in_group_'+str(fl)] = True
                            group_ids = group_obj.search(cr,uid,[('name','=','Technical Features')])
                            for fl in group_ids:
                                vals['in_group_'+str(fl)] = False
                            group_ids = group_obj.search(cr,uid,[('name','=','KW_Freight')])
                            for fl in group_ids:
                                vals['in_group_'+str(fl)] = False                      
                    
                                
                                
                    if 'role' in vals and vals['role']:
                        if vals['role'] == 'customer':
                            group_obj = self.pool.get('res.groups')
                            group_ids = group_obj.search(cr,uid,[('name','=','KW_Customer')])
                            for fl in group_ids:
                                vals['in_group_'+str(fl)] = True   
                            group_ids = group_obj.search(cr,uid,[('name','=','KW_Freight')])
                            for fl in group_ids:
                                vals['in_group_'+str(fl)] = False                     
                    
                     
                   
                        
                    if 'role' in vals and vals['role']:
                        if vals['role'] == 'depot':
                            group_obj = self.pool.get('res.groups')
                            group_ids = group_obj.search(cr,uid,[('name','=','KW_Depot')])
                            for fl in group_ids:
                                vals['in_group_'+str(fl)] = True    
                            group_ids = group_obj.search(cr,uid,[('name','=','KW_Freight')])
                            for fl in group_ids:
                                vals['in_group_'+str(fl)] = False                             
                    
                    
                                
                    if 'role' in vals and vals['role']:
                        if vals['role'] == 'supplier':
                            group_obj = self.pool.get('res.groups')
                            group_ids = group_obj.search(cr,uid,[('name','=','KW_Supplier')])
                            for fl in group_ids:
                                vals['in_group_'+str(fl)] = True  
                            group_ids = group_obj.search(cr,uid,[('name','=','KW_Freight')])
                            for fl in group_ids:
                                vals['in_group_'+str(fl)] = False                                 
                                
                    
                    if 'role' in vals and vals['role']:
                        if vals['role'] == 'freight':
                            group_obj = self.pool.get('res.groups')
                            group_ids = group_obj.search(cr,uid,[('name','=','KW_Freight')])
                            for fl in group_ids:
                                vals['in_group_'+str(fl)] = True  
                                
                    # For Billing Cycle Tab            
                    group_ids = group_obj.search(cr,uid,[('name','=','KW_billing_cycle')])
                    for fl in group_ids:
                        vals['in_group_'+str(fl)] = billing_cycle_tab
                    # For Facilitator Tab
                    group_ids = group_obj.search(cr,uid,[('name','=','KW_facilitor_billing_cycle_tab')])
                    for fl in group_ids:
                        vals['in_group_'+str(fl)] = billing_cycle          
                 
        return super(res_users, self).write(cr, uid, ids, vals, context=context)
    
res_users()

class billing_cycle(osv.osv):
    _name = 'billing.cycle'
    
    def _get_user(self, cr, uid, ids, field_name, args, context = None):
        res = {}
        user_obj=self.pool.get('res.users')
        for case in self.browse(cr, uid, ids):
            user=user_obj.search(cr,uid,[('partner_id','=',case.partner_id.id)])
            if user:
                res[case.id]=user[0]
        return res    
 
    
 
       
    _columns = {
                    'st_date'           :  fields.date('Start Date'),
                    'end_date'          :  fields.date('End Date'),
                    'open_bal'          :  fields.float('Opening Balance'),
                    'partner_id'        :  fields.many2one('res.partner','Partner'),
                    'show_field'        : fields.boolean('Show Field'),
                    'uid'               : fields.many2one('res.users','user'),
#                     'user_partner'      : fields.many2one('res.partner', 'User-Partner',track_visibility='onchange'),
                    'user_partner'       : fields.function(_get_user,type="many2one",relation="res.users",string="User-Partner",store=True),
                    
                    }
    _order = 'st_date desc'
    _defaults = {
                 'show_field'         :True,
                 'uid'                :lambda self,cr,uid,c: uid,
                
                 }
  
    def update(self, cr, uid, ids, context = None):
        res = {}
        user=self.search(cr,uid,[('user_partner','=',False)])
        self.write(cr,uid,user,{'uid':uid})
        return res
    
    
    def default_get(self, cr, uid, fields, context=None):
        res_obj = self.pool.get('res.users')
        b_ids = []
        res = super(billing_cycle,self).default_get(cr, uid, fields, context)
        if context.get('billing_ids'):
            for res_line_dict in res_obj.resolve_2many_commands(cr, uid, 'billing_ids', context.get('billing_ids'), context=context):
                res['partner_id'] = res.get('partner_id') or res_line_dict.get('partner_id')
                if res['partner_id']:
                    b_ids = self.search(cr, uid, [('partner_id','=',res['partner_id'][0])], order="end_date desc",limit=1)
        for case in self.browse(cr, uid,b_ids):
            next_date = (datetime.strptime(case.end_date, '%Y-%m-%d')+ relativedelta(days=1)).strftime('%Y-%m-%d')
            res.update({'st_date':next_date,'show_field':False })
        return res

    
    def generate_report(self, cr, uid, ids, context = None):
        res = {}
        freight = False
        for case in self.browse(cr, uid, ids):
            if case.st_date > case.end_date:
                raise osv.except_osv(_('Warning'),_('Please enter valid Start and End dates'))
            data = {}
            data['ids'] = context.get('active_ids', [])
            data['model'] = context.get('active_model', 'ir.ui.menu')
            data['output_type'] = 'pdf'
            
            # to get the financial year start date
            cr.execute("select date_start from account_fiscalyear where date_start <= '" + case.st_date + "' and date_stop >='" + case.st_date + "' limit 1")
            fydate = cr.fetchone()
            if not fydate:
                raise osv.except_osv(_('Warning'),_('There is No valid FiscalYear Defined in the System'))
            else:
                fy_st_date = fydate[0]
            sub_fac_ids = []
            cr.execute("select sub_part_id from sub_facilitator where main_facilitator_id="+str(case.partner_id and case.partner_id.id))
            sub_fac_ids = [x[0] for x in cr.fetchall()]
            sub_fac_ids.append(case.partner_id.id)
            data['variables'] = {
                                 'st_date'           : case.st_date,
                                 'end_date'          : case.end_date,
                                 'supplier'          : sub_fac_ids,
                                 'unpaid'            : "True",
                                 'unpaid_st_date'    : case.st_date,
                                 'supplier_name'     : case.partner_id.name or '',
                                 'freight'           : freight,
                                 'fy_st_date'        : fy_st_date,
                                 }

        tot_amount = 0.00
        part = (str(tuple(sub_fac_ids)).rstrip(',)')+ ')')
        sql = "select \
                        case when (sum(a.bal) + sum(freight))>0 then sum(a.bal) + sum(freight) else 0 end  AS debit,\
                        case when (sum(a.bal) + sum(freight))>0 then 0 else sum(a.bal) + sum(freight) end AS credit \
                    from\
                    (select\
                        case when sum(debit-credit) is null then 0 else  sum(debit-credit) end as bal,\
                        (select case when sum(sp.freight_balance)>0 then sum(sp.freight_balance) else 0 end \
                            from stock_picking sp \
                            inner join account_voucher a on sp.name = a.reference   \
                            where sp.sup_invoice is true and sp.state='freight_paid' and sp.id in \
                            (select distinct del_ord_id from supp_delivery_invoice_rel where invoice_id in \
                                (select \
                                    id  \
                                from account_invoice where partner_id in " + str(part) + " \
                                and date_invoice >='2014-04-01'::date and date_invoice <'"+case.st_date+"'::date and state not in ('draft','cancel') \
                                and type = 'in_invoice'))\
                                and a.partner_id in " + str(part) + "\
                                ) as freight \
                    from account_move_line aml \
                    inner join res_partner rp on aml.partner_id = rp.id \
                    AND aml.account_id in \
                            ((SELECT substr(value_reference,17)::integer \
                             FROM ir_property \
                             WHERE name = 'property_account_payable' \
                             AND  split_part(res_id,',',2)::int in " + str(part) + "\
                             union all \
                             select rp.account_pay\
                             union all\
                             select id from account_account where name ilike '%GST%'))\
                        and aml.partner_id in " + str(part) + "\
                    and aml.date <'"+case.st_date+"'::date \
                    and aml.date>='2014-04-01'::date \
                    and aml.ref not similar to 'DC%|KA%'\
                )a"
        print 'sql',sql
        cr.execute(sql)
        vals = cr.fetchall()
        vals = vals and vals[0] or []
        if vals:
            if vals[0]>0:
                amount = vals[0]
            else:
                amount = vals[1]

            # tot_amount = tot_amount + amount

        self.write(cr, uid, ids, {'open_bal':amount})

        print "data['variables']==========",data['variables']
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'delivery_summary',
            'datas': data,
                }



           
billing_cycle()         

class res_country_state(osv.osv):
    _inherit='res.country.state'
    _columns={
        'branch_office' :   fields.boolean('Branch Office'),
        "is_union"      :   fields.boolean("Is Union Territory"),
        "state_code"    :   fields.char("State Code"),
              }

    _sql_constraints = [
        ('code_uniq', 'unique (code)',
            'The code of the State must be unique !')
    ]
res_country_state()


class goods_trucks(osv.osv):
    _name='goods.trucks'
    _columns={
              'name'    :   fields.char('Trucks Wheelers',size=20),

              }

goods_trucks()

class goods_dealers(osv.osv):
    _name='goods.dealers'
    _columns={
              'partner_id' : fields.many2one('res.partner','partner'),             
              'name'    :   fields.many2one('goods.trucks','Trucks Wheelers'),
              'tol_rate':   fields.float("Rate/Kg"),
              'tol_qty' :   fields.float("Tolerance Qty in Kgs"),
              'date'    :   fields.date('Date'),
              
              }
    _defaults={
               'date':lambda *a: time.strftime('%Y-%m-%d'),
               
               }
    _order = 'date desc'

    
goods_dealers()

class res_partner_bank(osv.osv):
    _inherit = 'res.partner.bank'
    # name '_bank_type_get' is not defined error occurs if not defined here
    
    _columns={
               
           'name': fields.char('Bank Account', size=100), # to be removed in v6.2 ?
            'bank_name': fields.char('Bank Name', size=100),
            'owner_name': fields.char('Owner Name', size=100),
              }
        
    def _bank_type_get(self, cr, uid, context=None):
        bank_type_obj = self.pool.get('res.partner.bank.type')

        result = []
        type_ids = bank_type_obj.search(cr, uid, [])
        bank_types = bank_type_obj.browse(cr, uid, type_ids, context=context)
        result.append(("current_account", "Current Account"))
        result.append(("savings_account", "Savings Account"))
        for bank_type in bank_types:
            result.append((bank_type.code, bank_type.name))
        return result
    
    _columns={
              
            'state': fields.selection(_bank_type_get, 'Bank Account Type',required=False,
                                          change_default=True),
            'bank_address': fields.text('Bank Address'),
            'account_owner'  : fields.char('Owner Name',size=30),
            'owner_name': fields.char('Facilitator Name', size=128),
              }

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        result = []
        acc=self.search(cr,uid,[('id','=',ids[0])])
        if acc:
            if 'acc_num' in context :
                if context['acc_num'] :
#                    partner= context['partner']
#                    acc_ids=self.search(cr,uid,[('partner_id','=',partner)])
                   for i in self.browse(cr,uid,ids):
                        number=i.acc_number
                        result.append((i.id, number))
        return result
        
res_partner_bank()



    
