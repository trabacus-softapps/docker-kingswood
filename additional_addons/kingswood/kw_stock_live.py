from openerp.osv import fields,osv
from openerp.tools.translate import _
from lxml import etree
from openerp import tools
import math
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import subprocess
from selenium.webdriver.common import utils
import os
import re
import base64
from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO
import requests
# from pyPdf import PdfFileWriter, PdfFileReader

import zipfile
import logging
# import os
import signal
# import sys
import threading
import traceback
import time

import openerp
import operator
# from . import Command
# import common
#delete
import base64
import netsvc

import sys

import random
from openerp.report import report_sxw
from openerp import pooler

_logger = logging.getLogger(__name__)


# FIXME: this is a temporary workaround because of a framework bug (ref: lp996816). It should be removed as soon as
#        the bug is fixed
# Need to remove the columns



class stock_picking_out(osv.osv):
    _name = "stock.picking.out"
    _inherit=['stock.picking.out','mail.thread', 'ir.needaction_mixin']
    
    
    
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        user = self.pool.get('res.users').browse(cr,uid,uid)
        
        if context is None:context = {}
        res = super(stock_picking_out, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # For Supplier Groups: Filtering related Customers in OUT
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if context.get('type', '') == 'out' and view_type =='form':
            cr.execute("select true from res_groups_users_rel gu \
                        inner join res_groups g on g.id = gu.gid \
                        where g.name = 'KW_Supplier' and uid ="+str(uid))
            is_supp = cr.fetchone()
            
            if is_supp and is_supp[0] == True:
                cust_ids = [] 
                cr.execute("select customer_id from customer_list_rel where supplier_id = " + str(user.partner_id.id))         
                custs = cr.fetchall()
                for s in custs:
                    cust_ids.append(s[0]) 
                
                for field in res['fields']:
                    if field == 'partner_id':
                        res['fields'][field]['domain'] = [('id','in', cust_ids)]
            else:
                cust_ids = [] 
                cr.execute("select id from res_partner")
                custs=cr.fetchall()
                for s in custs:
                    cust_ids.append(s[0]) 
                
                for field in res['fields']:
                    if field == 'partner_id':
                        res['fields'][field]['domain'] = [('customer','=',True)]
                    
                        

                        
                        
        return res
    
    def _get_paying_agent(self, cr, uid, ids, args, field_name, context = None):
        res={}
        g_ids = []
        paying_agent=[]
        warning=''
        log_user={}
        picking={}
        driver=""
        u_id=context.get('uid')
        if u_id:
            uid=u_id
        user_obj = self.pool.get('res.users')
        
        for case in self.browse(cr, uid, ids):
            res[case.id] = ""
            if case.type=='out':
                cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                paying_agent=cr.fetchall()
                paying_agent=zip(*paying_agent)[0]
                if case.paying_agent_id.id in paying_agent:
                    res[case.id]='kingswood'
                
                cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
                gid = cr.dictfetchall()
                for x in gid:
                    g_ids.append(x['gid'])
                for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
                   
                    if g.name == 'KW_Supplier':
                        log_user = 'KW_Supplier'
                        res[case.id]='not'
                    if g.name == 'KW_Customer':
                        log_user = 'KW_Customer'
                    if g.name == 'KW_Depot':
                       log_user = 'KW_Depot'
                    if g.name == 'KW_Admin':
                        log_user = 'KW_Admin'
                
          
                    if log_user=='KW_Depot' or log_user == 'KW_Admin':
                        user = user_obj.browse(cr, uid, [uid])[0]
                        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                        paying_agent=cr.fetchall()
                        paying_agent=zip(*paying_agent)[0]
                        if user.role!='representative':
                                if case.paying_agent_id.id in paying_agent:
                                    res[case.id]='kingswood'
                                    driver=case.transporter_id.name
                                    case.driver_name=driver
                       
                                
        
        return res
    
         
    def _get_default_state(self, cr, uid, context=None):
        
        g_ids = []
        user_obj = self.pool.get('res.users')

        res=0
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):

            user = user_obj.browse(cr, uid, [uid])[0]
            if g.name != 'KW_Admin' or g.name != 'KW_Depot':
                res=user.state_id.id
            elif g.name == 'KW_Admin' or g.name == 'KW_Depot':
                cr.execute("select id from res_country_state where name='Karnataka'")
                res=cr.fetchone()

        return res
    
    
    
    def _get_default_paying_agent(self, cr, uid, context=None):
        
        g_ids = []
        user_obj = self.pool.get('res.users')

        res = "not"
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):

            user = user_obj.browse(cr, uid, [uid])[0]
            if g.name == 'KW_Admin':
                res='not'
            if g.name == 'KW_Depot' and user.role!='representative':
                res = 'kingswood'
                
        return res
    
    
    
    
    def _get_default_paying_agent_id(self, cr, uid, context=None):
        res ={}
        g_ids = []
        user_obj = self.pool.get('res.users')

        res = False
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):

            user = user_obj.browse(cr, uid, [uid])[0]
            if g.name == 'KW_Supplier':
               res=user.partner_id.id
             

        return res
    
    def get_freight_balance(self,cr,uid,ids,context=None):
        for case in self.browse(cr, uid, ids):
            freight_balance=case.freight_total - case.freight_deduction - case.freight_advance 
            i=case.id
            cr.execute("UPDATE stock_picking SET freight_balance =%s where id=%s", (freight_balance,i)) 
        return True
    
    def _get_freight_amount(self, cr, uid, ids, args, field_name, context = None):
        res = {}
        for case in self.browse(cr, uid, ids):
            if case.type=='out':
                res[case.id] = {'freight_deduction': 0.00, 'freight_total':0.00}
                deduction = total = 0.00
                
                tol_qty = case.partner_id.tol_qty
                tol_rate = case.partner_id.tol_rate
#                 freight_charge=0
                for ln in case.move_lines:
#                     for temp in ln.product_id.customer_ids:
#                         if temp.name.id==case.partner_id.id:
#                             
#                             case.freight_charge=temp.transport_rate
#                             cr.execute('UPDATE stock_picking SET freight_charge = %s WHERE id=%s',(temp.transport_rate,case.id,))
                    if case.freight_charge > 0:
                        total += (case.freight_charge * ln.unloaded_qty)
                        
                        # Picking Qty > Product Qty
                        if ((ln.product_qty - ln.unloaded_qty) * 1000) > (ln.product_qty * tol_qty) :
                            deduction += (((ln.product_qty - ln.unloaded_qty)*1000) - (ln.product_qty * tol_qty)) * tol_rate
                        
                res[case.id]['freight_deduction'] = deduction
                res[case.id]['freight_total'] = total
#                 self.get_freight_balance(cr, uid, ids, context)
#                 if case.freight_charge > 0:
#                     res[case.id]['freight_balance'] = total - deduction - case.freight_advance
        return res
    
    def _get_move_lines(self, cr, uid, ids, args, field_name, context = None):
        res = {}
        u_id=context.get('uid')
        if u_id:
            uid=u_id
#         cr.execute("select login from res_users where id  ="+str(uid))
#         user=cr.fetchone()[0]
        product_change = False
        for case in self.browse(cr, uid, ids):
            d=case.id
            if case.type=='out':
                for temp in case.move_lines:
#                     if case.product_id.product_change:
#                        product_change= case.product_id.product_change
#                     self.write(cr, uid, [case.id],{'product_change':case.product_id.product_change},context = context)
#                         
                    
                    res[case.id] = {'product': " ", 'qty':0.000,'transporter':" ",'price_unit':0.0,'users':'' ,'freight':'','del_quantity':0.000}
#                     res[case.id]['product']  = temp.product_id.name
                    res[case.id]['qty']  = temp.product_qty
                    res[case.id]['product_id']= temp.product_id.id
                    res[case.id]['price_unit'] = temp.price_unit
                    res[case.id]['del_quantity'] = temp.unloaded_qty
                    case.product_id.id=temp.product_id.id
#                     res[case.id]['location_id']=temp.location_id.id
                    cr.execute("select create_uid from stock_picking where id="+str(case.id))
                    create_uid=cr.fetchone()[0]
                    cr.execute("select login from res_users where id  ="+str(create_uid))
                    user=cr.fetchone()[0]
                    res[case.id]['users']=user
                    res[case.id]['freight']=case.partner_id.freight
 
                    cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                    paying_agent=cr.fetchall()
                    paying_agent=zip(*paying_agent)[0]
                    if case.paying_agent_id.id in paying_agent:
                        res[case.id]['transporter']  = case.transporter_id.name
                    else:
                        res[case.id]['transporter']  = case.driver_name  
                    
               # if case.date_function!=case.date:
                 #       cr.execute("UPDATE stock_picking SET date_function =%s where id=%s", (case.date,d))
                if case.year!='':
#                     self.get_day_date(cr,uid,ids)
                    cr.execute("select to_char(s.date, 'YYYY') as year,to_char(s.date, 'MM') as month,to_char(s.date, 'YYYY-MM-DD') as day from stock_picking s where id =%s",(d,))
                    date=cr.fetchall()[0]
                    if date:
   
                        cr.execute("UPDATE stock_picking SET year =%s where id=%s", (date[0],d))
                        cr.execute("UPDATE stock_picking SET month =%s where id=%s", (date[1],d))
                        cr.execute("UPDATE stock_picking SET day =%s where id=%s", (date[2],d))
                
                         
                    cr.execute("select product_id from stock_move where picking_id=%s",(d,))
                    product_id=cr.fetchone()
                    if product_id:
                        product_id=product_id[0]
                        cr.execute("UPDATE stock_picking SET product_id =%s where id=%s", (product_id,d))
                 
               
        return res
    
    
    

    
    def _get_permission(self, cr, uid, ids, args, field_name, context = None):
        res ={}
        g_ids = []
        u_id=context.get('uid')
        if u_id:
            uid=u_id
        for case in self.browse(cr, uid, ids):
            if case.type=='out':
                res[case.id] = True
                cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
                gid = cr.dictfetchall()
                for x in gid:
                    g_ids.append(x['gid'])
                for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
    #                 if g.name == 'KW_Freight':
    #                     res[case.id] = False
                    
                    if g.name == 'KW_Supplier':
                         res[case.id] = False
                    if g.name == 'KW_Customer':
                        res[case.id] = True
                    if g.name == 'KW_Admin':
                        if case.state_id.id:
                            state_id=case.state_id.id
                            cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (state_id,case.id))
                        
                    if g.name == 'KW_Customer' or g.name == 'KW_Depot' or g.name == 'KW_Supplier':
                        cr.execute("select create_uid from stock_picking where id="+str(case.id))
                        create_uid=cr.fetchone()[0]
                        cr.execute("select partner_id from res_users where id  ="+str(create_uid))
                        user=cr.fetchone()[0]
                        cr.execute("select state_id from res_partner where id="+str(user))
                        state_id=cr.fetchone()[0]
                        if state_id:
                            cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (state_id,case.id))

        return res
    
    def _get_user(self, cr, uid, ids, args, field_name, context = None):
        res ={}
        g_ids = []
        user_obj = self.pool.get('res.users')
        u_id=context.get('uid')
        if u_id:
            uid=u_id
        for case in self.browse(cr, uid, ids):
            if case.type=='out':
                res[case.id] = " "
                cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
                gid = cr.dictfetchall()
                for x in gid:
                    g_ids.append(x['gid'])
                for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
    #                 if g.name == 'KW_Freight':
    #                     res[case.id] = False
                    if g.name == 'KW_Supplier':
                        res[case.id] = 'KW_Supplier'
    #                     for temp in case.move_lines:
    #                           res[case.paying_agent_id]=temp.supplier_id
                         
                    if g.name == 'KW_Customer':
                        res[case.id] = 'KW_Customer'
                    if g.name == 'KW_Depot':
                        res[case.id] = 'KW_Depot'   
                    if g.name == 'KW_Admin':
                        res[case.id] = 'KW_Admin'
#                         cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (case.state_id.id,d))
                        
                    if res[case.id]=='KW_Depot' or res[case.id] == 'KW_Admin':
                        
                        user = user_obj.browse(cr, uid, [uid])[0]
                        
                        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                        paying_agent=cr.fetchall()
                        paying_agent=zip(*paying_agent)[0]
                        if res[case.id] !='KW_Admin':
                            if user.role=='representative':
                                if case.paying_agent_id in paying_agent:
                                    case.paying_agent='representative'
                
                                    
                                        
                            else:
                                if case.paying_agent_id in paying_agent:
                                    case.paying_agent='kingswood'
                    
                    if g.name == 'KW_Customer' or g.name == 'KW_Depot' or g.name == 'KW_Supplier':
                        cr.execute("select create_uid from stock_picking where id="+str(case.id))
                        create_uid=cr.fetchone()[0]
                        cr.execute("select partner_id from res_users where id  ="+str(create_uid))
                        user=cr.fetchone()[0]
                        cr.execute("select state_id from res_partner where id="+str(user))
                        state_id=cr.fetchone()[0]
                        if state_id:
                            cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (state_id,case.id))
#             cr.execute("select to_char(s.date, 'YYYY') as year,to_char(s.date, 'MM') as month,to_char(s.date, 'YYYY-MM-DD') as day from stock_picking s where id =%s",(d,))
          
        return res
    
    def _get_default_user(self, cr, uid, context=None):
        res ={}
        g_ids = []
        
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
                    
        return res
    
    
    def _get_default_permission(self, cr, uid, context=None):
        res = True
        g_ids = []
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
            if g.name == 'KW_Supplier':
                res = False
            
            if g.name == 'KW_Customer':
                res = True
        return res
    
    def _get_new_date(self, cr, uid, ids, args, field_name, context = None):
        res={}
        for case in self.browse(cr, uid, ids):
            if case.type=='out':
                for temp in case.move_lines:
#                     if case.product_id.product_change:
#                        product_change= case.product_id.product_change
#                     self.write(cr, uid, [case.id],{'product_change':case.product_id.product_change},context = context)
#                         
                    
                    res[case.id] = {'date_function': " ", 'delivery_date_function':""}
                    
                    res[case.id]['date_function']=case.date
                    res[case.id]['delivery_date_function']=temp.delivery_date
#                     self.get_day_date(cr,uid,ids)
                    
                     
                        
                   
        return res
    
    def get_day_date(self,cr,uid,ids,context=None):
        day_id=[]
        for case in self.browse(cr, uid, ids):
            cr.execute("select id from stock_picking where delivery_date_function is null or day is null")
            day_ids=cr.fetchall()
            g=0
            for g in day_ids:
                day_id.append(g[0])
            
            
  
                
            for p in day_id:
                cr.execute("select to_char(s.date, 'YYYY') as year,to_char(s.date, 'MM') as month,to_char(s.date, 'YYYY-MM-DD') as day from stock_picking s where id =%s",(p,))
                date=cr.fetchall()[0]
                cr.execute("select to_char(sm.delivery_date, 'YYYY-MM-DD') from stock_move sm where sm.picking_id =%s",(p,))
                date1=cr.fetchall()
                
                if date:
                    cr.execute("UPDATE stock_picking SET year =%s where id=%s", (date[0],p))
                    cr.execute("UPDATE stock_picking SET month =%s where id=%s", (date[1],p))
                    cr.execute("UPDATE stock_picking SET day =%s where id=%s", (date[2],p))
                    cr.execute("UPDATE stock_picking SET date_function =%s where id=%s", (date[2],p))
                if date1:
                    cr.execute("UPDATE stock_picking SET delivery_date_function =%s where id=%s", (date1[0],p))
                    
