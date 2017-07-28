from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime
import time
import operator
import re

class kw_product_price(osv.osv):
    _name = 'kw.product.price'
    
    
    
    def _get_total_amount(self, cr, uid, ids, args, field_name, context=None):
        cur_date=datetime.today().strftime("%Y-%m-%d")
        res={}
        tot=0.0
        total=0.0
        for case in self.browse(cr,uid,ids): 
            res[case.id] = {'total': 0.00, 'sub_total':0.00}       
#             tot = case.product_price + case.transport_price + case.handling_charge
            
            res[case.id]['total'] = (case.product_price + case.transport_price + case.handling_charge)
            res[case.id]['sub_total'] = (case.product_price + case.transport_price)
            
        cr.execute("select id from kw_product_price")
        prod_ids=cr.fetchall()  
        i=0

        
        return res
        
    _columns = {
                'ef_date'           : fields.date('Effective Date'),
                'product_price'     : fields.float("Goods Price",digits=(0, 2)),
                'cust_info_id'      : fields.many2one('product.supplierinfo'),
                'supp_info_id'      : fields.many2one('product.supplierinfo'),
                'transport_price'   : fields.float("Freight Price",digits=(0, 2)),
                'total'             : fields.function(_get_total_amount, type='float', string='Total', store=True,multi="total_amount"),
                 'partner_id'       : fields.many2one('res.partner',"Other Facilitators"),
                 'handling_charge'  : fields.float("Differencial Amount", digits=(0, 2)),
                 'proforma_price'   : fields.float("Proforma Goods Rate", digits=(0, 2)),
                 'customer_id'      :   fields.many2one("res.partner","Customer"),
                 'sub_total'        : fields.function(_get_total_amount, type='float', string='Sub Total', store=True,multi="total_amount"),
                 'create_date'      : fields.date("Create Date"),
                 'write_date'       : fields.date("Edit Date"),
             # Re-start Invoice create schedular after rate update
                  
                 
               }
#     _sql_constraints = [
#         ('Customer Effective Date', 'unique(ef_date,cust_info_id)','No Two Rates Can be Added To The Same Date!'),
#         ('Paying Agent Effective Date', 'unique(ef_date,supp_info_id)','No Two Rates Can be Added To The Same Date!'),
#         ]

    _order = 'ef_date desc'
    
    _defaults = {
                   'transport_price': 0.00,
                   'product_price' : 0.00,
                   'ef_date': lambda *a: time.strftime('%Y-%m-%d'),
                   }
   


    
        
        
          
    def create(self, cr, uid, vals, context=None):
        total=0.00
        if 'cust_info_id' not in vals:
            total=vals['transport_price']+vals['product_price']+vals['handling_charge']
            sub_total=vals['transport_price']+vals['product_price']
            vals.update({"total":total,"sub_total":sub_total})
        else:
            total=vals['transport_price']+vals['product_price'] 
         
            vals.update({"total":total})
        return super(kw_product_price,self).create(cr, uid, vals, context)
    
    def write(self, cr, uid,ids, vals, context=None):
        transport_price=0.00
        product_price=0.00
        handling_charge=0.00
        res=0
        sub_total=0
        pro_info=self.pool.get('product.supplierinfo')
        cust_info_id=False
        for case in self.browse(cr,uid,ids):
            cust_info_id=vals.get('cust_info_id',case.cust_info_id.id)
            if 'cust_info_id' not in vals:
                transport_price = vals.get('transport_price',case.transport_price)
                product_price = vals.get('product_price',case.product_price)
                handling_charge = vals.get('handling_charge',case.handling_charge)
                sub_total=transport_price+product_price
                res=sub_total+handling_charge
                
#                 self.write(cr,uid,ids,{'total':res,'sub_total':sub_total})
                cr.execute("UPDATE kw_product_price SET total =%s where id=%s", (res,case.id))
                cr.execute("UPDATE kw_product_price SET sub_total =%s where id=%s", (sub_total,case.id))
            else:
                transport_price = vals.get('transport_price',case.transport_price)
                product_price = vals.get('product_price',case.product_price)
                res=transport_price+product_price
                cr.execute("UPDATE kw_product_price SET total =%s where id=%s", (res,case.id))
