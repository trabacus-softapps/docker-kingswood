from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import tools
from datetime import datetime
# import datetime
import logging
import time
from lxml import etree

class change_product_qty(osv.osv_memory):
    _name = "change.product.qty"
    

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        res = super(change_product_qty,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='partner_id']"):
            if context.get('default_type', False) !='out':
                node.set('string', 'Facilitator')
            else:
                node.set('string', 'Customer')
                    
        return res
    
    _columns = {
        'product_id'     : fields.many2one('product.product', 'Product'),
        'new_quantity'   : fields.float('Delivered Quantity',digits=(0,3)),
        'stock_move_id'  : fields.many2one('stock.move'),
        'name'           : fields.char('Reference'),
        'cust'           : fields.boolean('Customer invoice'),
        'sup'            : fields.boolean('Facilitator invoice'),
        'partner_id'     : fields.many2one('res.partner','Customer'),
        'rej_qty'        : fields.float('Rejected Quantity',digits=(0,3)),
        'deduction_amt'  : fields.float('Deduction Amount',digits=(0,2)),
        'date'           : fields.date('Delivery Date'),
        'supplier_id'    : fields.many2one('res.partner','Facilitator'),
        'dc_state'       : fields.selection([('draft','Draft'),('in_transit','In Transit'),('auto', 'Waiting Another Operation'),
                                                      ('confirmed', 'Waiting Availability'),
                                                      ('assigned', 'Ready to Deliver'),
                                                      ('done', 'Delivered'),
                                                      ('cancel', 'Cancelled'),
                                                      ('freight_paid','Freight Paid')],'Status', readonly=True, select=True,track_visibility='onchange',),
        'state'          :   fields.selection([('draft','Draft')],'Status', select=True,track_visibility='onchange',),
        'esugam_no'      :   fields.char('E-Sugam No.',size=20),
        'gen_freight'    :   fields.boolean("Generate Freight"),
        'show_freight'   :   fields.boolean("Show Freight"),
        'type'           : fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal')], 'Shipping Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
        'product_qty'     : fields.float('Quantity',digits=(0,3)),
        'freight_balance' :fields.float('Freight Balance',digits=(0,2),track_visibility='onchange'),
        'loaded_qty'     : fields.float('Loaded Quantity',digits=(0,3)),
        }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        cust=False
        sup=False
        stock_obj = self.pool.get('stock.picking.out')
        move=self.pool.get('stock.move')
        res = super(change_product_qty, self).default_get(cr, uid, fields, context=context)
        move_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
        if not move_ids or len(move_ids) != 1:
            # SO Processing may only be done for one at a time
            return res
        move_id, = move_ids 
                
        prod = self.pool.get('stock.picking').browse(cr, uid, move_id, context=context)
        moves = [self._partial_sale_for(cr, uid, s) for s in prod.move_lines ]
        res.update(supplier_id=prod.paying_agent_id.id)
        res.update(dc_state=prod.state)
        res.update(partner_id=prod.partner_id.id)
        res.update(name=prod.name)
        res.update(esugam_no=prod.esugam_no)
        res.update(gen_freight=prod.gen_freight)
        res.update(show_freight=prod.partner_id.show_freight)
        res.update(product_id=moves[0]['product_id'])
        res.update(new_quantity=moves[0]['new_quantity'])
        res.update(rej_qty=moves[0]['rej_qty'])
        
        res.update(stock_move_id=moves[0]['stock_move_id'])
        res.update(deduction_amt=moves[0]['deduction_amt'])
        res.update(date=moves[0]['date'])
        res.update(type=prod.type)
        res.update(product_qty= moves[0]['product_qty'])
        res.update(freight_balance=prod.freight_balance)
        #             res.update(name=prod.name)
        #             res.update({'stock_move_id' : context['active_ids'][0]})
        #             
        if prod.type!='out':
           res.update(date=prod.date)
           
             
        #             cr.execute("SELECT invoice_id FROM delivery_invoice_rel where del_ord_id = "+str(prod.id))
        cr.execute("""SELECT dr.invoice_id FROM delivery_invoice_rel dr inner 
        join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id=%s and ac.state <>'cancel'""",(str(prod.id),))            
        cinv_ids = cr.fetchall()
             
        if cinv_ids:
            cust=True                
        else:
        #                 cr.execute("SELECT invoice_id FROM supp_delivery_invoice_rel where del_ord_id = "+str(prod.id))
            cr.execute("""SELECT dr.invoice_id FROM supp_delivery_invoice_rel dr inner 
            join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id=%s and ac.state <>'cancel'""",(str(prod.id),))
            sinv_ids = cr.fetchall()
        #                 cr.execute("SELECT invoice_id FROM incoming_shipment_invoice_rel where in_shipment_id = "+str(prod.id))
            cr.execute("""SELECT dr.invoice_id FROM incoming_shipment_invoice_rel dr inner 
            join account_invoice ac on ac.id=dr.invoice_id WHERE dr.in_shipment_id=%s and ac.state <>'cancel'""",(str(prod.id),))
            
            in_sinv_ids = cr.fetchall()                
            if sinv_ids or in_sinv_ids:
                sup=True
        
         
        res.update(cust=cust)
        res.update(sup=sup)
        stock_obj.write(cr, uid, [prod.id],{'cust_invoice':cust,'sup_invoice':sup},context = context)    
        return res
    # To Autofill the wizrd data with product,quantity and move line id 
    def _partial_sale_for(self, cr, uid, moln):
        partial_qty = {
            'product_id'        : moln.product_id.id,
            'new_quantity'      : moln.unloaded_qty ,
            'stock_move_id'     : moln.id,
            'rej_qty'           : moln.rejected_qty,
            'deduction_amt'     : moln.deduction_amt,
            'date'              : moln.delivery_date,
            'product_qty'       : moln.product_qty, 
            }
        return partial_qty
    
    
    def onchange_type(self, cr, uid, ids, type=None,context=None):