#                 cr.execute("select to_char(s.date_function, 'YYYY') as year,to_char(s.date_function, 'MM') as month,to_char(s.date_function, 'YYYY-MM-DD') as day from stock_picking s where id =%s",(p,))
#                 date2=cr.fetchall()[0]
#                 if date2:
#                     cr.execute("UPDATE stock_picking SET year =%s where id=%s", (date2[0],p))
#                     cr.execute("UPDATE stock_picking SET month =%s where id=%s", (date2[1],p))
#                     cr.execute("UPDATE stock_picking SET day =%s where id=%s", (date2[2],p))
                
        return True
    
    def _get_inv_status(self, cr, uid, ids, field_name, args, context = None):
        res = {}
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'cust_invoice' : False, 'sup_invoice':False}
            cr.execute("SELECT invoice_id FROM delivery_invoice_rel where del_ord_id = "+str(case.id))
            cinv_ids = cr.fetchall()
            if cinv_ids:
                res[case.id]['cust_invoice'] = True
            cr.execute("SELECT invoice_id FROM supp_delivery_invoice_rel where del_ord_id = "+str(case.id))
            sinv_ids = cr.fetchall()
            cr.execute("SELECT invoice_id FROM incoming_shipment_invoice_rel where in_shipment_id = "+str(case.id))
            Iinv_ids = cr.fetchall()
            if sinv_ids or Iinv_ids:
                res[case.id]['sup_invoice'] = True
        return res
    
    def get_workorder(self, cr, uid, ids, field_name, args, context = None):
        work_obj = self.pool.get('work.order')
        res = {}
        for case in self.browse(cr, uid, ids):
            res[case.id] = ''
            if case.type=="out" and case.paying_agent_id:
                w_ids = work_obj.search(cr, uid, [('product_id','=',case.product_id.id),('state_id','=',case.paying_agent_id.state_id.id),('partner_id','=',case.partner_id.id)],limit=1)
                for w in work_obj.browse(cr, uid, w_ids):
                    res[case.id]= w.work_order_no or ''
        return res
     
    
    _columns={ 
#               'customer_list'   : fields.function(_get_customer,type='text', string='Customers List' ,store=True),
              'hide_fields'     : fields.function(_get_permission,type='boolean',method=True,string="Permission", store=True), 
              'user_log'        : fields.function(_get_user,type='char',method=True,string="Permission", store=False),
              # Overriden:
#                 'partner_id': fields.many2one('res.partner', 'Partner',  domain="[('id', 'in', [int(s) for s in customer_list.split(',')])] )]", states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
                  
#                 'partner_id': fields.many2one('res.partner', 'Partner',   domain="[('id', 'in', [s for s in [13,5,6,22,970]] )]", states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
              'partner_id': fields.many2one('res.partner', 'Partner', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
              # NEw:
                'work_order'    :   fields.function(get_workorder,store=True,type="char",string='Work Order Number',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
                'truck_no'      :   fields.char('Vehicle Number',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
                'esugam_no'     :   fields.char('E-Sugam Number',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
                'state'         :   fields.selection([('draft','Draft'),('in_transit','In Transit'),('auto', 'Waiting Another Operation'),
                                                      ('confirmed', 'Waiting Availability'),
                                                      ('assigned', 'Ready to Deliver'),
                                                      ('done', 'Delivered'),
                                                      ('cancel', 'Cancelled'),
                                                      ('freight_paid','Freight Paid')],'Status', readonly=True, select=True,track_visibility='onchange',),
              'freight_charge'   : fields.float('Freight Charge/MT',digits=(0,2),states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'freight_advance'  : fields.float('Freight Advance',digits=(0,2),states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}), 
              'driver_name'      : fields.char('Transporter/Owner Name',size=100,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'diver_contact'    : fields.char('Driver Contact',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              
              'freight_total'    : fields.function(_get_freight_amount, type='float', string='Frieght Total', store=True, multi="tot"),
              'freight_deduction': fields.function(_get_freight_amount, type='float', string='Frieght Deduction', store=True, multi="tot"),                 
#               'freight_balance'  : fields.function(_get_freight_amount, type='float', string='Frieght Balance', store=True, multi="tot"),
                'freight_balance' :fields.float('Freight Balance',digits=(0,2)),
              'city_id'          : fields.many2one('kw.city','From'),
              'transporter_id'   : fields.many2one('res.partner','Transporter'),
#               'date'             : fields.datetime('Delivery Date', help="Creation date, usually the time of the order.", select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
              'date_function'   : fields.function(_get_new_date,type='date',string="Creation Date",store=True,multi="date"),
              'delivery_date_function'   : fields.function(_get_new_date,type='date',string="Delivery Date",store=True,multi="date"),
              'paying_agent_id' : fields.many2one('res.partner','Paying Agent'),
#               ,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'paying_agent'    : fields.function(_get_paying_agent,type='char',method=True,string="paying_agent", store=True),
               'product'         : fields.function(_get_move_lines,type="char", size=30, string="Product",store=False, multi="move_lines"),
              'qty'             : fields.function(_get_move_lines,type="float", digits=(0,3),string="Quantity in MTs",store=True, multi="move_lines"),
              'del_quantity'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string="Delivered Quantity in MTs",store=True, multi="move_lines"),
              'transporter'     : fields.function(_get_move_lines,type="char", size=30,string="Transporter",store=True,multi="move_lines"),
              'price_unit'      : fields.function(_get_move_lines,type="float",string="Unit Price",store=True,multi="move_lines"),
              'product_id'      : fields.many2one('product.product', 'Products'),
              'state_id'        : fields.many2one('res.country.state','State'),
              
              #for reporting purpose
              'invoice_line_id'    : fields.many2one('account.invoice.line', 'invoice line'),
              'finvoice_line_id'    : fields.many2one('account.invoice.line', 'Freight invoice line'),
              'purchase_id': fields.many2one('purchase.order', 'Purchase Order',
                                             ondelete='set null', select=True),
              'location_id'     : fields.function(_get_move_lines,type="integer",string="location_id",store=True,multi="move_lines"),
              'users'           : fields.function(_get_move_lines,type="char", string="User",store=True, multi="move_lines"),
              'freight'         : fields.function(_get_move_lines,type="boolean",string="freight",store=True,multi="move_lines"), 
             
               #FOR VIEW PURPOSE
               
               'year': fields.char('Year', size=6, readonly=True),
              'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                                            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
                                            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
              'day': fields.char('Day', size=128, readonly=True),
              
              # invoice PURPOSE
              
#               'cust_invoice'    :   fields.boolean('Customer Invoice'),
#               'sup_invoice'    :   fields.boolean('Facilitator Invoice'),
#               
              'cust_invoice'    :   fields.function(_get_inv_status, multi = "all",type="boolean",string ='Customer Invoice'),
              'sup_invoice'    :   fields.function(_get_inv_status, multi = "all",type="boolean",string ='Facilitator Invoice'),
              
              #for search view
              'date_from':fields.function(lambda *a,**k:{}, method=True, type='date',string="From"),
              'date_to':fields.function(lambda *a,**k:{}, method=True, type='date',string="To"),
              
              #esugam, for specific users
              'gen_esugam'   : fields.boolean("Generate E-sugam"),
              'show_esugam'  : fields.related('partner_id','show_esugam',type='boolean',store=False) 
              } 
    
    _order = 'date desc'
    
    _defaults = { 'hide_fields' : _get_default_permission,
                 #'date_function': _get_default_new_date,
                  'user_log'     :_get_default_user,
                 'esugam_no'    :'0',
                 'paying_agent' :_get_default_paying_agent,
                   'paying_agent_id':_get_default_paying_agent_id,
                    'purchase_id': False,
                    'freight': False,
                    'state_id'     : _get_default_state,
                    'cust_invoice' : False, 
                    'sup_invoice':False,
#                  'customer_list' : _default_get_customer,
#                  'hide_fields' : True 
# cur_date=datetime.today().strftime("%Y-%m-%d")
#                 'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
                 }
    
    def onchange_paying_agent(self, cr, uid, ids, paying_agent_id=False, transporter_id=False,context=None):
        res={}
        g_ids = []
        paying_agent=[]
        warning=''
        log_user={}
        picking={}
        res['paying_agent_id'] = paying_agent_id
        user_obj = self.pool.get('res.users')
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
            if g.name == 'KW_Depot':
                log_user = 'KW_Depot'
                
                
                
                
            if g.name == 'KW_Admin':    
                log_user = 'KW_Admin'
                res['paying_agent']='not'    
        
        if log_user!='KW_Admin'and paying_agent_id:
            cr.execute("select state_id from res_partner where id=%s",(res['paying_agent_id'],))
            state=cr.fetchone()
            if state:
                res['state_id']= state[0]
        
        if log_user=='KW_Depot' or log_user == 'KW_Admin':
            user = user_obj.browse(cr, uid, [uid])[0]
            
            cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
            paying_agent=cr.fetchall()
            paying_agent=zip(*paying_agent)[0]
            
            if paying_agent_id not in paying_agent:
               res['paying_agent']='not'
            if paying_agent_id in paying_agent:
                res['paying_agent']='kingswood'
                if log_user !='KW_Admin':
                    
                    if user.role=='representative':
                        
                            res['paying_agent_id'] = False
                            res['paying_agent']='representative'
        #                         raise osv.except_osv(_('Warning'),_('You Are Not Authorised To Select "KINGSWOOD" As Paying Agent'))
                            warning={
                                     'title':_('Warning!'), 
                                            'message':_('You Are Not Authorised To Select "KINGSWOOD" As Paying Agent')
                                         }
                                
                    else:
                        if paying_agent_id in paying_agent:
                            res['paying_agent']='kingswood'
            
            #check for the kings wood logicstics
            if paying_agent_id:
                cr.execute("select id from res_partner where lower(name) like 'kingswood lo%'")
                paying_agent=cr.fetchall()
                paying_agent=zip(*paying_agent)[0]
                if paying_agent_id in paying_agent:
                    res['paying_agent_id'] = False
                    warning={
                                         'title':_('Warning!'), 
                                                'message':_('You Are Not Authorised To Select "KINGSWOOD LOGISTICS" As Facilitator')
                                             }
                if transporter_id:
                    if paying_agent_id == transporter_id:
                        res['paying_agent_id'] = False
                        warning={
                                         'title':_('Warning!'), 
                                                'message':_('You Are Not Allowed To Select Same Company as Facilitator and Transporter')
                                             }
               
                
             
        return{'value' : res,'warning':warning}
     
    
    #for reading pdf file 
    def convert_pdf(self,path):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    
        fp = file(path, 'rb')
        process_pdf(rsrcmgr, device, fp)
        fp.close()
        device.close()
    
        str = retstr.getvalue()
        retstr.close()
        return str
    
    
    #to check paying agent and transporter 
    def onchange_transporter_id(self, cr, uid, ids, paying_agent_id=False, transporter_id = False,context=None):
        res ={} 
        g_ids = []
        paying_agent=[]
        warning=''
        log_user={}
        picking={}
        transport=[]
        warning = ""
        if transporter_id == paying_agent_id:
            res['transporter_id'] = False
            
            warning={
                                         'title':_('Warning!'), 
                                                'message':_('You Are Not Allowed To Select Same Company as Facilitator and Transporter')
                                             }
            
            
        res['paying_agent'] = paying_agent_id
        user_obj = self.pool.get('res.users')
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):

                cr.execute("select id from res_partner where lower(name) like 'others'")
                transport=cr.fetchall()
                transport=zip(*transport)[0]
                
                if transporter_id in transport:
                    res['paying_agent']='representative'
                else:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
                    res['paying_agent']='kingswood'
        return{'value':res ,'warning':warning}
        
        
    
        
    def onchange_partner_in(self, cr, uid, ids, partner_id=None,context=None):
#         res=super(stock_picking,self).onchange_partner_in(cr, uid, ids,partner_id=False,context=None)
        g_ids = []
        res={}
        dom={}
        state_id=0
        group_obj=self.pool.get('res.groups')
        user_obj = self.pool.get('res.users')
        partner_obj=self.pool.get('res.partner')
        partner_ids=partner_obj.search(cr,uid,[('id','=',partner_id)])
        for i in partner_obj.browse(cr,uid,partner_ids):
            res['show_esugam'] = i.show_esugam or False
#             if i.work_order:
#                 res['work_order']=i.work_order
#             else:
#                 res['work_order']=False
         
        
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
#         for g in self.pool.get('res.groups').browse(cr, uid, g_ids):   
#             if g.name=='KW_Depot':
#                 user_ids=user_obj.search(cr,uid,[('id','=',uid)])
#                 for j in user_obj.browse(cr,uid,user_ids):
# #                     state_id=j.state_id

#                     print j.state_id.name
        if state_id>0:
            dom = {'paying_agent_id':  [('state_id','=', state_id.id)]}
        
        return {'value':res,'domain':dom}
    
    
    def onchange_user_in(self, cr, uid, ids, user_log=None,context=None):
#         res=super(stock_picking,self).onchange_partner_in(cr, uid, ids,partner_id=False,context=None)
        g_ids = []
        res={}
        dom={}
        state_id=0
        group_obj=self.pool.get('res.groups')
        user_obj = self.pool.get('res.users')
        partner_obj=self.pool.get('res.partner')
        
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):   
            if g.name=='KW_Depot':
                user_ids=user_obj.search(cr,uid,[('id','=',uid)])
                for j in user_obj.browse(cr,uid,user_ids):
                    state_id=j.state_id
                    
        if state_id:
            dom = {'paying_agent_id':  [('state_id','=', state_id.id),('supplier','=',True)]}
        
        return {'value':res,'domain':dom}

    

    def generate_esugam(self, cr, uid, desc, qty, price, product_id, username, password, url1,url2, case,context):
    #for calulating taxes
        tax_amount = 0
        esugam = 0
        if case.partner_id.state_id.name == 'Karnataka':
            taxes = product_id.taxes_id
        else:
            taxes = product_id.cst_taxes_id
        for t in taxes:
            tax_amount += t.amount * price
        
        today = time.strftime('%Y-%m-%d %H:%M:%S')
        last_month_date = datetime.strptime(today, '%Y-%m-%d %H:%M:%S')
        veh_owner = case.driver_name and case.driver_name or ''
        inv_date = parser.parse(''.join((re.compile('\d')).findall(case.date))).strftime('%d/%m/%Y')
        del_date = parser.parse(''.join((re.compile('\d')).findall(str(last_month_date)))).strftime('%d/%m/%Y')
        #Code using Splinter
        #                 browser = Browser('phantomjs')
        #                 browser.visit(url)
        #                 browser.fill('UserName',username)
        #                 browser.fill('Password',password)
        #                 browser.find_by_id('btn_login').click()
        #                 browser.find_by_css('.Menu1_3').mouse_over()
        #                 browser.find_by_css('.Menu1_5').mouse_over()
        #                 browser.find_link_by_text("New Entry").click()
        #                 #browser.find_by_id('ctl00_MasterContent_rbl_doctype_5').click()
        # #                 browser.find_by_id('ctl00_MasterContent_btnContinue').click()
        # #                 browser.find_by_id('LinkButton1').click()
        #                 if case.partner_id.state_id.name == 'Karnataka':
        #                     browser.find_by_id('ctl00_MasterContent_rdoStatCat_0').click()
        #
        #
        #                 else:
        #                     browser.find_by_id('ctl00_MasterContent_rdoStatCat_1').click()
        #
        #                 time.sleep(1)
        #
        #                 browser.fill('ctl00$MasterContent$txtFromAddrs','bangalore')
        #                 browser.fill('ctl00$MasterContent$txtToAddrs',case.partner_id.city)
        #                 browser.fill('ctl00$MasterContent$txt_commodityname',desc)
        #                 browser.fill('ctl00$MasterContent$txtQuantity',str(qty))
        #                 browser.fill('ctl00$MasterContent$txtNetValue',str(price * qty))
        # #                 browser.fill('ctl00$MasterContent$txtVatTaxValue',str(tax_amount))
        #                 browser.fill('ctl00$MasterContent$txtVehicleOwner',veh_owner)
        #                 browser.fill('ctl00$MasterContent$txtVehicleNO',case.truck_no)
        #                 browser.fill('ctl00$MasterContent$txtGCLRNO',case.name)
        #                 browser.fill('ctl00$MasterContent$txtInvoiceNO',case.name)
        #                 browser.fill('ctl00$MasterContent$txtInvoiceDate',inv_date)
        #                 browser.fill('ctl00$MasterContent$txtDeliveryDate',del_date)
        #                 #browser.find_by_id('ctl00_MasterContent_RadioButton2').click() # for pdfprint
        #
        #
        #                 if case.partner_id.state_id.name == 'Karnataka':
        #                      browser.fill('ctl00$MasterContent$txtTIN',case.partner_id.tin_no)
        #
        #
        #                 else:
        #                     browser.fill('ctl00$MasterContent$txtTIN',case.partner_id.tin_no)
        #                     browser.fill('ctl00$MasterContent$txtVehicleOwner',veh_owner)
        #                     time.sleep(1)
        #
        #                     browser.fill('ctl00$MasterContent$txtNameAddrs',case.partner_id.name)
        #
        #
        #                 #browser.find_by_id('ctl00_MasterContent_btnSave').click()
        #                 browser.find_by_id('ctl00_MasterContent_btn_savecumsubmit').click()
        #                 time.sleep(1)
        #                 esugam = browser.find_by_id('ctl00_MasterContent_lbl_serialno').first.value
        #                 browser.find_by_name('ctl00$MasterContent$Button1').click()
        #                 #browser.quit()
        #                 browser.find_by_id('link_signout').click()
        #                 browser.quit()
        #Code Using Selenium
        #os.environ["webdriver.chrome.driver"] = "/usr/bin/chromedriver"
        #browser = webdriver.Chrome("/usr/bin/chromedriver")
#         fp = webdriver.FirefoxProfile()
#         fp.set_preference("browser.download.folderList", 2)
#         #fp.set_preference("browser.download.manager.showWhenStarting",False)
#         fp.set_preference("browser.download.dir", '/home/serveradmin/esugama')
#         fp.set_preference("browser.download.downloadDir", '/home/serveradmin/esugama')
#         fp.set_preference("browser.download.defaultFolder", '/home/serveradmin/esugama')
#         fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
#         fp.set_preference("plugin.disable_full_page_plugin_for_types", "application/pdf")
#         fp.set_preference("pdfjs.disabled", True) #browser = webdriver.Firefox(firefox_profile=fp)
        browser = webdriver.PhantomJS()
        #browser = webdriver.Firefox()
        url_status = browser.get(url1)
        
        try:
            browser.find_element_by_id('UserName')
        
        except:
            try:
                browser.find_element_by_id('Button2')
            except:
                raise osv.except_osv(_('Esugam Site Is Down'),_('Please Try After Some Time'))
            browser.find_element_by_id('Button2').click()
        
        
        
        try:
            browser.find_element_by_id('UserName')
            browser.find_element_by_id('Password')
            browser.find_element_by_id('btn_login')
            browser.find_element_by_css_selector('.Menu1_3')
            
            browser.find_element_by_id('UserName').send_keys(username)
            browser.find_element_by_id('Password').send_keys(password)
            browser.find_element_by_id('btn_login').click()
            browser.find_element_by_css_selector('.Menu1_3').click()
            browser.find_element_by_css_selector('.Menu1_3').send_keys(Keys.RIGHT)
            browser.find_element_by_css_selector('.Menu1_5').click()
            #browser.find_by_id('ctl00_MasterContent_rbl_doctype_5').click()
            #browser.find_by_id('ctl00_MasterContent_btnContinue').click()
            #browser.find_by_id('LinkButton1').click()
            if case.partner_id.state_id.name == 'Karnataka':
                browser.find_element_by_id('ctl00_MasterContent_rdoStatCat_0').click()
            else:
                browser.find_element_by_id('ctl00_MasterContent_rdoStatCat_1').click()
            time.sleep(1)
            browser.find_element_by_name('ctl00$MasterContent$txtFromAddrs').send_keys(case.city_id.name)
            browser.find_element_by_name('ctl00$MasterContent$txtToAddrs').send_keys(case.partner_id.city)
            browser.find_element_by_name('ctl00$MasterContent$txt_commodityname').send_keys(desc)
            browser.find_element_by_name('ctl00$MasterContent$txtQuantity').send_keys(str(qty))
            browser.find_element_by_name('ctl00$MasterContent$txtNetValue').send_keys(str(price * qty))
            #browser.fill('ctl00$MasterContent$txtVatTaxValue',str(tax_amount))
            browser.find_element_by_name('ctl00$MasterContent$txtVehicleOwner').send_keys(veh_owner)
            browser.find_element_by_name('ctl00$MasterContent$txtVehicleNO').send_keys(case.truck_no)
            browser.find_element_by_name('ctl00$MasterContent$txtGCLRNO').send_keys(case.name.replace('/', '').replace('-', ''))
            browser.find_element_by_name('ctl00$MasterContent$txtInvoiceNO').send_keys(case.name.replace('/', '').replace('-', ''))
            browser.find_element_by_name('ctl00$MasterContent$txtInvoiceDate').send_keys(inv_date)
            browser.find_element_by_name('ctl00$MasterContent$txtDeliveryDate').send_keys(del_date)
            browser.find_element_by_id('ctl00_MasterContent_RadioButton2').click() # for pdfprint
            browser.find_element_by_id('ctl00_MasterContent_rdoListGoods_9').click()
            time.sleep(1)
            browser.find_element_by_name('ctl00$MasterContent$txtOthCat').send_keys('DC')
            browser.find_element_by_id('ctl00_MasterContent_rbl_doctype_5').click()
            if case.partner_id.state_id.name == 'Karnataka':
                browser.find_element_by_name('ctl00$MasterContent$txtTIN').send_keys(case.partner_id.tin_no)
            else:
                browser.find_element_by_name('ctl00$MasterContent$txtTIN').send_keys(case.partner_id.tin_no)
                browser.find_element_by_name('ctl00$MasterContent$txtVehicleOwner').send_keys(veh_owner)
                time.sleep(1)
                browser.find_element_by_name('ctl00$MasterContent$txtNameAddrs').send_keys(case.partner_id.name)
            #browser.find_element_by_id('ctl00_MasterContent_btnSave').click()
            browser.find_element_by_id('ctl00_MasterContent_btn_savecumsubmit').click()
            time.sleep(5)
            #esugam = browser.find_element_by_id('ctl00_MasterContent_lbl_serialno').text
            all_cookies = browser.get_cookies()
            URL = browser.current_url.replace('Vat505_Etrans.aspx?mode=new','e_trans_pdf.aspx?mode=ack')
            
            cookies = {}
            s = requests.Session()
            for s_cookie in all_cookies:
                c_name = s_cookie["name"]
                c_value = s_cookie["value"]
                cookies['ASP.NET_SessionId'] = c_value
            response = requests.get(URL, cookies=cookies)
            #with file('/home/serveradmin/esugama/esugam.pdf','wb') as f:
            f = open('/tmp/'+case.name.replace('/', '').replace('-', '')+'.pdf','wb')
            f.write(response.content)
            f.close()
           
            
            
            #for creating file
            current_file = '/tmp/'+case.name.replace('/', '').replace('-', '')+'.pdf'
            pdf_data = self.convert_pdf(current_file)
            fp = open(current_file,'rb')
            esugam = pdf_data[pdf_data.find('Sl.No')-20:pdf_data.find('Sl.No')-9]
            result = base64.b64encode(fp.read())
            file_name = 'esugam_' + esugam
            file_name += ".pdf"
            self.pool.get('ir.attachment').create(cr, uid,
                                                  {
                                                   'name': file_name,
                                                   'datas': result,
                                                   'datas_fname': file_name,
                                                   'res_model': self._name,
                                                   'res_id': case.id,
                                                   'type': 'binary'
                                                  },
                                                  context=context)
            os.remove(current_file)
        
        except:
            raise osv.except_osv(_('Esugam Site Is Down'),_('Please Try After Some Time'))
        
        return esugam

    def kw_confirm(self, cr, uid, ids, context = None):
#         if context.get('type', '') == 'out':
        user_id = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        esugam_obj = self.pool.get('esugam.master')
        voucher_obj = self.pool.get('account.voucher')
        journal_obj = self.pool.get('account.journal')
        
        desc =""
        qty = 0
        price = 0
        product_id = False
        tax_amount = 0.0
        esugam = '0'
        move_ids = []
        move_obj = self.pool.get('stock.move')
#         for c in self.pool.get('res.company').browse(cr,uid, [1]):
#             username = c.username
#             password = c.password
#             url = c.url
        for case in self.browse(cr, uid, ids):
            for ln in case.move_lines:
                move_ids.append(ln.id)
                desc = ln.product_id.name
                qty = ln.product_qty
                price = ln.price_unit
                product_id = ln.product_id
#                 if ln.hide_fields == False:
#                     ln.state = 'done'
#                     self.write(cr, uid, ids, {'ln.state':'done'})
#                 print ln.state, "state"
                if not ln.product_qty >0 : 
                    raise osv.except_osv(_('Warning'),_('Please Enter the Valid Loaded Qty'))
                
                
                  
            #for creating vKW_Depotoucher lines
            if case.transporter_id and case.freight_advance >0 and case.transporter_id.name !='Others':
                j_ids = journal_obj.search(cr, uid, [('name','=','Cash'),('company_id','=',case.company_id.id)]) 
                voucher_vals1 = {   'partner_id'       : case.transporter_id.id,
                                          'type'              :   'payment',
                                          'amount'            : case.freight_advance,
                                          'account_id'        : case.transporter_id.property_account_payable.id,
                                          'journal_id'        : j_ids[0],
                                          'reference'         : case.name
                                          }
                vid = voucher_obj.create(cr, uid, voucher_vals1, context= context)
                voucher_obj.proforma_voucher(cr, uid,[vid],context=None)
                    
            if case.partner_id.gen_esugam == True or case.gen_esugam and user_id.partner_id.state_id.name =='Karnataka':
                for e in case.company_id.esugam_ids:
                    if e.state_id.id == user_id.partner_id.state_id.id:
                        username = e.username
                        password = e.password
                        url1 = e.url1
                        url2 = e.url2
                esugam = self.generate_esugam(cr,uid,desc, qty, price, product_id, username, password, url1,url2, case, context)
            
            elif case.partner_id.gen_esugam == True or case.gen_esugam and case.partner_id.state_id.name == 'Karnataka' and user_id.partner_id.state_id.name !='Andhra Pradesh':
                esugam_ids = esugam_obj.search(cr, uid, [('state_id','=',case.partner_id.state_id.id)])
                username = case.partner_id.es_username 
                password = case.partner_id.es_password 
                url1 = case.partner_id.es_url1
                url2 = case.partner_id.es_url2
                esugam = self.generate_esugam(cr, uid, desc, qty, price, product_id, username, password, url1, url2, case, context)

            self.write(cr, uid, ids, {'state':'in_transit','esugam_no':esugam}) 
#             move_obj.action_done(cr, uid, move_ids, context=None)
            return True
    
    
    def kw_pay_freight(self, cr, uid, ids, context = None):
#         if context.get('type', '') == 'out':
        voucher_obj = self.pool.get('account.voucher')
        journal_obj = self.pool.get('account.journal') 
        period_obj = self.pool.get('account.period')
        invoice_obj=self.pool.get('account.invoice')
        voucher_vals = {}
        voucher_vals1 = {}
        cust = freight = False
        g_ids = []
        dummy_id=[]
        inv=[]
        sup_invoice_id=[]
        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
        kw_paying_agent=cr.fetchall()
        kw_paying_agent=zip(*kw_paying_agent)[0] 
        user_id = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        cr.execute("select id from res_partner where lower(name) like '%dummy%' or lower(name) like 'karur%'")
#         cr.execute("select id from res_partner where lower(name) like '%kingswood%' or lower(name) like '%dummy%' or lower(name) like 'karur%'")
        dummy_ids=cr.fetchall()
        for i in dummy_ids:
            dummy_id.append(i[0])
        for case in self.browse(cr, uid, ids):
            cr.execute("SELECT invoice_id FROM supp_delivery_invoice_rel WHERE del_ord_id = %s ",(case.id,))
            order_id = cr.fetchall()
            if order_id:
                for d in order_id:
                    sup_invoice_id.append(d[0])
                    
                inv=invoice_obj.search(cr,uid,[('id','in',sup_invoice_id)])
                sup_invoice_ids=invoice_obj.browse(cr,uid,inv)
                for s in sup_invoice_ids:
                    if not s.freight:
                        
                        if s.state == 'open':
                            raise osv.except_osv(_('Warning'),_('Facilitator Invoice for this Delivery Challan is in Open State, Cannot Pay Freight'))
            
            partner=case.paying_agent_id
            company=case.company_id.id
            if partner:
                if partner.id not in dummy_id:
                    if case.partner_id.freight:
    #                 if case.partner_id.freight or case.paying_agent_id.id in kw_paying_agent:
                        freight=True
                        context.update({'freight':freight})
                        company=False
                        cr.execute("select id from res_company where lower(name) like '%logistics%'")
                        company=cr.fetchone()
                        if company:
                            company=company[0]
                        
                    for ln in case.move_lines:
                        supplier_id = ln.supplier_id
                        j_ids = journal_obj.search(cr, uid, [('name','like','Cash'),('company_id','=',case.company_id.id)])
                        
                        if case.partner_id.freight:
    #                          cr.execute("select id from account_journal where lower(name) like '%cash%' order by company_id desc")
    #                          j_ids=cr.fetchone()[0]
                             j_ids = journal_obj.search(cr, uid, [('name','like','Cash'),('company_id','=',company)])
                        if j_ids:
                            j_ids=j_ids[0]   
                        p_ids = period_obj.search(cr, uid, [('company_id','=',company)])
                    acc_id = journal_obj.browse(cr, uid, j_ids)
                    p_id = period_obj.browse(cr, uid, p_ids)[0]
        #             print "acc_id.id",acc_id.id
        #             print "acc_id.default_credit_account_id.id",acc_id.default_credit_account_id.id,"acc_id.default_debit_account_id.id",acc_id.default_debit_account_id.id
                    
                    if user_id.role == 'customer' and case.freight_balance >0:
                        voucher_vals = {  'partner_id'       : case.partner_id.id,
                                          'type'             : 'receipt',
                                          'amount'           : case.freight_balance,
                                          'account_id'       : acc_id.default_debit_account_id.id,
                                          'journal_id'       : j_ids,
                                          'freight'          : True,
                                          'reference'        : case.name,
                                          'company_id'       : company,
                                          'date'             : case.delivery_date_function,
#                                           'customer_id'      : case.partner_id.id,
                                          }
                        vid = voucher_obj.create(cr, uid, voucher_vals, context= context)
                        if case.partner_id.freight:
                            context.update({'freight':freight})
                        #TODO: Remove the functionlity of posting the entries
                        #voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                    
                    
                     
        #             if (user_id.role == 'depot' or user_id.role =='admin') and case.freight_balance >0:
        #                 if user_id == supplier_id:
        #                     partner = case.transporter_id
        #                 else:
        #                     partner = supplier_id.partner_id
                        
                            
                    if case.freight_balance >0 and partner:
                        voucher_vals1 = {  'partner_id'       : partner.id,
                                          'type'              : 'payment',
                                          'amount'            : case.freight_balance,
                                          'account_id'        : acc_id.default_credit_account_id.id,
                                          'journal_id'        : j_ids,
                                          'freight'           : True,
                                          'reference'         : case.name,
                                          'company_id'        : company,
                                          'period_id'         : p_id.id,
                                          'date'             : case.delivery_date_function,
#                                           'customer_id'      : case.partner_id.id,
                                          }
                        vid = voucher_obj.create(cr, uid, voucher_vals1, context= context)
                        if case.partner_id.freight:
                            context.update({'freight':freight})
                        #TODO: Remove the functionlity of posting the entries
                        #voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                        self.write(cr, uid, ids, {'state':'freight_paid'})
        return True
    

    
    
    
    
    def all_pay_freight_button(self, cr, uid, ids, context = None):
#         if context.get('type', '') == 'out':
        voucher_obj = self.pool.get('account.voucher')
        journal_obj = self.pool.get('account.journal') 
        period_obj = self.pool.get('account.period')
        voucher_vals = {}
        voucher_vals1 = {}
        stock_ids=[]
        cust = freight = False
        g_ids = []
        m=[]
        inv=[]
        sup_invoice_id=[]
        dummy_id=[]
        companys=[]
        user_id = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        
#         stock_ids=self.search(cr,uid,[('state','=','done'),('freight_balance','>',0)])
# #         stock_id=self.browse(cr, uid, stock_ids)
#         for n in self.browse(cr, uid, stock_ids):
#             print n.name
#             m.append(n.name)
#         lenght=len(m)
#         print m
        
        user_id = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        cr.execute("select id from res_partner where lower(name) like '%dummy%' or lower(name) like 'karur%'")
#         cr.execute("select id from res_partner where lower(name) like '%kingswood sup%'")
        dummy_ids=cr.fetchall()
        for i in dummy_ids:
            dummy_id.append(i[0])
        
       
            
        cr.execute("select id from stock_picking where paying_agent_id not in %s and delivery_date_function<='2014-1-31' and state='done'and type='out' and freight_balance>0 ",(tuple(dummy_id),))
        stock_id=cr.fetchall()
        for z in stock_id:
            stock_ids.append(z[0])
       
        
        
        for case in self.browse(cr, uid, stock_ids):
            
            cr.execute("SELECT invoice_id FROM supp_delivery_invoice_rel WHERE del_ord_id = %s ",(case.id,))
            order_id = cr.fetchall()
            if order_id:
                
                for d in order_id:
                    sup_invoice_id.append(d[0])
                    
                inv=invoice_obj.search(cr,uid,[('id','in',sup_invoice_id)])
                sup_invoice_ids=invoice_obj.browse(cr,uid,inv)
                for s in sup_invoice_ids:
                    if not s.freight:
                        print "state=",s.state
                        if s.state == 'open':
                            raise osv.except_osv(_('Warning'),_('Facilitator Invoice for this Delivery Challan is in Open State, Cannot Pay Freight'))
            
            
            print "DO-",case.name
            partner=case.paying_agent_id
            if partner:
                company=case.company_id.id
                if partner.id not in dummy_id:
                    #print "partner",partner.id, partner.name
                    if case.partner_id.freight:
                        #context.update({'freight':freight})
                        
                        company=False
                        cr.execute("select id from res_company where lower(name) like '%logistics%'")
                        company=cr.fetchone()
                        if company:
                             company=int(company[0])
                        
                    for ln in case.move_lines:
                        supplier_id = ln.supplier_id
                        j_ids = journal_obj.search(cr, uid, [('name','like','Cash'),('company_id','=',case.company_id.id)])
                        if case.partner_id.freight:
                            j_ids = journal_obj.search(cr, uid, [('name','like','Cash'),('company_id','=',company)])
                        if j_ids:
                            j_ids=j_ids[0]     
                        p_ids = period_obj.search(cr, uid, [('company_id','=',company)])
                   
                    
                        acc_id = journal_obj.browse(cr, uid, j_ids)
                      
                    p_id = period_obj.browse(cr, uid, p_ids)[0]
        #             print "acc_id.id",acc_id.id
        #             print "acc_id.default_credit_account_id.id",acc_id.default_credit_account_id.id,"acc_id.default_debit_account_id.id",acc_id.default_debit_account_id.id
                    
                    
                    if user_id.role == 'customer' and case.freight_balance >0 and acc_id:
                        voucher_vals = {  'partner_id'       : case.partner_id.id,
                                          'type'             : 'receipt',
                                          'amount'           : case.freight_balance,
                                          'account_id'       : acc_id.default_debit_account_id.id,
                                          'journal_id'       : j_ids,
                                          'freight'          : True,
                                          'reference'        : case.name,
                                          'company_id'       : company,
                                          'date'             : case.delivery_date_function,
                                          }
                        vid = voucher_obj.create(cr, uid, voucher_vals, context= context)
                        if case.partner_id.freight:
                            context.update({'freight':True})
                        else:
                            context.update({'freight':False})
#                         voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                    
                    
                     
        #             if (user_id.role == 'depot' or user_id.role =='admin') and case.freight_balance >0:
        #                 if user_id == supplier_id:
        #                     partner = case.transporter_id
        #                 else:
        #                     partner = supplier_id.partner_id
                        
    #                 if (user_id.role == 'depot' or user_id.role =='admin') and case.freight_balance >0:       
                 
                    if case.freight_balance >0 and acc_id:
                        voucher_vals1 = {  'partner_id'       : partner.id,
                                          'type'              : 'payment',
                                          'amount'            : case.freight_balance,
                                          'account_id'        : acc_id.default_credit_account_id.id,
                                          'journal_id'        : j_ids,
                                          'freight'           : True,
                                          'reference'         : case.name,
                                          'company_id'        : company,
                                          'period_id'         : p_id.id,
                                          'date'             : case.delivery_date_function,
                                          
                                          }
                        vid = voucher_obj.create(cr, uid, voucher_vals1, context= context)
                        if case.partner_id.freight:
                            context.update({'freight':True})
                        else:
                            context.update({'freight':False})
#                         voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                        self.write(cr, uid, [case.id], {'state':'freight_paid'})
        
        return True
    
    
    
    def deliver(self, cr, uid, ids, context = None):
        move_obj = self.pool.get('stock.move')
        today = time.strftime('%Y-%m-%d %H:%M:%S')
        move_ids=[]
        freight_balance = 0.0
        for case in self.browse(cr, uid, ids):
            freight_balance=case.freight_total - case.freight_deduction - case.freight_advance 
            for ln in case.move_lines:
                move_ids.append(ln.id)
               
                if not ln.unloaded_qty >0 and not ln.rejected_qty >0:
                    raise osv.except_osv(_('Warning'),_('Please Enter the Valid Qty in Unloaded and Rejected'))
                    
                if ln.delivery_date > today:
                    raise osv.except_osv(_('Warning'),_('Please Enter the Valid Delivery Date'))
        move_obj.action_done(cr, uid, move_ids, context=None)
            
        return self.write(cr, uid, ids, {'state':'done','freight_balance':freight_balance}, context=context)
    


    def print_delivery_challan(self,cr,uid,ids,context=None):
        rep_obj = self.pool.get('ir.actions.report.xml')
        res={}
        res1={}
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment') 
#         pwriter = PdfFileWriter()
#         os.makedirs('/home/serveradmin/Desktop/temp')
        
        res = rep_obj.pentaho_report_action(cr, uid, 'Proforma Invoice', ids,None,None)

        return res
    
    
    def print_freight_advice(self,cr,uid,ids,context=None):
        rep_obj = self.pool.get('ir.actions.report.xml')
        res={}
        res1={}
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment') 
#         pwriter = PdfFileWriter()
#         os.makedirs('/home/serveradmin/Desktop/temp')
        res = rep_obj.pentaho_report_action(cr, uid, 'Freight Advice', ids,None,None)
        return res
        

    
    

    # To Create customer and Paying agents Refund
    def create_refund(self, cr, uid, ids,type,case, ln,price):
        inv_obj = self.pool.get('account.invoice')
        inv_ln_obj = self.pool.get('account.invoice.line')
        journal_obj = self.pool.get('account.journal')
        prod_obj =self.pool.get('kw.product.price')
        refund_vals = {}
        refund_ln_vals = {}
        if type == 'in_refund': 
#             partner_id = ln.supplier_id.partner_id.id
            partner_id = case.paying_agent_id.id
            journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase_refund')])[0]
#             for i in ln.product_id.seller_ids:
#                 if ln.supplier_id.partner_id.id == i.name.id:
#                     prod_ids=prod_obj.search(cr, uid, [('ef_date','<=',case.date),('supp_info_id','=',i.id)],limit=1, order='ef_date desc')
#                     for j in prod_obj.browse(cr,uid,prod_ids):
#                         if i.customer_id and i.customer_id.id == case.partner_id.id:
#                             if case.partner_id.freight:
#                                 price=j.product_price
#                             else:
#                                 price = j.sub_total
            
            price=(ln.deduction_amt/ln.rejected_qty)
                         
            
            
        else:
            journal_id = journal_obj.search(cr, uid, [('type', '=', 'sale_refund')])[0]
            partner_id = case.partner_id.id
            refund_vals.update({'delivery_orders_ids': [(6, 0, [case.id])]}),
        
        refund_vals = {'partner_id':partner_id, 
                       'type':type, 
                       'journal_id':journal_id, 
#                        'date_invoice':datetime.today().strftime('%Y-%m-%d %H:%M:%S'), 
#                        'date_due':datetime.today().strftime('%Y-%m-%d %H:%M:%S'), 
                        'date_invoice':ln.delivery_date,
                        'date_due':ln.delivery_date,
                       'origin':case.name
                       }
        refund_vals.update(inv_obj.onchange_partner_id(cr, uid, ids, type, partner_id)['value'])
        refund_ln_vals.update(inv_ln_obj.product_id_change(cr, uid, ids, ln.product_id.id, ln.product_uom, qty=0, name='', type=type, partner_id=partner_id, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None))
        refund_ln_vals = {'product_id':ln.product_id.id, 
            'name':ln.name, 
            'quantity':ln.rejected_qty, 
            'price_unit':price, 
            'uos_id':ln.product_uom.id}
        refund_vals.update({'invoice_line':[(0, 0, refund_ln_vals)]})
        if type =='in_refund':
            refund_vals.update({'supp_delivery_orders_ids': [(6, 0, [case.id])]}),
#         else:
#             refund_vals.update({'delivery_orders_ids': [(6, 0, [case.id])]}),
#         
        inv_obj.create(cr, uid, refund_vals)

   
    def get_supplier_invoice(self, cr, uid, ids, freight, context = None):
        order_line = {} 
        tax_vals={}
        vals={}
        supp_del_orders = {}
        supp_inv_group = {}
        supp_invoice_lines = {}
        handling_vals={}
        sup_inv_vals = {}
        line_groups = {}
        line_vals = {}
        freight_line_vals = {}
        sup_freight_val={}
        supplier_freight_val={}
        ft_account_expense={}
        supplier_freight_del_orders=[]
        handling_del_orders={}
        freight_vals = {}
        freight_inv_vals = {}
        freight_del_orders = {}
        freight_inv_group = {}
        handling_group={}
        freight_invoice_lines = {}
        handling_invoices_lines={}
        handling_invoices ={}
        sup_inv_val_c={}
        s_id={}
        name=""
        journal=False
        type = ""
        partner = False
        freight=False
        a_id=False
        sup_parent_id= price1 = 0
        s_parent_id=False
        handling_price = 0.0
        handling_vals['quantity']=0.00
        sup_freight_val['price_unit']=0.000
        handling_vals['price_unit'] = 0
        supplier_freight_val['price_unit']=0.000
        freight_price=0.000
        prod_obj = self.pool.get('product.product')
        kwprod_obj=self.pool.get('kw.product.price')
        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        sup_freight_ids=prod_obj.search(cr, uid, [('name_template','=','Freight')])
        partner_id={}
        h_price={}
        #to fetch the Logistic company_id
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company=cr.fetchone()
        if company:
            company=company[0]
        freight_obj=self.pool.get('product.product')
        #to get all journal_ids
        journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase')])[0]
        cust_journal_id = journal_obj.search(cr, uid, [('type', '=', 'sale')])[0]
        journal_id_l = journal_obj.search(cr, uid, [('type', '=', 'purchase'),('company_id','=',company)])[0]
        cust_journal_id_l =journal_obj.search(cr, uid, [('type', '=', 'sale'),('company_id','=',company)])[0]
        c_account_parent=self.pool.get('account.account')
        
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        g_ids = []
        if user.role != 'admin':
            raise osv.except_osv(_('Warning'),_('You Cannot Create Invoice'))
        
        cr.execute("SELECT del_ord_id FROM supp_delivery_invoice_rel WHERE del_ord_id IN %s ",(tuple(ids),))
        order_id = cr.fetchall()
        
        if order_id:
            raise osv.except_osv(_('Warning'),_('Invoice Already Created for the Selected Delivery Order'))

        #to fetch the supplier where name != kingswood
        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
        kw_paying_agent=cr.fetchall()
        kw_paying_agent=zip(*kw_paying_agent)[0]
          
        ids = self.search(cr,uid,[('id','in',ids)],order='paying_agent_id,id')
        for case in self.browse(cr, uid, ids):  
             journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase'),('company_id','=',case.company_id.id)])[0]
             if case.state not in ('done','freight_paid'):
                 raise osv.except_osv(_('Warning'),_('Delivery Order "%s" Should Be In Delivered State')% (case.name,))
                 
             kw_paying_agent_id=case.paying_agent_id.id
             if case.partner_id.freight==True:
                freight=True
             else:
                freight=False
             if case.type=="out":
                 type = case.type
                 loaded_qty = 0
                 rejected_qty = 0
                 frt=0
#                  handling_vals['quantity']=0
                 for ln in case.move_lines:
                     cr.execute("select substr(value_reference,17)::integer from ir_property where name =  'property_account_expense_categ' and res_id = 'product.category,' || %s", (ln.product_id.categ_id.id, ))
                     account_expense_sup = cr.fetchall()
                     if account_expense_sup:
                        vals['account_id'] = account_expense_sup[0]
                        handling_vals['account_id']=account_expense_sup[0]
                     #### for lacation name not equal to supplier (eg: kingswood)
                                  ###################################################################################
                        ######             FOR KW LOGISTIC Account Supplier Invoice
                        #################################################################################
                     if kw_paying_agent_id not in kw_paying_agent:
                        if freight:
                            sup_parent_id= case.paying_agent_id.account_pay and case.paying_agent_id.account_pay.id or False
                            if not sup_parent_id:
                                 raise osv.except_osv(_('Warning'),_('"%s"Account Not Found in Kingswood Logistic"')% (case.paying_agent_id.name,))
                     
                    
                     
                     if ln.location_id.name != "Stock":
                         
                         for ft in prod_obj.browse(cr,uid,sup_freight_ids):
                             cr.execute("select substr(value_reference,17)::integer from ir_property where name =  'property_account_expense_categ' and res_id = 'product.category,' || %s", (ft.categ_id.id,))
                             ft_account_expense = cr.fetchall()
                             if ft_account_expense:
                                 sup_freight_val['account_id'] = ft_account_expense[0]    
                                 
                                 
                                 
                         sup_freight_val['product_id']=ft.id
                         frt=ft.id
                         sup_freight_val['name']=ft.name_template
                         f_name=ft.name_template
                         sup_freight_val['quantity'] = ln.unloaded_qty
                         sup_freight_val['uos_id']=ft.uom_id.id
                         sup_freight_val['state'] = 'done' 
                          
                          
                         #for Supplier invoice Vals
                         vals['product_id'] = ln.product_id.id
                         vals['name'] = ln.name
                         vals['quantity'] = ln.unloaded_qty
                         vals['rejected_qty'] = ln.rejected_qty
                         vals['uos_id'] = ln.product_uom.id    
                         vals['price_unit'] = 0
                         vals['move_line_id'] = ln.id
                          
                              
                        #for supplier handling invoice vals
                         handling_vals['product_id']=frt
                         handling_vals['name'] = f_name
                         if handling_vals['quantity'] ==0:
                            handling_vals['quantity'] = ln.unloaded_qty
                         handling_vals['rejected_qty'] = ln.rejected_qty
                         handling_vals['uos_id'] = ln.product_uom.id    
                         
                         handling_vals['move_line_id'] = ln.id
                         if ft_account_expense and freight:
                             handling_vals['account_id'] = ft_account_expense[0]
                        
                              
                              
                              
                         for i in ln.product_id.seller_ids:
                             freight_price =0.0
                             handling_price = 0.0
                             if case.paying_agent_id.id == i.name.id :
                                 prod_ids=kwprod_obj.search(cr, uid, [('ef_date','<=',ln.delivery_date),('supp_info_id','=',i.id)],limit=1, order='ef_date desc')
                                 for j in kwprod_obj.browse(cr,uid,prod_ids):
                                     #to fetch values based on partner_id and facilitaor
                                     if i.customer_id and i.customer_id.id == case.partner_id.id:
                                         if case.partner_id.freight:
                                             price1=j.product_price
                                         else:
                                             price1 = j.sub_total
                                         freight_price = j.transport_price
                                         #handling_price = j.handling_charge
                                         partner = j.partner_id
                                         partner_name = j.partner_id.name
                                         vals['price_unit'] = price1
                                         sup_freight_val['price_unit'] = freight_price
                                         handling_vals['price_unit'] = j.handling_charge or 0
                                         qty = ln.unloaded_qty
#                                          i.name.name
#                                          cr.execute("update stock_picking set sup_invoice=True where id=%s ",(case.id,))
                         
                                     
                        ######  FOR KW LOGISTIC Account Supplier Invoice
                                         if kw_paying_agent_id not in kw_paying_agent:
                                            if j.partner_id:
                                                if freight:
                                                    s_parent_id = j.partner_id.account_pay and j.partner_id.account_pay.id or False
                                                else:
                                                    s_parent_id = j.partner_id.property_account_payable and j.partner_id.property_account_payable.id or False
                                                if not s_parent_id:
                                                     raise osv.except_osv(_('Warning'),_('"%s"Account Not Found in Kingswood Logistic"')% (j.partner_id.name,))
                                         if partner:
                                            s_id.update({partner.id:s_parent_id})
                                        
                                         #CHECK THE CODE
                                         if ln.rejected_qty > 0 and ln.deduction_amt > 0:
                                             if price1 > 0:
                                                self.create_refund(cr, uid, ids,'in_refund',case, ln,price1)
                                      
                                                                            
                         if ln.location_id.name == "Stock" and price1==0:
                             price1=1
                         if vals['price_unit']==0 and case.paying_agent_id.id not in kw_paying_agent:
                             raise osv.except_osv(_('Warning'),_('Check Goods Price, Selected Supplier "%s" Do Not Have Rate for "%s" In The Goods Master')% (case.paying_agent_id.name,ln.product_id.name ))
                 
                         #check for the key for supplier Invoices
                         supp_key = case.paying_agent_id.id,case.partner_id.freight,ln.delivery_date
                         freight_key = case.paying_agent_id.id, case.partner_id.id,freight_price,ln.delivery_date
                         product_key =case.paying_agent_id.id,ln.product_id.id,ln.price_unit
                         
                         #Handling Invoice Key
                         if handling_vals['price_unit'] >0 and partner:
                        #added Handling price to handling key[If Handling price differs then create new invoice]                          
                             handling_key=ln.product_id.id,partner,case.paying_agent_id.id,handling_vals['price_unit']
                         
                         
                        
                          #grouping the supplier Handling invoices based on product_id and partner
#                          print "facilitator",case.paying_agent_id.id," partner_name",partner_name,"-prince",ln.unloaded_qty
                         
                         handling_ft=False
                         if partner and handling_vals['price_unit'] >0:
                             if handling_key not in handling_group :
                                 handling_vals['quantity'] = ln.unloaded_qty
                                 handling_del_orders[handling_key]=[case.id]
                                 if freight:
                                     handling_ft=True
                                     journal=journal_id_l
                                 else:
                                     handling_ft=False
                                     journal=journal_id
                                 a_id=s_id[partner.id]
                                     
                                 
                                 handling_group[handling_key]={
                                                                    'partner_id'      : partner.id,
                                                                    'date_invoice'   : ln.delivery_date,
                                                                    'type'           : 'in_invoice',
                                                                     'journal_id'    : journal,
                                                                     'account_id'    : a_id,
                                                                      'freight'      :handling_ft
                                                                }
                                 
                                 
                                 handling_invoices_lines[handling_key] = [(handling_vals.copy())]
                             else:
                                  #handling_vals['quantity'] += ln.unloaded_qty
                                  handling_invoices_lines[handling_key][0]['quantity'] += ln.unloaded_qty
                                  #handling_invoices_lines[handling_key] = [(handling_vals.copy())]
                                  handling_del_orders[handling_key].append(case.id)   
                         
                        #grouping the supplier invoices based on supplier,freight, and freight_price  
                         if ln.location_id.name != "Stock":
                             if supp_key not in supp_inv_group :
                                 supp_del_orders[supp_key] =[case.id]
                                 supp_inv_group[supp_key] = {
                                                             'partner_id'     : case.paying_agent_id.id,
                                                             'date_invoice'   : ln.delivery_date,
                                                             'type'           :   'in_invoice',
                                                             'journal_id'     : journal_id,
                                                           }
                                 supp_invoice_lines[supp_key] = [(vals.copy())]
                                 if not case.partner_id.freight :
                                     supp_invoice_lines[supp_key][0]['price_unit'] += freight_price
                                 if case.partner_id.freight and freight_price >0: 
                                     freight_vals[supp_key] = [(sup_freight_val.copy())]
                              
                             else:
                                 if not case.partner_id.freight :
                                     vals['price_unit'] += freight_price
                                 supp_invoice_lines[supp_key].append((vals.copy()))
                                 supp_del_orders[supp_key].append(case.id)
                                 if case.partner_id.freight and freight_price >0: 
                                     freight_vals[supp_key] = [(sup_freight_val.copy())]
                                 
                              
                       
                         # for creating freight invoices based on supplier,customer and freight price 
                         if ln.location_id.name != "Stock":
                             if freight_key not in freight_inv_group:
                                 if case.partner_id.freight:
                                     freight_del_orders[freight_key] = [case.id]
                                     freight_inv_group[freight_key] = {'partner_id'   : case.paying_agent_id.id,
                                                          'date_invoice': ln.delivery_date,
                                                          'type':   'in_invoice',
                                                          'journal_id' : journal_id_l,
                                                          'account_id':sup_parent_id,
                                                           'freight':True,
                                                          }
                                     freight_invoice_lines[freight_key] = [(sup_freight_val.copy())]
                             else:
                                 freight_invoice_lines[freight_key].append((sup_freight_val.copy()))
                                 freight_del_orders[freight_key].append(case.id)
      
                     
                     
                     
                     
                     
  
#                      if ln.location_id.name == "Stock":
                     if case.paying_agent_id.id in kw_paying_agent:    
                         transporter_id=0
                         cr.execute("select id from res_partner where lower(name) like 'others%'")
                         other=cr.fetchall()
                         other=zip(*other)[0]
                          
                         cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                         paying_agent=cr.fetchall()
                         paying_agent=zip(*paying_agent)[0]
                         if case.paying_agent_id.id in paying_agent:
                             paying_agent_ids=self.search(cr, uid, [('partner_id', '=', case.transporter_id.id)])
                             for j in self.browse(cr,uid,paying_agent_ids):
                                         total_freight=j.freight_total
                                         
                             for ft in freight_obj.browse(cr,uid,sup_freight_ids):
                                 cr.execute("select substr(value_reference,17)::integer from ir_property where name =  'property_account_expense_categ' and res_id = 'product.category,' || %s", (ft.categ_id.id,))
                                 ft_account_expense = cr.fetchall()
                                 if ft_account_expense:
                                     supplier_freight_val['account_id'] = ft_account_expense[0]    
                                 supplier_freight_val['product_id']=ft.id
                                 supplier_freight_val['name']=ft.name_template
                                 supplier_freight_val['quantity'] = ln.unloaded_qty
                                 supplier_freight_val['uos_id']=ft.uom_id.id
                                 supplier_freight_val['state'] = 'done' 
                                 supplier_freight_val['price_unit'] = case.freight_total
                                  
                             supplier_freight_del_orders.append(case.id)
                              
                             if kw_paying_agent_id in kw_paying_agent:
                                 if case.transporter_id.id not in paying_agent and ln.location_id.usage=='internal':
                                     supp_fr_group = {'partner_id'   : case.transporter_id.id,
                                                                         'date_invoice': ln.delivery_date,
                                                                         'type':   'in_invoice',
                                                                         'journal_id' : journal_id_l
                                                                  }
                                     if case.transporter_id.id not in other and ln.location_id.usage=='internal':
                                         transporter_id=case.transporter_id.id
#                                          cr.execute("update stock_picking set sup_invoice=True where id=%s ",(case.id,))
                                     sup_inv_val_c.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_invoice', supp_fr_group['partner_id'])['value'])
                                     sup_inv_val_c.update(supp_fr_group)  
                                     sup_inv_val_c.update({
                                                                                 
                                                                'supp_delivery_orders_ids': [(6, 0, supplier_freight_del_orders)],
                                                                'invoice_line': [(0,0, supplier_freight_val)],
                                                                                 
                                                     }) 
                                      
                                      
#                                      if freight==True:
#                                          if company and sup_parent_id:
#                                              sup_inv_val_c.update({'company_id':company,
#                                                                   'account_id':sup_parent_id,
#                                                                   'journal_id' : journal_id_l,
#                                                                   })
#                                          
#                                                            
#                                                   
#                                              sup_inv_val_c.update({'freight':True}) 
                                              
                                     if transporter_id>0:

                                             other_parent_id= case.transporter_id.account_pay and case.transporter_id.account_pay.id or False
                                             if not other_parent_id:
                                                  raise osv.except_osv(_('Warning'),_('"%s"Account Not Found in Kingswood Logistic"')% (case.transporter_id.name,))
                                             sup_inv_val_c.update({'company_id':company,
                                                                  'account_id':other_parent_id,
                                                                  'journal_id' : journal_id_l,
                                                                  })
                                             
                                             sup_inv_val_c.update({'freight':True}) 
                                             inv_obj.create(cr, uid, sup_inv_val_c)
                              
         #for grouping the product id_price and product_id for supplier goods invoice lines
        
        if type=="out":
            supp_data = {}
            freight_data = {}
            for keys in supp_invoice_lines:
                line_groups = []
                for k in supp_invoice_lines[keys]:
                    product_key = k['product_id'],k['price_unit']
                    if product_key not in line_groups:
                        if not keys in supp_data:
                            supp_data[keys] = {product_key:[(0,0,k)]}
                        else:
                            supp_data[keys].update({product_key:[(0,0,k)]})
                        line_groups.append(product_key)
                        
                    else:
                        supp_data[keys][product_key][0][2]['rejected_qty'] += k['rejected_qty']
                        supp_data[keys][product_key][0][2]['quantity'] += k['quantity']
                
            #for separating the product_keys from vals
            for x in supp_data:
                for i in supp_data[x].values():
                    if x in line_vals:
                        line_vals[x].append(i[0])
                    else:
                        line_vals[x]= i

             # for creating the freight invoice lines
            for f_key in freight_invoice_lines:
                freight_groups = []
                for f in freight_invoice_lines[f_key]:
                    freight_product_key = f['product_id'],f['price_unit']
                    if freight_product_key not in freight_groups:
                        if not f_key in freight_line_vals:
                            freight_line_vals[f_key] = [(0,0,f)]
                        else:
                            freight_line_vals[f_key].append((0,0,f))
                        freight_groups.append(freight_product_key)
                        
                    else:
                        freight_line_vals[f_key][0][2]['price_unit'] =f['price_unit']
                        freight_line_vals[f_key][0][2]['quantity'] +=f['quantity']
            
            #creating supplier goods invoice
            price_unit=0
            for inv in line_vals:
#             if kw_paying_agent_id not in kw_paying_agent:  
                context.update({'type':'in_invoice'})
#                 for inv in line_vals:
                if supp_inv_group[inv]['partner_id'] not in kw_paying_agent:
                    sup_inv_vals.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_invoice', supp_inv_group[inv]['partner_id'])['value'])
                    sup_inv_vals.update(supp_inv_group[inv])
                    sup_inv_vals.update({
                                                      
                                         'invoice_line': line_vals[inv],
                                         'supp_delivery_orders_ids': [(6, 0, supp_del_orders[inv])],
                                     }) 
                    
                    sup_inv_vals.update({
    #                                                      
                                                          'journal_id' : journal_id,
                                                          })
                    inv_obj.create(cr, uid, sup_inv_vals,context=context) 
                      
             #for creating supplier freight invoices
            for freight_inv in freight_line_vals:
                price_unit=0
                facilitator=[]
                freight_inv_vals.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_invoice', freight_inv_group[freight_inv]['partner_id'])['value'])
                freight_inv_vals.update(freight_inv_group[freight_inv])
                freight_inv_vals.update({
                                                                     
                                            'supp_delivery_orders_ids': [(6, 0, freight_del_orders[freight_inv])],
                                            'invoice_line': freight_line_vals[freight_inv],
                                                                                                                                        
                                         })
               
                if freight_line_vals[freight_inv][0][2]['price_unit']>0:
#                     if sup_freight_val['price_unit']>0:
#                     if kw_paying_agent_id not in kw_paying_agent:
                    if freight_inv_group[freight_inv]['partner_id'] not in kw_paying_agent:
                        if freight_inv_group[freight_inv]['freight']:
                            if company and sup_parent_id:
                                freight_inv_vals.update({'company_id':company,
    #                                                       'account_id':sup_parent_id,
                                                          'journal_id' : journal_id_l,
                                                          })
                                
                                freight_inv_vals.update({'freight':True}) 
                             #to create freight invoice for supplier
                                inv_obj.create(cr, uid, freight_inv_vals) 
                  
            for handling_inv in handling_invoices_lines:
                handling_invoices.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_invoice', handling_group[handling_inv]['partner_id'])['value'])
                handling_invoices.update(handling_group[handling_inv])
                handling_invoices.update({
                                                                    
                                            'supp_delivery_orders_ids': [(6, 0, handling_del_orders[handling_inv])],
                                            'invoice_line': [(0,0,handling_invoices_lines[handling_inv][0])],
                                                                                                                                        
                                         }) 
                  
             
                if s_parent_id:
                       
                     if handling_group[handling_inv]['freight']==True and company:                  
                         handling_invoices.update({'company_id':company}) 
                     #to create freight invoice for supplier
                     inv_obj.create(cr, uid, handling_invoices) 
                 
        return True

   
   
    # To Create customer
    def get_invoice(self,cr,uid,ids,freight,context=None):
        today = time.strftime('%Y-%m-%d')
        if context ==  None:
            context = {} 
        quantity=0.0
        journal_obj = self.pool.get('account.journal')
        product_groups = {}
        delivery_orders = {}
        date_groups={}
        inv_obj = self.pool.get('account.invoice')
        inv_groups = {}
        freight_group= {}
        order_line = {} 
        inv_vals={}
        sup_grp={}
        qty = 0  
        supp_group = {}
        supp_invoice_lines = {}
        supp_del_orders = {}
        product_line = {}
        supp_inv_group = {}
        price=0.00
        price1=0
        paying_agent={}
        line_vals = {}
        total_freight=0.00
        freight=False
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company=cr.fetchone()
        if company:
            company=company[0]
        prod_obj=self.pool.get('kw.product.price')
        freight_val={}
        journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase')])[0]
#         cust_journal_id = journal_obj.search(cr, uid, [('type', '=', 'sale')])[0]
        journal_id_l = journal_obj.search(cr, uid, [('type', '=', 'purchase'),('company_id','=',company)])[0]
        cust_journal_id_l =journal_obj.search(cr, uid, [('type', '=', 'sale'),('company_id','=',company)])[0]
        c_account_parent=self.pool.get('account.account')
        
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        g_ids = []
        if user.role != 'admin':
            raise osv.except_osv(_('Warning'),_('You Cannot Create Invoice'))
            
        for case in self.browse(cr, uid, ids):
            type=case.type
            if case.partner_id.freight==True:
                freight=True
            cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
            kw_paying_agent=cr.fetchall()
            kw_paying_agent=zip(*kw_paying_agent)[0]   
            kw_paying_agent_id=case.paying_agent_id.id
            
#                 continue
#         print ids
        #TO check whether the invoices has been created for selected delivery orders
        
        cr.execute("SELECT del_ord_id FROM delivery_invoice_rel WHERE del_ord_id IN %s ",(tuple(ids),))
        order_id = cr.fetchall()
        
        if order_id:
            raise osv.except_osv(_('Warning'),_('Invoice Already Created for the Selected Delivery Order'))
  
        for case in self.browse(cr, uid, ids):
            cust_journal_id = journal_obj.search(cr, uid, [('type', '=', 'sale'),('company_id','=',case.company_id.id)])[0]
#             print "company",case.partner_id.property_account_receivable.company_id
#             print "accounts",case.partner_id.property_account_receivable.account_id
            type=case.type
            if type=="out":
#             print 'id-', uid
#             if case.user_log != 'KW_Admin':
#                 raise osv.except_osv(_('Warning'),_('You Cannot Create Invoice For The Delivery Challan'))

                if case.state in ('done','freight_paid'):
                   kw_paying_agent_id=case.paying_agent_id.id 
                   val={}
                   vals={}
                   val['price_unit'] = 0
                   freight_val={}
                   freight_val['price_unit'] = 0
                   for ln in case.move_lines:
                       price=0
                       prod_obj=self.pool.get('kw.product.price')
                       for i in ln.product_id.customer_ids:
                           if case.partner_id.id == i.name.id:
                                prod_ids=prod_obj.search(cr, uid, [('ef_date','<=',ln.delivery_date),('cust_info_id','=',i.id)],limit=1, order='ef_date desc')
                                for j in prod_obj.browse(cr,uid,prod_ids):
                                    if case.partner_id.freight:
#                                         if j.transport_price>0:
#                                             price = j.product_price
# #                                         else:
# #                                             raise osv.except_osv(_('Warning'),_('Update the Freight Price in "%s" Product Master For The customer "%s"')% (ln.product_id.name,case.partner_id.name,))
#                                     else:
                                        price = j.product_price 
                                       
                                    else:
                                        price = j.product_price+j.transport_price
                                        
                                    
                                val['price_unit']  = price
                                # for creating Customer and Paying agents Refunds if rejected Quantity is > 0
#                                 if ln.rejected_qty > 0 or ln.deduction_amt > 0:
#                                     if price > 0:    
#                                     self.create_refund(cr, uid, ids,'in_refund',case, ln,price)
#                                         self.create_refund(cr, uid, ids,'out_refund',case, ln,price)
                        
                       cr.execute("select substr(value_reference,17)::integer from ir_property where name =  'property_account_income_categ' and res_id = 'product.category,' || %s", (ln.product_id.categ_id.id, ))
                       account_expense = cr.fetchall()
                       if account_expense:
                           val['account_id'] = account_expense[0]
#                        if price1==0 and price==0:
#                               raise osv.except_osv(_('Warning'),_('Check Goods Price, Selected Customer "%s" Do Not Have Rate for "%s" In The Goods Master')% (case.partner_id.name,ln.product_id.name ))
                       
                       freight_obj=self.pool.get('product.product')
                       freight_ids=freight_obj.search(cr, uid, [('name_template','=','Freight')])
                       for ft in freight_obj.browse(cr,uid,freight_ids):
                           freight_val['product_id']=ft.id
                           freight_val['name']=ft.name_template
                           freight_val['quantity'] = ln.unloaded_qty
                           freight_val['uos_id']=ft.uom_id.id
                           freight_val['rejected_qty'] = ln.rejected_qty
                           cr.execute("select substr(value_reference,17)::integer from ir_property where name =  'property_account_income_categ' and res_id = 'product.category,' || %s", (ft.categ_id.id, ))
                           account_expense = cr.fetchall()
                           if account_expense:
                               if account_expense:
                                   freight_val['account_id'] = account_expense[0]
     #to do freight line in invoice line readonly                      
    #                        freight_val['state'] = 'done' 
                           
                       val['product_id'] = ln.product_id.id
                       val['name'] = ln.name
                       val['quantity'] = ln.unloaded_qty
                       val['rejected_qty'] = ln.rejected_qty
                       val['uos_id'] = ln.product_uom.id
                       val['state'] = 'draft' 
                       if val['price_unit']==0:
                            raise osv.except_osv(_('Warning'),_('Check Goods Price, Selected Customer "%s" Do Not Have Rate for "%s" In The Goods Master')% (case.partner_id.name,ln.product_id.name ))
                       cr.execute("select state_id from account_tax")
                       tax_state=cr.fetchall()
                      
                       k=0
                       tax=[]
                       tax_obj=[]
                       for k in tax_state:
                            tax.append(k[0])
                        
                       if case.partner_id.state_id.id in tax or case.paying_agent_id.state_id.name in tax:
                           if case.partner_id.state_id.name == case.paying_agent_id.state_id.name:
                               cr.execute("select id from account_tax where state_id=%s",(case.partner_id.state_id.id,))
                               tax_id=cr.fetchone()[0]
                               if tax_id:      
                                   cr.execute("select tax_id from product_taxes_rel where prod_id=%s and tax_id=%s",(ln.product_id.id,tax_id))
                                   tax_obj=cr.fetchall()
                               else:
                                   raise osv.except_osv(_('Warning'),_('No State Taxes Mappend in Account Taxes For The Customer State "%s" Or Supplier State "%s"')% (case.partner_id.state_id.name,case.paying_agent_id.state_id.name))
                              
                       if case.partner_id.state_id.name != case.paying_agent_id.state_id.name:
                            cr.execute("select tax_id from product_csttaxes_rel where prod_id=%s",(ln.product_id.id,))
                            tax_obj = cr.fetchall()
                       
                           
                       if tax_obj: 
                           val.update({
                                               'invoice_line_tax_id': [(6, 0,list(tax_obj[0]))]
                                       })
                       
                       i=[]
                       
                       #for grouping the customer invoices based on product,price and partner_id
                       key = ln.product_id.id,price,case.partner_id.id,ln.delivery_date
                       sup_grp[key]=vals
                       
                       ###################################################################################
                       ######             FOR KW LOGISTIC Account 
                       #################################################################################
                       
#                        if kw_paying_agent_id not in kw_paying_agent:
                       if freight:
                           c_parent_id= case.partner_id.account_rec and case.partner_id.account_rec.id or False
                           if not c_parent_id:
                                raise osv.except_osv(_('Warning'),_('"%s"Account Not Found in Kingswood Logistic"')% (case.partner_id.name,))
                          
                               
                       
                       if not key in product_groups:                           
                           product_groups[key] = val.copy()
                           freight_group[key] = freight_val.copy()
                           delivery_orders[key] = [case.id]
                           inv_groups[key] = {'partner_id'   : case.partner_id.id,
                                             'date_invoice': ln.delivery_date,
                                             'type':   'out_invoice',
                                             'journal_id' : cust_journal_id,
                                             
                                             }
                       else:
                           prod_obj=self.pool.get('kw.product.price')
                           for i in ln.product_id.customer_ids:
                              
                                if case.partner_id.id == i.name.id:
                                  prod_ids=prod_obj.search(cr, uid, [('ef_date','<=',ln.delivery_date),('cust_info_id','=',i.id)],limit=1, order='ef_date desc')
                               
                                  for j in prod_obj.browse(cr,uid,prod_ids):
                                       val['price_unit']  = j.product_price
          
                                       
                                       product_groups[key]['quantity'] += ln.unloaded_qty
                                       
                                       product_groups[key]['rejected_qty'] += ln.rejected_qty
                                       val['price_unit']  += ln.product_id.list_price
                                       freight_group[key]['rejected_qty'] += ln.rejected_qty
                                       freight_group[key]['quantity']+=ln.unloaded_qty
                                       delivery_orders[key].append(case.id)
                                       
                      
                                       
                else:
                    raise osv.except_osv(_('Warning'),_('Delivery Order "%s" Should Be In Delivered State')% (case.name,))  
        
 


    #Customer Invoice
        if type=="out":
            partner = [] # for control
            transport_rate=0
            destination=""
            
            for case in self.browse(cr,uid, ids):
#                 cr.execute("update stock_picking set cust_invoice=True where id=%s ",(case.id,))
                c=0
                kw_paying_agent_id=case.paying_agent_id.id
                if case.partner_id.freight==True:
                     
                           
                    for p in product_groups:
                        freight_val['price_unit']=0
                        
                        if case.partner_id.id in p and p not in partner:
                            destination=case.partner_id.city
                            for i in self.browse(cr, uid,delivery_orders[p]):
                                for temp in i.move_lines:
                                    for j in temp.product_id.customer_ids:
                                        #to fetch transport price based on the delivery date
                                        if case.partner_id.id==j.name.id:
                                            prod_ids=prod_obj.search(cr, uid, [('ef_date','<=',temp.delivery_date),('cust_info_id','=',j.id)],limit=1, order='ef_date desc')
                                            for tp in prod_obj.browse(cr,uid,prod_ids):
                                                transport_rate = tp.transport_price 
                                freight_val['price_unit']=transport_rate
#                                 val['price_unit']  = price1
                                
                                freight_group[p].update({'price_unit'   : freight_val['price_unit'],
                                                     })
                              
                            inv_vals = inv_groups[p].copy()
                            inv_vals.update(inv_obj.onchange_partner_id(cr, uid, ids,'out_invoice', inv_groups[p]['partner_id'])['value'])
                            inv_vals.update({
                                                    'delivery_orders_ids': [(6, 0, delivery_orders[p])],
                                                    'invoice_line': [(0, 0, product_groups[p])],
                                            })
                          
                            inv_vals.update({'destination':destination,
                                             'journal_id' : cust_journal_id,
                                             })
                            
                            inv_obj.create(cr, uid, inv_vals)
                            
                            #for creating Freight Invoice
                            inv_vals.update({
                                                    'delivery_orders_ids': [(6, 0, delivery_orders[p])],
                                                    'invoice_line': [(0,0,freight_group[p])],
                                                    
                                            })
                            
                            #for Reporting purpose
                            partner.append(p)
                            if freight_val['price_unit']>0:
                                if freight==True:
                                    if company and c_parent_id:
                                        inv_vals.update({'company_id':company,
                                                     'account_id':c_parent_id,
                                                     'freight':True,
                                                     'journal_id' : cust_journal_id_l,
                                                     })
                                                       
                                            
                                inv_vals.update({
                                                 'destination':destination,
                                                 })
                                                         
                                #partner.append(p)
                                inv_obj.create(cr, uid, inv_vals)
                            
                              
                                       
                else: 
                    
                    val['state'] = 'draft'            
                    for p in product_groups:
                        if case.partner_id.id in p and p not in partner:
                            inv_vals = inv_groups[p].copy()
                            inv_vals.update(inv_obj.onchange_partner_id(cr, uid, ids,'out_invoice', inv_groups[p]['partner_id'])['value'])
                            inv_vals.update({
                                                 'delivery_orders_ids': [(6, 0, delivery_orders[p])],
                                                  'invoice_line': [(0, 0, product_groups[p])],
                                                })
                            order_obj=self.pool.get('delivery_order_rel')
                            inv_vals.update({'destination':destination,
                                             'journal_id' : cust_journal_id,
                                             })
                            inv_obj.create(cr, uid, inv_vals)
                            partner.append(p)
                            
                              
                   
            
        return True
    
    #schedular for Creating Invoices
    def do_invoice(self, cr, uid, automatic = False, use_new_cursor = False,context = None ):
        

        #for creating invoices from deliver orders
        cr.execute("""select id from stock_picking where state in ('done', 'freight_paid') and date::date = """+"'"+datetime.today().strftime("%Y-%m-%d")+"'")
        do_ids = cr.fetchall()
        
        do_ids = [d[0] for d in do_ids]
        inv_ids = do_ids
        
        
       
        if do_ids:
            cr.execute('SELECT del_ord_id FROM delivery_invoice_rel WHERE del_ord_id IN %s',(tuple(do_ids),))
            order_ids = cr.fetchall()
            if order_ids:
                order_ids = [i[0] for i in order_ids ]
                inv_ids = list(set(do_ids).difference(order_ids))
                
            if inv_ids:
                self.get_invoice(cr, uid, inv_ids, False, context)
        
        #for creating invoices from incoming shipments
        
        cr.execute("""select id from stock_picking where state in ('done') and type = 'in' and date::date = """+"'"+datetime.today().strftime("%Y-%m-%d")+"'")
        in_ids = cr.fetchall()
        shipment_ids = [d[0] for d in in_ids]
        ship_inv_ids = shipment_ids
        if shipment_ids:
            cr.execute('SELECT in_shipment_id FROM incoming_shipment_invoice_rel WHERE in_shipment_id IN %s',(tuple(shipment_ids),))
            ship_order_ids = cr.fetchall()
            if ship_order_ids:
                ship_order_ids = [s[0] for s in ship_order_ids ]
                ship_inv_ids = list(set(shipment_ids).difference(ship_order_ids))
              
            if ship_inv_ids:
                self.pool.get('stock.picking.in').get_invoice(cr, uid,ship_inv_ids, False, context )
        return True   
    
    def create(self,cr,uid,vals,context=None):
        today = time.strftime('%Y-%m-%d')    
        res={}
        u_name=''
        proforma_price=0.00
        user_obj = self.pool.get('res.users')
        partner=vals['partner_id']
        cr.execute("select freight from res_partner where id=%s",(partner,))
        freight=cr.fetchone()
        vals['freight']=freight[0]
        if 'move_lines' in vals:
            if vals['move_lines']==[]:
                raise osv.except_osv(_('Warning'),_("Add Goods Details"))
        for ml in vals['move_lines']:
                vals['product_id']=ml[2]['product_id']
    
                price_obj=self.pool.get('kw.product.price')
                prod_obj=self.pool.get('product.product')
                for p in prod_obj.browse(cr,uid,[ml[2]['product_id']]):

                    for i in p.customer_ids:
                        if i.name.id==vals['partner_id']:

                            ml[2]['price_unit']=i.proforma_price
                            proforma_price=i.proforma_price
                    if proforma_price==0:
                        ml[2]['price_unit'] = p.list_price
                product_qty = ml[2]['product_qty']
                if product_qty>40:
                     raise osv.except_osv(_('Warning'),_("Enter the Quantity in Metric Tons Eg. if the loaded quantity is 16800 kgs enter 16.800"))
                if vals.get('move_lines',False):
                   for m in vals['move_lines']:
                      
                       lines_len=len(vals['move_lines'])
                       
                       if lines_len>1:
                           raise osv.except_osv(_('Warning'),_('Add only one product'))
                       
                       m[2].update({'partner_id':vals['partner_id']})
                       if vals.get('paying_agent_id',False):
                           user_id = user_obj.search(cr,uid,[('partner_id','=',vals['paying_agent_id'])])
                           for user in user_id:
                               m[2].update({'supplier_id':user})
                       else:
                           user = user_obj.browse(cr, uid, [uid])[0]
                           vals['paying_agent_id'] = user.partner_id.id
                else:
                    raise osv.except_osv(_('Warning'),_('Add one product'))  
                
        g_ids = []
        user_obj = self.pool.get('res.users')
        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
        paying_agent=cr.fetchall()
        paying_agent=zip(*paying_agent)[0]
         
        driver = vals.get('transporter_id',False)
        
        stock_obj = self.browse(cr,uid,[driver])[0] 
        
        vals['paying_agent']='not' 
        res = " "
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):

            user = user_obj.browse(cr, uid, [uid])[0]
            if g.name == 'KW_Admin':
                u_name='KW_Admin'
                vals['paying_agent']='representative'
            
            if vals['paying_agent_id'] in paying_agent:
                if g.name == 'KW_Depot' or  g.name == 'KW_Admin':
                    if user.role!='representative':      
                        vals['paying_agent']= 'kingswood'
                       
            

                    cr.execute("select id from res_partner where lower(name) like 'others'")
                    transport=cr.fetchall()
                    transport=zip(*transport)[0]
                    if transport:
                        if vals['transporter_id'] in transport:
                            vals['paying_agent']='representative'
                        else:
                            vals['paying_agent']='kingswood'
                    
        cr.execute("select state_id from res_partner where id=%s",(vals['paying_agent_id'],))
        state=cr.fetchone()
        
        if state and u_name == 'KW_Admin':
            if vals['state_id']!=state[0]:
                raise osv.except_osv(_('Warning'),_("State and Facilitator's State which you selected is not same "))
                vals['city_id']=False     
        res = super(stock_picking_out,self).create(cr, uid, vals, context)
        
        # for creating the sequence code
        tate_id=0
        state_code=[]
        if 'state_id' in vals:
            state_id=vals['state_id']
        
            
        cr.execute("select code from account_fiscalyear where date_start < '"+today+"' and date_stop >'" +today+"'")
        code = cr.fetchone()
        if code:
            year = code[0]
            if state_id:
                cr.execute('select code from res_country_state where id =%s',(state_id,))
                state_code=cr.fetchone()[0]
            else:
                vals['state_id']=user.state_id.id
        if state_code:
            format = 'DC/' + year + '/' + str(state_code) +'/'
        else:
            format = 'DC/' + year + '/' + user.state_id.code +'/'
        cr.execute("select name from stock_picking where name like '"+format+"'|| '%' order by to_number(substr(name,(length('"+format+"')+1)),'99999') desc limit 1")
        prev_format = cr.fetchone()
        if not prev_format:
            name = format + '00001'
        else:
            auto_gen = prev_format[0][-5:]
            name = format + str(int(auto_gen) + 1).zfill(5)
        self.write(cr, uid, [res],{'name':name},context=context)                   
        return res
    
    def write(self, cr, uid, ids, vals, context = None):
#         if context.get('type', '') == 'out':
            price=0.0
            result={}
            g_ids = []
            proforma_price=0.0
            res = super(stock_picking_out,self).write(cr, uid, ids, vals, context)
            if 'move_lines' in vals:
#               if vals['move_lines'][0][2]:
                     
                if not vals['move_lines'][0][2]:
                    if ids:
                        cr.execute("select product_id from stock_move where picking_id=%s",(ids[0],))
                        sp=cr.fetchone()
                        if not sp:
                            raise osv.except_osv(_('Warning'),_('Add one product'))
                else:       
                    if vals['move_lines'][0][2].get('product_qty',False):
                        product_qty = vals['move_lines'][0][2]['product_qty']
                        if product_qty>40:
                            raise osv.except_osv(_('Warning'),_("Enter the Quantity in Metric Tons Eg. if the loaded quantity is 16800 kgs enter 16.800"))
        
                        prod_price_obj=self.pool.get('kw.product.price')
                        if vals['move_lines'][0][2].get('product_id',False):
                            for case in self.browse(cr,uid,ids):
                                
                                for ln in case.move_lines:
                                     id=vals['move_lines'][0][2]['product_id']
                                     case.product_id=vals['move_lines'][0][2]['product_id']
                                     cr.execute('UPDATE stock_picking SET product_id = %s WHERE id=%s',(id,case.id,))
                                     for i in ln.product_id.customer_ids:
                                        if i.name.id==case.partner_id.id:
                                            
                                            vals['move_lines'][0][2]['price_unit']=i.proforma_price
                                            proforma_price=i.proforma_price
                                     if proforma_price==0:  
                                        vals['move_lines'][0][2]['price_unit']=ln.product_id.list_price
                              
                    sm_obj = self.pool.get('stock.move')
    #                 res = super(stock_picking_out,self).write(cr, uid, ids, vals, context)
                    sm_ids=sm_obj.browse(cr, uid, ids, context=context)
                    vals1 ={}
                    user_obj = self.pool.get('res.users')
                    for case in self.browse(cr, uid, ids):
                        
            
                        for ln in case.move_lines:
                            if 'move_lines' in vals: 
                                lines_len=len(vals['move_lines'])
                                
                                if lines_len>1:
                                    if vals['move_lines'][0][2].get('product_id',False):
                                        pr_id=vals['move_lines'][0][2]['product_id']
                                        if pr_id:
                                            vals['move_lines'][0][2]['product_id']=False
                                    raise osv.except_osv(_('Warning'),_('Add only one product'))
                            
                            ln.partner_id = vals.get('partner_id',ln.partner_id.id)
                            #vals['move_lines'].update({'partner_id':ln.partner_id})
                            
                            if 'move_lines' in vals:
                                 vals1 = vals['move_lines'][0][2]
                            if case.paying_agent_id :
                                user_id = user_obj.search(cr,uid,[('partner_id','=',case.paying_agent_id.id)])
                                for user in user_id:
                                    vals1.update({'supplier_id':user})
                               
                                        
                                
                            vals1.update({'partner_id':ln.partner_id})
                    sm_obj.write(cr, uid, [ln.id], vals1,context)
                
            for case in self.browse(cr, uid, ids):
        

                for ln in case.move_lines:
                    i=0
                    paying_agent={}
                    paying_agent_id=[]
                    
                    
                    if 'state_id' in vals:
                        if case.paying_agent_id.state_id.id!=vals['state_id']:
                            raise osv.except_osv(_('Warning'),_("State and Facilitator's State which you selected is not same "))
                        if 'city_id' in vals:
                            if case.city_id.state_id.id!=vals['state_id']:  
                                raise osv.except_osv(_('Warning'),_("City which you selected is not Belongs to Selected Sate"))

                    if vals.get('paying_agent_id', False):
                        paying_agent_id = vals.get('paying_agent_id',False)
                        paying_agent_obj = self.browse(cr,uid,[paying_agent_id])[0]
                        

                        user_obj = self.pool.get('res.users')
                        user = user_obj.browse(cr, uid, [uid])[0]
                        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
                        gid = cr.dictfetchall()
                        for x in gid:
                            g_ids.append(x['gid'])
                        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
            
                                if g.name == 'KW_Supplier':
                                    result = 'KW_Supplier'
                                
                                elif g.name == 'KW_Depot':
                                    result= 'KW_Depot'
                                    cr.execute("select id from stock_location where lower(name) like 'supplier%'")
                                    paying_agent=cr.fetchall()
                                    paying_agent=zip(*paying_agent)[0]
                                    cr.execute('UPDATE stock_move SET location_id = %s WHERE picking_id=%s',(paying_agent,case.id,))
                                    paying_agent_obj.location_id=paying_agent
                                    
                                    if user.role=='depot':
                                        
                                        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                                        paying_agent=cr.fetchall()
                                        paying_agent=zip(*paying_agent)[0]
                                        if paying_agent_id in paying_agent:
                                            cr.execute('UPDATE stock_picking SET paying_agent = %s WHERE id=%s',("kingswood",case.id,))
                                            cr.execute('UPDATE stock_move SET location_id = %s WHERE picking_id=%s',(user.location_id.id,case.id,))
                                            paying_agent_obj.location_id=user.location_id.id
                                           
                                    if user.role=='admin':
                                        cr.execute("select id from stock_location where here lower(name) like 'stock%'")
                                        stock=cr.fetchall()
                                        stock=zip(*stock)[0]
                                        cr.execute('UPDATE stock_move SET location_id = %s WHERE picking_id=%s',(paying_agent,case.id,))
                                        paying_agent_obj.location_id=paying_agent
                                        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                                        paying_agent=cr.fetchall()
                                        paying_agent=zip(*paying_agent)[0]
                                        if paying_agent_id in paying_agent:                                                   
                                            cr.execute("select id from res_partner where lower(name) like 'others'")
                                            transport=cr.fetchall()
                                            transport=zip(*transport)[0]
                                            if transport:
                                                if transporter_id in transport:
                                                    cr.execute('UPDATE stock_picking SET paying_agent = %s WHERE id=%s',("representative",case.id,))
                                                else:
                                                    cr.execute('UPDATE stock_picking SET paying_agent = %s WHERE id=%s',("kingswood",case.id,))
                                
                                elif g.name!='KW_Supplier' and g.name != 'KW_Depot':
                                    cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                                    k_paying_agent=cr.fetchall()
                                    k_paying_agent=zip(*k_paying_agent)[0]
                                    id=case.paying_agent_id.id
                                    if id in k_paying_agent:
                                        cr.execute('UPDATE stock_picking SET paying_agent = %s WHERE id=%s',("kingswood",case.id,))
                                        cr.execute("select id from stock_location where lower(name) like 'stock%'")
                                        paying_agent=cr.fetchall()
                                    else:
                                        cr.execute("select id from stock_location where lower(name) like 'supplier%'")
                                        paying_agent=cr.fetchall()
                                    if paying_agent:
                                        paying_agent=zip(*paying_agent)[0]
                                        cr.execute('UPDATE stock_move SET location_id = %s WHERE picking_id=%s',(paying_agent,case.id,))
                                        paying_agent_obj.location_id=paying_agent   
                                    
                                
                                else:
                                    cr.execute("select id from stock_location where here lower(name) like 'stock%'")
                                    paying_agent=cr.fetchall()
                                    paying_agent=zip(*paying_agent)[0]
                                    cr.execute('UPDATE stock_move SET location_id = %s WHERE picking_id=%s',(paying_agent,case.id,))
                                    paying_agent_obj.location_id=paying_agent

                 
               
                
                cr.execute("select partner_id from stock_picking where id=%s",(ids[0],))   
                partner=cr.fetchone()
                cr.execute("select freight from res_partner where id=%s",(partner,))
                freight=cr.fetchone()
                cr.execute('UPDATE stock_picking SET freight = %s WHERE id=%s',(freight,ids[0],))
                
                
                    
                      
            return res
        
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        if context is None:
            context = {}
        user_id = self.pool.get('res.users').browse(cr, uid,[uid])[0]
        if user_id:
            raise osv.except_osv(_('Warning!'), _("You Cannot Duplicate the record, You Can only Create New Record "))
        return super(stock_picking_out, self).copy(cr, uid, id, default, context=context)
    
    def unlink(self, cr, uid, ids, context=None):
        for case in self.browse(cr, uid, ids):
            if case.state != 'draft':
                raise osv.except_osv(_('Warning!'), _("You Cannot Delete the record, You Can only Delete Draft Record "))
        return super(stock_picking_out, self).unlink(cr, uid, ids, context = context) 
    
    
    def get_del_qty(self, cr, uid, ids,context = None):
        self.get_day_date(cr,uid,ids)
        cr.execute("select id from stock_picking where type='out' and del_quantity is null or del_quantity=0")
        qty_ids=cr.fetchall()
        if qty_ids:
            for i in qty_ids:
                n=int(i[0])
                cr.execute("select unloaded_qty from stock_move where picking_id=%s",(n,))
                qty=cr.fetchone()
                if qty>0:
                    cr.execute("update stock_picking set del_quantity=%s where id=%s",(qty,n))
                else:
                    cr.execute("update stock_picking set del_quantity=%s where id=%s",(0.000,n))
        
#         cr.execute("SELECT del_ord_id FROM delivery_invoice_rel")
#         order_ids = cr.fetchall()
#         for i in order_ids:
#             n=int(i[0])
#             cr.execute("update stock_picking set cust_invoice=True where id=%s",(i[0],))
#              
#         cr.execute("SELECT del_ord_id FROM supp_delivery_invoice_rel")
#         sup_ids = cr.fetchall()
#         for j in sup_ids:
#             cr.execute("update stock_picking set sup_invoice=True where id=%s",(j[0],))
#              
#         cr.execute("SELECT in_shipment_id FROM incoming_shipment_invoice_rel")  
#         in_ids = cr.fetchall()
#         for k in in_ids:
#             cr.execute("update stock_picking set sup_invoice=True where id=%s",(k[0],)) 
            
   
        return True
               
stock_picking_out()


class stock_picking(osv.osv):
    _inherit='stock.picking' 
    
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        user = self.pool.get('res.users').browse(cr,uid,uid)
        
        if context is None:context = {}
        res = super(stock_picking, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # For Supplier Groups: Filtering related Customers in OUT
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if context.get('type', '') == 'out' and view_type =='form':
            cr.execute("select true from res_groups_users_rel gu \
                        inner join res_groups g on g.id = gu.gid \
                        where g.name = 'KW_Supplier' and uid ="+str(uid))
            is_supp = cr.fetchone()
            
            if is_supp and is_supp[0] == True:
                cust_ids = [] 
                cr.execute("select customer_id from customer_list_rel where supplier_id = " + str(user.partner_id.id))         
                custs = cr.fetchall()
                for s in custs:
                    cust_ids.append(s[0]) 
                
                for field in res['fields']:
                    if field == 'partner_id':
                        res['fields'][field]['domain'] = [('id','in', cust_ids)]
                    
        
              
        return res
    
    def _get_paying_agent(self, cr, uid, ids, args, field_name, context = None):
        res={}
        g_ids = []
        paying_agent=[]
        warning=''
        log_user={}
        picking={}
        u_id=context.get('uid')
        if u_id:
            uid=u_id
        user_obj = self.pool.get('res.users')
        for case in self.browse(cr, uid, ids):
            if case.type=='out':
                res[case.id] = "" 
                cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
                gid = cr.dictfetchall()
                for x in gid:
                    g_ids.append(x['gid'])
                for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
   
                    if g.name == 'KW_Supplier':
                        res[case.id] = 'KW_Supplier'
      
                    if g.name == 'KW_Customer':
                        res[case.id] = 'KW_Customer'
                    if g.name == 'KW_Depot':
                        res[case.id] = 'KW_Depot'
                    if g.name == 'KW_Admin':
                        res[case.id] = 'KW_Admin'
                
          
                    if res[case.id]=='KW_Depot' or res[case.id] == 'KW_Admin':
                        user = user_obj.browse(cr, uid, [uid])[0]
                        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                        paying_agent=cr.fetchall()
                        paying_agent=zip(*paying_agent)[0]
                        if log_user !='KW_Admin':
                            if user.role != 'representative':
                                if case.paying_agent_id in paying_agent:
                                    res[case.id]='kingswood'
        
        return res 
     
    def _get_default_state(self, cr, uid, context=None):
        
        g_ids = []
        user_obj = self.pool.get('res.users')

        res = "not"
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):

            user = user_obj.browse(cr, uid, [uid])[0]
            if g.name != 'KW_Admin':
                res=user.state_id.id


        return res
    
    def _get_default_paying_agent(self, cr, uid, context=None):
        
        g_ids = []
        user_obj = self.pool.get('res.users')

        res = "not"
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):

            user = user_obj.browse(cr, uid, [uid])[0]
            if g.name == 'KW_Admin':
                res='kingswood'
            if g.name == 'KW_Depot' and user.role!='representative':
                res = 'kingswood'

        return res
    
    
    def _get_default_paying_agent_id(self, cr, uid, context=None):
        res ={}
        g_ids = []
        user_obj = self.pool.get('res.users')

        res = False
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):

            user = user_obj.browse(cr, uid, [uid])[0]
            if g.name == 'KW_Supplier':
                 res=user.partner_id.id
            
        return res
    
    
    def _get_move_lines(self, cr, uid, ids, args, field_name, context = None):
        res = {}
        u_id=context.get('uid')
        if u_id:
            uid=u_id
        cr.execute("select login from res_users where id  ="+str(uid))
        user=cr.fetchone()[0]
        
        for case in self.browse(cr, uid, ids):
            if case.type=='out':
                for temp in case.move_lines:
                    case.freight=case.partner_id.freight
                    res[case.id] = {'product': " ", 'qty':0.000,'del_quantity':0.000,'transporter':" ",'price_unit':0.0,'location_id':0,'users':'','freight':''}
                    res[case.id]['product']  = temp.product_id.name
                    res[case.id]['qty']  = temp.product_qty 
                    res[case.id]['product_id']= temp.product_id.id
                    res[case.id]['price_unit']= temp.price_unit
                    res[case.id]['location_id']=temp.location_id.id
                    res[case.id]['users']=user
                    res[case.id]['freight']=case.partner_id.freight
                    res[case.id]['del_quantity'] = temp.unloaded_qty
                    if case.transporter_id:   
                        res[case.id]['transporter']  = case.transporter_id.name
                    else:
                        res[case.id]['transporter']  = case.driver_name 
                 
        return res 
    
    
    def _get_user(self, cr, uid, ids, args, field_name, context = None):
        res ={}
        g_ids = []  
        user_obj = self.pool.get('res.users')
        u_id=context.get('uid')
        if u_id:
            uid=u_id
        for case in self.browse(cr, uid, ids):
            if case.type=='out':
                res[case.id] = " "
                cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
                gid = cr.dictfetchall()
                for x in gid:
                    g_ids.append(x['gid'])
                for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
   
                    if g.name == 'KW_Supplier':
                        res[case.id] = 'KW_Supplier'
   
                         
                    if g.name == 'KW_Customer':
                        res[case.id] = 'KW_Customer'
                    if g.name == 'KW_Depot':
                        res[case.id] = 'KW_Depot'   
                    if g.name == 'KW_Admin':
                        res[case.id] = 'KW_Admin'
                        
                    if res[case.id]=='KW_Depot' or res[case.id] == 'KW_Admin':
                        
                        user = user_obj.browse(cr, uid, [uid])[0]
                        
                        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                        paying_agent=cr.fetchall()
                        paying_agent=zip(*paying_agent)[0]
                        if res[case.id] !='KW_Admin':
                            if user.role=='representative':
                                if case.paying_agent_id in paying_agent:
                                    case.paying_agent='representative'
                
                                    
                                        
                            else:
                                if case.paying_agent_id in paying_agent:
                                    case.paying_agent='kingswood'
         
        return res
    
    def _get_default_user(self, cr, uid, context=None):
        res ={}
        g_ids = []
        
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
        
                    
        return res
     
    def _get_permission(self, cr, uid, ids, args, field_name, context = None):
        res ={}
        g_ids = []
        for case in self.browse(cr, uid, ids):
            if case.type=='out':
                res[case.id] = True
                cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
                gid = cr.dictfetchall()
                for x in gid:
                    g_ids.append(x['gid'])
                for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
 
                    if g.name == 'KW_Supplier':
                       res[case.id] = False
                    if g.name == 'KW_Customer':
                        res[case.id] = True
        return res
    
    def _get_default_new_date(self, cr, uid, context=None):
       res=datetime.today().strftime('%Y-%m-%d %H:%M:%S')
       return res 
    def _get_default_permission(self, cr, uid, context=None):
        res = True
        g_ids = []
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
            if g.name == 'KW_Supplier':
                res = False
            if g.name == 'KW_Depot':
                res = False
            if g.name == 'KW_Customer':
                res = True
        return res
    
    def _get_freight_amount(self, cr, uid, ids, args, field_name, context = None):
        res = {}
        for case in self.browse(cr, uid, ids):
            if case.type=='out':
                res[case.id] = {'freight_deduction': 0.00, 'freight_total':0.00}
                deduction = total = 0.00
                
                tol_qty = case.partner_id.tol_qty
                tol_rate = case.partner_id.tol_rate
                
                for ln in case.move_lines:
                    total += (case.freight_charge * ln.unloaded_qty)
                    
                    # Picking Qty > Product Qty
                    if ((ln.product_qty - ln.unloaded_qty) * 1000) > (ln.product_qty * tol_qty) :
                        deduction += (((ln.product_qty - ln.unloaded_qty)*1000) - (ln.product_qty * tol_qty)) * tol_rate
                        
                res[case.id]['freight_deduction'] = deduction
                res[case.id]['freight_total'] = total