#                 self.write(cr,uid,ids,{'total':res})
            
            if cust_info_id:
               cust_info = pro_info.browse(cr,uid,cust_info_id)
               transport_price = vals.get('transport_price',case.transport_price)
               product_price = vals.get('product_price',case.product_price)
               ef_date = vals.get('ef_date',case.ef_date)               
               if vals.get('ef_date',False) or vals.get('transport_price',False) or vals.get('product_price',False):
                   cr.execute("""select ai.id from account_invoice ai 
                                    inner join account_invoice_line al on al.invoice_id=ai.id
                                    inner join product_supplierinfo ps on ps.cust_product_id=al.product_id
                                    inner join kw_product_price kp on kp.cust_info_id=ps.id
                                    where 
                                    al.product_id=%s and
                                    
                                    al.partner_id= %s and
                                    al.partner_id=ps.name and
                                    ai.type='out_invoice' and ai.state!='cancel'
                                    and date_invoice>=%s
                                   """,(cust_info.cust_product_id.id,cust_info.name.id,ef_date,))
                   inv_id=cr.fetchall()
                   if inv_id:
                       print 'invoice',inv_id
                       raise osv.except_osv(_('Warning'),_(' Cannot Edit This Price Since It Is Used in the Invoice '))
        return super(kw_product_price,self).write(cr, uid,ids, vals, context)
    
kw_product_price()   

         
    


class product_supplierinfo(osv.osv):
    _inherit = "product.supplierinfo"
    
    def _get_uom_id(self, cr, uid, *args):
        cr.execute("select id from product_uom where name='MT(s)'")
        res = cr.fetchone()
        return res and res[0] or False
    
    def _get_city_id(self, cr, uid, *args):

        return res and res[0] or False
    
    def _get_total_amount(self, cr, uid, ids, args, field_name, context=None):
        res={}
        tot=0.0
        for case in self.browse(cr,uid,ids):   
            res[case.id] = {'total': 0.00, 'sub_total':0.00,'name_function':'','city_id':False}     
#             print  "rate=",case.rate  
#             print  "transport_rate=",case.transport_rate  
            res[case.id]['total'] = case.rate + case.transport_rate + case.handling_charge
            res[case.id]['sub_total'] = case.rate + case.transport_rate
            res[case.id]['name_function'] = case.name.name
            res[case.id]['city_id'] = case.name.city_id.id
#             res[case.id] = case.total
            
        return res 
    
    
    _columns = {
                
              'name'             :  fields.many2one('res.partner', 'Facilitators', required=True, ondelete='cascade', help="Supplier of this product"),
              'rate'             :  fields.float("Goods Rate", digits=(0, 2)),
              'total'            : fields.function(_get_total_amount, type='float', string='Total', store=True,multi="total_amount"),
              'transport_rate'   :  fields.float("Freight Rate", digits=(0, 2)),
              'product_id'       :  fields.many2one('product.template', 'Goods'),
              'cust_product_id'  :  fields.many2one('product.template', 'Goods'),

              'type'             :  fields.selection([('customer', 'Customer'), ('supplier', 'Paying Agents')], 'Type'),
              'cust_price_ids'   :  fields.one2many('kw.product.price', 'cust_info_id', 'Customer Price'),
              'supp_price_ids'   :  fields.one2many('kw.product.price', 'supp_info_id', 'Supplier Price'),
              'product_uom'      : fields.related('product_id', 'uom_po_id', type='many2one', relation='product.uom', string="Supplier Unit of Measure", readonly="1", help="This comes from the product form."),
              'min_qty'          : fields.float('Minimal Quantity', required=True, help="The minimal quantity to purchase to this supplier, expressed in the supplier Product Unit of Measure if not empty, in the default unit of measure of the product otherwise."),
              'partner_id'       : fields.many2one('res.partner',"Other Facilitators"),
              'handling_charge'  : fields.float("Differencial Amount", digits=(0, 2)),
              'proforma_price'   : fields.float("Proforma Goods Rate", digits=(0, 2)),
              'depot'            : fields.many2one('stock.location', "Depot"),
              'customer_id'      : fields.many2one("res.partner","Customer"),
               'sub_total'       : fields.function(_get_total_amount, type='float', string='Sub Total', store=True,multi="total_amount"),
               'name_function'   : fields.function(_get_total_amount, type='char', size=30,string='Facilitator', store=True,multi="total_amount"),
#                'city_id'         : fields.many2one('kw.city','Area'),
               'city_id'         : fields.function(_get_total_amount, type='many2one', relation='kw.city', store=True,string='Area',multi="total_amount"),
               'dc_count'        : fields.integer('Daily Quota'),
               'location_id'     : fields.many2one('stock.location',"Location"),
               'comp_location'   : fields.boolean("Location"),
               }
    
    