#         res=super(stock_picking,self).onchange_partner_in(cr, uid, ids,partner_id=False,context=None)
        g_ids = []
        res={}
        dom={}
        if type:
            res['type']=type
    
            if type=='out':
                dom = {'partner_id':  [('customer','=', True)]}
            else:
                dom = {'partner_id':  [('supplier','=', True)]}
            
        return {'value':res,'domain':dom}   
   
     
    
    def change(self, cr, uid, ids, context = None):
        loc_id= False
        gen_fr=False
        log_partner=False
        loc_dest_id=False
        cust_voucher = []
        prod_id=False
        loc_dest_id=False
        cust=False
        sup=False
        pick_type = ''
        pick_obj = self.pool.get('stock.picking.out')
        move=self.pool.get('stock.move')
        voucher_obj=self.pool.get('account.voucher')
        journal_obj=self.pool.get('account.journal')
        acc_obj=self.pool.get('account.account')
        move_line_obj=self.pool.get('account.move.line')
        user_obj=self.pool.get('res.users')
        stock_id=context['active_ids']
        stock_ids=pick_obj.browse(cr,uid,ids)
        state=False
        esugam=False
        freight=False
        transporter=False
        name=''
        cust_id=False
        pay_freight=False
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company1=cr.fetchone()
        if company1:
            company1=company1[0]
        today = time.strftime('%Y-%m-%d')
        freight_account=0
        for case in self.browse(cr, uid, ids):
            if case.dc_state in ('in_transit'):
                st_id=pick_obj.browse(cr,uid,stock_id)
                
                if case.loaded_qty > 40:
                    raise osv.except_osv(_('Warning'),_("Enter the Quantity in Metric Tons Eg. if the loaded quantity is 16800 kgs enter 16.800"))
                else:       
                    pick_obj.write(cr, uid, stock_id,{
                                                     'qty':case.loaded_qty,
                                                   
                                              },context = context)  
                    cr.execute("""update stock_picking set qty="""+str(case.loaded_qty)+"""where id in %s""",(tuple(stock_id),))    
                    move.write(cr, uid, [case.stock_move_id.id],{'product_qty':case.loaded_qty},context = context)            
            
            if case.dc_state not in ('in_transit'):
                if case.new_quantity>50:
                     raise osv.except_osv(_('Warning'),_("Enter the Quantity in Metric Tons Eg. if the loaded quantity is 16800 kgs enter 16.800"))            
                supplier_id=case.supplier_id.id
                print case.state
                state=case.dc_state
                print "status",case.dc_state
                name= str(case.name)
                cust=case.cust
                sup=case.sup
                if case.esugam_no:
                    if len(case.esugam_no)>1:
                        esugam=case.esugam_no
                if not cust or not sup:
    #                 cr.execute("SELECT invoice_id FROM delivery_invoice_rel where del_ord_id = "+str(stock_id[0]))
                    cr.execute("""SELECT dr.invoice_id FROM delivery_invoice_rel dr inner 
                    join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id=%s and ac.state <>'cancel'""",(str(stock_id[0]),))
                    cinv_ids = cr.fetchall()
                    if cinv_ids:
                        cust=True
                        
                    else:
    #                     cr.execute("SELECT invoice_id FROM supp_delivery_invoice_rel where del_ord_id = "+str(stock_id[0]))
                        cr.execute("""SELECT dr.invoice_id FROM supp_delivery_invoice_rel dr inner 
                        join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id=%s and ac.state <>'cancel'""",(str(stock_id[0]),))
                        sinv_ids = cr.fetchall()
                        if sinv_ids:
                            sup=True
    
    #             if cust not sup:
                        
    #                     raise osv.except_osv(_('Warning'),_('Customer Invoice Already Generated For The "%s" Cannot Change Product or Quantity, Click on Cancel')% (case.name))
                    
                if sup:
                        raise osv.except_osv(_('Warning'),_('Facilitator Invoice Already Generated For The "%s" Cannot Change Product or Quantity, Click on Cancel')% (case.name))
                   
                st_id=pick_obj.browse(cr,uid,stock_id)
                for temp in st_id:
                    for i in temp.move_lines:
                        loc_id=i.location_id.id
                        prod_id=i.product_id.id
                        partner_id=temp.partner_id.id
                        move.write(cr,uid,[i.id],{'state':'draft'})
                        state=str(temp.state)
                        
                    transporter=temp.transporter_id.id
                    freight=temp.gen_freight or temp.partner_id.freight
                    paying_agent_id=temp.paying_agent_id
                    company=temp.company_id.id
                    today=temp.delivery_date_function and temp.delivery_date_function or temp.date
                    cust_id=case.partner_id.id or temp.partner_id.id
                    pick_type=temp.type
                    freight_balance = temp.freight_balance
                    pay_freight = temp.partner_id.pay_freight
                if case.state=='draft':
                    state=str(case.state)
                    if esugam:
                        raise osv.except_osv(_('Warning'),_('Esugam Number Already generated, Cannot Change The Status'))
                    
                    voucher=voucher_obj.search(cr,uid,[('state','=','draft'),('reference','=',case.name),('partner_id','=',cust_id)])
                    voucher_done=voucher_obj.search(cr,uid,[('state','=','posted'),('reference','=',case.name),('partner_id','=',cust_id)])
                    if voucher:
                        voucher_obj.unlink(cr, uid, voucher,context = context)
                    if voucher_done:
                        state=case.dc_state
                        raise osv.except_osv(_('Warning'),_('Voucher Posted, Cannot Change The Status'))
                    
                move.onchange_product_id(cr, uid, [case.stock_move_id.id], prod_id, loc_id,loc_dest_id, partner_id)
                move.write(cr, uid, [case.stock_move_id.id],{'product_id':case.product_id.id,'unloaded_qty':case.new_quantity,
                                                          'rejected_qty':case.rej_qty, 'deduction_amt':case.deduction_amt,
                                                          'delivery_date':case.date},context = context)
                                                          
                
                if case.supplier_id.id==temp.company_id.partner_id.id and case.supplier_id.id!=temp.paying_agent_id.id:
                    cr.execute("select partner_id from res_company where lower(name) like '%logistics%'")
                    log_partner=cr.fetchone()
                    if log_partner:
                        log_partner=log_partner[0]
                    if not temp.transporter_id:
                        pick_obj.write(cr, uid, context['active_ids'],{'transporter_id':log_partner},context = context)
                else:
                    if temp.transporter_id:
                        pick_obj.write(cr, uid, context['active_ids'],{'transporter_id':False},context = context)
                        
                pick_obj.write(cr, uid, context['active_ids'],{'product_id':case.product_id.id,
                                                               'del_quantity':case.new_quantity,
                                                                'cust_invoice':cust,
                                                                'sup_invoice':sup,
                                                                'partner_id':cust_id,
                                                                 'delivery_date_function':case.date,
                                                                 'paying_agent_id':case.supplier_id.id,
                                                                 'deduction_amt':case.deduction_amt,
                                                                 'rej_quantity':case.rej_qty,
                                                                 'state':state,
                                                                 'freight_balance':case.freight_balance,
                                                                 'gen_freight':case.gen_freight
                                                          },context = context)
                if pick_type == 'in':
                    pick_obj.write(cr, uid, context['active_ids'],{
                                                     'date':case.date,
                                                   
                                              },context = context)
                context.update({'state':state,'name':name})
                
    #             pick_obj.onchange_paying_agent(cr,uid,context['active_ids'],case.supplier_id.id,transporter,context=context)
                if case.state!='draft':
                    move.action_done(cr, uid,[case.stock_move_id.id], context=None)
                 
                
                gen_freight=case.gen_freight or case.partner_id.freight or False
                if gen_freight:
                    comp=company1
                else:
                    comp=company
                freight_journal=journal_obj.search(cr, uid, [('name','like','Freight'),('company_id','=',comp)])
                if freight_journal:
                    journal_id=freight_journal[0]
                    
                freight_account=acc_obj.search(cr, uid, [('name','like','Freight'),('company_id','=',comp)])
                if freight_account:
                    freight_account=freight_account[0]        
                            
                if state=='freight_paid':
                   cr.execute("""SELECT dr.invoice_id FROM supp_delivery_invoice_rel dr inner 
                   join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id  IN %s and ac.state <>'cancel'""",(tuple(stock_id),))    
                        
                   order_id = cr.fetchall()                    
                    
                   voucher=voucher_obj.search(cr,uid,[('reference','=',name),('type','=','payment'),('partner_id','=',paying_agent_id.id)])
                   cust_voucher=voucher_obj.search(cr,uid,[('reference','=',name),('type','=','receipt'),('partner_id','=',cust_id)])
                   if case.freight_balance != freight_balance:
                       if cust_voucher and pay_freight and order_id:
                           raise osv.except_osv(_('Warning'),_('Freight Paid By Customer, Cannot change Freight balance')) 
                         
                if state=='freight_paid' and not sup:                  
    #                    if cust_voucher:
    #                        cr.execute("select create_uid from account_voucher where id=%s",(tuple(cust_voucher),))
    #                        voucher_uid=[x[0] for x in cr.fetchall()]
    #                        for v_uid in user_obj.browse(cr,uid,voucher_uid):
    #                            if v_uid.role =='customer':
    #                                raise osv.except_osv(_('Warning'),_('Freight Paid By Customer, Cannot change Freight balance')) 
    #                                                   
    #                    if cust_voucher and :
    #                        raise osv.except_osv(_('Warning'),_('Freight Paid By Customer, Cannot change Freight balance'))   
    #                        cr.execute("select create_uid from account_voucher where id=%s",(tuple(voucher),))
    #                        voucher_uid=[x[0] for x in cr.fetchall()]   
                                               
    #                        for v_uid in user_obj.browse(cr,uid,voucher_uid):
    #                            if v_uid.role =='customer':
                                    
                       
                   cr.execute("select invoice_id from supp_delivery_invoice_rel where del_ord_id=%s",(case.id,))
                   invoice=[x[0] for x in cr.fetchall()]
                   paying_agent_id=case.supplier_id
                   for i in invoice:
                       invoice_id=invoice_obj.search(cr,uid,[('id','=',i),('state','=',open)])  
                       if invoice_id:
                           for inv in invoice_obj.browse(cr,uid,invoice_id):
                               if inv.state=='in_invoice':   
                                   raise osv.except_osv(_('Warning'),_('Invoice Is in open state')% (inv.name,))   
                       
                   acc_id=case.supplier_id.property_account_payable and case.supplier_id.property_account_payable.id or False
                   if paying_agent_id.parent_id:
                       cc_id=case.supplier_id.parent_id.property_account_payable and case.supplier_id.property_account_payable.parent_id.id or False
                   if gen_freight:
                       
                       acc_id=case.supplier_id.account_rec and case.supplier_id.account_pay.id or False
                       if paying_agent_id.parent_id:
                           acc_id=case.supplier_id.parent_id.account_pay and case.supplier_id.parent_id.account_pay.id or False
                           
                   cr.execute("select id from account_period where company_id='"+ str(comp) +"'and date_start <= '" + today + "' and date_stop >='" + today + "'")
                   period = cr.fetchone()  
                   
                   if freight_balance != case.freight_balance:
                       for vc in voucher_obj.browse(cr,uid,cust_voucher):
                           if vc.state=='draft':
                               voucher_obj.write(cr,uid,cust_voucher,{'amount':case.freight_balance})                       
                               for move in vc.move_ids:
                                   if move.credit>0:
                                       move_line_obj.write(cr,uid,[move.id],{'credit':case.freight_balance})
                                   if debit > 0:
                                       move_line_obj.write(cr,uid,[move.id],{'debit':case.freight_balance})
                           else:
                               voucher_obj.cancel_voucher(cr, uid, [vc.id], context=None)
                               voucher_obj.action_cancel_draft( cr, uid, cust_voucher, context=None)
                               voucher_obj.write(cr,uid,[vc.id],{'amount':case.freight_balance})
                               voucher_obj.button_proforma_voucher(cr,uid,[vc.id],context=None)               
                   
                
                   for v in voucher_obj.browse(cr,uid,voucher):
                       if v.state=='draft':
                           voucher_obj.write(cr,uid,voucher,{'partner_id':case.supplier_id.id,'account_id':freight_account,'company_id':comp,'period_id':period[0],'journal_id':journal_id,'amount':case.freight_balance})                       
                           for move in v.move_ids:
                               if move.credit>0:
                                   move_line_obj.write(cr,uid,[move.id],{'account_id':freight_account,'partner_id':case.supplier_id.id,'credit':case.freight_balance})
                               if debit > 0:
                                   move_line_obj.write(cr,uid,[move.id],{'account_id':freight_account,'partner_id':case.supplier_id.id,'credit':case.freight_balance})
                       else:
                           voucher_obj.cancel_voucher(cr, uid, [v.id], context=None)
                           voucher_obj.action_cancel_draft( cr, uid, voucher, context=None)
                           voucher_obj.write(cr,uid,[v.id],{'partner_id':case.supplier_id.id,'account_id':freight_account,'company_id':comp,'period_id':period[0],'journal_id':journal_id,'amount':case.freight_balance})
                           voucher_obj.button_proforma_voucher(cr,uid,[v.id],context=None)
                
                if pick_type == 'in':
                   gen_fr=True
                else:
                   gen_fr=case.gen_freight   
                                    
                if state =='freight_paid' and gen_fr:
                    
                       vouchers=voucher_obj.search(cr,uid,[('reference','=',name)])
                       if case.partner_id.customer:
                           acc_cust = case.partner_id.account_rec.id
                       if case.partner_id.supplier:
                           acc_supp = case.supplier_id.parent_id.account_pay   
                              
                       for kw_vocher in voucher_obj.browse(cr,uid,vouchers):
    
                           if kw_vocher.company_id.id==1:
                               if kw_vocher.state=='draft':
                                   voucher_obj.write(cr,uid,[kw_vocher.id],{'account_id':freight_account,'company_id':comp,'period_id':period[0],'journal_id':journal_id})                       
                                   for move in kw_vocher.move_ids:
                                       if move.credit>0:
                                           if kw_vocher.partner_id.supplier:
                                               if move.account_id.id != freight_account:
                                                   if move.partner_id.property_account_payable.id==move.account_id:
                                                       partner_acc = case.partner_id.representative_id.property_account_payable and case.partner_id.representative_id.property_account_payable.id or False
                                                       move_line_obj.write(cr,uid,[move.id],{'account_id':partner_acc,'company_id':comp,'credit':case.freight_balance})
      
                                           move_line_obj.write(cr,uid,[move.id],{'account_id':freight_account})
                                       if move.debit>0:
                                           move_line_obj.write(cr,uid,[move.id],{'debit':case.freight_balance}) 
                                           
                               else:
                                   voucher_obj.cancel_voucher(cr, uid, [kw_vocher.id], context=None)
                                   voucher_obj.action_cancel_draft( cr, uid, [kw_vocher.id], context=None)
                                   voucher_obj.write(cr,uid,[kw_vocher.id],{'account_id':freight_account,'company_id':comp,'period_id':period[0],'journal_id':journal_id,'amount':case.freight_balance})
                                   voucher_obj.button_proforma_voucher(cr,uid,[kw_vocher.id],context=None)
                               
                                   

               
        return True
    
    
    
    
    def change_in(self, cr, uid, ids, context = None):
        loc_id=False
        loc_dest_id=False
        prod_id=False
        loc_dest_id=False
        cust=False
        sup=False
        pick_obj = self.pool.get('stock.picking.in')
        move=self.pool.get('stock.move')
        voucher_obj=self.pool.get('account.voucher')
        journal_obj=self.pool.get('account.journal')
        acc_obj=self.pool.get('account.account')
        move_line_obj=self.pool.get('account.move.line')
        stock_id=context['active_ids']
        stock_ids=pick_obj.browse(cr,uid,ids)
        state=False
        esugam=False
        freight=False
        transporter=False
        name=''
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company1=cr.fetchone()
        if company1:
            company1=company1[0]
        today = time.strftime('%Y-%m-%d')
         
        for case in self.browse(cr, uid, ids):
            supplier_id=case.supplier_id.id
            print case.state
            state=case.dc_state
            print "status",case.dc_state
            name= str(case.name)
            cust=case.cust
            sup=case.sup
            if case.esugam_no:
                if len(case.esugam_no)>1:
                    esugam=case.esugam_no
            if not sup:
#                     cr.execute("SELECT invoice_id FROM incoming_shipment_invoice_rel where in_shipment_id = "+str(stock_id[0]))
                    cr.execute("""SELECT dr.invoice_id FROM incoming_shipment_invoice_rel dr inner 
                    join account_invoice ac on ac.id=dr.invoice_id WHERE dr.in_shipment_id=%s and ac.state <>'cancel'""",(str(stock_id[0]),))
                    sinv_ids = cr.fetchall()
                    if sinv_ids:
                        sup=True

            
            if sup:
                    raise osv.except_osv(_('Warning'),_('Facilitator Invoice Already Generated For The "%s" Cannot Change Product or Quantity, Click on Cancel')% (case.name))
               
            st_id=pick_obj.browse(cr,uid,stock_id)
            for temp in st_id:
                for i in temp.move_lines:
                    loc_id=i.location_id.id
                    prod_id=i.product_id.id
                    partner_id=temp.partner_id.id
                    move.write(cr,uid,[i.id],{'state':'draft'})
                    state=str(temp.state)

                company=temp.company_id.id
            today=case.date
            if case.state=='draft':
                state=str(case.state)

                
            move.onchange_product_id(cr, uid, [case.stock_move_id.id], prod_id, loc_id,loc_dest_id, partner_id)
            if case.product_qty>0:
                prod_qty=case.product_qty
            else:
                raise osv.except_osv(_('Warning'),_('Enter Valid Quantity'))
            move.write(cr, uid, [case.stock_move_id.id],{'product_id':case.product_id.id,'product_qty':prod_qty},context = context)
                                                      
                                                      
                                                      
            
            pick_obj.write(cr, uid, context['active_ids'],{'partner_id':case.partner_id.id,'product_id':case.product_id.id,'freight_balance':case.freight_balance,'date':case.date},context = context)
                                                           
                                                            
                                                      
            context.update({'state':state,'name':name})
            
#             pick_obj.onchange_paying_agent(cr,uid,context['active_ids'],case.supplier_id.id,transporter,context=context)
            if case.state!='draft':
                move.action_done(cr, uid,[case.stock_move_id.id], context=None)
                
            freight_account=acc_obj.search(cr, uid, [('name','like','Freight'),('company_id','=',company)])
            if freight_account:
                freight_account=freight_account[0]    
                         
            vouchers=voucher_obj.search(cr,uid,[('reference','=',name),('state','=','draft')])     
            cc_id=case.partner_id.parent_id.property_account_payable and case.partner_id.property_account_payable.parent_id.id or False         
            voucher_obj.write(cr,uid,vouchers,{'partner_id':case.partner_id.id,'account_id':freight_account,'company_id':company,'amount':case.freight_balance})             

               
        return True    
    
    
    
    
    
    
    
    
    
    
        
       
    
change_product_qty()