#                 res[case.id]['freight_balance'] = total - deduction - case.freight_advance
        return res
    
    def kw_pay_freight(self, cr, uid, ids, context = None):
#         if context.get('type', '') == 'out':
        voucher_obj = self.pool.get('account.voucher')
        journal_obj = self.pool.get('account.journal') 
        period_obj = self.pool.get('account.period')
        invoice_obj=self.pool.get('account.invoice')
        voucher_vals = {}
        voucher_vals1 = {}
        cust = freight = False
        g_ids = []
        dummy_id=[]
        inv=[]
        sup_invoice_id=[]
        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
        kw_paying_agent=cr.fetchall()
        kw_paying_agent=zip(*kw_paying_agent)[0] 
        user_id = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        cr.execute("select id from res_partner where lower(name) like '%dummy%' or lower(name) like 'karur%'")
#         cr.execute("select id from res_partner where lower(name) like '%kingswood%' or lower(name) like '%dummy%' or lower(name) like 'karur%'")
        dummy_ids=cr.fetchall()
        for i in dummy_ids:
            dummy_id.append(i[0])
        for case in self.browse(cr, uid, ids):
            cr.execute("SELECT invoice_id FROM supp_delivery_invoice_rel WHERE del_ord_id = %s ",(case.id,))
            order_id = cr.fetchall()
            if order_id:
                for d in order_id:
                    sup_invoice_id.append(d[0])
                    
                inv=invoice_obj.search(cr,uid,[('id','in',sup_invoice_id)])
                sup_invoice_ids=invoice_obj.browse(cr,uid,inv)
                for s in sup_invoice_ids:
                    if not s.freight:
                        
                        if s.state == 'open':
                            raise osv.except_osv(_('Warning'),_('Facilitator Invoice for this Delivery Challan is in Open State, Cannot Pay Freight'))
            
            partner=case.paying_agent_id
            company=case.company_id.id
            if partner:
                if partner.id not in dummy_id:
                    if case.partner_id.freight:
    #                 if case.partner_id.freight or case.paying_agent_id.id in kw_paying_agent:
                        freight=True
                        context.update({'freight':freight})
                        company=False
                        cr.execute("select id from res_company where lower(name) like '%logistics%'")
                        company=cr.fetchone()
                        if company:
                            company=company[0]
                        
                    for ln in case.move_lines:
                        supplier_id = ln.supplier_id
                        j_ids = journal_obj.search(cr, uid, [('name','like','Cash'),('company_id','=',case.company_id.id)])
                        
                        if case.partner_id.freight:
    #                          cr.execute("select id from account_journal where lower(name) like '%cash%' order by company_id desc")
    #                          j_ids=cr.fetchone()[0]
                             j_ids = journal_obj.search(cr, uid, [('name','like','Cash'),('company_id','=',company)])
                        if j_ids:
                            j_ids=j_ids[0]   
                        p_ids = period_obj.search(cr, uid, [('company_id','=',company)])
                    acc_id = journal_obj.browse(cr, uid, j_ids)
                    p_id = period_obj.browse(cr, uid, p_ids)[0]
        #             print "acc_id.id",acc_id.id
        #             print "acc_id.default_credit_account_id.id",acc_id.default_credit_account_id.id,"acc_id.default_debit_account_id.id",acc_id.default_debit_account_id.id
                    
                    if user_id.role == 'customer' and case.freight_balance >0:
                        voucher_vals = {  'partner_id'       : case.partner_id.id,
                                          'type'             : 'receipt',
                                          'amount'           : case.freight_balance,
                                          'account_id'       : acc_id.default_debit_account_id.id,
                                          'journal_id'       : j_ids,
                                          'freight'          : True,
                                          'reference'        : case.name,
                                          'company_id'       : company,
                                          'date'             : case.delivery_date_function,
#                                           'customer_id'      : case.partner_id.id,
                                          }
                        vid = voucher_obj.create(cr, uid, voucher_vals, context= context)
                        if case.partner_id.freight:
                            context.update({'freight':freight})
                        #TODO: Remove the functionlity of posting the entries
                        #voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                    
                    
                     
        #             if (user_id.role == 'depot' or user_id.role =='admin') and case.freight_balance >0:
        #                 if user_id == supplier_id:
        #                     partner = case.transporter_id
        #                 else:
        #                     partner = supplier_id.partner_id
                        
                            
                    if case.freight_balance >0 and partner:
                        voucher_vals1 = {  'partner_id'       : partner.id,
                                          'type'              : 'payment',
                                          'amount'            : case.freight_balance,
                                          'account_id'        : acc_id.default_credit_account_id.id,
                                          'journal_id'        : j_ids,
                                          'freight'           : True,
                                          'reference'         : case.name,
                                          'company_id'        : company,
                                          'period_id'         : p_id.id,
                                          'date'             : case.delivery_date_function,
#                                           'customer_id'      : case.partner_id.id,
                                          }
                        vid = voucher_obj.create(cr, uid, voucher_vals1, context= context)
                        if case.partner_id.freight:
                            context.update({'freight':freight})
                        #TODO: Remove the functionlity of posting the entries
                        #voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                        self.write(cr, uid, ids, {'state':'freight_paid'})
        return True
    
    def _get_new_date(self, cr, uid, ids, args, field_name, context = None):
        res={}
        for case in self.browse(cr, uid, ids):
            if case.type=='out':
                for temp in case.move_lines:

                         
                    
                    res[case.id] = {'date_function': " ", 'delivery_date_function':""}
                    
                    res[case.id]['date_function']=case.date
                    res[case.id]['delivery_date_function']=temp.delivery_date