#     _sql_constraints = [
#                         ('customer_name_company_uniq', 'unique(name,cust_product_id)', 'Same Customer Name Cannot Be Added To The Product!'),
#                         ('paying_agent_name_company_uniq', 'unique(name,product_id)', 'Same Paying Agent Name Cannot Be Added To The Product!'),
#                         ]
   
   
    
    def _check_date(self, cr, uid, ids, context=None):
        all_cust = []
        all_sup =[]
        prod_s = self.browse(cr, uid, ids, context=context)
        for prod in prod_s:
            res = True
            res1=True
            for cust in prod.cust_price_ids:
                if cust.ef_date in all_cust:
                    res = res and False
                    raise osv.except_osv(_('Warning'),_(' Product Rate For The customer "%s" The Date Entered "%s" Already Exist')% (prod.name.name,cust.ef_date))
                all_cust.append(cust.ef_date)
                
            for sup in prod.supp_price_ids:
                if sup.ef_date in all_sup:
                    res = res and False
                    raise osv.except_osv(_('Warning'),_(' Product Rate For The Paying Agent "%s" The Date Entered "%s" Already Exist"')% (prod.name.name, sup.ef_date))
                all_sup.append(sup.ef_date)   
            return res
        return True  
    
    _constraints = [(_check_date, 'Please avoid spam in Date !', ['name'])]
    _order = 'name_function'
    _defaults = {
               #  overridden
               'product_uom':_get_uom_id,
               'min_qty' :  1,
               "sub_total": 0,
               'dc_count' : 10,
               'comp_location':False,
               }  

#     
    
    def onchange_depot(self, cr, uid, ids, depot=False, customer_id = False, context=None):
        res ={} 
        warning=''
        res['depot']=depot
        res['customer_id']= False
        
        if customer_id != False:
            res['depot']=False
            res['customer_id']= False
            
            warning={
                                         'title':_('Warning!'), 
                                                'message':_('Select Either Depot or Customer....! You Cannot Select Both.')
                                             }
            
            
                
        
        return{'value':res ,'warning':warning}
        
    def onchange_customer(self, cr, uid, ids, customer_id=False, depot = False, context=None):
        res ={} 
        warning=''
        res['customer_id']=customer_id
        res['depot']= False
        
        if  depot != False:
            res['customer_id']= False
            res['depot']=False
            warning={
                                         'title':_('Warning!'), 
                                                'message':_('Select Either Customer or Depot....! You Cannot Select Both.')
                                             }
 
        return{'value':res ,'warning':warning}  
        
    def onchange_facilitator(self, cr, uid, ids, name=False, context=None):
        res ={} 
        warning=''
        
        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
        kw_paying_agent=cr.fetchall()
        kw_paying_agent=zip(*kw_paying_agent)[0]        
        
        if  name not in kw_paying_agent:
            res['location_id']= False
            res['comp_location']= False
        else:
            res['comp_location']= True
            
        return{'value':res}        
        
      
    def create(self, cr, uid, vals, context=None):
        
        res = {}
        rate = 0
        count=0
        date=0
        r=0
        customer_id=""
        depot=""
        price_date={}
        prod=[]
        price=0
        transport_price=0
        transport_date={}
        handling_charge=0.00
        handling_date={}
        other_partner={}
        proforma_date={}
        transport_price=0.00
        account_pool = self.pool.get('account.invoice.line')
        partner_obj = self.pool.get('res.partner')
        if vals.get('customer_id', False):
            customer_id=vals.get('customer_id', False)
        if vals.get('depot', False):
            depot=vals.get('depot', False)
        if vals.get('name', False):
            partner_id=vals.get('name', False) 
        supplier_id=partner_obj.browse(cr,uid,partner_id)
        
        if supplier_id:
            vals.update({'city_id':supplier_id.city_id.id})
        
        if depot==False and customer_id==False:
            raise osv.except_osv(_('Warning'),_(' select Customer or Depot For the Supplier "%s" ')% (vals['name']))
            
        
        if vals.get('cust_price_ids', False):
                prod = vals.get('cust_product_id',False)
        
                prod_obj = self.pool.get('product.template').browse(cr,uid,[prod])[0]
                price = prod_obj.list_price
                
                cur_date=datetime.today().strftime("%Y-%m-%d")
                
                start_date = vals['cust_price_ids'][0][2]['ef_date']
                
                for ln in vals['cust_price_ids']:
                      if ln[2]['ef_date'] <= cur_date:
                          price_date.update({ ln[2]['product_price']:ln[2]['ef_date']})
                          transport_date.update({ ln[2]['transport_price']:ln[2]['ef_date']})
                          proforma_date.update({ln[2]['proforma_price']:ln[2]['ef_date']})
