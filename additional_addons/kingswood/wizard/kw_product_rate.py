from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import tools
from datetime import datetime
# import datetime
import logging
import time
from lxml import etree

class kw_product_rate(osv.osv_memory):
    _name = "kw.product.rate"
    _columns = {
                    'product_id'    :   fields.many2one("product.product","Goods"),
                    'partner_id'    :   fields.many2one("res.partner","Customer"),
                    'depot'         :   fields.many2one('stock.location', "Depot"),
                    'city_id'          : fields.many2one('kw.city','Area'),    
 #                    'city_id'       :   fields.many2one("res.country.state","Area"),
                    'ef_date'           : fields.date('Effective Date'),
                    'product_price'     : fields.float("Goods Price",digits=(0, 2)),
                    'transport_price'   : fields.float("Freight Price",digits=(0, 2)),
    
                     'facilitator_id'       : fields.many2one('res.partner',"Other Facilitators"),
                     'handling_charge'  : fields.float("Differencial Amount", digits=(0, 2)),                
              }
    
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
    
    def default_get(self, cr, uid, fields, context=None):
        res={}
        product_obj=self.pool.get('product.product')
        active_id=context.get('active_id',False)
        supplierinfo_obj=self.pool.get('product.supplierinfo')
#         product_sup=supplierinfo_obj.search(cr,uid,[('city_id','=',False)])
#         for case in supplierinfo_obj.browse(cr,uid,product_sup):
#             supplierinfo_obj.write(cr,uid,[case.id],{'city_id':case.name.city_id.id})
        
        res['product_id']=False
        res['partner_id']=False
        res['depot']=False
        res['city_id']=False
        res['ef_date']=False
        res['product_price']=False
        res['transport_price']=False
        res['facilitator_id']=False
        res['handling_charge']=False  
        if active_id:
            res['product_id']=active_id
        return res
    
    def change(self, cr, uid, ids, context = None):
        today = time.strftime('%Y-%m-%d')
        price_obj=self.pool.get('kw.product.price')
        product_obj=self.pool.get('product.product')
        prod_sup_obj=self.pool.get('product.supplierinfo')
        partner_obj=self.pool.get('res.partner')
        vals={}
        partner_id=[]
        for case in self.browse(cr,uid,ids):
            vals.update({
                         'ef_date' : case.ef_date,
                         'product_price':case.product_price,
                         'transport_price':case.transport_price,
#                          'partner_id':case.facilitator_id.id,
                         'handling_charge':case.handling_charge,
                         
                         })
            
        if case.product_price>0 or case.transport_price>0 or case.handling_charge>0:
            sup_name=''            
                         
            if case.partner_id:
                supplierinfo_id=prod_sup_obj.search(cr,uid,[('customer_id','=',case.partner_id.id),('product_id','=',case.product_id.id)])
                for i in prod_sup_obj.browse(cr,uid,supplierinfo_id):
                     all_sup=[]
                     if case.city_id:
                         if i.name.city_id.id == case.city_id.id:
                            sup_name=i.name.name
                            sup_name=sup_name.upper()
                            if sup_name:
                                 partner_id=partner_obj.search(cr,uid,[('name','=',sup_name)])
                            if partner_id:
                                 vals.update({ 'partner_id':partner_id[0]}) 
                                                         
                            vals.update({'supp_info_id':i.id})
                            for sup in i.supp_price_ids:
    #                             if sup.ef_date in all_sup:
                                if case.ef_date==sup.ef_date:
                                    raise osv.except_osv(_('Warning'),_(' Product Rate For The Paying Agent "%s" The Date Entered "%s" Already Exist"')% (i.name.name, sup.ef_date))
                                if case.ef_date<sup.ef_date:
                                    raise osv.except_osv(_('Warning'),_(' Product Rate For The Paying Agent "%s" The Date Entered "%s" Already Exist, Enter Greater Than "%s" Date"')% (i.name.name, sup.ef_date,sup.ef_date))
                                all_sup.append(sup.ef_date)
                                  
                            prod_sup_obj._check_date(cr,uid,[i.id])
                            price_obj.create(cr,uid,vals)
                            prod_sup_obj.write(cr,uid,[i.id],{'supp_price_ids':vals})