#                     self.get_day_date(cr,uid,ids)
                    
                     
                        
                   
        return res
 
    def get_day_date(self,cr,uid,ids,context=None):
        day_id=[]
        for case in self.browse(cr, uid, ids):
            cr.execute("select id from stock_picking where delivery_date_function is null")
            day_ids=cr.fetchall()
            g=0
            for g in day_ids:
                day_id.append(g[0])
            
            
   
                
            for p in day_id:
                cr.execute("select to_char(s.date, 'YYYY') as year,to_char(s.date, 'MM') as month,to_char(s.date, 'YYYY-MM-DD') as day from stock_picking s where id =%s",(p,))
                date=cr.fetchall()[0]
                cr.execute("select to_char(sm.delivery_date, 'YYYY-MM-DD') from stock_move sm where sm.picking_id =%s",(p,))
                date1=cr.fetchall()
                
                if date:
                    cr.execute("UPDATE stock_picking SET year =%s where id=%s", (date[0],p))
                    cr.execute("UPDATE stock_picking SET month =%s where id=%s", (date[1],p))
                    cr.execute("UPDATE stock_picking SET day =%s where id=%s", (date[2],p))
                    cr.execute("UPDATE stock_picking SET date_function =%s where id=%s", (date[2],p))
                if date1:
                    cr.execute("UPDATE stock_picking SET delivery_date_function =%s where id=%s", (date1[0],p))
                                   
        return True
    
    def _get_inv_status(self, cr, uid, ids, field_name, args, context = None):
        res = {}
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'cust_invoice' : False, 'sup_invoice':False}
            cr.execute("SELECT invoice_id FROM delivery_invoice_rel where del_ord_id = "+str(case.id))
            cinv_ids = cr.fetchall()
            if cinv_ids:
                res[case.id]['cust_invoice'] = True
            cr.execute("SELECT invoice_id FROM supp_delivery_invoice_rel where del_ord_id = "+str(case.id))
            sinv_ids = cr.fetchall()
            cr.execute("SELECT invoice_id FROM incoming_shipment_invoice_rel where in_shipment_id = "+str(case.id))
            Iinv_ids = cr.fetchall()
            if sinv_ids or Iinv_ids:
                res[case.id]['sup_invoice'] = True
        return res
    
    def get_workorder(self, cr, uid, ids, field_name, args, context = None):
        work_obj = self.pool.get('work.order')
        res = {}
        for case in self.browse(cr, uid, ids):
            res[case.id] = ''
            if case.type=="out" and case.paying_agent_id:
                w_ids = work_obj.search(cr, uid, [('product_id','=',case.product_id.id),('state_id','=',case.paying_agent_id.state_id.id),('partner_id','=',case.partner_id.id)])
                for w in work_obj.browse(cr, uid, w_ids):
                    res[case.id]= w.work_order_no or ''
        return res

     
    _columns={
               #standard
               'partner_id': fields.many2one('res.partner', 'Partner', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
              # New:
               
               'work_order'    :   fields.function(get_workorder,store=True,type="char",string='Work Order Number',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
               'truck_no'      :   fields.char('Vehicle No',size=20, states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
               'esugam_no'     :   fields.char('E-Sugam No.',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
               'state'         :   fields.selection([('draft','Draft'),('in_transit','In Transit'),('auto', 'Waiting Another Operation'),
                                                      ('confirmed', 'Waiting Availability'),
                                                      ('assigned', 'Ready to Deliver'),
                                                      ('done', 'Delivered'),
                                                      ('cancel', 'Cancelled'),('freight_paid','Freight Paid')],'Status', readonly=True, select=True,),
                                                      
              'freight_charge' : fields.float('Freight Charge',digits=(0,2),states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'freight_advance': fields.float('Freight Advance',digits=(0,2),states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'driver_name'    : fields.char('Driver Name',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'diver_contact'  : fields.char('Driver Contact',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'hide_fields'    : fields.function(_get_permission,type='boolean',method=True,string="Permission", store=True),
              
              'freight_total'    : fields.function(_get_freight_amount, type='float', string='Frieght Total', store=True, multi="tot"),
              'freight_deduction': fields.function(_get_freight_amount, type='float', string='Frieght Deduction', store=True, multi="tot"),                 
#               'freight_balance'  : fields.function(_get_freight_amount, type='float', string='Frieght Balance', store=True, multi="tot"),
              'city_id'          : fields.many2one('kw.city','From'),
              'transporter_id'   : fields.many2one('res.partner','Transporter'),
              'date_function'   : fields.function(_get_new_date,type='date',string="Creation Date",store=True,multi="date"),
              'delivery_date_function'   : fields.function(_get_new_date,type='date',string="Delivery Date",store=True,multi="date"),    
              'user_log'        : fields.function(_get_user,type='char',method=True,string="Permission", store=False),
              'paying_agent_id'     : fields.many2one('res.partner','Paying Agent'),
#                                                       states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'paying_agent'    : fields.function(_get_paying_agent,type='char',method=True,string="paying_agent", store=True),        
#               'customer_list'   : fields.function(_get_customer, type='text', string='Customers List' ,store=True),
            'product'         : fields.function(_get_move_lines,type="char", size=30, string="Product",store=True, multi="move_lines"),
            'qty'             : fields.function(_get_move_lines,type="float", digits=(0,3),string="Quantity in Mts",store=True, multi="move_lines"),
            'del_quantity'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string="Delivered Quantity",store=True, multi="move_lines"),
            'transporter'     : fields.function(_get_move_lines,type="char", size=30,string="Transporter",store=True,multi="move_lines"),
            'price_unit'      : fields.function(_get_move_lines,type="float",string="Unit Price",store=True,multi="move_lines"),

            'product_id'       : fields.many2one('product.product', 'Products'),
            'freight_balance' :fields.float('Freight Balance',digits=(0,2)),
             'state_id'        : fields.many2one('res.country.state','State'),
            
             #FOR VIEW PURPOSE
               
               'year': fields.char('Year', size=6, readonly=True),
              'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                                            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
                                            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
              'day': fields.char('Day', size=128, readonly=True),
        
            #for reporting purpose
              'invoice_line_id'    : fields.many2one('account.invoice.line', 'invoice line'),
              'finvoice_line_id'    : fields.many2one('account.invoice.line', 'Freight invoice line'),
               'purchase_id': fields.many2one('purchase.order', 'Purchase Order',
                                             ondelete='set null', select=True),
              'location_id'     : fields.function(_get_move_lines,type="integer",string="location_id",store=True,multi="move_lines"),
              'users'           : fields.function(_get_move_lines,type="char", string="User",store=True, multi="move_lines"), 
              'freight'         : fields.function(_get_move_lines,type="boolean",string="freight",store=True,multi="move_lines"),
              
            #invoice Purpose
#              'cust_invoice'    :   fields.boolean('Customer Invoice'),
#               'sup_invoice'    :   fields.boolean('Facilitator Invoice'), 
#             
             'cust_invoice'    :   fields.function(_get_inv_status, multi = "all",type="boolean",string ='Customer Invoice'),
              'sup_invoice'    :   fields.function(_get_inv_status, multi = "all",type="boolean",string ='Facilitator Invoice'),
              
            #for search view
              'date_from':fields.function(lambda *a,**k:{}, method=True, type='date',string="From"),
              'date_to':fields.function(lambda *a,**k:{}, method=True, type='date',string="To"),
            
              #esugam, for specific users
              'gen_esugam'   : fields.boolean("Generate E-sugam"),
              'show_esugam'  : fields.related('partner_id','show_esugam',type='boolean',store=False)
              
              }
    _order = 'date desc'
    _defaults={
               
                'paying_agent_id':_get_default_paying_agent_id,
               'hide_fields' : _get_default_permission,
               'esugam_no'    :'0',
#                'purchase_id': False,
#                'hide_fields' : True
#                 'date_function': _get_default_new_date,
                 'user_log'     :_get_default_user,
                'paying_agent' :_get_default_paying_agent,
                'state_id'     : _get_default_state,
                'freight': False,
                'cust_invoice' : False, 
                'sup_invoice':False
               }
    

    def onchange_partner_in(self, cr, uid, ids, partner_id=None, context=None):
#         res=super(stock_picking,self).onchange_partner_in(cr, uid, ids,partner_id=False,context=None)
        res={}
        partner_obj=self.pool.get('res.partner')
        partner_ids=partner_obj.search(cr,uid,[('id','=',partner_id)])
        for i in partner_obj.browse(cr,uid,partner_ids):
            if i.work_order:
                res['work_order']=i.work_order
            else:
                res['work_order']=False
        return {'value':res}
    
    def draft_force_assign(self, cr, uid, ids, *args):
        """ Confirms picking directly from draft state.
        @OVERRIDING STANDARD METHOD
        """
        res={}
        for case in self.browse(cr,uid,ids):
            for temp in case.move_lines:
                lines_len=len(case.move_lines)
                if lines_len>1:
                    raise osv.except_osv(_('Warning'),_('You cannot process picking more than one stock moves.'))
                  
        res=super(stock_picking,self).draft_force_assign(cr, uid,ids, *args)
        return res
stock_picking()



class stock_move(osv.osv):
    _inherit='stock.move'
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        
        user = self.pool.get('res.users').browse(cr,uid,uid)
        
        if context is None:context = {}
        res = super(stock_move, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # For Supplier Groups: Filtering related Customers in OUT
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if context.get('picking_type', '') == 'out' and view_type =='tree':
            cr.execute("select true from res_groups_users_rel gu \
                        inner join res_groups g on g.id = gu.gid \
                        where g.name = 'KW_Supplier' and uid ="+str(uid))
            is_supp = cr.fetchone()
            
            if is_supp and is_supp[0] == True:
                prod_ids = [] 
                cr.execute("select product_id from product_supplierinfo where name = " + str(user.partner_id.id))         
                prods = cr.fetchall()
                
                for s in prods:
                    prod_ids.append(s[0]) 
                
                for field in res['fields']:
                    if field == 'product_id':
                        res['fields'][field]['domain'] = [('id','in', prod_ids)]
                
                
        return res
    

    def _get_permission(self, cr, uid, ids, args, field_name, context = None):
        res ={}
        g_ids = []
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        for case in self.browse(cr, uid, ids):
            res[case.id] = True
            cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
            gid = cr.dictfetchall()
            for x in gid:
                g_ids.append(x['gid'])
            for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
                if g.name == 'KW_Supplier':
                    res[case.id] = False
                if g.name == 'KW_Depot':
                    res[case.id] = False
                if g.name == 'KW_Customer':
                    res[case.id] = True
                    
                    cr.execute("select partner_id from res_users where id="+str(uid))
                    partner_id=cr.fetchone()[0]
                    cr.execute("select product_change from res_partner where id="+str(partner_id))
                    partner=cr.fetchone()[0]
                    if not partner:
                        partner=False
                    cr.execute("UPDATE stock_move SET product_change =%s where id=%s", (partner,case.id))
                    cr.execute("UPDATE stock_move SET location_dest_id =%s where id=%s", (case.location_dest_id.id,case.id))
                if g.name == 'KW_Admin': 
                    res[case.id] = False
                    if case.id != 'in_transit':
                        picking_id=case.picking_id.id
    
                        cr.execute("select partner_id from stock_picking where id="+str(picking_id))
                        partner_id=cr.fetchone()[0]
                        
                        cr.execute("select product_change from res_partner where id="+str(partner_id))
                        partner=cr.fetchone()[0]
                        if not partner:
                            partner=False
                        cr.execute("UPDATE stock_move SET product_change =%s where id=%s", (partner,case.id))  
                        if case.state=='done':
                            res[case.id] = False

                        
                            cr.execute("select product_change from res_partner where id="+str(partner_id))
                            partner=cr.fetchone()[0]
                        paying_agent=[]
                        
                        
                        cr.execute("select paying_agent_id from stock_picking where id="+str(picking_id))
                        paying_agent_id=cr.fetchone()[0]
                        cr.execute("select transporter_id from stock_picking where id="+str(picking_id))
                        transporter_id=cr.fetchone()[0]
                        
                        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                        paying_agent=cr.fetchall()
                        paying_agent=zip(*paying_agent)[0]
                        if paying_agent_id in paying_agent:                                                   
                            cr.execute("select id from res_partner where lower(name) like 'others'")
                            transport=cr.fetchall()
                            transport=zip(*transport)[0]
                            if transport:
                                if transporter_id in transport:
                                    cr.execute('UPDATE stock_picking SET paying_agent = %s WHERE id=%s',("representative",picking_id,))
                                else:
                                    cr.execute('UPDATE stock_picking SET paying_agent = %s WHERE id=%s',("kingswood",picking_id,))
                        else:
                            cr.execute('UPDATE stock_picking SET paying_agent = %s WHERE id=%s',("not",picking_id,))
                        res[case.id] = True
#                     case.product_change=partner
        return res
    
    def _get_default_permission(self, cr, uid, context=None):
        res = True
        g_ids = []
        cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
        gid = cr.dictfetchall()
        for x in gid:
            g_ids.append(x['gid'])
        for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
            if g.name == 'KW_Supplier':
                res = False
            if g.name == 'KW_Depot':
                res = False
            if g.name == 'KW_Customer':
                res = True
        return res
    
    def _get_location(self, cr, uid, ids, args, field_name, context = None):
        res ={}
        for case in self.browse(cr, uid, ids):
            res[case.id]=case.location_id.complete_name
        
        
           
        return res
   
    def _get_default_location(self, cr, uid, context=None):
        res =""
        cr.execute("select complete_name from stock_location where lower(name) like 'supplier%' order by id limit 1")
        paying_agent=cr.fetchone()   
        
        res=paying_agent
        return res
    
    def _default_location_source(self, cr, uid, context=None):
        
        log_user={}
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        if context.get('picking_type', '') == 'out':
            res = True
    #         context.update({'address_in_id': False})
            mod_obj = self.pool.get('ir.model.data')
            picking_type = context.get('picking_type')
            m=context.get('move_line', [])
            pid=context.get('default_partner_id')
            paying_agent_id=context.get('paying_agent_id')
            
            #context.update({'address_in_id': False})
            location=0
    #         context.update({'address_out_id': False})
            location_id = False
            g_ids = []
            if context is None:
                context = {}
            cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
            gid = cr.dictfetchall()
            for x in gid:
                g_ids.append(x['gid'])
            for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
                if g.name == 'KW_Supplier':
                    context.update({'address_in_id': paying_agent_id})
    #             else:     
    #             if g.name== 'KW_Admin':
    #                   context.update({'default_partner_id':pid,'address_out_id': pid,'picking_type': 'out'})
    
                if g.name == 'KW_Depot':
                    log_user= 'KW_Depot'
                    context.update({'address_in_id': pid})
                
                elif g.name!='KW_Supplier':
                    cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                    paying_agent=cr.fetchall()
                    paying_agent=zip(*paying_agent)[0]
                    if paying_agent_id not in paying_agent:
                        context.update({'address_in_id': pid})
                        
                if log_user=='KW_Depot' and user.role=='depot':
                    context.update({'address_in_id': ''})
                    cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                    paying_agent=cr.fetchall()
                    paying_agent=zip(*paying_agent)[0]
                    if paying_agent_id in paying_agent:
                           
                            #paying_agent_obj = self.browse(cr,uid,[paying_agent_id])[0]
                           
                            prod_obj = self.pool.get('stock.picking').browse(cr,uid,[paying_agent_id])[0]
                            prod_obj.paying_agent='kingswood'
                            location=1
                            location_id=user.location_id.id 
                        
                if g.name!='KW_Admin':
                    cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                    paying_agent=cr.fetchall()
                    paying_agent=zip(*paying_agent)[0]
                    context.update({'address_in_id': pid})
                    if paying_agent_id in paying_agent:
                        context.update({'address_out_id': pid})           
                        context.update({'address_in_id': ''})
                    else:
                        context.update({'address_out_id':''})   
                        

                    
                       
                            
            
                """ Gets default address of partner for source location
                    @return: Address id or False
                    """
            if location==0:
                
                if context.get('move_line', []) is False:
                    try:
                        location_id = context['move_line'][0][2]['location_id']
                    except:
                        pass
                elif context.get('address_in_id', False):
                    context.update({'address_in_id':paying_agent_id})
                    part_obj_add = self.pool.get('res.partner').browse(cr, uid, context['address_in_id'], context=context)
                    if part_obj_add:
                         location_id = part_obj_add.property_stock_supplier.id
                else:
                    location_xml_id = False
                    if picking_type == 'internal':
                        location_xml_id = 'stock_location_suppliers'
                    elif picking_type in ('out', 'internal'):
                        location_xml_id = 'stock_location_stock'
                    if location_xml_id:
                        try:
                            location_model, location_id = mod_obj.get_object_reference(cr, uid, 'stock', location_xml_id)
                            self.pool.get('stock.location').check_access_rule(cr, uid, [location_id], 'read', context=context)
                        except (orm.except_orm, ValueError):
                            location_id = False
        else:
                location_id=super(stock_move,self)._default_location_source(cr, uid, context=context)
        
        return location_id 
    
    def _default_location_destination(self, cr, uid, context=None):
        """ Gets default address of partner for destination location
        @return: Address id or False
        """
        location_dest_id=super(stock_move,self)._default_location_destination(cr, uid, context=context)
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        if context.get('picking_type', '') == 'internal':
            mod_obj = self.pool.get('ir.model.data')
            g_ids = []
            if context is None:
                context = {}
            cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
            gid = cr.dictfetchall()
            for x in gid:
                g_ids.append(x['gid'])
            for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
                if g.name=='KW_Depot' and user.role=='depot':
                    if user.location_id.id:
                        location_dest_id=user.location_id.id
                    else:
                        raise osv.except_osv(_('Warning'),_('Check Location for the logged in User "%s" ')% (user.log))
        return location_dest_id
 
    
    _columns={
              'unloaded_qty'    :   fields.float('Delivered Quantity (MT)',digits=(0,3)),
              'rejected_qty'    :   fields.float('Rejected Quantity (MT)',digits=(0,3)),
              #'supplier_id'     : fields.function(_get_supplier, type='many2one', relation='res.users', string='Suppliers'),
               'supplier_id'    :   fields.many2one('res.users','Suppliers'),
               #'partner_id'     : fields.related('picking_id', 'partner_id',type='many2one',relation='res.users',store=True ),
              'hide_fields'     : fields.function(_get_permission,type='boolean',method=True,string="Permission"),
              'state'           : fields.selection([('draft', 'New'),
                                   ('cancel', 'Cancelled'),
                                   ('waiting', 'Waiting Another Move'),
                                   ('confirmed', 'Waiting Availability'),
                                   ('assigned', 'Available'),
                                   ('done', 'Done'),
                                   ], 'Status', readonly=True, select=True,
                                     help= "* New: When the stock move is created and not yet confirmed.\n"\
                                           "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"\
                                           "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to me manufactured...\n"\
                                           "* Available: When products are reserved, it is set to \'Available\'.\n"\
                                           "* Done: When the shipment is processed, the state is \'Done\'."),
              'deduction_amt'   : fields.float('Deduction Amount',digits=(0,2)),
              'location'        : fields.function(_get_location,type='char',method=True,string="Source Location"),
              'delivery_date'   : fields.date('Delivery Date',required=True),
              'product_change'  : fields.boolean("Allow Product Change"), 
              

              }
    _defaults={
                'location_id': _default_location_source,
                'location_dest_id': _default_location_destination,
                'hide_fields' : _get_default_permission,
                'partner_id': False,
                'supplier_id': lambda self,cr,uid,c: uid,
                'state'      :   'draft',
                'deduction_amt'    : 0,
                'location': _get_default_location,
                'delivery_date': lambda *a: time.strftime('%Y-%m-%d'),
#                 'location_dest_id': _default_location_destination,
              }
    
    
    
    
    
    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
                            loc_dest_id=False, partner_id=False):
        """ On change of product id, if finds UoM, UoS, quantity and UoS quantity.
        @param prod_id: Changed Product id
        @param loc_id: Source location id
        @param loc_dest_id: Destination location id
        @param partner_id: Address id of partner
        @return: Dictionary of values
        """
        res={}
        price=0.0
        proforma_price=0.0
        res=super(stock_move,self).onchange_product_id(cr, uid, ids, prod_id=prod_id, loc_id=loc_id,loc_dest_id=False, partner_id=False)
        if partner_id:
            if prod_id:
                product = self.pool.get('product.product').browse(cr, uid, [prod_id], context={})[0]
                price=product.list_price
                
                for i in product.customer_ids:
                    if i.name.id==partner_id:
                        
                        res['value']['price_unit']=i.proforma_price
                        proforma_price=i.proforma_price
                if proforma_price==0:
                    res['value']['price_unit']=product.list_price
                if price==0.0 and proforma_price==0:    
                       raise osv.except_osv(_('Warning'),_('Check Goods Price, Selected Customer Do Not Have Rate In The Goods Master'))  
#         else:
#                        
#             raise osv.except_osv(_('Warning'),_('Select The Customer'))
#         
        
       
        return res

            
     
            
            
        
    def default_get(self, cr, uid, fields, context=None):
        loc_obj = self.pool.get('stock.location')
        user_id = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        res = super(stock_move, self).default_get(cr, uid, fields, context=context)
        if 'default_partner_id' in context:
            res.update({'partner_id':context['default_partner_id']})

        return res
  
    def create(self,cr,uid,vals,context=None):
        

        return super(stock_move,self).create(cr, uid, vals, context)
    
    def write(self, cr, uid, ids, vals, context=None):
        for case in self.browse(cr,uid,ids):
            

            n= case.rejected_qty
            rejected_qty = vals.get('rejected_qty',case.rejected_qty)
            unloaded_qty = vals.get('unloaded_qty',case.unloaded_qty)
            product_qty = vals.get('product_qty',case.product_qty)
            res=unloaded_qty+rejected_qty
#             if res>product_qty:
#                 raise osv.except_osv(_('Warning'),_('Check  Quantity'))
            
           
        return super(stock_move, self).write(cr, uid, ids, vals, context=context)    
     
stock_move()


class stock_picking_in(osv.osv):
    _inherit='stock.picking.in'
    
    def _get_new_date(self, cr, uid, ids, args, field_name, context = None):
        res={}
        for case in self.browse(cr,uid,ids):
            res[case.id]=case.date
            
        return res
    
    
    def _get_move_lines(self, cr, uid, ids, args, field_name, context = None):
        res = {}
        u_id=context.get('uid')
        qty_id=[]
        quantity_list=[]
        users=[]
        if u_id:
            uid=u_id
        cr.execute("select login from res_users where id  ="+str(uid))
        user=cr.fetchone()[0]
        
         
        for case in self.browse(cr, uid, ids):
            for temp in case.move_lines:
            
                res[case.id] = {'product': " ", 'qty':0.00,'location_id':0,'users':''}
                res[case.id]['product']  = temp.product_id.name
                res[case.id]['qty']  = temp.product_qty  
                res[case.id]['location_id']=temp.location_dest_id.id
                cr.execute("select create_uid from stock_picking where id="+str(case.id))
                create_uid=cr.fetchone()[0]
                cr.execute("select login from res_users where id  ="+str(create_uid))
                user=cr.fetchone()[0]
                res[case.id]['users']=user
                d=case.id
                
                
            if case.date_function!=case.date:
                        cr.execute("UPDATE stock_picking SET date_function =%s where id=%s", (case.date,d))
            if case.year=='':
                cr.execute("select to_char(s.date, 'YYYY') as year,to_char(s.date, 'MM') as month,to_char(s.date, 'YYYY-MM-DD') as day from stock_picking s where id =%s",(d,))
                date=cr.fetchall()[0]
                if date:
  
                    cr.execute("UPDATE stock_picking SET year =%s where id=%s", (date[0],d))
                    cr.execute("UPDATE stock_picking SET month =%s where id=%s", (date[1],d))
                    cr.execute("UPDATE stock_picking SET day =%s where id=%s", (date[2],d))
                cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (case.state_id.id,d))  
                cr.execute("select product_id from stock_move where picking_id=%s",(d,))
                product_id=date=cr.fetchone()[0]
                cr.execute("UPDATE stock_picking SET product_id =%s where id=%s", (product_id,d))
#                 self._get_user_qty(cr, uid, ids, context)
        return res
    
    
    
    def _get_inv_status(self, cr, uid, ids, field_name, args, context = None):
        res = {}
        for case in self.browse(cr, uid, ids):
            cr.execute("SELECT invoice_id FROM incoming_shipment_invoice_rel where in_shipment_id = "+str(case.id))
            Iinv_ids = cr.fetchall()
            if Iinv_ids:
                res[case.id]['sup_invoice'] = True
        return res

    
    
    
    def get_location(self, cr, uid, context=None):
        user_id = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        res = False
        if user_id.role == 'depot':
            res = user_id.location_id.id
        return res
        
    
    _columns={
              'product'         : fields.function(_get_move_lines,type="char", size=30, string="Product",store=True, multi="move_lines"),
              'qty'             : fields.function(_get_move_lines,type="float", string="Quantity",store=True, multi="move_lines"),

              'location_id'     : fields.function(_get_move_lines,type="many2one",relation = 'stock.location',string="Location",store=True,multi="move_lines"),
           
              'product_id'      : fields.many2one('product.product', 'Products'),
              'truck_no'        : fields.char('Vehicle Number',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'purchase_id'     : fields.many2one('purchase.order', 'Purchase Order',
                                             ondelete='set null', select=True),
               'users'           : fields.function(_get_move_lines,type="char", string="User",store=True, multi="move_lines"),
                'state_id'        : fields.many2one('res.country.state','State'),
                'date_function'   : fields.function(_get_new_date,type='date',string="Creation Date",store=True),
               
               #FOR VIEW PURPOSE
               
               'year': fields.char('Year', size=4, readonly=True),
              'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                                            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
                                            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
              'day': fields.char('Day', size=128, readonly=True),   
              #For Invoice Purpose
#               'sup_invoice'    :   fields.boolean('Facilitator Invoice'),
             'sup_invoice'    :   fields.function(_get_inv_status, type="boolean",string ='Facilitator Invoice'),
              
               #for search view
              'date_from':fields.function(lambda *a,**k:{}, method=True, type='date',string="From"),
              'date_to':fields.function(lambda *a,**k:{}, method=True, type='date',string="To"), 
                   
              }
    
    _order = 'date desc'
    

    _defaults={
                 'purchase_id': False,
                 'location_id': get_location,
                 'type'       : 'in',
                 'sup_invoice':False,
              }
    
    def get_invoice(self,cr,uid,ids,freight,context=None):
        journal_obj = self.pool.get('account.journal')
        
        product_groups = {}
        delivery_orders = {}
        date_groups={}
        inv_obj = self.pool.get('account.invoice')
        inv_groups = {}
        freight_group= {}
        order_line = {} 
        inv_vals={}
        sup_grp={}
        qty = 0  
        supp_group = {}
        supp_invoice_lines = {}
        supp_del_orders = {}
        product_line = {}
        supp_inv_group = {}
        price=0.00
        price1=0
        order_line = {} 
        not_draft=[]
#         inv_obj = self.pool.get('account.invoice')
#         inv_groups = {} 
        type=''
        tax_vals={}
        vals={}
        handling_vals={}
        handling_vals['quantity']=0.00
        handling_vals['price_unit']=0.00
        handling_invoices_lines={}
        handling_invoices ={}
        handling_group={}
        handling_del_orders={}
        sup_inv_vals = {}
        line_groups = {}
        line_vals = {}
        partner=False
        qty=0.000
        partner_name=''
        s_id={}
        s_parent_id=False
        frt=0
#         journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase')])[0]
        prod_obj=self.pool.get('kw.product.price')
        kw_prod_obj = self.pool.get('product.product')
        sup_freight_ids=kw_prod_obj.search(cr, uid, [('name_template','=','Freight')])
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        
        company=cr.fetchone()
        if company:
            company=company[0]
        log_user={}
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        g_ids = []
        if user.role!='admin':
                raise osv.except_osv(_('Warning'),_('You Cannot Create Invoice For The Incoming Shipments'))
            
        cr.execute("SELECT in_shipment_id FROM incoming_shipment_invoice_rel WHERE in_shipment_id IN %s ",(tuple(ids),))
        order_id = cr.fetchall()
        
        if order_id:
            raise osv.except_osv(_('Warning'),_('Invoice Already Created for the Selected Delivery Order'))
        for case in self.browse(cr, uid, ids):
            journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase'),('company_id','=',case.company_id.id)])[0]
#             handling_journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase'),('company_id','=',company)])[0]
            type=case.type
            if case.state in ('done') and type=='in':
                a=""
                loaded_qty = 0
                rejected_qty = 0
                loc=0
                for ln in case.move_lines:
                    vals['product_id'] = ln.product_id.id
                    vals['name'] = ln.name
                    vals['quantity'] = ln.product_qty
                    #vals['rejected_qty'] = ln.rejected_qty
                    vals['uos_id'] = ln.product_uom.id    
                    vals['price_unit'] = 0
                    
                    
                    
                    #for supplier handling invoice vals
                    for ft in kw_prod_obj.browse(cr,uid,sup_freight_ids):
                        cr.execute("select substr(value_reference,17)::integer from ir_property where name =  'property_account_expense_categ' and res_id = 'product.category,' || %s", (ft.categ_id.id,))
                        ft_account_expense = cr.fetchall()
                        frt=ft.id
                        f_name=ft.name
                    handling_vals['product_id']=frt
                    handling_vals['name'] = f_name
                    if handling_vals['quantity'] ==0:
                        handling_vals['quantity'] = ln.product_qty
                    handling_vals['uos_id'] = ln.product_uom.id    
                    handling_vals['move_line_id'] = ln.id
                    
                    
                    
                    
                    cr.execute("select substr(value_reference,17)::integer from ir_property where name =  'property_account_expense_categ' and res_id = 'product.category,' || %s", (ln.product_id.categ_id.id, ))
                    account_expense = cr.fetchall()
                    if account_expense:
                        vals['account_id'] = account_expense[0]
                        handling_vals['account_id'] = account_expense[0]
                    for i in ln.product_id.seller_ids:
                         if case.partner_id.id == i.name.id:
                             if ln.location_dest_id.id == i.depot.id:
                                
                                loc=1;
                                prod_ids=prod_obj.search(cr, uid, [('ef_date','<=',case.date),('supp_info_id','=',i.id)],limit=1, order='ef_date desc')
                                for j in prod_obj.browse(cr,uid,prod_ids):
                                    price1 = j.sub_total
                                    
                                    vals['price_unit']  = price1
                                    freight_price = j.transport_price
                                    partner = j.partner_id
                                    partner_name = j.partner_id.name
                                    handling_vals['price_unit'] = j.handling_charge or 0
                                    qty = ln.product_qty
                                    if partner:
                                        s_parent_id = j.partner_id.property_account_payable and j.partner_id.property_account_payable.id or False
                                        s_id.update({partner.id:s_parent_id})
                                    
                    if handling_vals['price_unit'] >0 and partner:
                        #added Handling price to handling key[If Handling price differs then create new invoice]                          
                             handling_key=ln.product_id.id,partner,case.partner_id.id,handling_vals['price_unit']
                         
                         
                     #grouping the supplier Handling invoices based on product_id and partner
                          
                         
                    handling_ft=False
                    if partner and handling_vals['price_unit'] >0:
                         if handling_key not in handling_group :
                             handling_vals['quantity'] = ln.product_qty
                             handling_del_orders[handling_key]=[case.id]
                             
                             a_id=s_id[partner.id]

                             handling_group[handling_key]={
                                                                'partner_id'      : partner.id,
                                                                'date_invoice'   :  case.date_function,
                                                                'type'           : 'in_invoice',
                                                                 'journal_id'    : journal_id,
                                                                
                                                                  'freight'      : False,
                                                                  'origin'       :  'IN',
                                                            }
                             
                             
                             handling_invoices_lines[handling_key] = [(handling_vals.copy())]
                         else:
                             
                              handling_invoices_lines[handling_key][0]['quantity'] += ln.product_qty
                              handling_del_orders[handling_key].append(case.id)                        
                    
                          
                    if loc==0:
                        raise osv.except_osv(_('Warning'),_('Check Loccation, %s  for the Selected Supplier "%s" Not Found in Goods Master for "%s"')% 
                                         (ln.location_dest_id.complete_name,case.partner_id.name,ln.product_id.name ))   
                    if price1==0:
                        raise osv.except_osv(_('Warning'),_('Check Goods Price, Selected Supplier "%s" Do Not Have Rate for "%s" In The Goods Master')% (case.partner_id.name,ln.product_id.name ))
#                     else:
#                         cr.execute("update stock_picking set sup_invoice=True where id=%s ",(case.id,))


#                     #check for the key
                    supp_key = case.partner_id.id,case.date_function
                    product_key =case.partner_id.id,ln.product_id.id,ln.price_unit
                    if supp_key not in supp_inv_group:
                        supp_del_orders[supp_key] =[case.id]
                        supp_inv_group[supp_key] = {'partner_id'   : case.partner_id.id,
                                                     'origin'   :   'IN',
                                                     'date_invoice': case.date_function,
                                                     'type':   'in_invoice',
                                                     'freight'      : False,
                                                     'journal_id' : journal_id,
                                             }
                        supp_invoice_lines[supp_key] = [(vals.copy())]
                        
                    
                    else:
                        supp_invoice_lines[supp_key].append((vals.copy()))
                        supp_del_orders[supp_key].append(case.id)
                    
            else:
                
                not_draft.append(case.name)

                raise osv.except_osv(_('Warning'),_('Imcoming Shipment "%s" Should Be In Received State')% (case.name,))  
                
        
        
        #for grouping the product id price and product_id

        supp_data = {}
        freight_data = {}
        for keys in supp_invoice_lines:
            line_groups = []
            for k in supp_invoice_lines[keys]:
                product_key = k['product_id'],k['price_unit']
                if product_key not in line_groups:
                    if not keys in supp_data:
                        supp_data[keys] = {product_key:[(0,0,k)]}
                    else:
                        supp_data[keys].update({product_key:[(0,0,k)]})
                    line_groups.append(product_key)
                    
                else:
                    supp_data[keys][product_key][0][2]['quantity'] += k['quantity']
            
        #for separating the product_keys from vals
        for x in supp_data:
            for i in supp_data[x].values():
                if x in line_vals:
                    line_vals[x].append(i[0])
                else:
                    line_vals[x]= i
                
        
        
        
                     
        #creating invoice
        for inv in line_vals:
            sup_inv_vals.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_invoice', supp_inv_group[inv]['partner_id'])['value'])
            sup_inv_vals.update(supp_inv_group[inv])
            sup_inv_vals.update({
                                            
                                'invoice_line': line_vals[inv],
                                'incoming_shipment_ids': [(6, 0, supp_del_orders[inv])],
                            }) 
            
#             if ln.location_id.name == "Suppliers":
            context.update({'type':'in_invoice'})
            inv_obj.create(cr, uid, sup_inv_vals,context=context) 
         
         
        #Handing Charges invoice
        for handling_inv in handling_invoices_lines:
            handling_invoices.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_invoice', handling_group[handling_inv]['partner_id'])['value'])
            handling_invoices.update(handling_group[handling_inv])
            handling_invoices.update({
                                                                
                                        'incoming_shipment_ids': [(6, 0, handling_del_orders[handling_inv])],
                                        'invoice_line': [(0,0,handling_invoices_lines[handling_inv][0])],
                                                                                                                                    
                                     }) 
              
         
            if s_parent_id:
                   
                 context.update({'type':'in_invoice'})
                 #to create freight invoice for supplier
                 inv_obj.create(cr, uid, handling_invoices)    
        return True
    

    
#     # TODO: commented for testing 
    def create(self,cr,uid,vals,context=None):
        move_lines=[]
        today = time.strftime('%Y-%m-%d') 
        user = self.pool.get('res.users').browse(cr, uid, [uid])[0]
         
        # for creating the sequence code
         
                 
        cr.execute("select code from account_fiscalyear where date_start < '"+today+"' and date_stop >'" +today+"'")
        seq_code = cr.fetchone()
        if seq_code:
            code = seq_code[0]
        format = 'IN/' + code + '/' + user.state_id.code + '/'
        cr.execute("select name from stock_picking where name like '"+format+"'|| '%' order by to_number(substr(name,(length('"+format+"')+1)),'99999') desc limit 1")
        prev_format = cr.fetchone()
        if not prev_format:
            name = format + '00001'
        else:
            auto_gen = prev_format[0][-5:]
            name = format + str(int(auto_gen) + 1).zfill(5)
        vals.update({'name':name})
        move_lines=vals.get('move_lines')
        if move_lines==[]:
            raise osv.except_osv(_('Warning'),_('Add one product')) 

        if 'move_lines' in vals:
            for ml in vals['move_lines']:
                    vals['product_id']=ml[2]['product_id']        
        return super(stock_picking_in,self).create(cr, uid, vals, context)
    
    def get_day_date(self,cr,uid,ids,context=None):
        day_id=[]
        for case in self.browse(cr, uid, ids):
            cr.execute("select id from stock_picking where delivery_date_function is null")
            day_ids=cr.fetchall()
            g=0
            for g in day_ids:
                day_id.append(g[0])
            
            
   
                
            for p in day_id:
                cr.execute("select to_char(s.date, 'YYYY') as year,to_char(s.date, 'MM') as month,to_char(s.date, 'YYYY-MM-DD') as day from stock_picking s where id =%s",(p,))
                date=cr.fetchall()[0]
                cr.execute("select to_char(sm.delivery_date, 'YYYY-MM-DD') from stock_move sm where sm.picking_id =%s",(p,))
                date1=cr.fetchall()
                
                if date:
                    cr.execute("UPDATE stock_picking SET year =%s where id=%s", (date[0],p))
                    cr.execute("UPDATE stock_picking SET month =%s where id=%s", (date[1],p))
                    cr.execute("UPDATE stock_picking SET day =%s where id=%s", (date[2],p))
                    cr.execute("UPDATE stock_picking SET date_function =%s where id=%s", (date[2],p))
                if date1:
                    cr.execute("UPDATE stock_picking SET delivery_date_function =%s where id=%s", (date1[0],p))
                    
            

                
        return True
    
    
    
        
    def get_user_qty(self, cr, uid, ids,context = None):
        self.get_day_date(cr,uid,ids)
        cr.execute("select id from stock_picking where type='in'and qty is null or users is null")
        qty_ids=cr.fetchall()
        if qty_ids:
            for i in qty_ids:
                n=int(i[0])
                cr.execute("select product_qty from stock_move where picking_id=%s",(n,))
                qty=cr.fetchone()
                cr.execute("update stock_picking set qty=%s where id=%s",(qty,n))
                
                cr.execute("select create_uid from stock_picking where id="+str(n))
                create_uid=cr.fetchone()
                cr.execute("select login from res_users where id  ="+str(create_uid[0]))
                user=cr.fetchone()
                cr.execute("update stock_picking set users=%s where id=%s",(user,n))

        return True
    
    
    def draft_force_assign(self, cr, uid, ids, *args):
        """ Confirms picking directly from draft state.
        OVERRIDING STANDARD METHOD
        """
        for case in self.browse(cr,uid,ids):
            for temp in case.move_lines:
                lines_len=len(case.move_lines)
                if lines_len>1:
                    raise osv.except_osv(_('Warning'),_('You cannot process picking more than one stock moves.'))
                   
        return super(stock_picking_in,self).draft_force_assign(cr, uid,ids,*args)
       
    
    def unlink(self, cr, uid, ids, context=None):
        for case in self.pool.get('stock.picking').browse(cr, uid, ids):
            
            if case.state != 'draft':
                raise osv.except_osv(_('Warning!'), _("You Cannot Delete the record, You Can only Delete Draft Record "))
        return super(stock_picking_in, self).unlink(cr, uid, ids, context = context)

stock_picking_in()