#                           handling_date.update({ ln[2]['transport_price']:ln[2]['handling_charge']})
                      if ln[2]['ef_date'] >= start_date:

#                             a.append(start_date)
    #                     and ln[2]['ef_date']<=cur_date:
                            rate = ln[2]['product_price']
                            transport_price=ln[2]['transport_price']
                            proforma_price=ln[2]['proforma_price']
                            start_date = ln[2]['ef_date']
#                     if start_date > cur_date:

#################################################################################################################

#                sort for product price and date

###################################################################################################################
                sorted_price_date = sorted(price_date.iteritems(), key=operator.itemgetter(1))    
                sorted_price_date.reverse()
                if sorted_price_date:
                    rate=sorted_price_date[0][0]
                else:
                    rate=price
 #################################################################################################################

#                sort for tranceport price and date

###################################################################################################################
                sorted_transport_date = sorted(transport_date.iteritems(), key=operator.itemgetter(1))    
                sorted_transport_date.reverse()
                if sorted_transport_date:
                    transport_price=sorted_transport_date[0][0]
                    
#################################################################################################################

#                sort for Proforma price and date

###################################################################################################################
                sorted_proforma_date = sorted(proforma_date.iteritems(), key=operator.itemgetter(1))    
                sorted_proforma_date.reverse()
                if sorted_proforma_date:
                    proforma_price=sorted_proforma_date[0][0]       
                  
                cust_total = transport_price + rate
                vals.update({'rate':rate,'transport_rate':transport_price,'total':cust_total,'proforma_price':proforma_price})
                
#         cur_date=datetime.today().strftime("%Y-%m-%d")
        
        if vals.get('supp_price_ids', False):
                prod = vals.get('product_id',False)
        
                prod_obj = self.pool.get('product.template').browse(cr,uid,[prod])[0]
                price = prod_obj.list_price
                cur_date=datetime.today().strftime("%Y-%m-%d")
                
                start_date = vals['supp_price_ids'][0][2]['ef_date']
                
                for ln in vals['supp_price_ids']:
                      if ln[2]['ef_date'] <= cur_date:
                          price_date.update({ ln[2]['product_price']:ln[2]['ef_date']})
                          transport_date.update({ ln[2]['transport_price']:ln[2]['ef_date']})
                          handling_date.update({ ln[2]['handling_charge']:ln[2]['ef_date']})
                          other_partner.update({ ln[2]['partner_id']:ln[2]['ef_date']})
                      if ln[2]['ef_date'] >= start_date:

#                             a.append(start_date)
    #                     and ln[2]['ef_date']<=cur_date:
                            rate = ln[2]['product_price']
                            transport_price=ln[2]['transport_price']
                            handling_charge=ln[2]['handling_charge']
                            start_date = ln[2]['ef_date']