#                             price_id=price_obj.search(cr,uid,[('supp_info_id','=',i.id)])
#                             price_obj.write(cr,uid,price_id,{'write_date':today})
                            print " sup_name",sup_name
                            sup_name=''
                     else:
                            sup_name=i.name.name
                            sup_name=sup_name.upper()
                            if sup_name:
                                 partner_id=partner_obj.search(cr,uid,[('name','=',sup_name)])
                            if partner_id:
                                 vals.update({ 'partner_id':partner_id[0]}) 
                                                         
                            vals.update({'supp_info_id':i.id})
                            for sup in i.supp_price_ids:
    #                             if sup.ef_date in all_sup:
                                if case.ef_date==sup.ef_date:
                                    raise osv.except_osv(_('Warning'),_(' Product Rate For The Paying Agent "%s" The Date Entered "%s" Already Exist"')% (i.name.name, sup.ef_date))
                                if case.ef_date<sup.ef_date:
                                    raise osv.except_osv(_('Warning'),_(' Product Rate For The Paying Agent "%s" The Date Entered "%s" Already Exist, Enter Greater Than "%s" Date"')% (i.name.name, sup.ef_date,sup.ef_date))
                                all_sup.append(sup.ef_date)
                                  
                            prod_sup_obj._check_date(cr,uid,[i.id])
                            price_obj.create(cr,uid,vals)
                            prod_sup_obj.write(cr,uid,[i.id],{'supp_price_ids':vals})
#                             price_id=price_obj.search(cr,uid,[('supp_info_id','=',i.id)])
#                             price_obj.write(cr,uid,price_id,{'write_date':today})
                            print " sup_name",sup_name
                            sup_name=''
                                                       
            if case.depot:
                supplierinfo_id=prod_sup_obj.search(cr,uid,[('depot','=',case.depot.id),('product_id','=',case.product_id.id)])
                for i in prod_sup_obj.browse(cr,uid,supplierinfo_id):
                     all_sup=[]
                     if case.city_id:
                         if i.name.city_id.id == case.city_id.id:
                            sup_name=i.name.name
                            sup_name=sup_name.upper()
                            if sup_name:
                                 partner_id=partner_obj.search(cr,uid,[('name','=',sup_name)])
                            if partner_id:
                                 vals.update({ 'partner_id':partner_id[0]})  
                            vals.update({'supp_info_id':i.id})
                            for sup in i.supp_price_ids:
                                if case.ef_date==sup.ef_date:
                                    raise osv.except_osv(_('Warning'),_(' Product Rate For The Paying Agent "%s" The Date Entered "%s" Already Exist"')% (i.name.name, sup.ef_date))
                                if case.ef_date<sup.ef_date:
                                    raise osv.except_osv(_('Warning'),_(' Product Rate For The Paying Agent "%s" The Date Entered "%s" Already Exist Give Greater That Date"')% (i.name.name, sup.ef_date))
                                all_sup.append(sup.ef_date)                        
                            prod_sup_obj._check_date(cr,uid,[i.id])
                            price_obj.create(cr,uid,vals)    
                            prod_sup_obj.write(cr,uid,[i.id],{'supp_price_ids':vals})                     
                            print " sup_name",sup_name
                            sup_name=''
                     else:

                        sup_name=i.name.name
                        sup_name=sup_name.upper()
                        if sup_name:
                             partner_id=partner_obj.search(cr,uid,[('name','=',sup_name)])
                        if partner_id:
                             vals.update({ 'partner_id':partner_id[0]})  
                        vals.update({'supp_info_id':i.id})
                        for sup in i.supp_price_ids:
                            if case.ef_date==sup.ef_date:
                                raise osv.except_osv(_('Warning'),_(' Product Rate For The Paying Agent "%s" The Date Entered "%s" Already Exist"')% (i.name.name, sup.ef_date))
                            if case.ef_date<sup.ef_date:
                                raise osv.except_osv(_('Warning'),_(' Product Rate For The Paying Agent "%s" The Date Entered "%s" Already Exist Give Greater That Date"')% (i.name.name, sup.ef_date))
                            all_sup.append(sup.ef_date)                        
                        prod_sup_obj._check_date(cr,uid,[i.id])
                        price_obj.create(cr,uid,vals)  
                        prod_sup_obj.write(cr,uid,[i.id],{'supp_price_ids':vals})                       
                        print " sup_name",sup_name
                        sup_name=''  
                                              
        return True
    
kw_product_rate()









 