#                     if start_date > cur_date:
                sorted_price_date = sorted(price_date.iteritems(), key=operator.itemgetter(1))    
                sorted_price_date.reverse()
                if sorted_price_date:
                    rate=sorted_price_date[0][0]
                else:
                    rate=price
                  
                sorted_transport_date = sorted(transport_date.iteritems(), key=operator.itemgetter(1))    
                sorted_transport_date.reverse()
                if sorted_transport_date:
                    transport_price=sorted_transport_date[0][0]
                    
#####################################################################################################

#                sort for Handling charge and date

###################################################################################################################


                sorted_handling_charge = sorted(handling_date.iteritems(), key=operator.itemgetter(1))    
                sorted_handling_charge.reverse()
                if sorted_handling_charge:
                    handling_charge=sorted_handling_charge[0][0]                    
                
                sorted_other_partner = sorted(other_partner.iteritems(), key=operator.itemgetter(1))    
                sorted_other_partner.reverse()
                if sorted_other_partner:
                    other_partner=sorted_other_partner[0][0]   
                sub_total=transport_price+rate   
                total=transport_price+rate+handling_charge
                
                vals.update({'rate':rate,'transport_rate':transport_price,"total":total,'handling_charge':handling_charge,'partner_id':other_partner,'sub_total':sub_total})
        return super(product_supplierinfo,self).create(cr, uid, vals, context)
    

    def write(self, cr, uid, ids, vals, context=None):
        for case in self.browse(cr,uid,ids):
            if case.name.city_id.id and not case.city_id:
                vals.update({'city_id':case.name.city_id.id})            
        res = super(product_supplierinfo, self).write(cr, uid, ids, vals, context=None)
        cur_date=datetime.today().strftime("%Y-%m-%d")
        total=0
        product_price_id=0
        prod_det=[]
        prod_ids=[]
        product=[]
        value={}
        p_id=[]
        product_price=[]
        partner_name=[]
        transport_price=[]
        ef_date=[]
        date=[]
        partner=[]
        cur_ids=[]
        all_ids=[]
        depot=''
        customer_id=''
#         print "vals.values()[0][1]=", vals.values()[0][1]
        if vals:
            
            if vals.get('customer_id', False):
                customer_id=vals.get('customer_id', False)
            if vals.get('depot', False):
                depot=vals.get('depot', False)
        
            if depot==False and customer_id==False:
                raise osv.except_osv(_('Warning'),_(' select Customer or Depot For the Supplier "%s" ')% (vals['name']))
#             if vals.values()[0][1]:
#                 print "vals.values()[0][1]=", vals.values()[0][1]
#             if 'cust_price_ids' in vals:
#                 account_pool = self.pool.get('account.invoice.line')
#                 cr.execute('select id from kw_product_price where cust_info_id =%s', (str(ids[0]),) )
#                 cur_prod=cr.fetchall()
#                 x=0
#                 y=0
#                 z=0
#                 for x in cur_prod:
#                     cur_ids.append(x[0])
#                 y=len(cur_ids)
#                 
# #                 for case in self.browse(cr,uid,prod_ids):
#                 product= vals.values()   
#                 product_price_id=vals['cust_price_ids']
#                 price_id=product_price_id[0][1]
#                 value=product_price_id[0][2]
#                 
#                 if not value:
#                     price_id=product_price_id[y-1][1]
#                     value=product_price_id[y-1][2]
#                 for z in cur_ids:
#                     if value==False:
#                         y=y-1
#                         price_id=product_price_id[y][1]
#                         value=product_price_id[y][2]
#                         
#                         
#                 if value and price_id:
#                     if 'product_price' in value or 'transport_price' in value or "ef_date" in value:
#                         
#                         cr.execute('select cust_info_id,product_price,transport_price,ef_date from kw_product_price where id =%s', (str(price_id),) )
#                         prod=cr.fetchall()
#                         k=0
#                         for k in prod:
#                             p_id.append(k[0])
#                             product_price.append(k[1])
#                             transport_price.append(k[2])
#                             ef_date.append(k[3])
#                         
#                         b=0
#                         for b in p_id:
#                             if b==ids[0]:
#                                 cr.execute('select cust_product_id,name from product_supplierinfo where id =%s', (str(b),) )
#                                 prod_det=cr.fetchall()
#                         i=0
#                         for i in prod_det:
#                             prod_ids.append(i[0])
#                             partner_name.append(i[1])
#                         j=0
#     #                     if ids[0] in prod_ids:
#                             
#                         account_ids = account_pool.search(cr, uid, [('product_id','=',prod_ids[0])])
#                         if account_ids:
#                             tax_account = account_pool.browse(cr, uid, account_ids[0])
#                             for j in account_pool.browse(cr,uid,account_ids):
#                                 id=j.invoice_id.id
#                                 cr.execute("select date_invoice,partner_id from account_invoice where id = "+ str(id)+"and type='out_invoice'")
#                                 date_partner=cr.fetchall()
#                                 m=0
#                                 for m in date_partner:
#                                     date.append(m[0])
#                                     partner.append(m[1])
#                                 
#                                 if partner_name[0] in partner:
#     #                                 if ef_date[0] in date:
#     #                                     raise osv.except_osv(_('Warning'),_(' Cannot Edit This Price Since It Is Used in the Invoice '))
#                                     
#                                     cr.execute('select ef_date from kw_product_price where id =%s', (str(price_id),) )
#                                     cur_date=cr.fetchall()
#                                     p=0
#                                     prod_date_ids=[]
#                                     for p in cur_date:
#                                         prod_date_ids.append(p[0])
#                                     
#                                     lenght=len(cur_ids)
#                                     for n in ef_date:
#                                             if n<=prod_date_ids[0]:
#                                                 raise osv.except_osv(_('Warning'),_(' Cannot Edit This Price Since It Is Used in the Invoice '))
                                            
                                        
    #                 for j in prod_ids:
    #                     cr.execute('select id from kw_product_price where cust_info_id =%s', (str(j),) )
    #                     prod=cr.fetchall()
    #                     k=0
    #                     for k in prod:
    #                         product.append(k[0])
    #                     print product
                  
        # to fetch the recent date and price of the product for cuatomer and supplier
        for case in self.browse(cr, uid, ids):
            total=0
            if case.cust_price_ids:
                rate = 0
#                 cr.execute('select product_price from kw_product_price where cust_info_id =' + str(case.id) + 'order by ef_date desc limit 1')
                cr.execute('select product_price,total,proforma_price from kw_product_price where cust_info_id =%s and ef_date<= %s order by ef_date desc limit 1', 
                           (str(case.id),cur_date,) )
                rate = cr.fetchone()
                if rate:
                    cr.execute('update product_supplierinfo set rate=%s,total=%s,proforma_price=%s where id = %s', (rate[0],rate[1],rate[2], str(case.id)))
                else:
                    cr.execute('select list_price from product_template where id =' + str(case.cust_product_id.id))
                    rate = cr.fetchone()
                    if rate:
                         cr.execute('update product_supplierinfo set rate=%s where id = %s', (rate[0],str(case.id)))
                
                
                transport_rate=0
                cr.execute('select transport_price,total from kw_product_price where cust_info_id =%s and ef_date<= %s order by ef_date desc limit 1', 
                           (str(case.id),cur_date,) )
                transport_rate = cr.fetchone()
                if transport_rate:
                    cr.execute('update product_supplierinfo set transport_rate=%s, total=%s where id = %s', 
                               (transport_rate[0],transport_rate[1],str(case.id)))
               
                                        
                
            if case.supp_price_ids:
                rate = 0
                cr.execute('select product_price,transport_price,total,sub_total,partner_id,handling_charge from kw_product_price where supp_info_id =%s and ef_date<= %s order by ef_date desc limit 1', (str(case.id),cur_date,) )
                rate = cr.fetchone()
                if rate:
#                     total=rate[0]+rate[1]+rate[4]
                    cr.execute('update product_supplierinfo set rate=%s ,transport_rate = %s,total=%s, sub_total=%s,partner_id=%s,handling_charge=%s where id = %s', 
                               (rate[0], rate[1], rate[2],rate[3],rate[4],rate[5],str(case.id)))
                else:
                    cr.execute('select list_price from product_template where id =' + str(case.product_id.id))
                    rate = cr.fetchone()
                    if rate:
                        cr.execute('update product_supplierinfo set rate=%s where id = %s', (rate[0], str(case.id)))
#                 cr.execute('select product_price from kw_product_price where cust_info_id =' + str(case.id) + 'order by ef_date asc limit 1')
#                 rate = cr.fetchone()
#                 if rate:
#                     cr.execute('update product_supplierinfo set rate=%s where id = %s', (rate[0], str(case.id)))
            

            
        return res
    
product_supplierinfo()

class product_template(osv.osv):
    _inherit = "product.template"
    #  overridden
    def _get_uom_id(self, cr, uid, *args):
        cr.execute("select id from product_uom where name='MT(s)'")
        res = cr.fetchone()
#         self._get_update(cr, uid, [uid])
        return res and res[0] or False
    
    def _get_update(self, cr, uid, ids,context = None):
        res ={}
        cr.execute("select id from product_template")
        prod_ids=cr.fetchall()
        i=0
        i_ids=[]
        total=0
        for i in prod_ids:
            i_ids.append(i[0])
            
            for case in self.browse(cr,uid,i_ids):
                for temp in case.customer_ids:
                        for j in temp.cust_price_ids:
                            total=j.product_price+j.transport_price
                            cr.execute("UPDATE kw_product_price SET total =%s where id=%s", (total,j.id))
                            
            i_ids.remove(i[0])
        return True
    
    _columns = {
              'uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True, help="Default Unit of Measure used for all stock operation."),
              'seller_ids': fields.one2many('product.supplierinfo', 'product_id', 'Supplier') ,
              'customer_ids': fields.one2many('product.supplierinfo', 'cust_product_id', 'Customer') ,
              'cst_taxes_id': fields.many2many('account.tax', 'product_csttaxes_rel',
               'prod_id', 'tax_id', 'Customer Taxes(CST)',
                                    domain=[('parent_id','=',False),('type_tax_use','in',['sale','all'])]),
                'work_order_ids'  : fields.one2many('work.order','product_id','Work Orders'),
                'cft'  : fields.boolean("CFT"), 
               'product_rate'  :   fields.boolean('Product Rate'),

                'hsn_sac'           : fields.char("HSN/SAC", size=8),

                #UPDATE PURPOSE
#                 'update'    :   fields.function(_get_update,type="boolean",string="location_id",store=True),
              }
    _defaults = {
               #  overridden
                 'uom_id':_get_uom_id,
     
               }

    def onchange_hsn_sac_code(self, cr, uid, ids, hsn_sac, context=None):
        if not context:
            context = {}
        warning = {}
        res = {}
        if hsn_sac:
            if not re.match('^[a-z_A-Z]+$',hsn_sac):
                warning = {
                    'title': _('Warning!'),
                    'message': _('Special Charecters not allowed in GST Code.')
                      }
                res.update({'hsn_sac':False})
            else:
                res.update({'hsn_sac':hsn_sac})

        return {'value':res, 'warning' : warning}
    
    def create_inv(self,cr,uid,ids,context=None):
        inv_obj = self.pool.get('account.invoice')
        inv_obj.create_facilitator_inv(cr,uid,[uid],context)
        return True

    def _check_product(self, cr, uid, ids, context=None):
        all_cust = []
        all_sup ={}
        all_sup1 =[]
        all_sup2 =[]
        w_work=[]
        w_order=[]
        cust=[]
        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
        kw_paying_agent=cr.fetchall()
        kw_paying_agent=zip(*kw_paying_agent)[0]        
        
        products = self.browse(cr, uid, ids, context=context)
        for prod in products:
            res = True
            
            for cust in prod.customer_ids:
                if cust.name.id in all_cust:
                    res = res and False
                    raise osv.except_osv(_('Warning'),_(' Product Rate For The customer "%s" Already Exist ')% (cust.name.name))
                all_cust.append(cust.name.id)
               
            
                
            depot=[]
            cust=[]
            for sup in prod.seller_ids:
                if sup.name.id not in kw_paying_agent:
                    if sup.name.id and sup.customer_id.id:
                        all_sup1.append(sup.name.id)
                        all_sup1.append(sup.customer_id.id)
                        
                        if all_sup1 in cust:
                            
                            raise osv.except_osv(_('Warning'),_(' Product Rate For The Paying Agent "%s" And Customer %s Already Exist ')% 
                                                     (sup.name.name,sup.customer_id.name))
                        
                        
                        
                        cust.append(all_sup1)
                        all_sup1=[]
                        
                    
                    if sup.name.id and sup.depot.id:
                        all_sup2.append(sup.name.id)
                        all_sup2.append(sup.depot.id)
                        
                        if all_sup2 in depot:
                            
                            raise osv.except_osv(_('Warning'),_(' Product Rate For The Paying Agent "%s" And depot %s Already Exist ')% 
                                                      (sup.name.name,sup.depot.complete_name))
                        
                        
                        
                        depot.append(all_sup2)
                        
                        all_sup2=[]
            
            # Same Cutomer, Same State and Same Work order num should not be repeated    
            for w in prod.work_order_ids:
                w_work.append(w.partner_id.id)
                w_work.append(w.state_id.id)
                w_work.append(w.work_order_no)
                if w_work in w_order:
                    
                    raise osv.except_osv(_('Warning'),_(' Work Order Number For The Customer "%s", State "%s", And Work Order "%s" Already Exist on "%s", Cannot Add More Than Once')% 
                                              (w.partner_id.name,w.state_id.name,w.work_order_no,w.work_order_date))
                
                
                
                w_order.append(w_work)

                w_work=[]
               
            
                
            depot=[]
            cust=[]       
            w_order=[]
            return res
        
        
        return True  
    
    _constraints = [
        (_check_product, 'Product Rate For The Paying Agent Already Exist', []),
    ]
    
product_template()

# class product_product(osv.osv):
#     _inherit = 'product.product'
#     _columns = {
#                 'work_order_ids'  : fields.one2many('work.order','product_id','Work Orders')
#                 }
# product_product()


class work_order(osv.osv):
    _name = 'work.order'
    _rec_name = 'work_order_no'
    _columns = {
                'partner_id'    : fields.many2one('res.partner','Customer', domain=[('customer','=',True)]),
                'state_id'      : fields.many2one('res.country.state','State', domain=[('country_id','=',105)]),
                'work_order_no' : fields.char('Work Order',size=30),
                'product_id'    : fields.many2one('product.template','Product'),
                'work_order_date': fields.date('Date'),
                }
#     _sql_constraints = [
#         ('Work Order Number ', 'unique(work_order_no)','Work Order Number Should Be Repeat!'),
#         
#         ]
    _order = 'work_order_date desc'
    _defaults = {
        
        'work_order_date': lambda *a: time.strftime('%Y-%m-%d'),
    }

work_order()


class product_product(osv.osv):
    _inherit = "product.product"

    _columns = {

               'product_rate'       :   fields.boolean('Product Rate'),
                #UPDATE PURPOSE
                'dc_state'          :   fields.char('State',size=30),
                'less_addl_amt'     :   fields.float("Less: Addl.SD Rs.", digits=(16,2)),
              }

    _defaults = {
        
        'product_rate': False,
    }
    
    def create_inv(self,cr,uid,ids,context=None):
        inv_obj = self.pool.get('account.invoice')
        self.write(cr,uid,ids,{'product_rate':False})
#         for case in self.browse(cr,uid,ids):
#             context.update({'state':case.dc_state})
        inv = inv_obj.create_facilitator_inv(cr,uid,[uid],context)
        
        return True   

    def onchange_hsn_sac_code(self, cr, uid, ids, hsn_sac, context=None):
        if not context:
            context = {}
        warning = {}
        res = {}
        if hsn_sac:
            if not re.match('^[0-9]+$',hsn_sac):
                warning = {
                    'title': _('Warning!'),
                    'message': _('Special Charecters not allowed in HSN/SAC Code.')
                      }
                res.update({'hsn_sac':False})
            else:
                res.update({'hsn_sac':hsn_sac})

        return {'value':res, 'warning' : warning}


product_product()    
    
    
    
