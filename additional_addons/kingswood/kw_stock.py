# -*- coding: utf-8 -*-
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
#from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO
import requests
import amount_to_text_softapps
# from pyPdf import PdfFileWriter, PdfFileReader
from datetime import datetime
import zipfile
import logging
# import os
import signal
import sys
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
from openerp import netsvc
import sys
import ssl
import random
from openerp.report import report_sxw
from openerp import pooler

import pytz
_logger = logging.getLogger(__name__)

from PIL import Image
import pytesseract
import urllib
import re
import tempfile
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
import json
from selenium.webdriver.chrome.options import Options
# from seleniumrequests import Chrome
import codecs
# import pywinauto
# import img2pdf


# For Setting Chrome Web Drive Options selenium
#             chrome_options = Options()
#             if HEADLESS:
#                 chrome_options.add_argument("--headless")
#                 chrome_options.add_argument('--no-sandbox')
#                 chrome_options.add_argument('--disable-gpu')
#                 chrome_options.add_argument('--disable-popup-blocking')
#                 chrome_options.add_argument('--window-size=1440,900')
#             else:
#                 chrome_options.add_argument("--kiosk")
#             prefs = {
#                 'download.default_directory': DOWNLOAD_PATH,
#                 'download.prompt_for_download': False,
#                 'download.directory_upgrade': True,
#                 'safebrowsing.enabled': False,
#                 'safebrowsing.disable_download_protection': True}
#             chrome_options.add_experimental_option('prefs', prefs)
#             driver = webdriver.Chrome(
#                 chrome_options=chrome_options, executable_path=DRIVER_PATH)
#             if HEADLESS:
#                 driver.set_window_size(1440, 900)
#                 enable_download_in_headless_chrome(driver, DOWNLOAD_PATH)

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
        doc = etree.XML(res['arch'])
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
                        
                if view_type == 'form':
                    if context.get('type', 'out') in ('out'):
                        for node in doc.xpath("//field[@name='partner_id']"):
                            node.set('options', '{"no_open":True}')
              
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
        dealers_obj=self.pool.get('goods.dealers')
        res = {}
        truck=False
        
        for case in self.browse(cr, uid, ids):
            date=case.date_function
            truck=dealers_obj.search(cr,uid,[('name','=',case.truck_id.id),('date','<=',date)])
            truck_id=dealers_obj.browse(cr,uid,truck)
#             for tr in dealers_obj.browse(cr,uid,truck):
#                 print 'truck',tr.name.name
            if truck_id:
                truck_id=truck_id[0]
                print 'truck',truck_id.name.name
            if case.type=='out':
                res[case.id] = {'freight_deduction': 0.00, 'freight_total':0.00}
                total = 0.00
                deduction = 0.00
                tol_qty = 0.00
                tol_rate = 0
#                 freight_charge=0
                for ln in case.move_lines:
#                     for temp in ln.product_id.customer_ids:
#                         if temp.name.id==case.partner_id.id:
#                             
#                             case.freight_charge=temp.transport_rate
#                             cr.execute('UPDATE stock_picking SET freight_charge = %s WHERE id=%s',(temp.transport_rate,case.id,))
                    if case.freight_charge > 0:
                        total += (case.freight_charge * ln.unloaded_qty)
                        
                        for partner in case.partner_id.dealers_ids:
                            if case.truck_id.id==partner.name.id and partner.date <= date:
                                if tol_qty==0 and tol_rate==0:
                                    tol_qty=partner.tol_qty
                                    tol_rate=partner.tol_rate
                                
                                
                        # Picking Qty > Product Qty
                        if case.truck_id and ln.unloaded_qty> 0.00:
                              if ln.unloaded_qty < ln.product_qty and (ln.product_qty  - ln.unloaded_qty) > (tol_qty/1000):
                                  deduction += ((ln.product_qty - (tol_qty/1000)) - ln.unloaded_qty) *1000 * tol_rate
#                             if ((ln.product_qty - ln.unloaded_qty) * 1000) > (ln.product_qty * truck_id.tol_qty) :
#                                 deduction += (((ln.product_qty - ln.unloaded_qty)*1000) - (ln.product_qty * tol_qty)) * tol_rate
                                       
                        
                res[case.id]['freight_deduction'] = deduction
                res[case.id]['freight_total'] = total
#                 self.get_freight_balance(cr, uid, ids, context)
#                 if case.freight_charge > 0:
#                     res[case.id]['freight_balance'] = total - deduction - case.freight_advance
        return res
    
    def _get_move_lines(self, cr, uid, ids, args, field_name, context = None):
        res = {}
       
        u_id=context.get('uid')
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company=cr.fetchone()
        if company:
            company=company[0]
        if u_id:
            uid=u_id
#         cr.execute("select login from res_users where id  ="+str(uid))
#         user=cr.fetchone()[0]
        product_change = False
        for case in self.browse(cr, uid, ids):
            d=case.id
            if case.type=='out':
                for temp in case.move_lines:
                    txt=''
#                     if case.product_id.product_change:
#                        product_change= case.product_id.product_change
#                     self.write(cr, uid, [case.id],{'product_change':case.product_id.product_change},context = context)
#                         
                    
                    res[case.id] = {'location_id':False,'product': " ",'cft1':0.0,'cft2':0.0,'deduction_amt':0.0, 'amt_txt':'','qty':0.000,'transporter':" ",'rej_quantity':0.000,'price_unit':0.0,'users':'' ,'freight':False,'del_quantity':0.000}
#                     res[case.id]['product']  = temp.product_id.name
                    res[case.id]['qty']  = temp.product_qty
                    res[case.id]['product_id']= temp.product_id.id
                    res[case.id]['price_unit'] = temp.price_unit
                    res[case.id]['del_quantity'] = temp.unloaded_qty
                    res[case.id]['rej_quantity'] = temp.rejected_qty
                    res[case.id]['deduction_amt'] = temp.deduction_amt
                    res[case.id]['location_id'] = temp.location_id.id
                    if temp.location_id:
                        cr.execute("UPDATE stock_picking SET dest_location_id ="+str(temp.location_id.id)+" where id="+str(case.id))                    
#                     res[case.id]['source_location_id'] = temp.location_id.complete_name
                    res[case.id]['cft1'] = temp.cft1
                    res[case.id]['cft2'] = temp.cft2
                    case.product_id.id=temp.product_id.id
                    
                    if case.freight_balance>0:
                        txt += amount_to_text_softapps._100000000_to_text(int(round(case.freight_balance)))        
                        res[case.id]['amt_txt'] = txt
                        
                    if case.partner_id.freight or case.gen_freight:
                        cr.execute("UPDATE stock_picking SET dc_company =%s where id=%s", (company,case.id))
                    else:
                        cr.execute("UPDATE stock_picking SET dc_company =%s where id=%s", (case.company_id.id,case.id))
                    if case.paying_agent_id: 
                        cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (case.paying_agent_id.state_id.id,case.id)) 
#                     res[case.id]['location_id']=temp.location_id.id
                    cr.execute("select create_uid from stock_picking where id="+str(case.id))
                    create_uid=cr.fetchone()[0]
                    cr.execute("select login from res_users where id  ="+str(create_uid))
                    user=cr.fetchone()[0]
                    res[case.id]['users']=user
                    if case.partner_id.freight or case.gen_freight:
                        res[case.id]['freight']=True
 
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
            for temp in case.move_lines:
                cr.execute("update stock_picking set location_id ="+str(temp.location_id.id)+" where id="+str(case.id))
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
#                         cr.execute("select create_uid from stock_picking where id="+str(case.id))
#                         create_uid=cr.fetchone()[0]
#                         cr.execute("select partner_id from res_users where id  ="+str(create_uid))
#                         user=cr.fetchone()[0]
#                         cr.execute("select state_id from res_partner where id="+str(user))
#                         state_id=cr.fetchone()[0]
                         if case.paying_agent_id.state_id:
                            cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (case.paying_agent_id.state_id.id,case.id))

        return res
    
    def _get_user(self, cr, uid, ids, args, field_name, context = None):
        res ={}
        g_ids = []
        user_obj = self.pool.get('res.users')
        u_id=context.get('uid')
        if u_id:
            uid=u_id
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'partner' : '', 'user_log':''}       
            if case.partner_id:
                if uid!=1:
                    res[case.id]['partner']=case.partner_id.ref     
            if case.type=='out':
                
                cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
                gid = cr.dictfetchall()
                for x in gid:
                    g_ids.append(x['gid'])
                for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
    #                 if g.name == 'KW_Freight':
    #                     res[case.id] = False
                    if g.name == 'KW_Supplier':
                        res[case.id]['user_log'] = 'KW_Supplier'
    #                     for temp in case.move_lines:
    #                           res[case.paying_agent_id]=temp.supplier_id
                         
                    if g.name == 'KW_Customer':
                        res[case.id]['user_log'] = 'KW_Customer'
                    if g.name == 'KW_Depot':
                        res[case.id]['user_log'] = 'KW_Depot'   
                    if g.name == 'KW_Admin':
                        res[case.id]['user_log'] = 'KW_Admin'
#                         cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (case.state_id.id,d))3
                    if g.name == 'KW_Freight':
                        res[case.id]['user_log'] = 'kw_freight'
                       
                    if res[case.id]['user_log']=='KW_Depot' or res[case.id]['user_log'] == 'KW_Admin':
                        
                        user = user_obj.browse(cr, uid, [uid])[0]
                        
                        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                        paying_agent=cr.fetchall()
                        paying_agent=zip(*paying_agent)[0]
                        if res[case.id]['user_log'] !='KW_Admin':
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
                            cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (case.paying_agent_id.state_id.id,case.id))
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
            if g.name == 'KW_Freight':
                res = 'kw_freight'                   
        return res

    def _get_default_user_partner(self, cr, uid, context=None):
        res ={}
        g_ids = []
        users=self.pool.get('res.users')
        user_id=users.browse(cr, uid, uid)
        res=user_id.partner_id.id                 
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
        self.get_date_update(cr,uid,[uid])
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
    
    def get_date_update(self,cr,uid,ids,context=None):
        if uid !=1:
            cr.execute("select sp.id from stock_picking sp inner join stock_move sm on sm.picking_id=sp.id where sp.type='out' and sp.delivery_date_function<>sm.delivery_date")
            pick=[i[0] for i in cr.fetchall()]
            for i in pick:
                cr.execute("select delivery_date from stock_move where picking_id=%s",(i,))
                date=cr.fetchone()
                if date:
                    cr.execute("update stock_picking set delivery_date_function=%s where id=%s",(date[0],i,))
        return True
    
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
        cinv_ids=[]
        sinv_ids=[]
        Iinv_ids=[]
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'cust_invoice' : False, 'sup_invoice':False}
            cr.execute("""SELECT dr.invoice_id FROM delivery_invoice_rel dr inner 
                            join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id=%s and ac.type <> 'out_refund' and ac.state <>'cancel'""",(str(case.id),)) 
            cinv_ids = [x[0] for x in cr.fetchall()]
            if cinv_ids:
                res[case.id]['cust_invoice'] = True
            cr.execute("""SELECT dr.invoice_id FROM supp_delivery_invoice_rel dr inner 
            join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id=%s and ac.state <>'cancel'""",(str(case.id),))
            sinv_ids = [x[0] for x in cr.fetchall()]
            cr.execute("""SELECT dr.invoice_id FROM incoming_shipment_invoice_rel dr inner 
            join account_invoice ac on ac.id=dr.invoice_id WHERE dr.in_shipment_id=%s and ac.state <>'cancel'""",(str(case.id),))
            Iinv_ids = [x[0] for x in cr.fetchall()]
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
               
              'user_log'        : fields.function(_get_user,type='char',method=True,string="Permission", store=False,multi='user'),
              # Overriden:
#                 'partner_id': fields.many2one('res.partner', 'Partner',  domain="[('id', 'in', [int(s) for s in customer_list.split(',')])] )]", states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
                  
#                 'partner_id': fields.many2one('res.partner', 'Partner',   domain="[('id', 'in', [s for s in [13,5,6,22,970]] )]", states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
              'partner_id': fields.many2one('res.partner', 'Partner',track_visibility='onchange', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}, select=True),
              # NEw:
                'work_order'    :   fields.function(get_workorder,store=True,type="char",string='Work Order Number',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
                'truck_no'      :   fields.char('Vehicle Number',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
                'esugam_no'     :   fields.char('E-Sugam Number',size=20,states={'in_transit': [('readonly', False)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
               'distance'      :   fields.integer("Approximate Distance(KM)"),
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
              
              'freight_total'    : fields.function(_get_freight_amount, type='float', string='Freight Total', store=True, multi="tot",track_visibility='onchange'),
              'freight_deduction': fields.function(_get_freight_amount, type='float', string='Freight Deduction', store=True, multi="tot",track_visibility='onchange'),                 
#               'freight_balance'  : fields.function(_get_freight_amount, type='float', string='Freight Balance', store=True, multi="tot"),
                'freight_balance' :fields.float('Freight Balance',digits=(0,2),track_visibility='onchange'),
              'city_id'          : fields.many2one('kw.city','From', select=True),
              'transporter_id'   : fields.many2one('res.partner','Transporter'),
#               'date'             : fields.datetime('Delivery Date', help="Creation date, usually the time of the order.", select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
              'date_function'   : fields.function(_get_new_date,type='date',string="Creation Date",store=True,multi="date", track_visibility='onchange'),
              'delivery_date_function'   : fields.function(_get_new_date,type='date',string="Delivery Date",store=True,multi="date",track_visibility='onchange'),
              'paying_agent_id' : fields.many2one('res.partner','Paying Agent',track_visibility='onchange', select=True),
#               ,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'paying_agent'    : fields.function(_get_paying_agent,type='char',method=True,string="paying_agent", store=True),
               'product'         : fields.function(_get_move_lines,type="char", size=30, string="Product",store=True, multi="move_lines"),
              'qty'             : fields.function(_get_move_lines,type="float", digits=(0,3),string="Quantity in MTs",store=True, multi="move_lines"),
              'del_quantity'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string="Delivered Quantity in MTs",store=True, multi="move_lines",track_visibility='onchange'),
              'transporter'     : fields.function(_get_move_lines,type="char", size=30,string="Transporter",store=True,multi="move_lines"),
              'price_unit'      : fields.function(_get_move_lines,type="float",string="Unit Price",store=True,multi="move_lines"),
              'product_id'      : fields.many2one('product.product', 'Products',track_visibility='onchange', select=True),
              'state_id'        : fields.many2one('res.country.state','State', select=True),
              
              'truck_id'           : fields.many2one('goods.trucks','Trucks'),
              #for reporting purpose
              
              'amt_txt'         :   fields.function(_get_move_lines,type="char",string="Amount in Words",store=True,multi="move_lines"),
              'invoice_line_id'    : fields.many2one('account.invoice.line', 'invoice line'),
              'finvoice_line_id'    : fields.many2one('account.invoice.line', 'Freight invoice line'),
              'oinvoice_line_id'    : fields.many2one('account.invoice.line', 'Other Facilitator invoice line'),
              
              'purchase_id': fields.many2one('purchase.order', 'Purchase Order',
                                             ondelete='set null', select=True),
                'location_id'     : fields.function(_get_move_lines,type="integer",string="location_id",store=True,multi="move_lines", select=True),
#                 'location_id'     : fields.function(_get_move_lines,type="many2one",relation = 'stock.location',string="Location",store=True,multi="move_lines"),
           
              'users'           : fields.function(_get_move_lines,type="char", string="User",store=True, multi="move_lines", select=True),
              'freight'         : fields.function(_get_move_lines,type="boolean",string="freight",store=True,multi="move_lines"), 
              'transit_date'    : fields.datetime('Transit Date'),
              'rej_quantity'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string="Rejected Quantity",store=True, multi="move_lines",track_visibility='onchange'),
              'deduction_amt'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string="Deduction",store=True, multi="move_lines",track_visibility='onchange'),
            'cft1'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string='CFT Size1',multi="move_lines",track_visibility='onchange',
                                         store=True),
            'cft2'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string='CFT Size2',multi="move_lines",track_visibility='onchange',
                                         store=True),               
               
               
               #FOR VIEW PURPOSE
               
               'year': fields.char('Year', size=6, readonly=True),
              'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                                            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
                                            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
              'day': fields.char('Day', size=128, readonly=True),
              'dc_company' : fields.many2one('res.company','company'),
              
              # invoice PURPOSE
              
#               'cust_invoice'    :   fields.boolean('Customer Invoice'),
#               'sup_invoice'    :   fields.boolean('Facilitator Invoice'),
#               
              'cust_invoice'    :   fields.function(_get_inv_status, multi = "all",type="boolean",string ='Customer Invoice', store=True),
              'sup_invoice'    :   fields.function(_get_inv_status, multi = "all",type="boolean",string ='Facilitator Invoice', store=True),
              
              #for search view
              'date_from':fields.function(lambda *a,**k:{}, method=True, type='date',string="From"),
              'date_to':fields.function(lambda *a,**k:{}, method=True, type='date',string="To"),
              
              #esugam, for specific users
              'gen_esugam'   : fields.boolean("Generate E-sugam"),
              'show_esugam'  : fields.related('partner_id','show_esugam',type='boolean',store=False),
              
              #Freight for specific users
              'show_freight'  : fields.related('partner_id','show_freight',type='boolean',store=False),
              'gen_freight'   : fields.boolean("Generate Freight"),
               'pay_freight'   : fields.related('partner_id','pay_freight',type='boolean',store=True,string="Pay Freight"),
               'report'        : fields.related('partner_id','report',type='boolean',store=True,string="DC-LR Report"),
               'wc_number'     :fields.char('W.C. Number',size=20),
               'wc_num'        : fields.related('partner_id','wc_num',type='boolean',store=True,string="WC Num"),
               'attachment'   : fields.related('company_id','attachment',type='binary',store=False,string="APMC Attachment",readonly=True),
               'amc_attachment'        :   fields.related('partner_id','amc_attachment',type='boolean',store=False,string="APMC Attachment",readonly=True),     
               'filename'   :   fields.char('File Name',size=100),
                'billing_cycle'        :   fields.related('partner_id','billing_cycle',type='boolean',store=False,string="Billing Cycle",readonly=True),
                'user_partner_id': fields.many2one('res.partner', 'Partner'), 
                'w_report'        : fields.related('partner_id','w_report',type='boolean',store=True,string="Weighment Slip Report"),   
                'dc_report'        : fields.related('partner_id','dc_report',type='boolean',store=True,string="DC Report"),
                'partner'       :   fields.function(_get_user,type='char',method=True,string="Partner", store=False,multi='user'),
                 'dest_location_id'        : fields.many2one('stock.location','Location', select=True),
                 'report_date'  :       fields.char('Date'),  
                 'hide_fields'     : fields.function(_get_permission,type='boolean',method=True,string="Permission", store=True),
                 'farmer_declaration' : fields.related('company_id','farmer_declaration', string="Farmer Declaration", type='binary', store=False),
                 'is_farm_decl' : fields.related('partner_id','is_farm_decl',string="Is Farmer Declaration", type="boolean", store=False),
                 'fd_filename'   :   fields.char('File Name',size=100),
                 
                 'transit_pass'     : fields.related('partner_id','transit_pass',type='boolean',store=True,string="Transit Pass"),
#                  'tax_link'         : fields.related('partner_id','tax_link',type='char',store=True,string="Tax Link"),

              # Bank details
                'bank_name'     :   fields.char("Bank Name", size=100),
                'ifsc_code'     :   fields.char("IFSC Cde", size=11),
                'ac_holder'     :   fields.char("Beneficiary Name", size=100),
                'ac_number'     :   fields.char("Account Number", size=30),
                'bank_addr'     :   fields.text("Bank Address"),
                'ac_holder_mob' :   fields.char("Mobile Number", size=10),
                'ac_holder_pan' :   fields.char("Pan Number"),
                'bene_code'     :   fields.char("Beneficiary Code"),


                #esugam, for specific users
                'gen_jjform'   : fields.boolean("Generate JJform"),
                'show_jjform'  : fields.related('partner_id','show_jjform',type='boolean',store=False),
                'jjform_no'    : fields.char("JJform Number", size=50),

                'es_active'    : fields.related('partner_id','es_active',type='boolean',store=False),

                # For Bank Account Details Report
                'frtpaid_date'   : fields.date("Freight Paid Date", select=1),
                'is_bank_submit' : fields.boolean("Is Online Bank Submit",select=1),
                'frieght_paid'   : fields.boolean("Is Freight Paid", select=True),

                'sub_facilitator_id'    :   fields.many2one("res.partner", "Sub Facilitator"),
                'purchase_amount'       :   fields.float("Purchase Amount", digits=(16,2)),
                'is_sub_facilitator'    :   fields.boolean("Is Sub Facilitator"),

                'hnl_attachment'        :   fields.related('company_id','hnl_attachment',type='binary',store=False,string="HNL Attachment"),
                'is_hnl_attachment'     :   fields.related('partner_id','is_hnl_attachment',type='boolean',store=False,string="HNL Attachment",readonly=True),
                'hnl_filename'          :   fields.char("File Name", size=30),
                'po_hnl_attachment'     :   fields.related('company_id','hnl_po_attachment',type='binary',store=False,string="HNL Attachment"),
                'hnl_po_filename'          :   fields.char("File Name", size=30),
              }
    
    _order = 'date desc'
    
    _defaults = { 
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
                    'delivery_date_function':lambda *a: time.strftime('%Y-%m-%d'),
                    'date_function': lambda *a: time.strftime('%Y-%m-%d'),
                    'filename'      :"APMC_CESS.pdf",
                    'fd_filename'   : "Farmer Declaration.pdf",
                    'user_partner_id':_get_default_user_partner,
                    'hide_fields' : _get_default_permission,
                    'transit_pass' : False,
                    'is_bank_submit' :  False,
                    'frieght_paid'   : False,
                    'hnl_filename'  :   "HNL-Letter to DFO.pdf",
                    'hnl_po_filename' : "HNL PO File.pdf",

#                  'customer_list' : _default_get_customer,
#                  'hide_fields' : True 
# cur_date=datetime.today().strftime("%Y-%m-%d")
#                 'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
                 }


    # Actions

    def open_tax_link(self, cr, uid, ids, context=None):
        ''' Open the website page with the Tax form '''
        trail = ""
        context = dict(context or {}, relative_url=True)
#         if 'survey_token' in context:
#             trail = "/" + context['survey_token']
        case = self.browse(cr, uid, ids[0])
#         if case.partner_id.tax_link:
        print "case.partner_id.tax_link",case.partner_id.id
        return {
            'type': 'ir.actions.act_url',
            'name': "Transit Pass",
            'target': 'new',
            'url': case.partner_id.tax_link#self.read(cr, uid, ids, ['public_url'], context=context)[0]['public_url'] + trail
        }

    
    
    #to check Freight Rate/MT Should not exceeds four digits before decimal point 
    def onchange_freight_charge(self, cr, uid, ids, freight_charge=False,context=None):
        res ={}
        warning = ""
        res['freight_charge'] = freight_charge
          
        if freight_charge > 9999.99:
            res['freight_charge'] = 0.00
            warning={
                                         'title':_('Freight Rate !'), 
                                                'message':_(' Freight Rate/MT Should Not be Greater Than "9,999" ')
                                             }
            
            
       
        return{'value':res ,'warning':warning}
        

    def onchange_paying_agent(self, cr, uid, ids, paying_agent_id=False, transporter_id=False,context=None):
        res={}
        g_ids = []
        paying_agent=[]
        warning=''
        log_user={}
        picking={}
        res['paying_agent_id'] = paying_agent_id
        user_obj = self.pool.get('res.users')
        part_obj = self.pool.get("res.partner")
        dom = {}
        if not paying_agent_id and ids:
            case = self.browse(cr, uid, ids)
            paying_agent_id = case.paying_agent_id and case.paying_agent_id.id or False

        if paying_agent_id:
            sub_fac = part_obj.browse(cr, uid, paying_agent_id)
            if sub_fac.sub_facilitator_ids:
                cr.execute("select sub_part_id from sub_facilitator where main_facilitator_id="+str(paying_agent_id))
                sub_facilitator_id = [x[0] for x in cr.fetchall()]
                if sub_facilitator_id:
                    # dom.update({'sub_facilitator_id':  [('id','in',sub_facilitator_id )]})
                    res.update({'is_sub_facilitator': True})
            else:
                # dom = {'sub_facilitator_id':  [('id','=',0 )]}
                res.update({'is_sub_facilitator':False})

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
        #changed process_pdf to get_pages
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
        
        
    
        
    def onchange_partner_in(self, cr, uid, ids, partner_id=None,freight=False,context=None):
#         res=super(stock_picking,self).onchange_partner_in(cr, uid, ids,partner_id=False,context=None)
        g_ids = []
        res={}
        dom={}
        state_id=0
        group_obj=self.pool.get('res.groups')
        user_obj = self.pool.get('res.users')
        partner_obj=self.pool.get('res.partner')
        partner_ids=partner_obj.search(cr,uid,[('id','=',partner_id)])
        res['pay_freight']=False
        for i in partner_obj.browse(cr,uid,partner_ids):
            res['partner'] = ''
            if 'associate' in i.name.lower():
                if uid!=1:
                    res['partner']=i.ref
                
            res['show_esugam'] = i.show_esugam or False
            res['show_freight'] = i.show_freight or False
            res['pay_freight'] = i.pay_freight or False
            res['report'] = i.report or False
            res['attachment'] = i.company_id.attachment or False
            res['amc_attachment'] = i.amc_attachment or False
            res['is_farm_decl'] = i.is_farm_decl or False
            res['farmer_declaration'] = i.company_id.farmer_declaration or False
            res['billing_cycle'] = i.billing_cycle or False
            res['wc_num'] = i.wc_num or False
            res['w_report'] = i.w_report or False
            res['dc_report'] = i.dc_report or False
            res['show_jjform'] = i.show_jjform or False
            res['es_active'] = i.es_active or False
            res['is_hnl_attachment'] = i.is_hnl_attachment or False
            res['hnl_attachment'] = i.company_id and i.company_id.hnl_attachment or False
            res['po_hnl_attachment'] = i.company_id and i.company_id.hnl_po_attachment or False

            if freight:
                res['freight']=freight
            else:
                res['freight'] = i.freight or False

            if i.sub_facilitator_ids:
                cr.execute("select sub_part_id from sub_facilitator where main_facilitator_id="+str(i.id))
                sub_facilitator_id = [x[0] for x in cr.fetchall()]
                if sub_facilitator_id:
                    dom.update({'sub_facilitator_id':  [('id','in',sub_facilitator_id )]})
                    res.update({'is_sub_facilitator': True})

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
            dom.update( {'paying_agent_id':  [('state_id','=', state_id.id)]})

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
            
                user_ids=user_obj.search(cr,uid,[('id','=',uid)])
                for j in user_obj.browse(cr,uid,user_ids):
                    res['pay_freight']=j.pay_freight
                    
                    if g.name=='KW_Depot':
                        state_id=j.state_id
                 
                                   
        if state_id>0:
            dom = {'paying_agent_id':  [('state_id','=', state_id.id),('supplier','=',True),('handling_charges','=',False),('representative','=',False)]}
        else:
            dom = {'paying_agent_id':  [('supplier','=',True),('handling_charges','=',False),('representative','=',False)]}
            
        return {'value':res,'domain':dom}

    

    def generate_esugam(self, cr, uid, desc, qty, price, product_id, username, password, url1,url2, url3, case,context):
        tax_obj = self.pool.get("account.tax")
        tax_amount = 0
        esugam = 0
        # Commented for GST
        # if case.partner_id.state_id.name == 'Karnataka':
        #     for t in product_id.taxes_id:
        #         if t.state_id.name == 'Karnataka':
        #             tax_amount += t.amount * price * qty
        #         else:
        #             # for CST Taxes
        #             if context.get('confirm_esugam'):
        #                 for t in product_id.cst_taxes_id:
        #                     tax_amount += t.amount * price * qty
        #
        # else:
        #     # for CST Taxes
        #     for t in product_id.cst_taxes_id:
        #         tax_amount += t.amount * price * qty

        # Commented Because tax will be updated later. esugam will generate based in DC
        if case.state_id.id == case.partner_id.state_id.id:
            cr.execute("select id from account_tax where gst_categ='intra' ")
            intra_tax_id= [x[0] for x in cr.fetchall()]
            intra_tax_id = tuple(intra_tax_id)
            if intra_tax_id:
                cr.execute("select tax_id from product_taxes_rel where prod_id=%s and tax_id in %s",(product_id.id,intra_tax_id))
                tx_ids = [x[0] for x in cr.fetchall()]
                for tx in tax_obj.browse(cr, uid, tx_ids):
                    tax_amount += tx.amount * price * qty

        else:
            cr.execute("select id from account_tax where gst_categ='inter' ")
            inter_tax_id= [x[0] for x in cr.fetchall()]
            inter_tax_id = tuple(inter_tax_id)
            if inter_tax_id:
                cr.execute("select tax_id from product_taxes_rel where prod_id=%s and tax_id in %s",(product_id.id,inter_tax_id))
                tx_ids = [x[0] for x in cr.fetchall()]
                for tx in tax_obj.browse(cr, uid, tx_ids):
                    tax_amount += tx.amount * price * qty


        cr.execute("select tin_no from res_partner where name ilike '%Kingswood Suppliers Pvt. Ltd.(TN)%' ")
        tn_tin = [x[0] for x in cr.fetchall()]
        if tn_tin:
            tn_tin = tn_tin[0]
        else:
            tn_tin = 33944481896
        
        
        today = time.strftime('%Y-%m-%d %H:%M:%S')
        last_month_date = datetime.strptime(today, '%Y-%m-%d %H:%M:%S')
        veh_owner = case.driver_name and case.driver_name or ''
        inv_date = parser.parse(''.join((re.compile('\d')).findall(case.date))).strftime('%d/%m/%Y')
        del_date = parser.parse(''.join((re.compile('\d')).findall(str(last_month_date)))).strftime('%d/%m/%Y')
        
        
        browser = webdriver.PhantomJS()
        #browser = webdriver.Firefox()
        url_status1 = browser.get(url1)
        _logger.info('url_status1....... %s',url_status1)


        try:
            # check URL1
            try:
                url_status1 = browser.find_element_by_id('Button2')
                browser.find_element_by_id('Button2').click()
            
            except:    
                url_status1 = browser.find_element_by_id('UserName')
        except:
            if not url_status1:
                # check URL2
                url_status2 = browser.get(url2)
                try:
                    url_status2 = browser.find_element_by_id('UserName')
                except:
                    # check URL3
                    url_status3 = browser.get(url3)
                    url_status3 = browser.find_element_by_id('UserName')
        try:
            # check URL3
            if not url_status1 and not url_status2:
                browser.find_element_by_id('UserName')
                url_status1 = False
        
        except:
            try:
                browser.find_element_by_id('Button2')
            except:
                raise osv.except_osv(_('Esugam Site Is Down'),_('Please Try After Some Time'))
            browser.find_element_by_id('Button2').click()
        
        
        
        #captcha = self.get_captcha(cr, uid, [], browser, context)
        try:
            #captcha = self.get_captcha(cr, uid, [], browser, context)
            #captcha = '787sd'
            error = "Invalid Captcha Characters."
            
            while error in ("Invalid Captcha Characters.","Please enter the captcha."):
                browser.find_element_by_id('UserName')
                browser.find_element_by_id('Password')
                
                captcha = self.get_captcha(cr, uid, [], browser, context)
                _logger.info('captcha....... %s',captcha)
                if re.match("^([a-zA-Z0-9']{0,5})$",captcha) == None:
                    continue
                    
                time.sleep(1)
                browser.find_element_by_id('UserName').send_keys(username)
                browser.find_element_by_id('Password').send_keys(password)
                browser.find_element_by_id('txtCaptcha')
                browser.find_element_by_id('txtCaptcha').send_keys(captcha)
                time.sleep(2)
                
                browser.find_element_by_id('btn_login')
                browser.find_element_by_id('btn_login').click()
                time.sleep(2)
                try:
                    browser.find_element_by_id('lbl_error')
                    error = browser.find_element_by_id('lbl_error').text
                    print "error.........",error
                except:
                    error = ''
                    
                
                

            
            if not url_status1 and (url_status2 or url_status3):
                try:
                    browser.find_element_by_id('ctl00_MasterContent_btnContinue').click()
                    browser.find_element_by_id('LinkButton1').click()
                except:
                    browser.find_element_by_id('LinkButton1').click()
#                     browser.find_element_by_css_selector('.Menu1_3').click()
#                     browser.find_element_by_css_selector('.Menu1_3').send_keys(Keys.RIGHT)
#                     browser.find_element_by_css_selector('.Menu1_5').click()
                    pass
            elif url_status1:
                try:
                    browser.find_element_by_id('ctl00_MasterContent_btnContinue').click()
                    browser.find_element_by_css_selector('.Menu1_3').click()
                    browser.find_element_by_css_selector('.Menu1_3').send_keys(Keys.RIGHT)
                    browser.find_element_by_css_selector('.Menu1_5').click()
                    try:
                        browser.find_element_by_id('ctl00_MasterContent_btn_ok').click()
                    except:
                        pass

                    
                except:
                    browser.find_element_by_id('chkConfirmation').click()
                    browser.find_element_by_id('btnContinue').click()
                    time.sleep(2)
                    browser.find_element_by_css_selector('.Menu1_3').click()
                    browser.find_element_by_css_selector('.Menu1_3').send_keys(Keys.RIGHT)
                    browser.find_element_by_css_selector('.Menu1_5').click()
                    try:
                        browser.find_element_by_id('ctl00_MasterContent_btn_ok').click()
                    except:
                        pass
            else:
                browser.find_element_by_css_selector('.Menu1_3').click()
                browser.find_element_by_css_selector('.Menu1_3').send_keys(Keys.RIGHT)
                browser.find_element_by_css_selector('.Menu1_5').click()
                try:
                    browser.find_element_by_id('ctl00_MasterContent_btn_ok').click()
                except:
                    pass
            #browser.find_by_id('ctl00_MasterContent_rbl_doctype_5').click()
            #browser.find_by_id('ctl00_MasterContent_btnContinue').click()
            #browser.find_by_id('LinkButton1').click()
            time.sleep(1)
            if case.partner_id.state_id.id == case.state_id.id:
                browser.find_element_by_id('ctl00_MasterContent_rdoStatCat_0').click()
            else:
                browser.find_element_by_id('ctl00_MasterContent_rdoStatCat_1').click()
            time.sleep(1)
            browser.find_element_by_name('ctl00$MasterContent$txtFromAddrs').send_keys(case.city_id.name)
            browser.find_element_by_name('ctl00$MasterContent$txtToAddrs').send_keys(case.partner_id.city)
            browser.find_element_by_name('ctl00$MasterContent$ddl_commoditycode').send_keys('OTHERS')
            browser.find_element_by_name('ctl00$MasterContent$txt_commodityname').send_keys(desc)
            browser.find_element_by_name('ctl00$MasterContent$txtQuantity').send_keys(str(qty))
            browser.find_element_by_name('ctl00$MasterContent$txtNetValue').send_keys(str(price * qty))
            #for taxes
            #browser.fill('ctl00$MasterContent$txtVatTaxValue',str(tax_amount))
            # browser.find_element_by_name('ctl00$MasterContent$txtVatTaxValue').send_keys(str(round(tax_amount,2)))
            
            browser.find_element_by_name('ctl00$MasterContent$txtVehicleOwner').send_keys(veh_owner)
            browser.find_element_by_name('ctl00$MasterContent$txtVehicleNO').send_keys(case.truck_no)
            browser.find_element_by_id('ctl00_MasterContent_rdoListGoods_5').click()
            browser.find_element_by_name('ctl00$MasterContent$ddl_state').send_keys(str(case.state_id.name.upper()))
            browser.find_element_by_name('ctl00$MasterContent$txtOthCat').send_keys(case.product_id.name.replace('/', '').replace('-', ''))

            browser.find_element_by_name('ctl00$MasterContent$txtGCLRNO').send_keys(case.name.replace('/', '').replace('-', ''))
            browser.find_element_by_name('ctl00$MasterContent$txtInvoiceNO').send_keys(case.name.replace('/', '').replace('-', ''))
            browser.find_element_by_name('ctl00$MasterContent$txtInvoiceDate').send_keys(inv_date)
            browser.find_element_by_name('ctl00$MasterContent$txtDeliveryDate').send_keys(del_date)
            # browser.find_element_by_id('ctl00_MasterContent_RadioButton2').click() # for pdfprint
            #  for others
            #browser.find_element_by_id('ctl00_MasterContent_rdoListGoods_9').click()
            #browser.find_element_by_id('ctl00_MasterContent_rdoListGoods_0').click()
            time.sleep(2)
            #browser.find_element_by_name('ctl00$MasterContent$txtOthCat').send_keys('DC')
            #Document Type Others
            #browser.find_element_by_id('ctl00_MasterContent_rbl_doctype_5').click()
            #Document Type Invoice
            if context.get('confirm_esugam'):
                browser.find_element_by_id('ctl00_MasterContent_rdoStatCat_1').click()
                browser.find_element_by_id('ctl00_MasterContent_rdoListGoods_1').click()
                time.sleep(1)


            # browser.find_element_by_id('ctl00_MasterContent_rbl_doctype_0').click()
            if context.get('confirm_esugam'):
                browser.find_element_by_id('ctl00_MasterContent_rbl_doctype_0').click()
            else:
                browser.find_element_by_id('ctl00_MasterContent_rbl_doctype_4').click()
            if (case.partner_id.state_id.name == 'Karnataka' or case.state_id.name =='Karnataka') and not context.get('confirm_esugam'):
                browser.find_element_by_name('ctl00$MasterContent$txtTIN').send_keys(case.partner_id.tin_no)
                time.sleep(1)
                if case.partner_id.state_id.name != case.state_id.name:
                    browser.find_element_by_name('ctl00$MasterContent$txtTIN').send_keys(Keys.TAB)
                    time.sleep(1)
                    browser.find_element_by_name('ctl00$MasterContent$txtNameAddrs').send_keys(str(case.partner_id.name))
            else:
                if context.get('confirm_esugam'):
                    browser.find_element_by_name('ctl00$MasterContent$txtTIN').send_keys(tn_tin)
                    time.sleep(1)
                    browser.find_element_by_name('ctl00$MasterContent$txtTIN').send_keys(Keys.TAB)
                    time.sleep(1)
                    browser.find_element_by_id('ctl00_MasterContent_txtNameAddrs').send_keys(str(case.company_id.name))
                browser.find_element_by_name('ctl00$MasterContent$txtVehicleOwner').send_keys(veh_owner)
                time.sleep(5)

            _logger.info('Final Page....... ')
            #browser.find_element_by_id('ctl00_MasterContent_btnSave').click()
            browser.find_element_by_id('ctl00_MasterContent_RadioButton2').click() # for pdfprint
            time.sleep(2)
            browser.find_element_by_id('ctl00_MasterContent_btn_savecumsubmit').click()
            time.sleep(10)
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
                
            response = requests.get(URL, cookies=cookies)
            #with file('/home/serveradmin/esugama/esugam.pdf','wb') as f:
            f = open('/tmp/'+case.name.replace('/', '').replace('-', '')+'.pdf','wb')
            f.write(response.content)
            f.close()
           
            
            
            #for creating file
            current_file = '/tmp/'+case.name.replace('/', '').replace('-', '')+'.pdf'
            _logger.info('Final Page Before PDF ....... ')
            browser.save_screenshot('/tmp/final_page.png')
            pdf_data = self.convert_pdf(current_file)
            fp = open(current_file,'rb')
            esugam = pdf_data[pdf_data.find('Sl.No')-20:pdf_data.find('Sl.No')-9]
            result = base64.b64encode(fp.read())
            file_name = 'esugam_' + esugam
            file_name += ".pdf"
            _logger.info('Final Page After PDF ....... ')
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
        
        except Exception as e:
            _logger.info('Error reason %s',e)
            raise osv.except_osv(_('Esugam Site Is Down'),_('Please Try After Some Time'))
        
        return esugam
    

    def kw_confirm(self, cr, uid, ids, context = None):
        today = time.strftime('%Y-%m-%d %H:%M:%S')
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
        jjform = '0'
        move_ids = []
        ctxt={}
        move_obj = self.pool.get('stock.move')
#         for c in self.pool.get('res.company').browse(cr,uid, [1]):
#             username = c.username
#             password = c.password
#             url = c.url
        for case in self.browse(cr, uid, ids):
            if case.jjform_no != '0':
                jjform = case.jjform_no

            else:
                jjform = '0'

            if case.paying_agent_id:
                self.write(cr,uid,ids,{'state_id':case.paying_agent_id.state_id.id})            
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

            if case.distance == 0:
                raise osv.except_osv(_('Warning'),_('Please Eneter the Approximate Distance and Confirm'))

            if context.get("confirm_esugam") and len(case.esugam_no) > 1:
                raise osv.except_osv(_('Warning'),_('eWayBill is Already Generated for this Delivery Challan'))


            #for creating vKW_Depotoucher lines
            if case.transporter_id and case.freight_advance >0 and case.transporter_id.name !='Others':
                j_ids = journal_obj.search(cr, uid, [('type','=','cash'),('company_id','=',case.company_id.id)]) 
                voucher_vals1 = {         'partner_id'       : case.transporter_id.id,
                                          'type'              :   'payment',
                                          'amount'            : case.freight_advance,
                                          'account_id'        : case.transporter_id.property_account_payable.id,
                                          'journal_id'        : j_ids[0],
                                          'reference'         : case.name,
                                          'advance_type'      : 'advance',
                                          }
                vid = voucher_obj.create(cr, uid, voucher_vals1, context= context)
                ctxt.update({'freight_advance':True,'dc_reference':case.name})
                voucher_obj.proforma_voucher(cr, uid,[vid],context=ctxt)

            # Tamilnadu Vat
            # if not context.get("confirm_esugam", False):
            #     if (case.partner_id.gen_jjform == True or case.gen_jjform) and case.state_id.code == 'TN':
            #         esugam_ids = []
            #         cr.execute(""" select e.id
            #            from esugam_master e
            #            inner join res_country_state rcs on rcs.id = e.state_id
            #             where rcs.code = 'TN' order by e.id desc limit 1
            #                    """)
            #         esugam_ids = [x[0] for x in cr.fetchall()]
            #         if esugam_ids:
            #             for e in esugam_obj.browse(cr, uid, esugam_ids):
            #                 if e.state_id.id == case.state_id.id:
            #                     username = e.username
            #                     password = e.password
            #                     url = e.url1
            #                     url2 = e.url2
            #                     url3 = e.url3
            #                     jjform = self.generate_tnvat(cr, uid, desc, qty, price, product_id, username, password, url, url2, url3, case, context)


            if (case.partner_id.gen_esugam == True or case.gen_esugam) and case.state_id.code == 'KA' :
                for e in case.company_id.esugam_ids:
                    if e.state_id.code == 'KA':
                        username = e.username
                        password = e.password
                        url1 = e.url1
                        url2 = e.url2
                        url3 = e.url3

                """ Esugam Site security reason commented"""
                # esugam = self.generate_esugam(cr,uid,desc, qty, price, product_id, username, password, url1,url2, url3, case, context)
                esugam = self.generate_eway_bill(cr, uid, ids, username, password, url1,url2, url3, context=context)

            elif (case.partner_id.gen_esugam == True or case.gen_esugam) and case.state_id.code == 'TN' :
                for e in case.company_id.esugam_ids:
                    if e.state_id.code == 'TN':
                        username = e.username
                        password = e.password
                        url1 = e.url1
                        url2 = e.url2
                        url3 = e.url3
                # esugam = self.generate_esugam(cr, uid, desc, qty, price, product_id, username, password, url1, url2, url2, case, context)
                esugam =  self.generate_eway_bill(cr, uid, ids, username, password, url1,url2, url3, context=context)
            self.write(cr, uid, ids, {
                                      'state'           :'in_transit',
                                      'esugam_no'       : esugam,
                                      'transit_date'    : today,
                                      'jjform_no'       : jjform
                                      })
#             move_obj.action_done(cr, uid, move_ids, context=None)
            return True

    def generate_eway_bill(self, cr, uid, ids, username, password, url1, url2, url3, context=None):
        if not context:
            context = {}
        tax_obj = self.pool.get("account.tax")
        today = time.strftime('%Y-%m-%d')
        today = datetime.strptime(today,'%Y-%m-%d')
        esugam_no = ''
        value = 0.00

        for case in self.browse(cr, uid, ids):
            dc_date = parser.parse(''.join((re.compile('\d')).findall(case.date))).strftime('%Y-%m-%d')
            dc_date = datetime.strptime(dc_date, '%Y-%m-%d')
            cust_street = case.partner_id.street.replace('.','').replace(',','').replace('-','').replace('#','').replace('/','')
            cust_street2 = case.partner_id.street2 and case.partner_id.street2.replace('.','').replace(',','').replace('-','').replace('#','').replace('/','')
            truck_no = case.truck_no.replace('-','').replace('/','').replace('.','').replace(' ','')

            # cr.execute("""
            #                 select case when kw.sub_total is null then kw.product_price else kw.sub_total end
            #
            #                 from product_supplierinfo ps
            #                 inner join kw_product_price kw on ps.id = kw.supp_info_id
            #                 and ps.product_id = """+str(case.product_id.id)+"""
            #
            #                 and ef_date <= '"""+str(case.date)+"""' ::date
            #                 and ps.name = """+str(case.paying_agent_id.id)+"""
            #                 and (case when ps.customer_id is null then ps.depot = (select location_id from stock_move where picking_id = """+str(case.id)+""" limit 1)
            #                 else case when ps.customer_id is null and ps.depot is null then ps.city_id = """+str(case.city_id.id)+""" else ps.customer_id = """+str(case.partner_id.id)+""" end end)
            #                 order by ef_date desc limit 1
            #             """)
            # goods_rate = [x[0] for x in cr.fetchall()]
            # if goods_rate:
            #     goods_rate = goods_rate[0]
            #     goods_rate = int(goods_rate)
            for move in case.move_lines:
                goods_rate = move.price_unit
                goods_rate = int(goods_rate)
                qty = move.product_qty
            print "goods_rate----------------->",goods_rate
            # Tax Calculation
            tax_amount = 0.00
            if case.state_id.id == case.partner_id.state_id.id:
                cr.execute("select id from account_tax where gst_categ='intra' ")
                intra_tax_id= [x[0] for x in cr.fetchall()]
                intra_tax_id = tuple(intra_tax_id)
                if intra_tax_id:
                    cr.execute("select tax_id from product_taxes_rel where prod_id=%s and tax_id in %s",(case.product_id.id,intra_tax_id))
                    tx_ids = [x[0] for x in cr.fetchall()]
                    for tx in tax_obj.browse(cr, uid, [tx_ids[0]]):
                        tax_amount += tx.amount


            else:
                cr.execute("select id from account_tax where gst_categ='inter' ")
                inter_tax_id= [x[0] for x in cr.fetchall()]
                inter_tax_id = tuple(inter_tax_id)
                if inter_tax_id:
                    cr.execute("select tax_id from product_taxes_rel where prod_id=%s and tax_id in %s",(case.product_id.id,inter_tax_id))
                    tx_ids = [x[0] for x in cr.fetchall()]
                    for tx in tax_obj.browse(cr, uid, tx_ids):
                        tax_amount += tx.amount

            # For PDF Download Setting options
            def enable_download_in_headless_chrome(browser, download_dir):
                #add missing support for chrome "send_command"  to selenium webdriver
                browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

                params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
                browser.execute("send_command", params)
                return browser

            chrome_options = Options()
            DOWNLOAD_PATH = '/tmp'
            chrome_options = webdriver.ChromeOptions()
            # chrome_options.add_argument("--headless")
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--window-size=1440,900')
            chrome_options.add_argument ( "--disable-extensions" )
            chrome_options.add_argument ( "--disable-print-preview" )
            chrome_options.add_argument('--ignore-certificate-errors')
            # chrome_options.add_argument ( "--print-to-pdf=/tmp/file1.pdf" )


            prefs = {
                'download.default_directory': DOWNLOAD_PATH,
                'download.prompt_for_download': False,
                "plugins.always_open_pdf_externally": True,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': False,
                'safebrowsing.disable_download_protection': True,
                # 'plugins.plugins_list': [{'enabled':False,'name':'Chrome PDF Viewer' }],
                "plugins.plugins_disabled": ['Chrome PDF Viewer'],
            }

            chrome_options.add_experimental_option('prefs', prefs)
            ssl._create_default_https_context = ssl._create_unverified_context
            try:
                browser = webdriver.Chrome(chrome_options=chrome_options) #chrome_options=options
            except:
                pass


            # browser = webdriver.Chrome(
            # chrome_options=options)
            # browser.set_window_size(1440, 900)

            enable_download_in_headless_chrome(browser, DOWNLOAD_PATH)



            # profile = {"plugins.plugins_list": [{"enabled": False,
            #                                      "name": "Chrome PDF Viewer"}],
            #            "download.default_directory": download_folder,
            #            "download.extensions_to_open": ""}
            #
            # options = webdriver.ChromeOptions()
            # options.add_experimental_option("prefs", profile)
            # options.add_argument("--test-type");
            # options.add_argument("--disable-extensions")
            #
            #
            # # Setting Options for Headless
            # options.add_argument('headless')


            # browser = webdriver.Chrome() #webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
            # browser.maximize_window()
            # browser.implicitly_wait(10)

            # browser = webdriver.PhantomJS()
            # browser = webdriver.Firefox()
            # browser.maximize_window()

            url_status1 = browser.get(url1)
            _logger.info('url_status1....... %s',url_status1)

            try:
                # check URL1
                try:
                    url_status1 = browser.find_element_by_name('txt_username')

                except:
                    url_status1 = browser.find_element_by_name('txt_username')
            except:
                if not url_status1:
                    # check URL2
                    url_status2 = browser.get(url2)
                    try:
                        url_status2 = browser.find_element_by_id('txt_username')
                    except:
                        # check URL3
                        url_status3 = browser.get(url3)
                        url_status3 = browser.find_element_by_id('txt_username')
            try:
                # check URL3
                if not url_status1 and not url_status2:
                    browser.find_element_by_id('txt_username')
                    url_status1 = False

            except:
                try:
                    browser.find_element_by_id('btnLogin').click()
                except:
                    raise osv.except_osv(_('Eway Bill Site Is Down'),_('Please Try After Some Time'))
                browser.find_element_by_id('btnLogin').click()

            try:
                error = "Invalid Captcha"

                while error in ("Invalid Captcha","Please enter the captcha."):
                    browser.set_window_size(1280, 1024)
                    browser.find_element_by_xpath('.//*[@id="txt_username"]')
                    browser.find_element_by_xpath('.//*[@id="txt_password"]')
                    browser.find_element_by_id('btnCaptchaImage').click()
                    # browser.find_element_by_id('btnCaptchaImage').click()
                    captcha = self.get_eway_captch(cr, uid, [], browser, context)
                    _logger.info('captcha....... %s',captcha)
                    if re.match("^([a-zA-Z0-9']{0,5})$",captcha) == None:
                        continue

                    browser.find_element_by_xpath('.//*[@id="txt_username"]').clear()
                    browser.find_element_by_xpath('.//*[@id="txt_username"]').send_keys(str(username))
                    browser.find_element_by_xpath('.//*[@id="txt_username"]').send_keys(Keys.TAB)
                    browser.find_element_by_xpath('.//*[@id="txt_password"]').send_keys(str(password))
                    time.sleep(1)
                    browser.find_element_by_id('txtCaptcha')
                    browser.find_element_by_id('txtCaptcha').send_keys(captcha)
                    browser.save_screenshot('/home/serveradmin/Desktop/screenie1.png')

                    time.sleep(1)

                    browser.find_element_by_id('btnLogin').click()

                    try:
                        if browser.find_element_by_xpath('.//*[@id="R10"]/a'):
                            break
                    except  Exception as e:
                        alert = browser.switch_to.alert
                        alert.accept()
                        print ",,,,,,,,,,,,,,",e
                        continue
                less_days = 0
                if url_status1 or url_status2 or url_status3:
                    browser.find_element_by_xpath('.//*[@id="R10"]/a').click()
                    browser.find_element_by_xpath('.//*[@id="R11"]/a').click()
                    time.sleep(1)
                    browser.find_element_by_id('ctl00_ContentPlaceHolder1_ddlDocType').send_keys("Delivery Challan")
                    # browser.find_element_by_id('ctl00_ContentPlaceHolder1_ddlDocType').send_keys(Keys.TAB)
                    browser.find_element_by_xpath('.//*[@id="txtDocNo"]').send_keys(case.name)
                    browser.find_element_by_xpath('.//*[@id="txtDocNo"]').send_keys(Keys.TAB)
                    if dc_date < today:
                        less_days = today - dc_date
                        print "less_days--------",type(less_days)
                        less_days = str(less_days)[0:2]
                        for i in range(int(less_days)):
                            browser.find_element_by_xpath('.//*[@id="HeadTable"]/tbody/tr[3]/td/table/tbody/tr/td[3]/div/div/a[1]').click()
                    time.sleep(1)
                    browser.find_element_by_xpath('.//*[@id="slFromState"]').send_keys(Keys.TAB)
                    browser.find_element_by_xpath('.//*[@id="ctl00_ContentPlaceHolder1_txtToTrdName"]').send_keys(case.partner_id.name)
                    browser.find_element_by_xpath('.//*[@id="ctl00_ContentPlaceHolder1_txtToGSTIN"]').send_keys(str(case.partner_id.gstin_code))
                    time.sleep(1)
                    # browser.find_element_by_xpath('.//*[@id="ctl00_ContentPlaceHolder1_txtToGSTIN"]').send_keys(Keys.TAB)
                    # Customer Addrress Details
                    # browser.find_element_by_xpath('.//*[@id="txtToAddr1"]').send_keys(cust_street)
                    # browser.find_element_by_xpath('.//*[@id="txtToAddr1"]').send_keys(Keys.TAB)
                    # browser.find_element_by_xpath('.//*[@id="txtToAddr2"]').send_keys(cust_street2)
                    # browser.find_element_by_xpath('.//*[@id="txtToAddr2"]').send_keys(Keys.TAB)
                    # browser.find_element_by_xpath('.//*[@id="ctl00_ContentPlaceHolder1_txtToPlace"]').send_keys(case.city_id and str(case.city_id.name))
                    # time.sleep(1)
                    # browser.find_element_by_xpath('.//*[@id="ctl00_ContentPlaceHolder1_txtToPincode"]').send_keys(str(case.partner_id.zip))
                    # browser.find_element_by_xpath('.//*[@id="ctl00_ContentPlaceHolder1_txtToPincode"]').send_keys(Keys.TAB)
                    # # browser.find_element_by_xpath('.//*[@id="slToState"]').send_keys('KARNATAKA') #to do
                    # time.sleep(1)

                    product = case.product_id.name_template.replace('-',' ')
                    default_code = case.product_id.default_code.replace('-',' ') or ''
                    # browser.find_element_by_xpath('.//*[@id="slToState"]').send_keys(Keys.TAB)
                    time.sleep(1)
                    browser.find_element_by_xpath('.//*[@id="txtProductName_1"]').send_keys(product)
                    browser.find_element_by_xpath('.//*[@id="txtProductName_1"]').send_keys(Keys.TAB)
                    browser.find_element_by_xpath('.//*[@id="txt_Description_1"]').send_keys(product +' ' +default_code)
                    browser.find_element_by_xpath('.//*[@id="txt_Description_1"]').send_keys(Keys.TAB)
                    browser.find_element_by_xpath('.//*[@id="txt_HSN_1"]').send_keys(str(case.product_id.hsn_sac))
                    browser.find_element_by_xpath('.//*[@id="txt_HSN_1"]').send_keys(Keys.TAB)

                    browser.find_element_by_xpath('.//*[@id="txt_Quanity_1"]').send_keys(str(qty))
                    browser.find_element_by_xpath('.//*[@id="txt_Quanity_1"]').send_keys(Keys.TAB)
                    browser.find_element_by_xpath('.//*[@id="txt_Unit_1"]').send_keys('MTS')
                    browser.find_element_by_xpath('.//*[@id="txt_Unit_1"]').send_keys(Keys.TAB)
                    print "str(goods_rate)---------------",str(goods_rate)
                    value = float(goods_rate) * float(qty)
                    browser.find_element_by_xpath('.//*[@id="txt_TRC_1"]').send_keys(str(value))
                    browser.find_element_by_xpath('.//*[@id="txt_TRC_1"]').send_keys(Keys.TAB)
                    time.sleep(1)
                    tax_amount = tax_amount * 100
                    if case.state_id.id == case.partner_id.state_id.id:
                        browser.find_element_by_xpath('.//*[@id="txtCgstRt_1"]').send_keys(str(tax_amount))
                        browser.find_element_by_xpath('.//*[@id="txtCgstRt_1"]').send_keys(Keys.TAB)
                        browser.find_element_by_xpath('.//*[@id="txtSgstRt_1"]').send_keys(str(tax_amount))
                        browser.find_element_by_xpath('.//*[@id="txtSgstRt_1"]').send_keys(Keys.TAB)
                    else:
                        browser.find_element_by_xpath('.//*[@id="txtIgstRt_1"]').send_keys(str(tax_amount))

                    time.sleep(1)
                    print ".............1"

                    browser.find_element_by_id('txtDistance').send_keys(str(case.distance))
                    browser.find_element_by_id('txtDistance').send_keys(Keys.TAB)
                    browser.find_element_by_id('ctl00_ContentPlaceHolder1_txtTransid').send_keys("")
                    browser.find_element_by_id('ctl00_ContentPlaceHolder1_txtTransid').send_keys(Keys.TAB)
                    browser.set_window_size(1280, 1024)
                    browser.find_element_by_id('ctl00_ContentPlaceHolder1_txtVehicleNo').send_keys(str(truck_no))
                    # browser.execute_script("document.body.style.zoom='80%'")
                    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    # browser.find_element_by_id('ctl00_ContentPlaceHolder1_txtVehicleNo').send_keys(Keys.ARROW_DOWN)



                    # browser.set_window_size(1920, 1080)
                    browser.save_screenshot('/home/serveradmin/Desktop/screenie3.png')
                    time.sleep(1)
                    browser.find_element_by_xpath('.//*[@id="btnsbmt"]').click()

                    alert = browser.switch_to.alert
                    print "tesrt alert===========", alert.text
                    alert.accept()
                    time.sleep(1)
                    esugam_no = browser.find_element_by_xpath('.//*[@id="ctl00_ContentPlaceHolder1_lblBillNoDetails"]')
                    if esugam_no:
                        esugam_no = esugam_no.text.replace(" ", "")
                    return esugam_no


                    """ Upload PDF File to respective DC"""
                    # time.sleep(2)
                    # browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    # browser.find_element_by_xpath('.//*[@id="ctl00_ContentPlaceHolder1_btn_detail"]').click()
                    # browser.find_element_by_xpath('.//*[@id="ctl00_ContentPlaceHolder1_printtr"]/td/a[1]').click()
                    # time.sleep(5)
                    # time.sleep(2)
                    # browser.save_screenshot('/tmp/'+case.name.replace('/', '').replace('-', '')+'.png')
                    # img = Image.open('/tmp/'+case.name.replace('/', '').replace('-', '')+'.png')
                    # img.size
                    # crop_specs = (185, 90, img.width - 190, img.height - 30)
                    # crop_img = img.crop(crop_specs)
                    # crop_img.size
                    # #grayimg = grayscale(crop_img)
                    # crop_img.save('/tmp/'+case.name.replace('/', '').replace('-', '')+'.png')
                    #
                    # a4inpt = (img2pdf.mm_to_pt(210),img2pdf.mm_to_pt(297))
                    # layout_fun = img2pdf.get_layout_fun(a4inpt)
                    # with open('/tmp/'+case.name+'.pdf',"wb") as f:
                    #     f.write(img2pdf.convert('/tmp/'+case.name+'.png',layout_fun=layout_fun))
                    #     f.close()
                    #
                    # #for creating file
                    # current_file = '/tmp/'+case.name.replace('/', '').replace('-', '')+'.pdf'
                    # fp = open(current_file,'rb')
                    # result = base64.b64encode(fp.read())
                    # file_name = 'ewaybill_' + '123'
                    # file_name += ".pdf"
                    # self.pool.get('ir.attachment').create(cr, uid,
                    #                                       {
                    #                                        'name': file_name,
                    #                                        'datas': result,
                    #                                        'datas_fname': file_name,
                    #                                        'res_model': self._name,
                    #                                        'res_id': case.id,
                    #                                        'type': 'binary'
                    #                                       },
                    #                                       context=context)
                    # os.remove(current_file)



            except Exception as e:
                _logger.info('Error reason %s',e)
                raise osv.except_osv(_('Eway Bill Site is Down'),_('Please Try After Some Time'))



        return True




    def get_eway_captch(self, cr, uid, ids, browser, context=None):
        """ Captcha Image Reading using PIL
        """

        img = browser.find_element_by_xpath('//div[@class="col-lg-3"]/div[@class="well boxshadow text-center"]/div[3]/table//img')
        if not img:
           img = browser.find_element_by_xpath('//*[@id="form"]/div[3]/div[2]/div[3]/div[1]/div[3]/table/tbody/tr[2]/td[1]/div/img')

        print "Inside....................",img
        src = img.get_attribute('src')
        urllib.urlretrieve(src, '/tmp/captcha.png')

        img = Image.open('/tmp/captcha.png')
        img = img.convert("RGBA")
        pixdata = img.load()
        print "pixdata[x, y]",pixdata

        for y in xrange(img.size[1]):
         for x in xrange(img.size[0]):
             if pixdata[x, y][1] < 50: #136
                pixdata[x, y] = (0, 0, 0, 255)

        img.save("/tmp/new_captcha.png")

        data = pytesseract.image_to_string(Image.open('/tmp/new_captcha.png'))
        print data
        return data.replace(' ', '')


    def generate_tnvat(self, cr, uid,  desc, qty, price, product_id, username, password, url, url2, url3, case, context=None):
        if not context:
            context = {}
        #for calulating taxes
        tax_amount = 0
        esugam = 0
        jjform = 0
        comp_tin = ''
        zip = ''
        pincode = ''
        tot_price = qty * price
        if case.state_id.code == 'TN':
            for t in product_id.cst_taxes_id:
                if t.id:
                    tax_amount += t.amount * price * qty
                else:
                    tax_amount += 0.02000 * price * qty

        cr.execute("""
                    select
                        rp.zip

                        from res_partner rp
                        inner join res_country_state rcs on rcs.id = rp.state_id
                        where rp.parent_id is not null and rcs.code = 'TN'  """)
        zip = [x[0] for x in cr.fetchall()]

        cr.execute("""
                select
                    c.pincode
                from stock_picking sp
                inner join kw_city c on c.id = sp.city_id
                where c.pincode ilike '6%' and sp.id ='""" +str(case.id)+"""'  """)
        pincode = [x[0] for x in cr.fetchall()]


        today = time.strftime('%Y-%m-%d %H:%M:%S')
        last_month_date = datetime.strptime(today, '%Y-%m-%d %H:%M:%S')
        veh_owner = case.driver_name and case.driver_name or ''
        inv_date = parser.parse(''.join((re.compile('\d')).findall(case.date))).strftime('%d/%m/%Y')

        truck_no = case.truck_no
        truck_no = truck_no.replace('-','')
        truck_no = truck_no.replace(' ','')
        truck_no = truck_no.replace('.','')
        truck_no = truck_no.replace('/','')
        _logger.info('Truck Number...... %s',truck_no)

        # browser = webdriver.Chrome()
        browser = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
        time.sleep(2)
        browser.get(url)
        _logger.info('URL....... %s',url)
        # browser.find_element_by_xpath("//a[contains(.,'Go to New Portal ')]").click()
        #
        # time.sleep(2)

        if len(browser.window_handles):
            browser.switch_to.window(browser.window_handles[-1])
        time.sleep(1)
        try:
            browser.find_element_by_link_text('e-Registration').click()
        except:
            time.sleep(2)
            browser.find_element_by_link_text('Home').click()
            browser.find_element_by_link_text('e-Registration').click()


        time.sleep(2)
        browser.window_handles
        if len(browser.window_handles):
            browser.switch_to.window(browser.window_handles[-1])

        try:
            error = "Invalid Captcha."
            _logger.info('Inside Try....... ')
            while error:
                time.sleep(2)
                browser.find_element_by_id('userName').clear()

                browser.find_element_by_id('xxZTT9p2wQ').clear()

                browser.find_element_by_xpath("//a[contains(@href,'refreshCaptchaImage()')]").click()
                captcha= self.get_tn_captcha(cr, uid, [case.id], browser, context)
                _logger.info('captcha....... %s',captcha)
                browser.find_element_by_id('userName').clear()

                browser.find_element_by_id('userName').send_keys(username)
                time.sleep(1)
                browser.save_screenshot('/tmp/tnlogin_page1.png')
                browser.find_element_by_id('xxZTT9p2wQ').send_keys(password)
                browser.save_screenshot('/tmp/tnlogin_page2.png')
                # browser.find_element_by_id('captcahText')
                browser.find_element_by_id('captcahText').send_keys(captcha)
                time.sleep(2)

                browser.find_element_by_id('loginSubmit')
                browser.find_element_by_id('loginSubmit').click()
                browser.save_screenshot('/tmp/tncaptcha3.jpg')
                time.sleep(3)
                try:
                    browser.find_element_by_class_name('alert-error')
                    error = browser.find_element_by_class_name('alert-error').text
                    _logger.info('Captcha Error %s',error)
                except:
                    error = ''

            time.sleep(4)
            browser.find_element_by_link_text('Authenticate for e-Services').click()
            time.sleep(2)
            browser.find_element_by_id('taxType').send_keys('Value Added Tax/Central Sales Tax')
            browser.find_element_by_id('transPassword').send_keys('KWSPL@305')
            time.sleep(2)
            browser.find_element_by_name('loginBtn').click()
            time.sleep(2)
            browser.find_element_by_link_text("e-Forms").click()
            time.sleep(1)
            browser.find_element_by_link_text("Online Forms(JJ/KK/LL/MM)").click()
            time.sleep(1)
            browser.find_element_by_id('menuId_452').click()
            browser.find_element_by_id('formType').send_keys('Form JJ')
            browser.find_element_by_id('trnsType').send_keys('Outgoing Declaration')
            time.sleep(2)
            browser.find_element_by_id('submitBtn').click()
            time.sleep(2)
            # to confirm the alert pop up
            # browser.switch_to_alert().accept()
            browser.execute_script("window.confirm = function(msg) { return true; }");
            time.sleep(1)
            browser.find_element_by_name('purOfConsignment').send_keys('Sale/Purchase')
            if case.partner_id and case.partner_id.tin_no:
                browser.find_element_by_name('dealerTinIfAny').send_keys(case.partner_id.tin_no)
            else:
                raise osv.except_osv(_('Warning'),_('Please enter the Consignee Tin Number.'))

            browser.find_element_by_name('dealerName').send_keys(case.partner_id and case.partner_id.name or '')
            browser.find_element_by_name('dealerCity').send_keys(str(case.partner_id.city_id.name) + ', ' + str(case.partner_id.zip))
            time.sleep(1)
            if case.company_id:
                cr.execute("""
                select p2.tin_no
                        from stock_picking st
                        inner join res_company c on c.id = st.company_id
                        inner join res_partner p on p.id = c.partner_id
                        inner join res_partner p2 on p2.parent_id = p.id
                        inner join res_country_state rcs on rcs.id = p2.state_id
                        where st.id = """+str(case.id)+""" and rcs.code = 'TN'

                """)
                comp_tin = [x[0] for x in cr.fetchall()]
                if comp_tin:
                    comp_tin[0]
                else:
                    comp_tin = '33944481896'
                browser.find_element_by_name('jobTinIfAny').send_keys(comp_tin)
            else:
                raise osv.except_osv(_('Warning'),_('Please enter the Company Tin Number.'))

            browser.find_element_by_name('shipCity').send_keys(case.city_id and case.city_id.name or '')
            time.sleep(1)
            browser.find_element_by_name('shipPinCode').send_keys(pincode or zip)
            browser.find_element_by_name('invoiceNo').send_keys(case.name)
            browser.find_element_by_name('invoiceDt').send_keys(inv_date)
            time.sleep(1)
            browser.find_element_by_name('goodsDesc').send_keys('FIREWOOD, EXCLUDING CASURINA AND EUCALYPTUS TIMBER')
            browser.find_element_by_name('cmdtyDesc').send_keys(case.product_id and case.product_id.name or '')
            time.sleep(2)
            _logger.info('Final Page......................')
            browser.find_element_by_name('quantity').send_keys(int(round(qty)))
            time.sleep(1)
            browser.find_element_by_name('unit').send_keys('Metric Ton')
            browser.find_element_by_name('basicPrice').send_keys(int(round(tot_price)))
            time.sleep(2)
            browser.find_element_by_name('taxrate').send_keys('2.0')
            browser.find_element_by_name('vatCstCharges').send_keys(int(round(tax_amount)))
            time.sleep(1)
            browser.find_element_by_name('transportMode').send_keys('By Road')
            browser.find_element_by_name('transportMode').send_keys(Keys.TAB)
            browser.find_element_by_name('vehRegNoIfAny').send_keys(truck_no)

            browser.find_element_by_name('lspName').send_keys(case.transporter_id and case.transporter_id.name or '')
            time.sleep(1)
            browser.find_element_by_id('a_gisInvoiceVehicleDtls').click()
            time.sleep(2)
            browser.find_element_by_id('save').click()
            time.sleep(2)
            dnld_url = 'https://ctd.tn.gov.in/Portal/popUpPDFController.htm?actionCode=gisDownloadForm&refId='
            pdf_lnk = browser.find_element_by_xpath("//a[contains(.,'FJJ')]")
            dnld_url = dnld_url + pdf_lnk.get_attribute('href').split("'")[1]
            jjform = pdf_lnk.text

            time.sleep(2)
            #pdf_lnk.click()
            all_cookies = browser.get_cookies()

            cookies = {}
            s = requests.Session()
            for s_cookie in all_cookies:
                c_name = s_cookie["name"]
                c_value = s_cookie["value"]
                cookies[c_name] = c_value
                #response = s.post(dnld_url, cookies=cookies,verify=False)

            response = s.post(dnld_url, cookies=cookies,verify=False)
            f = open('/tmp/'+case.name.replace('/', '').replace('-', '')+'.pdf','wb')
            f.write(response.content)
            f.close()



            #for creating file
            current_file = '/tmp/'+case.name.replace('/', '').replace('-', '')+'.pdf'
            pdf_data = self.convert_pdf(current_file)
            fp = open(current_file,'rb')
            result = base64.b64encode(fp.read())
            file_name = 'jjform_' + jjform
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
            return jjform

        except Exception as e:
            _logger.info('Error reason %s',e)
            raise osv.except_osv(_('JJ Form Site Is Down'),_('Please Try After Some Time'))

        return True

    def get_tn_captcha(self, cr, uid, ids, browser, context=None):
        if not context:
            context = {}

        time.sleep(1)
        img = browser.find_element_by_name('captchaImage')
        location = img.location
        location.update({'x':int(round(location.get('x'))),
                         'y':int(round(location.get('y'))) })
        size = img.size
        size.update({'width':int(round(size.get('width'))),
                         'height':int(round(size.get('height'))) })


        browser.save_screenshot('/tmp/tncaptcha.jpg')

        image = Image.open('/tmp/tncaptcha.jpg')
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        image = image.crop((left, top, right, bottom))  # defines crop points
        image.save('/tmp/tncaptcha1.jpg', 'jpeg')

        img = Image.open('/tmp/tncaptcha1.jpg')
        img = img.convert("RGBA")
        pixdata = img.load()
        # print "pixdata[x, y]",pixdata

        for y in xrange(img.size[1]):
         for x in xrange(img.size[0]):
             if pixdata[x, y][1] < 50: #136
                pixdata[x, y] = (0, 0, 0, 255)

        img.save("/tmp/tncaptcha1.jpg")

        #   Make the image bigger (needed for OCR)
        #img = img.resize((1000, 500))
        #img.save("/home/serveradmin/Desktop/esugam/new_"+case.driver_name+".jpeg")
        time.sleep(2)
        data = pytesseract.image_to_string(Image.open('/tmp/tncaptcha1.jpg'))
        _logger.info('data inside Captch.......... %s',data)

        return data.replace(' ', '')
        return True

    
    
    
    
    def kw_pay_freight(self, cr, uid, ids, context = None):
#         if context.get('type', '') == 'out':
        today = time.strftime('%Y-%m-%d')
        cur_date = time.strftime('%Y-%m-%d')
        voucher_obj = self.pool.get('account.voucher')
        journal_obj = self.pool.get('account.journal') 
        period_obj = self.pool.get('account.period')
        invoice_obj=self.pool.get('account.invoice')
        acc_obj=self.pool.get('account.account')
        voucher_vals = {}
        voucher_vals1 = {}
        cust = freight = False
        freight_journal=False
        freight_account=False
        g_ids = []
        dummy_id=[]
        inv=[]
        sup_invoice_id=[]
        res1={}
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
            if case.freight_balance>0:
                if case.paying_agent_id:
                    self.write(cr,uid,ids,{'state_id':case.paying_agent_id.state_id.id})
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
                if case.sub_facilitator_id:
                    partner=case.sub_facilitator_id
                else:
                    partner=case.paying_agent_id
                company=case.company_id.id
                if partner:
                    if partner.id not in dummy_id:
                        if case.partner_id.freight or case.gen_freight:
        #                 if case.partner_id.freight or case.paying_agent_id.id in kw_paying_agent:
                            freight=True
                            context.update({'freight':freight})

                            if case.date <= '2017-07-01 00:00:00':
                                company=False
                                cr.execute("select id from res_company where lower(name) like '%logistics%'")
                                company=cr.fetchone()
                                if company:
                                    company=company[0]
                            
                        for ln in case.move_lines:
                            supplier_id = ln.supplier_id
                            j_ids = journal_obj.search(cr, uid, [('name','like','Cash'),('company_id','=',case.company_id.id)])
                            
                            if case.partner_id.freight or case.gen_freight:
      
                                j_ids = journal_obj.search(cr, uid, [('name','like','Cash'),('company_id','=',company)])
                            if j_ids:
                                j_ids=j_ids[0]
                            today=case.delivery_date_function and case.delivery_date_function or today
                            cr.execute("select id from account_period where company_id='"+ str(company) +"'and date_start <= '" + today + "' and date_stop >='" + today + "'")
                            p_ids = cr.fetchone()   
                            if p_ids:
                                p_ids=p_ids[0]
                                p_id = period_obj.browse(cr, uid, p_ids)
                        acc_id = journal_obj.browse(cr, uid, j_ids)
                        freight_journal=journal_obj.search(cr, uid, [('name','like','Freight'),('company_id','=',company)])
                        
                        if freight_journal:
                            freight_journal=freight_journal[0]     
                        else:
                            raise osv.except_osv(_('Warning'),_('Freight Journal Not Found, Cannot Pay Freight'))   
                        
                        freight_account=acc_obj.search(cr, uid, [('name','like','Freight'),('company_id','=',company)])
                        if freight_account:
                            freight_account=freight_account[0]                     
                                   
                        if (user_id.role == 'customer' or user_id.role=='freight') and case.freight_balance >0 and case.state=='done':
                        
    #                         cr.execute("select id from account_journal where company_id='"+ str(company) +"' and lower(name) like '%freight%'")
    #                         freight_journal=cr.fetchone()
    
    
                                
    #                         cr.execute("select id from account_account where lower(name) like '%freight%' and company_id=%s",(str(company),))
    #                         freight_account=cr.fetchone()
    
                           
                            
                            if case.partner_id.pay_freight:
                                voucher_vals = {  'partner_id'       : case.partner_id.id,
                                                  'type'             : 'receipt',
                                                  'amount'           : case.freight_balance,
                                                  'account_id'       : freight_account,
                                                  'journal_id'       : freight_journal,
                                                  'freight'          : True,
                                                  'reference'        : case.name,
                                                  'company_id'       : company,
                                                  'date'             : case.delivery_date_function,
                                                  'period_id'        : p_ids and p_ids or False   
        #                                           'customer_id'      : case.partner_id.id,
                                                  }
                                vid = voucher_obj.create(cr, uid, voucher_vals, context= context)
                                if case.partner_id.freight or case.gen_freight:
                                    context.update({'freight':freight})
                                self.write(cr, uid, ids, {'state':'freight_paid','frtpaid_date':cur_date})
                                
                                #TODO: Added functionlity of posting the entries on 29/04/2014
                                voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                               
                                if case.freight_balance >0 and partner and p_id and case.state=='done':
                                      voucher_vals1 = {               'partner_id'        : partner.id,
                                                                      'type'              : 'payment',
                                                                      'amount'            : case.freight_balance,
                                                                      'account_id'        : freight_account,
                                                                      'journal_id'        : freight_journal,
                                                                      'freight'           : True,
                                                                      'reference'         : case.name,
                                                                      'company_id'        : company,
                                                                      'period_id'         : p_id.id,
                                                                      'date'              : case.delivery_date_function,
                            #                                           'customer_id'      : case.partner_id.id,
                                                                      }
                            
                            else:
                                if case.freight_balance >0 and partner and p_id and case.state=='done' and case.partner_id.representative_id:
                                    if freight:
                                        partner_acc= case.partner_id.representative_id.account_pay and case.partner_id.representative_id.account_pay.id or False
                                    else:
                                        partner_acc = case.partner_id.representative_id.property_account_payable and case.partner_id.representative_id.property_account_payable.id or False                             
                                    voucher_vals1 = {                      'partner_id'       : partner.id,
                                                                          'type'              : 'payment',
                                                                          'amount'            : case.freight_balance,
                                                                          'account_id'        : partner_acc,
                                                                          'journal_id'        : freight_journal,
                                                                          'freight'           : True,
                                                                          'reference'         : case.name,
                                                                          'company_id'        : company,
                                                                          'period_id'         : p_id.id,
                                                                          'date'              : case.delivery_date_function,
                                #                                           'customer_id'      : case.partner_id.id,
                                                                          }                           
                                
                                   
                            if case.freight_charge>0 and case.type=='out':
                                    
                                rep_obj = self.pool.get('ir.actions.report.xml') 
                                res1 = rep_obj.pentaho_report_action(cr, uid, 'Cash Voucher', ids,None,None)
                                
                            cr.execute("SELECT invoice_id FROM supp_delivery_invoice_rel WHERE del_ord_id = %s ",(case.id,))
                            vid = voucher_obj.create(cr, uid, voucher_vals1, context= context)
                            if case.partner_id.freight or case.gen_freight:
                                context.update({'freight':freight})
                            #TODO: Remove the functionlity of posting the entries
                            #voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                            self.write(cr, uid, ids, {'state':'freight_paid','frtpaid_date':cur_date})
     
                        if user_id.role != 'customer' and user_id.role!='freight':
                                                       
                            if case.freight_balance >0 and partner and p_id and case.state=='done':
                                voucher_vals1 = {  'partner_id'       : partner.id,
                                                  'type'              : 'payment',
                                                  'amount'            : case.freight_balance,
                                                  'account_id'        : freight_account,
                                                  'journal_id'        : freight_journal,
                                                  'freight'           : True,
                                                  'reference'         : case.name,
                                                  'company_id'        : company,
                                                  'period_id'         : p_id.id,
                                                  'date'              : case.delivery_date_function and case.delivery_date_function or case.date,
        #                                           'customer_id'      : case.partner_id.id,
                                                  }
                            if case.freight_charge>0 and case.type=='out':
                                
                                    rep_obj = self.pool.get('ir.actions.report.xml') 
                                    res1 = rep_obj.pentaho_report_action(cr, uid, 'Cash Voucher', ids,None,None)
                            
                            cr.execute("SELECT invoice_id FROM supp_delivery_invoice_rel WHERE del_ord_id = %s ",(case.id,))
                            vid = voucher_obj.create(cr, uid, voucher_vals1, context= context)
                            if case.partner_id.freight or case.gen_freight:
                                context.update({'freight':freight})
                            #TODO: Remove the functionlity of posting the entries
                            #voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                            self.write(cr, uid, ids, {'state':'freight_paid','frtpaid_date':cur_date})
                

        
        return res1
    

    
    
    
    
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
                    if case.partner_id.freight or case.gen_freight:
                        #context.update({'freight':freight})
                        
                        company=False
                        cr.execute("select id from res_company where lower(name) like '%logistics%'")
                        company=cr.fetchone()
                        if company:
                             company=int(company[0])
                        
                    for ln in case.move_lines:
                        supplier_id = ln.supplier_id
                        j_ids = journal_obj.search(cr, uid, [('name','like','Cash'),('company_id','=',case.company_id.id)])
                        if case.partner_id.freight or case.gen_freight:
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
                        if case.partner_id.freight or case.gen_freight:
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
                        if case.partner_id.freight or case.gen_freight:
                            context.update({'freight':True})
                        else:
                            context.update({'freight':False})
#                         voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                        self.write(cr, uid, [case.id], {'state':'freight_paid'})
        
        return True
    
    
    
    def deliver(self, cr, uid, ids, context = None):
        move_obj = self.pool.get('stock.move')
        today = time.strftime('%Y-%m-%d')
        move_ids=[]
        freight_balance = 0.0
        state_id = False
        for case in self.browse(cr, uid, ids):
            state_id = case.paying_agent_id.state_id.id
            freight_balance=case.freight_total - case.freight_deduction - case.freight_advance 
            for ln in case.move_lines:
                move_ids.append(ln.id)
                if not ln.product_id.cft:
                    if not ln.unloaded_qty >0 and not ln.rejected_qty >0:
                        raise osv.except_osv(_('Warning'),_('Please Enter the Valid Qty in Unloaded and Rejected'))
                else:
                    if not ln.cft1 >0 and not ln.cft2 >0 and not ln.rejected_qty >0:
                         raise osv.except_osv(_('Warning'),_('Please Enter the Valid CFT Qty and Rejected'))
                     
                if ln.delivery_date > today:
                    raise osv.except_osv(_('Warning'),_('Please Enter the Valid Delivery Date'))
            if case.type=='out':
                cr.execute("select id,name from res_partner where upper(name) like 'I.T.C%'")
                partner=cr.fetchall()
                if (case.partner_id.id in partner or case.partner_id.wc_num) and not case.wc_number:
                    raise osv.except_osv(_('Warning'),_('Please Enter WC Number'))
            
            # Pending Qty Functionality                        
            if case.partner_id.contract_ids:
                qty_pending = 0.00
                from_date = False
                to_date = False
                pick_date = False
                for cntrt in case.partner_id.contract_ids:
                    from_date = cntrt.from_date + ' 00:00:00'
                    from_date = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S')
                    to_date = cntrt.to_date + ' 23:59:59'
                    to_date = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S')
                    pick_date = datetime.strptime(case.date, '%Y-%m-%d %H:%M:%S')
                    if case.product_id.id == cntrt.product_id.id and pick_date >= from_date and pick_date <= to_date:
                        qty_pending = cntrt.qty_pending - case.del_quantity
                        cr.execute("update customer_contracts set qty_pending ="+str(qty_pending)+" where partner_id="+str(case.partner_id.id))
                
        move_obj.action_done(cr, uid, move_ids, context=None)
        
        
            
        return self.write(cr, uid, ids, {'state':'done','freight_balance':freight_balance,'state_id':state_id}, context=context)
    

    def freight_voucher(self,cr,uid,ids,context=None):
        rep_obj = self.pool.get('ir.actions.report.xml')
        res1={}
        rep_obj = self.pool.get('ir.actions.report.xml') 
        res1 = rep_obj.pentaho_report_action(cr, uid, 'Cash Voucher', ids,None,None)
        
        return res1
    
    def print_delivery_challan(self,cr,uid,ids,context=None):
        rep_obj = self.pool.get('ir.actions.report.xml')
        res={}
        res1={}
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment') 
#         pwriter = PdfFileWriter()
#         os.makedirs('/home/serveradmin/Desktop/temp')

        for case in self.browse(cr, uid, ids):
            if case.partner_id and case.partner_id.sup_num == 'C0036':
                res = rep_obj.pentaho_report_action(cr, uid, 'Seshasayee Proforma Invoice', ids,None,None)
            if case.partner_id and case.partner_id.sup_num == 'C0037':
                res = rep_obj.pentaho_report_action(cr, uid, 'TNP GST Delivery Challan', ids,None,None)
            else:
                res = rep_obj.pentaho_report_action(cr, uid, 'GST Delivery Challan', ids,None,None)

        # Commented as per the GST Changes
        # res = rep_obj.pentaho_report_action(cr, uid, 'Proforma Invoice', ids,None,None)
        # for case in self.browse(cr,uid,ids):
        #     if case.partner_id.dc_report == True:
        #         res = rep_obj.pentaho_report_action(cr, uid, 'DC', ids,None,None)
    

        return res


    def print_dc_lr(self,cr,uid,ids,context=None):
        rep_obj = self.pool.get('ir.actions.report.xml')
        res={}
        res1={}
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment') 
#         pwriter = PdfFileWriter()
#         os.makedirs('/home/serveradmin/Desktop/temp')

        for case in self.browse(cr,uid,ids):
            if case.dc_report:
                res = rep_obj.pentaho_report_action(cr, uid, 'DC', ids,None,None)

                        
            cr.execute("select id,name from res_partner where upper(name) like 'I.T.C%'")
            partner=cr.fetchall()
            if partner:
                partner=[d[0] for d in partner]
                if (case.partner_id.id in partner) or case.report:
                    res = rep_obj.pentaho_report_action(cr, uid, 'DC-LR For I.T.C', ids,None,None)
                else:   
#                     raise osv.except_osv(_('Warning'),_('Report Is Specifically For The Customer I.T.C Limited')% (case.partner_id.name,))
                    raise osv.except_osv(_('Warning'),_('Report Is Specifically For The Customer I.T.C Limited'))
        

        return res    
    
    
    
    def print_freight_advice(self,cr,uid,ids,context=None):
        rep_obj = self.pool.get('ir.actions.report.xml')
        res={}
        partner=False
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment')

        for case in self.browse(cr,uid,ids):
            cr.execute("select id from res_partner where lower(name) like '%grasim%'")
            partner=cr.fetchall()
            if partner:
                partner=[d[0] for d in partner]
                if case.partner_id.id in partner:
                    res = rep_obj.pentaho_report_action(cr, uid, 'Freight Advice For Grasim', ids,None,None)
                else:   
                    res = rep_obj.pentaho_report_action(cr, uid, 'Freight Advice', ids,None,None)
        return res
        
    def print_gst_dc(self,cr,uid,ids,context=None):
        rep_obj = self.pool.get('ir.actions.report.xml')
        res={}
        partner=False
        data = {}
        data2 ={}
        attachment_obj = self.pool.get('ir.attachment')

        for case in self.browse(cr,uid,ids):
            res = rep_obj.pentaho_report_action(cr, uid, 'GST Invoice', ids,None,None)
        return res


    
    

    # To Create customer and Paying agents Refund
    def create_refund(self, cr, uid, ids,type,case, ln,price,context=None):
        if not context:
            context={}
        inv_obj = self.pool.get('account.invoice')
        inv_ln_obj = self.pool.get('account.invoice.line')
        journal_obj = self.pool.get('account.journal')
        prod_obj =self.pool.get('kw.product.price')
        refund_vals = {}
        refund_ln_vals = {}
        # to calculate the price from deduction_amount
        price=(ln.deduction_amt/ln.rejected_qty)
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
                       'origin':case.name,
                       'branch_state':case.partner_id.state_id.id
                       }
        refund_vals.update(inv_obj.onchange_partner_id(cr, uid, ids, type, partner_id)['value'])
        refund_ln_vals.update(inv_ln_obj.product_id_change(cr, uid, ids, ln.product_id.id, ln.product_uom.id, qty=0, name='', type=type, partner_id=partner_id, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None))
        refund_ln_vals.update( {'product_id':ln.product_id.id, 
            'name':ln.name, 
            'quantity':ln.rejected_qty, 
            'price_unit':price, 
            'uos_id':ln.product_uom.id})
        context.update({
                       'acc_id':refund_ln_vals['value']['account_id']
                       })

        # print "refund_vals...",refund_vals
        # print "Refund Linessss", refund_ln_vals
        if not refund_ln_vals.get('account_id'):
            refund_ln_vals.update({'account_id': refund_ln_vals['value']['account_id']})
            #print "Refund Linessss1111", refund_ln_vals
        refund_vals.update({'invoice_line':[(0, 0, refund_ln_vals)]})
        if type =='in_refund':
            refund_vals.update({'supp_delivery_orders_ids': [(6, 0, [case.id])]}),
        else:
            refund_vals.update({'delivery_orders_ids': [(6, 0, [case.id])]}),
         
        inv_obj.create(cr, uid, refund_vals,context=context)

    # Mail,IF no product rate while creating facilitator invoice by schedular
    def send_mail_prod_rate(self,cr,uid,ids,context=None):
        res={}
        if not context:
            context = {}
        state = context.get('state',False)
        print 'context',context
        type = context.get('type','')
        partners = ''
        mail_obj = self.pool.get('mail.mail')
        partner_obj = self.pool.get('res.partner')
        email_obj = self.pool.get('email.template')
        prod_obj = self.pool.get('product.product')
        if type == 'in':
            template = self.pool.get('ir.model.data').get_object(cr, uid,'kingswood', 'kw_send_mail_prod_rate_ship')
        else:
            template = self.pool.get('ir.model.data').get_object(cr, uid,'kingswood', 'kw_send_mail_prod_rate')
        assert template._name == 'email.template'
        
        for case in self.browse(cr,uid,ids):
            
            cr.execute(""" select distinct rp.email 
                            from res_groups_users_rel gu 
                            inner join res_groups g on g.id = gu.gid
                            inner join res_users ru on ru.id = gu.uid
                            inner join res_partner rp on rp.id = ru.partner_id  
                            where g.name = 'KW_Admin' and rp.email is not null""")
            for p in cr.fetchall():
#                 p = partner_obj.browse(cr, uid,p[0])
                partners += (p and p[0] or "") + ","
            if partners:
#                 print partners
                email_obj.write(cr, uid, [template.id], {'email_to':partners[0:-1]})
                        
            mail_id = self.pool.get('email.template').send_mail(cr, uid, template.id, case.id, True, context=context)
            mail_state = mail_obj.read(cr, uid, mail_id, ['state'], context=context)
            if mail_state and mail_state['state'] == 'exception':
                raise osv.except_osv(_("Cannot send email(date): no outgoing email server configured.\nYou can configure it under Settings/General Settings."), case.partner_id.name)
            prod_obj.write(cr,uid,[case.product_id.id],{'product_rate':True,'dc_state':state})
#             print "--------------STOP No Rate__________",case.name
        return True 

    def get_supplier_rate(self, cr, uid, ids, freight, context = None):
        if not context:
            context={}
        schedular = context.get('schedular',False)
        today = time.strftime('%Y-%m-%d')
        schedular_state = context.get('state',False)
        stock_in = self.pool.get ('stock.picking.in')
        prod_obj = self.pool.get('product.product')
        kwprod_obj=self.pool.get('kw.product.price')
        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        kwprod_obj=self.pool.get('kw.product.price')
        sup_freight_ids=prod_obj.search(cr, uid, [('name_template','=','Freight')])
        partner_id={}
        h_price={}
        order_id = []
        back_date = False
        cr.execute("select id from res_company where lower(name) not like '%logistics%'")
        company1=cr.fetchone()
        if company1:
            company1=company1[0]
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
        
#        cr.execute("SELECT del_ord_id FROM supp_delivery_invoice_rel WHERE del_ord_id IN %s ",(tuple(ids),))
        if ids:
            cr.execute("""SELECT dr.invoice_id FROM supp_delivery_invoice_rel dr inner 
            join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id  IN %s and ac.state <>'cancel'""",(tuple(ids),))    
            
            order_id = [x[0] for x in cr.fetchall()]
#         print 'ids',ids
        if order_id:
#             sup_inv_id = inv_obj.search(cr,uid,[('id','in',order_id),('state','!=','cancel')])
#             if sup_inv_id:
            raise osv.except_osv(_('Warning'),_('Invoice Already Created for the Selected Delivery Order'))

        #to fetch the supplier where name != kingswood
        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
        kw_paying_agent=cr.fetchall()
        kw_paying_agent=zip(*kw_paying_agent)[0]
          
        ids = self.search(cr,uid,[('id','in',ids)],order='paying_agent_id,id')
        
#         IF no product rate while creating facilitator invoice by schedular
        if schedular:
            
            for stock in self.browse(cr, uid, ids):
                stock_type = stock.type
                back_date = True
                price1 = 0.0
                if stock.paying_agent_id.id not in kw_paying_agent:
                    for line in stock.move_lines:
                        if stock.type == 'out':
#                             prod_obj.write(cr,uid,[line.product_id.id],{'dc_state':schedular_state})
                            cr.execute(""" 
                                                            select 
                                                                    kw.id,
                                                                    kw.product_price,
                                                                    kw.sub_total,
                                                                    kw.handling_charge,
                                                                    kw.transport_price 
                                                                from product_supplierinfo ps
                                                                inner join kw_product_price kw on ps.id = kw.supp_info_id
                                                                and ps.product_id = %s
                                                                and ps.customer_id = %s
                                                                and ef_date <='%s'
                                                                and ps.name = %s
                                                                order by ef_date desc limit 1
                                                            """ % (line.product_id.id, stock.partner_id.id, line.delivery_date,stock.paying_agent_id.id ))
                            prod_ids = [x[0] for x in cr.fetchall()]
                        elif stock.type == 'in':
                            location = line.location_dest_id.id

                            cr.execute("""select 
                                    kw.id,
                                    kw.product_price,
                                    kw.sub_total,
                                    kw.handling_charge,
                                    kw.transport_price 
                                from product_supplierinfo ps
                                inner join kw_product_price kw on ps.id = kw.supp_info_id
                                and ps.product_id = %s
                                and ps.depot = %s
                                and ef_date <='%s'
                                and ps.name = %s
                                order by ef_date desc limit 1""" % (line.product_id.id, location,stock.date,stock.partner_id.id ))
                             
                            prod_ids = [x[0] for x in cr.fetchall()]
                        
                        
                    if stock.type == 'out':
                        for j in kwprod_obj.browse(cr,uid,prod_ids):
                            if stock.partner_id.freight or stock.gen_freight:
                                price1=j.product_price
                            else:
                                price1 = j.sub_total  
                    else:
                        for js in kwprod_obj.browse(cr,uid,prod_ids):
                            price1 = js.product_price + js.transport_price
                            freight_price = js.transport_price                        
                             
                    if price1 == 0 and stock.paying_agent_id.id not in kw_paying_agent:       
                        context.update({'DC':stock.name,'product':line.product_id.name,'date':line.delivery_date,'return_inv':True,'type':stock.type})
#                         print "Failed",stock.name
                        self.send_mail_prod_rate(cr,uid,[stock.id],context)
                        run_schedular = False
                        return False
        return True
      
    def get_supplier_invoice(self, cr, uid, ids, freight, context = None):
        if not context:
            context={}
        schedular = context.get('schedular',False)
        today = time.strftime('%Y-%m-%d')
        schedular_state = context.get('state',False)
        stock_in = self.pool.get ('stock.picking.in')
        sup_invoice=False
        company_id=False
        inv1 = False
        inv2 = False
        inv3 = False 
        inv_hc = False   
        run_schedular = True
        invoices = []    
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
        cft_vals={}
        cft_freight_vals={}
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
        cft=False
        sup_parent_id= price1 = 0
        s_parent_id=False
        handling_price = 0.0
        stock_type = 'out'
        handling_vals['quantity']=0.00
        sup_freight_val['price_unit']=0.000
        handling_vals['price_unit'] = 0
        supplier_freight_val['price_unit']=0.000
        freight_price=0.000
        tx_ids = []
        prod_obj = self.pool.get('product.product')
        kwprod_obj=self.pool.get('kw.product.price')
        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        kwprod_obj=self.pool.get('kw.product.price')
        sup_freight_ids=prod_obj.search(cr, uid, [('name_template','=','Freight')])
        partner_id={}
        h_price={}
        order_id = []
        back_date = False
        fre_company = False
        cr.execute("select id from res_company where lower(name) not like '%logistics%'")
        company1=cr.fetchone()
        if company1:
            company1=company1[0]
        #to fetch the Logistic company_id
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company=cr.fetchone()
        if company:
            company=company[0]
            fre_company = company
        hc_expense_sup = False
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
        
#        cr.execute("SELECT del_ord_id FROM supp_delivery_invoice_rel WHERE del_ord_id IN %s ",(tuple(ids),))
        if ids:
            cr.execute("""SELECT dr.invoice_id FROM supp_delivery_invoice_rel dr inner 
            join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id  IN %s and ac.state <>'cancel'""",(tuple(ids),))    
            
            order_id = [x[0] for x in cr.fetchall()]
#         print 'ids',ids
        if order_id:
#             sup_inv_id = inv_obj.search(cr,uid,[('id','in',order_id),('state','!=','cancel')])
#             if sup_inv_id:
            raise osv.except_osv(_('Warning'),_('Invoice Already Created for the Selected Delivery Order'))

        #to fetch the supplier where name != kingswood
        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
        kw_paying_agent=cr.fetchall()
        kw_paying_agent=zip(*kw_paying_agent)[0]
          
        ids = self.search(cr,uid,[('id','in',ids)],order='paying_agent_id,id')
        
#         IF no product rate while creating facilitator invoice by schedular
#         if schedular:
            
#             for stock in self.browse(cr, uid, ids):
#                 stock_type = stock.type
#                 back_date = True
#                 price1 = 0.0
#                 if stock.paying_agent_id.id not in kw_paying_agent:
#                     for line in stock.move_lines:
#                         if stock.type == 'out':
#                             prod_obj.write(cr,uid,[line.product_id.id],{'dc_state':schedular_state})
#                             cr.execute(""" 
#                                                             select 
#                                                                     kw.id,
#                                                                     kw.product_price,
#                                                                     kw.sub_total,
#                                                                     kw.handling_charge,
#                                                                     kw.transport_price 
#                                                                 from product_supplierinfo ps
#                                                                 inner join kw_product_price kw on ps.id = kw.supp_info_id
#                                                                 and ps.product_id = %s
#                                                                 and ps.customer_id = %s
#                                                                 and ef_date <='%s'
#                                                                 and ps.name = %s
#                                                                 order by ef_date desc limit 1
#                                                             """ % (line.product_id.id, stock.partner_id.id, line.delivery_date,stock.paying_agent_id.id ))
#                             prod_ids = [x[0] for x in cr.fetchall()]
#                         elif stock.type == 'in':
#                             location = line.location_dest_id.id
# 
#                             cr.execute("""select 
#                                     kw.id,
#                                     kw.product_price,
#                                     kw.sub_total,
#                                     kw.handling_charge,
#                                     kw.transport_price 
#                                 from product_supplierinfo ps
#                                 inner join kw_product_price kw on ps.id = kw.supp_info_id
#                                 and ps.product_id = %s
#                                 and ps.depot = %s
#                                 and ef_date <='%s'
#                                 and ps.name = %s
#                                 order by ef_date desc limit 1""" % (line.product_id.id, location,stock.date,stock.partner_id.id ))
#                              
#                             prod_ids = [x[0] for x in cr.fetchall()]
#                         
#                         
#                     if stock.type == 'out':
#                         for j in kwprod_obj.browse(cr,uid,prod_ids):
#                             if stock.partner_id.freight or stock.gen_freight:
#                                 price1=j.product_price
#                             else:
#                                 price1 = j.sub_total  
#                     else:
#                         for js in kwprod_obj.browse(cr,uid,prod_ids):
#                             price1 = js.product_price + js.transport_price
#                             freight_price = js.transport_price                        
#                              
#                     if price1 == 0 and stock.paying_agent_id.id not in kw_paying_agent:       
#                         context.update({'DC':stock.name,'product':line.product_id.name,'date':line.delivery_date,'return_inv':True,'type':stock.type})
#                         print "Failed",stock.name
#                         self.send_mail_prod_rate(cr,uid,[stock.id],context)
#                         run_schedular = False
#                         return False
                        
        if run_schedular and stock_type == 'in' :
           stock_in.get_invoice(cr,uid,ids,False,context)
                                                                     
        if run_schedular and stock_type == 'out':           
            for case in self.browse(cr, uid, ids):
                 cr.execute("select id from stock_picking where delivery_date_function >= '2017-07-01 00:00:00' and id ="+str(case.id))
                 pk_ids = [x[0] for x in cr.fetchall()]
                 if pk_ids:
                     sup_freight_ids=prod_obj.search(cr, uid, [('name_template','=','HC')])
                 else:
                     sup_freight_ids=prod_obj.search(cr, uid, [('name_template','=','Freight')])
                 # Updating Tax
                 if pk_ids:
                     _logger.info('Current DC==========================> %s',case.id)
                     if case.state_id.id == case.paying_agent_id.state_id.id:
                        cr.execute("select id from account_tax where gst_categ='intra' ")
                        intra_tax_id= [x[0] for x in cr.fetchall()]
                        intra_tax_id = tuple(intra_tax_id)
                        if intra_tax_id:
                            cr.execute("select tax_id from product_supplier_taxes_rel where prod_id=%s and tax_id in %s",(case.product_id.id,intra_tax_id))
                            tx_ids = [x[0] for x in cr.fetchall()]
                        else:
                            raise osv.except_osv(_('Warning'),_('Map proper Taxes for Intra State'))

                     else:
                        cr.execute("select id from account_tax where gst_categ='inter' ")
                        inter_tax_id= [x[0] for x in cr.fetchall()]
                        inter_tax_id = tuple(inter_tax_id)
                        if inter_tax_id:
                            cr.execute("select tax_id from product_supplier_taxes_rel where prod_id=%s and tax_id in %s",(case.product_id.id,inter_tax_id))
                            tx_ids = [x[0] for x in cr.fetchall()]
                        else:
                            raise osv.except_osv(_('Warning'),_('Map proper Taxes for Inter State'))
                     # _logger.info('Supplier Tax Ids==========================> %s',tx_ids)


                 stock_type = case.type
                 print case.name
                 journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase'),('company_id','=',case.company_id.id)])[0]
                 if case.state not in ('done','freight_paid'):
                     raise osv.except_osv(_('Warning'),_('Delivery Order "%s" Should Be In Delivered State')% (case.name,))
                     
                 kw_paying_agent_id=case.paying_agent_id.id
                 if case.partner_id.freight or case.gen_freight :
                    freight=True
                    company = company
                 else:
                    freight=False
                    company = case.company_id.id
                 if case.type=="out":
                     type = case.type
                     loaded_qty = 0
                     rejected_qty = 0
                     frt=0
    #                  handling_vals['quantity']=0
                     for ln in case.move_lines:
                         cft_quantity=0
                         cft=ln.product_id.cft
                         if cft:
                            cft_quantity=ln.cft1+ln.cft2
                         cr.execute("select substr(value_reference,17)::integer from ir_property where name =  'property_account_expense_categ' and res_id = 'product.category,' || %s", (ln.product_id.categ_id.id, ))
                         account_expense_sup = cr.fetchall()
                         if account_expense_sup:
                             hc_expense_sup = account_expense_sup[0]
                         if 'Firewood' in str(ln.product_id.name):
                             
                            if case.paying_agent_id.state_id.code == "KA":
                                account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of FW-Local')])
                                   
                            if case.paying_agent_id.state_id.code == "TN":
                                account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of FW-Interstate-TN')])
                            
                            if case.paying_agent_id.state_id.code == "AP":
                                    account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of FW-Interstate-AP')]) 
                         
                         else:
                            if case.paying_agent_id.state_id.code == "KA":
                               if case.partner_id.state_id.id == case.paying_agent_id.state_id.id:
                                   account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Local')])
                               
                               if case.partner_id.state_id.id != case.paying_agent_id.state_id.id:
                                   account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Interstate')])
                                        
                            if case.paying_agent_id.state_id.code == "TN":
                                if case.partner_id.state_id.id == case.paying_agent_id.state_id.id:
                                    account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Local-TN')])
                                else: 
                                    account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Interstate-TN')])
                            
                            if case.paying_agent_id.state_id.code == "AP":
                                if case.partner_id.state_id.id == case.paying_agent_id.state_id.id:
                                    account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Local-AP')])
                                else: 
                                    account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Interstate-AP')]) 
                        
#                             if case.partner_id.state_id.code == "AP":
#                                if case.partner_id.state_id.id == case.paying_agent_id.state_id.id:
#                                    account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Local-AP')])
#                                if case.partner_id.state_id.id != case.paying_agent_id.state_id.id:
#                                    account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Interstate-AP')])
  
                           
                         if account_expense_sup:
                            vals['account_id'] = account_expense_sup[0]
                         if hc_expense_sup:
                             handling_vals['account_id']=hc_expense_sup[0]
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
                             if cft:
                                 sup_freight_val['quantity']=cft_quantity                           
                             sup_freight_val['uos_id']=ft.uom_id.id
                             sup_freight_val['state'] = 'done' 
                              
                              
                             #for Supplier invoice Vals
                             vals['product_id'] = ln.product_id.id
                             vals['name'] = ln.name
                             vals['quantity'] = ln.unloaded_qty
                             if cft:
                                 vals['quantity']=cft_quantity      
                                               
                             vals['rejected_qty'] = ln.rejected_qty
                             vals['uos_id'] = ln.product_uom.id    
                             vals['price_unit'] = 0
                             vals['move_line_id'] = ln.id
                             vals['invoice_line_tax_id'] = [(6, 0,tx_ids)]
                              
                                  
                            #for supplier handling invoice vals
                             handling_vals['product_id']=frt
                             handling_vals['name'] = f_name
                             if handling_vals['quantity'] ==0:
                                handling_vals['quantity'] = ln.unloaded_qty
                                if cft:
                                    handling_vals['quantity']=cft_quantity                               
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
                                             if case.partner_id.freight or case.gen_freight:
                                                 price1=j.product_price
                                             else:
                                                 price1 = j.sub_total or (j.product_price +j.transport_price)
                                             freight_price = j.transport_price
                                             #handling_price = j.handling_charge
                                             partner = j.partner_id
                                             partner_name = j.partner_id.name
                                             vals['price_unit'] = price1
                                             sup_freight_val['price_unit'] = freight_price
                                             handling_vals['price_unit'] = j.handling_charge or 0
                                             qty = ln.unloaded_qty
    #                                          i.name.name
                                             cr.execute("update stock_picking set sup_invoice=True where id=%s ",(case.id,))
                                             
                                         
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
                                                comp_partner = (partner.id,company)
                                                s_id.update({comp_partner:s_parent_id})
                                            
                                             #CHECK THE CODE
                                             if ln.rejected_qty > 0 and ln.deduction_amt > 0:
                                                 if price1 > 0:
                                                    refund = self.create_refund(cr, uid, ids,'in_refund',case, ln,price1,context=context)
                                                    # for creating customer invoice
                                                    self.create_refund(cr, uid, ids,'out_refund',case, ln,price1,context=context)
                                                    if refund: 
                                                        invoices.append(refund)
                                                                                
                             if ln.location_id.name == "Stock" and price1==0:
                                 price1=1
                             if vals['price_unit']==0 and case.paying_agent_id.id not in kw_paying_agent:
                                 if not schedular:
                                     raise osv.except_osv(_('Warning'),_('Check Goods Price, Selected Supplier "%s" Do Not Have Rate for "%s" In The Goods Master')% (case.paying_agent_id.name,ln.product_id.name ))
                                 else:
                                     print "schedular Failed"
                             #check for the key for supplier Invoices
                             _logger.info('Before the Key Supplier Invoice Current DC==========================> %s',case.id)
                             if tx_ids:
                                cr.execute("select gst_categ, amount from account_tax where id in  %s ",(tuple(tx_ids),))
                                tx = cr.dictfetchall()[0]
                             if pk_ids and tx:
                                 if case.sub_facilitator_id:
                                    supp_key = case.sub_facilitator_id.id,case.partner_id.freight or case.gen_freight,ln.delivery_date or case.sub_facilitator_id.id,tx.get('gst_categ')+str(tx.get('amount'))
                                    freight_key = case.sub_facilitator_id.id, case.partner_id.id,freight_price,ln.delivery_date
                                    product_key =case.sub_facilitator_id.id,ln.product_id.id,ln.price_unit
                                 else:
                                    supp_key = case.paying_agent_id.id,case.partner_id.freight or case.gen_freight,ln.delivery_date or case.paying_agent_id.id,tx.get('gst_categ')+str(tx.get('amount'))
                                    freight_key = case.paying_agent_id.id, case.partner_id.id,freight_price,ln.delivery_date
                                    product_key =case.paying_agent_id.id,ln.product_id.id,ln.price_unit
                             else:
                                 supp_key = case.paying_agent_id.id,case.partner_id.freight or case.gen_freight,ln.delivery_date or case.paying_agent_id.id
                                 freight_key = case.paying_agent_id.id, case.partner_id.id,freight_price,ln.delivery_date
                                 product_key =case.paying_agent_id.id,ln.product_id.id,ln.price_unit
                             print "supp_key....................",supp_key
                             #Handling Invoice Key
                             if handling_vals['price_unit'] >0 and partner:
                            #added Handling price to handling key[If Handling price differs then create new invoice]                          
                                 handling_key=ln.product_id.id,partner,case.paying_agent_id.id,handling_vals['price_unit'],freight,ln.delivery_date
                             
                             
                            
                              #grouping the supplier Handling invoices based on product_id and partner
    #                          print "facilitator",case.paying_agent_id.id," partner_name",partner_name,"-prince",ln.unloaded_qty
                             
                             cft_vals=vals.copy()
                             cft_freight_vals=sup_freight_val.copy()
                             handling_ft=False
                             if partner and handling_vals['price_unit'] >0 and case.paying_agent_id.id not in kw_paying_agent:
                                 if handling_key not in handling_group :
                                     handling_vals['quantity'] = ln.unloaded_qty
                                     if cft:
                                        handling_vals['quantity']=cft_quantity                                 
                                     handling_del_orders[handling_key]=[case.id]
                                     if freight:
                                         handling_ft=True
                                         journal=journal_id_l
                                         company_id=company
                                     else:
                                         handling_ft=False
                                         journal=journal_id
                                         company_id=company1
                                     a_id=s_id[(partner.id,company)]
                                         
                                     
                                     handling_group[handling_key]={
                                                                        'partner_id'     : partner.id,
                                                                        'date_invoice'   : ln.delivery_date,
                                                                        'type'           : 'in_invoice',
                                                                         'journal_id'    : journal,
                                                                         'account_id'    : a_id,
                                                                          'freight'      : handling_ft,
                                                                          'company_id'   : company_id,
                                                                          'branch_state' : partner.state_id.id,
    #                                                                        'date_invoice': today,
                                                                          'back_date': back_date
                                                                    }
                                     
                                     
                                     handling_invoices_lines[handling_key] = [(handling_vals.copy())]
                                 else:
                                      #handling_vals['quantity'] += ln.unloaded_qty
                                      
                                      if cft:
                                          handling_invoices_lines[handling_key][0]['quantity']+=cft_quantity  
                                      else:
                                          handling_invoices_lines[handling_key][0]['quantity'] += ln.unloaded_qty                                
                                      #handling_invoices_lines[handling_key] = [(handling_vals.copy())]
                                      handling_del_orders[handling_key].append(case.id)   
                             
                            #grouping the supplier invoices based on supplier,freight, and freight_price  
                             if ln.location_id.name != "Stock":
                                 if supp_key not in supp_inv_group :
                                     supp_del_orders[supp_key] =[case.id]
                                     supp_inv_group[supp_key] = {
                                                                 'partner_id'     : case.sub_facilitator_id and case.sub_facilitator_id.id or case.paying_agent_id.id,
                                                                 'date_invoice'   : ln.delivery_date,
                                                                 'type'           :   'in_invoice',
                                                                 'journal_id'     : journal_id,
                                                                'branch_state'    : case.paying_agent_id.state_id.id,
                                                                'back_date'       : back_date,
                                                               }
                                     supp_invoice_lines[supp_key] = [(vals.copy())]
                                     if not case.partner_id.freight and not case.gen_freight:
                                         supp_invoice_lines[supp_key][0]['price_unit'] += freight_price
                                     if case.partner_id.freight and freight_price >0: 
                                         freight_vals[supp_key] = [(sup_freight_val.copy())]
                                  
                                 else:
                                     if not case.partner_id.freight and not case.gen_freight:
                                         vals['price_unit'] += freight_price
                                     supp_invoice_lines[supp_key].append((vals.copy()))
                                     supp_del_orders[supp_key].append(case.id)
                                     if case.partner_id.freight or case.gen_freight:
                                         if freight_price >0: 
                                             freight_vals[supp_key] = [(sup_freight_val.copy())]
                                     
                                  
                           
                             # for creating freight invoices based on supplier,customer and freight price 
                             if ln.location_id.name != "Stock":
                                 if freight_key not in freight_inv_group:
                                     if case.partner_id.freight or case.gen_freight:
                                         freight_del_orders[freight_key] = [case.id]
                                         freight_inv_group[freight_key] = {'partner_id'   : case.sub_facilitator_id and case.sub_facilitator_id.id or case.paying_agent_id.id,
                                                              'date_invoice': ln.delivery_date,
                                                              'type':   'in_invoice',
                                                              'journal_id' : journal_id_l,
                                                              'account_id':sup_parent_id,
                                                               'freight':True,
                                                               'branch_state'    : case.paying_agent_id.state_id.id,
                                                               'back_date': back_date
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
                                     if cft:
                                          supplier_freight_val['quantity']=cft_quantity  
                                     else:                                
                                          supplier_freight_val['quantity'] = ln.unloaded_qty
                                     supplier_freight_val['uos_id']=ft.uom_id.id
                                     supplier_freight_val['state'] = 'done' 
                                     supplier_freight_val['price_unit'] = case.freight_total
                                      
                                 supplier_freight_del_orders.append(case.id)
                                  
                                 if kw_paying_agent_id in kw_paying_agent and case.transporter_id:
                                     if case.transporter_id.id not in paying_agent and ln.location_id.usage=='internal':
                                         state_id = False
                                         if case.transporter_id:
                                             state_id = case.transporter_id.state_id.id
                                         supp_fr_group = {'partner_id'   : case.transporter_id.id,
                                                                             'date_invoice': ln.delivery_date,
                                                                             'type':   'in_invoice',
                                                                             'journal_id' : journal_id_l,
                                                                             'branch_state'    : state_id,
                                                                             'back_date': back_date
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
                                                                      'back_date': back_date
                                                                      })
                                                 
                                                 sup_inv_val_c.update({'freight':True}) 
                                                 inv1=inv_obj.create(cr, uid, sup_inv_val_c,context)
                                                 if inv1:
                                                     invoices.append(inv1)
             #for grouping the product id_price and product_id for supplier goods invoice lines
            
            if type=="out":
                supp_data = {}
                freight_data = {}
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
                            if not f_key in freight_data:
                                freight_data[f_key] = {freight_product_key:[(0,0,f)]}
                            else:
                                freight_data[f_key].update({freight_product_key:[(0,0,f)]})
                            freight_groups.append(freight_product_key)
                            
                        else:
                            freight_data[f_key][freight_product_key][0][2]['price_unit'] =f['price_unit']
                            freight_data[f_key][freight_product_key][0][2]['quantity'] +=f['quantity']
                
                  #for separating the freight_product_keys from vals
                for x in freight_data:
                    for i in freight_data[x].values():
                        if x in freight_line_vals:
                            freight_line_vals[x].append(i[0])
                        else:
                            freight_line_vals[x]= i
                
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
                                                          
                                             'invoice_line'             : line_vals[inv],
                                             'supp_delivery_orders_ids' : [(6, 0, supp_del_orders[inv])],

                                         })
                        sup_inv_vals.update({
        #                                                      
                                                              'journal_id' : journal_id,'back_date': back_date
                                                              })
                        inv2=inv_obj.create(cr, uid, sup_inv_vals,context=context) 
                        if inv2:
                            inv_obj.button_reset_taxes(cr, uid, [inv2], {})
                            invoices.append(inv2) 
                 #for creating supplier freight invoices
                for freight_inv in freight_line_vals:
                    price_unit=0
                    facilitator=[]
                    freight_inv_vals.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_invoice', freight_inv_group[freight_inv]['partner_id'])['value'])
                    freight_inv_vals.update(freight_inv_group[freight_inv])
                    freight_inv_vals.update({
                                                                         
                                                'supp_delivery_orders_ids'  : [(6, 0, freight_del_orders[freight_inv])],
                                                'invoice_line'              : freight_line_vals[freight_inv],
                                             })
                   
                    if freight_line_vals[freight_inv][0][2]['price_unit']>0:
    #                     if sup_freight_val['price_unit']>0:
    #                     if kw_paying_agent_id not in kw_paying_agent:
                        if freight_inv_group[freight_inv]['partner_id'] not in kw_paying_agent:
                            if freight_inv_group[freight_inv]['freight']:
                                if company and sup_parent_id:
                                    #updating the freight company to invoice
                                    freight_inv_vals.update({'company_id':company})
                                    if fre_company:
                                        freight_inv_vals.update({'company_id':fre_company})
                                        
                                    freight_inv_vals.update({
        #                                                       'account_id':sup_parent_id,
                                                              'journal_id' : journal_id_l,
                                                              'back_date': back_date
                                                              })
                                    
                                    freight_inv_vals.update({'freight':True}) 
                                 #to create freight invoice for supplier
                                    inv3=inv_obj.create(cr, uid, freight_inv_vals,context=context)
                                    if inv3:
                                        invoices.append(inv3)
                context.update({'invoices':invoices})      
                for handling_inv in handling_invoices_lines:
                    handling_invoices.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_invoice', handling_group[handling_inv]['partner_id'])['value'])
                    handling_invoices.update(handling_group[handling_inv])
                    handling_invoices.update({
                                                                        
                                                'supp_delivery_orders_ids'  : [(6, 0, handling_del_orders[handling_inv])],
                                                'invoice_line'              : [(0,0,handling_invoices_lines[handling_inv][0])],
                                             })
                      
                 
                    if s_parent_id:
                         company = company1
                         if handling_group[handling_inv]['freight']==True and company:                  
                             company = fre_company
                         handling_invoices.update({'company_id':company}) 
                         #to create HC invoice for supplier
                         inv_hc=inv_obj.create(cr, uid, handling_invoices,context=context) 
                     
            return True

   
   
    # To Create customer
    def get_invoice(self,cr,uid,ids,freight,context=None):
        today = time.strftime('%Y-%m-%d')
        if context ==  None:
            context = {} 
        quantity=0.0
        journal_obj = self.pool.get('account.journal')
        product_groups = {}
        product_cpf = {}
        delivery_orders = {}
        date_groups={}
        inv1=False
        inv2=False
        inv3=False
        c_acc_id = False
        inv_obj = self.pool.get('account.invoice')
        inv_groups = {} 
        freight_group= {}
        freight_cpf={}
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
        branch_state_id=False
        cft=False
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company=cr.fetchone()
        if company:
            company=company[0]

        cr.execute("select id from res_country_state where lower(name) like 'karnataka%'")
        branch_state_id=cr.fetchone()
        if branch_state_id:
            branch_state_id=branch_state_id[0]
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
            if case.partner_id.freight or case.gen_freight:
                freight=True
            cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
            kw_paying_agent=cr.fetchall()
            kw_paying_agent=zip(*kw_paying_agent)[0]   
            kw_paying_agent_id=case.paying_agent_id.id
            
#                 continue
#         print ids
        #TO check whether the invoices has been created for selected delivery orders
        
#         cr.execute("SELECT del_ord_id FROM delivery_invoice_rel WHERE del_ord_id IN %s ",(tuple(ids),))
        cr.execute("""SELECT dr.invoice_id FROM delivery_invoice_rel dr inner 
        join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id  IN %s and ac.type <> 'out_refund' and ac.state <>'cancel'""",(tuple(ids),))
                    
                        
        order_id = [x[0] for x in cr.fetchall()]
        
        if order_id:
#             cust_inv_id = inv_obj.search(cr,uid,[('id','in',order_id),('state','!=','cancel')])
#             if cust_inv_id:
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
                   cft_val={}
                   val['price_unit'] = 0
                   freight_val={}
                   freight_cpf_val={}
                   freight_val['price_unit'] = 0
                   for ln in case.move_lines:
                       cft=ln.product_id.cft
                       price=0
                       prod_obj=self.pool.get('kw.product.price')
                       for i in ln.product_id.customer_ids:
                           if case.partner_id.id == i.name.id:
                                prod_ids=prod_obj.search(cr, uid, [('ef_date','<=',ln.delivery_date),('cust_info_id','=',i.id)],limit=1, order='ef_date desc')
                                for j in prod_obj.browse(cr,uid,prod_ids):
                                    if case.partner_id.freight or case.gen_freight:
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
                       account_expense1 = cr.fetchall()
                       
                       if 'Firewood' in ln.product_id.name :
                           if case.paying_agent_id.state_id.code == "KA":
                              account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of Firewood')]) 
                           if case.paying_agent_id.state_id.code == "TN":
                              account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of FW-Interstate-TN')])
                           if case.paying_agent_id.state_id.code == "AP":
                              account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of FW-Interstate-AP')]) 
                           if case.paying_agent_id.state_id.code == "KL":
                              account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of FW-Interstate-KL')])



                       else:
                           #Karnataka
                           if case.paying_agent_id.state_id.code == "KA":
                              if case.partner_id.state_id.id == case.paying_agent_id.state_id.id:
                                  account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of Wood-Local')])
                              if case.partner_id.state_id.id != case.paying_agent_id.state_id.id:
                                  account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of Wood-Interstate')])     
                           #Tamilnadu
                           if case.paying_agent_id.state_id.code == "TN":
                              if case.partner_id.state_id.id == case.paying_agent_id.state_id.id:
                                  account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of Wood-Local-TN')])
                              if case.partner_id.state_id.id != case.paying_agent_id.state_id.id:
                                  account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of Wood-Interstate-TN')]) 
                           #Andhra Pradesh
                           if case.paying_agent_id.state_id.code == "AP":
                              if case.partner_id.state_id.id == case.paying_agent_id.state_id.id:
                                  account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of Wood-Local-AP')])
                              if case.partner_id.state_id.id != case.paying_agent_id.state_id.id:
                                  account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of Wood-Interstate-AP')])

                           #Kerala
                           if case.paying_agent_id.state_id.code == "KL":
                              if case.partner_id.state_id.id == case.paying_agent_id.state_id.id:
                                  account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of Wood-Local-KL')])
                              if case.partner_id.state_id.id != case.paying_agent_id.state_id.id:
                                  account_expense = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Sale of Wood-Interstate-KL')])


                       if account_expense:
                           val['account_id'] = account_expense[0]     
                       else:
                            val['account_id'] = account_expense1[0]                            
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
                       tx_ids = []
                       if case.date <='2017-07-01 00:00:00':
                           if case.partner_id.state_id.id in tax or case.paying_agent_id.state_id.name in tax:
                               if case.partner_id.state_id.name == case.paying_agent_id.state_id.name:
                                   cr.execute("select id from account_tax where gst_categ is null and state_id=%s",(case.partner_id.state_id.id,))
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

                       else:
                           if case.state_id.id == case.partner_id.state_id.id:
                               cr.execute("select id from account_tax where gst_categ='intra' ")
                               intra_tax_id= [x[0] for x in cr.fetchall()]
                               intra_tax_id = tuple(intra_tax_id)
                               if intra_tax_id:
                                   cr.execute("select tax_id from product_taxes_rel where prod_id=%s and tax_id in %s",(ln.product_id.id,intra_tax_id))
                                   tx_ids = [x[0] for x in cr.fetchall()]
                               else:
                                   raise osv.except_osv(_('Warning'),_('Map proper Taxes for Intra State'))

                           else:
                               cr.execute("select id from account_tax where gst_categ='inter' ")
                               inter_tax_id= [x[0] for x in cr.fetchall()]
                               inter_tax_id = tuple(inter_tax_id)
                               if inter_tax_id:
                                   cr.execute("select tax_id from product_taxes_rel where prod_id=%s and tax_id in %s",(ln.product_id.id,inter_tax_id))
                                   tx_ids = [x[0] for x in cr.fetchall()]
                               else:
                                   raise osv.except_osv(_('Warning'),_('Map proper Taxes for Inter State'))
                           _logger.info('Tax Ids==========================> %s',tx_ids)
                           if tx_ids:
                               val.update({
                                               'invoice_line_tax_id': [(6, 0,tx_ids)]
                                       })


                       
                       i=[]
                       
                       #for grouping the customer invoices based on product,price and partner_id
                       key = ln.product_id.id,price,case.partner_id.id,ln.delivery_date
                       sup_grp[key]=vals
                       
                       ###################################################################################
                       ######             FOR KW LOGISTIC Account 
                       #################################################################################
                       
#                        if kw_paying_agent_id not in kw_paying_agent:
                       cft_val=val.copy()
                       freight_cpf_val=freight_val.copy()
                       if freight:
                           c_parent_id= case.partner_id.account_rec and case.partner_id.account_rec.id or False
                           if case.partner_id.parent_id:
                               c_parent_id=case.partner_id.parent_id.account_rec and case.partner_id.parent_id.account_rec.id or False
                           if not c_parent_id:
                                raise osv.except_osv(_('Warning'),_('"%s"Account Not Found in Kingswood Logistic"')% (case.partner_id.name,))
                       else:
                           c_acc_id = case.partner_id.property_account_receivable and case.partner_id.property_account_receivable.id or False
                               
                       
                       if not key in product_groups:                        
                           if ln.product_id.cft:
                               val['quantity']=ln.cft1
                               cft_val['quantity']=ln.cft2                            
                               freight_val['quantity']=ln.cft1
                               freight_cpf_val['quantity']=ln.cft2
                               if not ln.cft1>0 and not ln.cft2>0:
                                   raise osv.except_osv(_('Warning'),_('Enter Valid CFT Quantity for DC "%s"')% (case.name,))
                           product_groups[key] = val.copy()
                           product_cpf[key]=cft_val.copy()
                           freight_group[key] = freight_val.copy()
                           freight_cpf[key]=freight_cpf_val.copy()
                           delivery_orders[key] = [case.id]
                           inv_groups[key] = {'partner_id'   : case.partner_id.id,
                                             'date_invoice': ln.delivery_date,
                                             'type':   'out_invoice',
                                             'journal_id' : cust_journal_id,
                                             'branch_state':case.state_id.id or branch_state_id,
                                             'report':case.partner_id.split_invoice,
                                             'cft':ln.product_id.cft,
                                             'account_id':c_acc_id,
                                             }
                       else:
                           prod_obj=self.pool.get('kw.product.price')
                           for i in ln.product_id.customer_ids:
                              
                                if case.partner_id.id == i.name.id:
                                  prod_ids=prod_obj.search(cr, uid, [('ef_date','<=',ln.delivery_date),('cust_info_id','=',i.id)],limit=1, order='ef_date desc')
                               
                                  for j in prod_obj.browse(cr,uid,prod_ids):
                                       val['price_unit']  = j.product_price
          
                                       if ln.product_id.cft:
                                           product_groups[key]['quantity'] += ln.cft1
                                           product_cpf[key]['quantity']+=ln.cft2
                                           freight_group[key]['quantity'] += ln.cft1
                                           freight_cpf[key]['quantity']+=ln.cft2                                           
                                       else:
                                           product_groups[key]['quantity'] +=ln.unloaded_qty
                                           freight_group[key]['quantity']+=ln.unloaded_qty
                                       product_groups[key]['rejected_qty'] += ln.rejected_qty
                                       val['price_unit']  += ln.product_id.list_price
                                       freight_group[key]['rejected_qty'] += ln.rejected_qty
                                       
                                       delivery_orders[key].append(case.id)
                                       
                      
                                       
                else:
                    raise osv.except_osv(_('Warning'),_('Delivery Order "%s" Should Be In Delivered State')% (case.name,))  
        
 


    #Customer Invoice
        if type=="out":
            partner = [] # for control
            transport_rate=0
            destination=""
            for case in self.browse(cr,uid, ids):
                cr.execute("update stock_picking set cust_invoice=True where id=%s ",(case.id,))
                c=0
                kw_paying_agent_id=case.paying_agent_id.id
                if case.partner_id.freight or case.gen_freight:
                     
                           
                    for p in product_groups:
                        freight_val['price_unit']=0
                        
                        if case.partner_id.id in p and p not in partner:
                            destination=case.partner_id.city
                            for i in self.browse(cr, uid,delivery_orders[p]):
                                for temp in i.move_lines:
                                    
                                    #to fetch transport price based on the delivery date
                                    for j in temp.product_id.customer_ids:
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
                            if cft:
                                inv_vals['invoice_line'] = [(0, 0, product_groups[p]),(0,0,product_cpf[p])]
                                
                            inv_vals.update({'destination':destination,
                                             'journal_id' : cust_journal_id,
                                              
                                             })
                            
                            inv1=inv_obj.create(cr, uid, inv_vals)
                            inv_obj.button_reset_taxes(cr, uid, [inv1], {})
                            
                            #for creating Freight Invoice
                            inv_vals.update({
                                                    'delivery_orders_ids': [(6, 0, delivery_orders[p])],
                                                    'invoice_line': [(0,0,freight_group[p])],
                                                    
                                            })
                            if cft:
                                freight_cpf[p].update({'price_unit'   : freight_val['price_unit'],
                                                     })                                
                                inv_vals['invoice_line'] = [(0, 0, freight_group[p]),(0,0,freight_cpf[p])]                            
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
                                inv2=inv_obj.create(cr, uid, inv_vals)
                                inv_obj.button_reset_taxes(cr, uid, [inv2], {})
                            
                              
                                       
                else: 
                    
                    val['state'] = 'draft'            
                    for p in product_groups:
                        if case.partner_id.id in p and p not in partner:
                            inv_vals = inv_groups[p].copy()
                            inv_vals.update(inv_obj.onchange_partner_id(cr, uid, ids,'out_invoice', inv_groups[p]['partner_id'])['value'])
                            inv_vals.update({
                                                 'delivery_orders_ids': [(6, 0, delivery_orders[p])],
                                                  'invoice_line': [(0, 0, product_groups[p])],
                                                 'branch_state' : case.state_id and case.state_id.id or branch_state_id
                                                })
                            order_obj=self.pool.get('delivery_order_rel')
                            
                            if cft:
                                inv_vals['invoice_line']= [(0, 0, product_groups[p]),(0,0,product_cpf[p])]
                                                                          
                            inv_vals.update({'destination':destination,
                                             'journal_id' : cust_journal_id,
                                             })
                            inv3=inv_obj.create(cr, uid, inv_vals)
                            inv_obj.button_reset_taxes(cr, uid, [inv3], {})
                            partner.append(p)
                            
                              
                   
            
        return True
    
#     #schedular for Creating Invoices
#     def do_invoice(self, cr, uid, automatic = False, use_new_cursor = False,context = None ):
#         
# 
#         #for creating invoices from deliver orders
#         cr.execute("""select id from stock_picking where state in ('done', 'freight_paid') and date::date = """+"'"+datetime.today().strftime("%Y-%m-%d")+"'")
#         do_ids = cr.fetchall()
#         
#         do_ids = [d[0] for d in do_ids]
#         inv_ids = do_ids
#         
#         
#        
#         if do_ids:
#             cr.execute('SELECT del_ord_id FROM delivery_invoice_rel WHERE del_ord_id IN %s',(tuple(do_ids),))
#             order_ids = cr.fetchall()
#             if order_ids:
#                 order_ids = [i[0] for i in order_ids ]
#                 inv_ids = list(set(do_ids).difference(order_ids))
#                 
#             if inv_ids:
#                 self.get_invoice(cr, uid, inv_ids, False, context)
#         
#         #for creating invoices from incoming shipments
#         
#         cr.execute("""select id from stock_picking where state in ('done') and type = 'in' and date::date = """+"'"+datetime.today().strftime("%Y-%m-%d")+"'")
#         in_ids = cr.fetchall()
#         shipment_ids = [d[0] for d in in_ids]
#         ship_inv_ids = shipment_ids
#         if shipment_ids:
#             cr.execute('SELECT in_shipment_id FROM incoming_shipment_invoice_rel WHERE in_shipment_id IN %s',(tuple(shipment_ids),))
#             ship_order_ids = cr.fetchall()
#             if ship_order_ids:
#                 ship_order_ids = [s[0] for s in ship_order_ids ]
#                 ship_inv_ids = list(set(shipment_ids).difference(ship_order_ids))
#               
#             if ship_inv_ids:
#                 self.pool.get('stock.picking.in').get_invoice(cr, uid,ship_inv_ids, False, context )
#         return True  
#     
    
    
    
    
     
    
    def create(self,cr,uid,vals,context=None):
        if not context:
            context={}
        year=False
        today = time.strftime('%Y-%m-%d')    
        res={}
        u_name=''
        proforma_price=0.00
        user_obj = self.pool.get('res.users')
        partner=vals['partner_id']
        cr.execute("select freight from res_partner where id=%s",(partner,))
        freight=cr.fetchone()
        unloaded_qty = 0.0
        if freight[0]==True:
            vals['freight']=freight[0]
        else:
            vals['freight']=vals['gen_freight']
        if 'move_lines' in vals:
            if vals['move_lines']==[]:
                raise osv.except_osv(_('Warning'),_("Add Goods Details"))
        if vals.get('truck_no').lower().replace('-','').replace('.','').replace(' ','') in ('ka53b0553','ka05ad4447','ka51b9744'):
            raise osv.except_osv(_('Warning'),_("You can't Create DC for this Vehicle No."))

        for ml in vals['move_lines']:
                vals['product_id']=ml[2]['product_id']
                context.update({'location_id':ml[2]['location_id']})
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
                
#                 unloaded_qty = ml[2]['unloaded_qty']
#                 if unloaded_qty>50:
#                     raise osv.except_osv(_('Warning'),_("Enter the Quantity in Metric Tons Eg. if the loaded quantity is 16800 kgs enter 16.800"))
                                    
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
        
            
        cr.execute("select code from account_fiscalyear where date_start <= '"+today+"' and date_stop >='" +today+"'")
        code = cr.fetchone()
        if code:
            year = code[0]
            if state_id:
                cr.execute('select code from res_country_state where id =%s',(state_id,))
                state_code=cr.fetchone()[0]
            else:
                vals['state_id']=user.state_id.id
        if not year:
            raise osv.except_osv(_('Warning'),_('Please Create Fiscal Year For "%s"')%(today))
        if today <='2017-06-30':
            if state_code:
                format = 'DC/' + year + '/' + str(state_code) +'/'
            else:
                format = 'DC/' + year + '/' + user.state_id.code +'/'
        # New DC Number
        else:
            if state_code:
                format =  str(state_code) +'/' + year + '/'
            else:
                format = user.state_id.code +'/' + year + '/'

        cr.execute("select name from stock_picking where name like '"+format+"'|| '%' order by to_number(substr(name,(length('"+format+"')+1)),'99999') desc limit 1")
        prev_format = cr.fetchone()
        if not prev_format:
            name = format + '00001'
        else:
            auto_gen = prev_format[0][-5:]
            name = format + str(int(auto_gen) + 1).zfill(5)
        self.write(cr, uid, [res],{'name':name},context=context)   
        context.update({'customer_id':vals['partner_id'],
                        'paying_agent_id':vals['paying_agent_id'],'product_id':vals['product_id'],'today':today
                        })
        self.get_dc_count(cr,uid,[res],context=context)               
        return res

    def get_dc_count(self,cr,uid,ids,context=None):
        today = context.get('today',time.strftime('%Y-%m-%d'))
        dc_count = 0
        dc = 0  
        location = ''
        location_ids = ''
        product_id = context.get('product_id',False)
        product_id1 = context.get('product_id',False)
        partner_id = context.get('customer_id',False)
        partner_id1 = context.get('customer_id',False)
        paying_agent_id =  context.get('paying_agent_id',False)
        paying_agent_id1 =  context.get('paying_agent_id',False)       
        location_obj = self.pool.get('stock.location')
        location_id = context.get('location_id',False)
        if location_id:
            location_ids = location_obj.browse(cr,uid,location_id)
            
        #        if location_ids and location_ids.name.lower() != 'suppliers':
                
        edit = context.get('edit',False)
        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
        kw_paying_agent=cr.fetchall()   
        if kw_paying_agent:
            kw_paying_agent=zip(*kw_paying_agent)[0]
        else:
            kw_paying_agent = []
                 
        if edit:
            for case in self.browse(cr,uid,ids):
                if product_id == case.product_id.id:
                    product_id1 = False
                if partner_id == case.partner_id.id:
                    partner_id1 = False 
                if paying_agent_id == case.paying_agent_id.id:
                    paying_agent_id1 = False                                  
                   
        if product_id1 or partner_id1 or paying_agent_id1:
            if paying_agent_id not in kw_paying_agent:
                cr.execute("select dc_count from product_supplierinfo where product_id = %s and customer_id = %s and name= %s",(product_id,partner_id,paying_agent_id,))
                dc_count=cr.fetchone()
                if dc_count:
                    dc_count = dc_count[0]
                else:
                    dc_count = 0
                
                print "dc_count,",dc_count,product_id,partner_id,paying_agent_id
                                
                        
                cr.execute("select count(id) from stock_picking where type='out' and product_id ="+ str(product_id) +" and partner_id ="+ str(partner_id) +" and paying_agent_id="+ str(paying_agent_id) +"and create_date::date = '"+str(today)+"' ::date")
                dc = cr.fetchone()
                if dc:
                    dc = dc[0]
                else:
                    dc = 0   
            else:
                cr.execute("select dc_count from product_supplierinfo where product_id = %s and customer_id = %s and name= %s and location_id = %s",(product_id,partner_id,paying_agent_id,location_id))
                dc_count=cr.fetchone()
                if dc_count:
                    dc_count = dc_count[0]
                else:
                    dc_count = 0
                                
                        
                cr.execute("""select count(sp.id) from stock_picking sp 
                            left outer join stock_move sm on sm.picking_id = sp.id
                            where type='out' and sm.product_id ="""+ str(product_id) +
                           """ and sp.partner_id ="""+ str(partner_id) +" ""and sp.paying_agent_id="""+ str(paying_agent_id) +"""and sp.create_date::date = '"""
                           +str(today)+"""' ::date and sm.location_id ="""+str(location_id))
                           
                           
               
                dc = cr.fetchone()
                if dc:
                    dc = dc[0]
                else:
                    dc = 0
        
            if paying_agent_id not in kw_paying_agent:
                if edit:
                    if dc >= dc_count:
                        raise osv.except_osv(_('Warning'),_('Cannot Edit DC, Quota is Completed for the day "%s"')%(today))

                if dc > dc_count:
                    raise osv.except_osv(_('Warning'),_('Cannot Creat DC, Quota is Completed for the day "%s"')%(today))
                    
                
            print "dc_count",dc_count, "and-",dc
        return True
   
    def write(self, cr, uid, ids, vals, context = None):
            if not context:
                context={}
#         if context.get('type', '') == 'out':
            voucher_obj = self.pool.get('account.voucher')
            user_obj = self.pool.get('res.users')
            sub_part_obj = self.pool.get("sub.facilitator")
            price=0.0
            result={}
            g_ids = []
            proforma_price=0.0
            rejected_qty=False
            deduction_amt=False
            count_partner = False
            count_facilitator = False
            count_product = False
            paying_agent=[]
            king=False
            cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
            king=cr.fetchall()
            king=zip(*king)[0]            
            for case in self.browse(cr, uid, ids):
                if vals.get('truck_no',case.truck_no).lower().replace('-','').replace('.','').replace(' ','') in ('ka53b0553','ka05ad4447','ka51b9744'):
                    raise osv.except_osv(_('Warning'),_("You can't Create DC for this Vehicle No."))

                count_partner = vals.get('partner_id',case.partner_id.id)
                count_facilitator = vals.get('paying_agent_id',case.paying_agent_id.id)
                count_product = vals.get('product_id',case.product_id.id)
                for ln in case.move_lines:
                    location_id=ln.location_id.id
                    if 'move_lines' in vals:
                        location_id=vals['move_lines'][0][2].get('location_id',ln.location_id.id)
                        count_product = vals['move_lines'][0][2].get('product_id',ln.product_id.id)
                    
                if ('paying_agent_id' or 'partner_id' or 'product_id') in vals or (count_product != case.product_id.id):
                    cr.execute("select to_char(s.create_date, 'YYYY-MM-DD') from stock_picking s where s.id=%s",(case.id,))
                    count_date = cr.fetchone()
                    if count_date:
                        context.update({'customer_id':count_partner,
                                        'paying_agent_id':count_facilitator,'product_id':count_product,
                                        'today':count_date[0],'edit':True,'location_id':location_id})
                        self.get_dc_count(cr,uid,ids,context=context) 
                    
                cancel_state = vals.get('state',False)
                if cancel_state == 'cancel':  
                    voucher_obj=self.pool.get('account.voucher')
                    voucher=voucher_obj.search(cr,uid,[('state','=','draft'),('reference','=',case.name)])
                    if voucher:
                        voucher_obj.unlink(cr, uid, voucher,context = context)
                    
                    voucher_done=voucher_obj.search(cr,uid,[('state','=','posted'),('reference','=',case.name)])
                    if voucher_done:
                        raise osv.except_osv(_('Warning'),_('Voucher Posted, Cannot Change The Status')) 
                               
                if case.type == 'out':
                    if 'paying_agent_id' not in vals:
                        vals['state_id'] = case.paying_agent_id.state_id.id
                if case.partner_id.report:
                    vals['report']=case.partner_id.report or False
                    vals['w_report'] = case.partner_id.w_report or False
                    vals['dc_report'] = case.partner_id.dc_report or False
                if case.partner_id.wc_num:
                    vals['wc_num']=case.partner_id.wc_num or False
                paying_agent_id=vals.get('paying_agent_id',case.paying_agent_id.id)  
                if 'gen_freight' in vals:
                        if case.gen_freight and vals['gen_freight' ]==False:
                                raise osv.except_osv(_('Warning'),_('You Cannot Change Generate Freight')) 
                cr.execute("select create_uid from stock_picking where id =%s",(case.id,))
                cr_uid=cr.fetchone()
                if cr_uid:
                    user_id = user_obj.browse(cr,uid,cr_uid[0])
                    if user_id.role == 'depot':
                        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                        paying_agent=cr.fetchall()
                        paying_agent=zip(*paying_agent)[0]
                        if paying_agent_id not in paying_agent:
                           cr.execute("select id from stock_location where lower(name) like 'supplier%'")
                           sup_id=cr.fetchall()
                           sup_id=zip(*sup_id)[0]
                           for ln in case.move_lines:
                               location_id=ln.location_id.id
                               if 'move_lines' in vals:
                                   location_id=vals['move_lines'][0][2].get('location_id',ln.location_id.id)
                                   
                               if location_id not in sup_id:
                                  cr.execute('UPDATE stock_move SET location_id = %s WHERE picking_id=%s',(sup_id,case.id,))
            context.update({"report": 1})
            res = super(stock_picking_out,self).write(cr, uid, ids, vals, context)
            for temp in self.browse(cr, uid, ids):

                # Purchase Amount Calculation
                if temp.sub_facilitator_id and temp.sub_facilitator_id.id:
                    if temp.type == 'in':
                        cr.execute("""
                            select case when kw.sub_total is null then kw.product_price else kw.sub_total end

                                from product_supplierinfo ps
                                inner join kw_product_price kw on ps.id = kw.supp_info_id
                                and ps.product_id = (select product_id from stock_picking where id ="""+str(temp.id)+""")
                                and ps.name = (select partner_id from stock_picking where id = """+str(temp.id)+""")
                                and ef_date <= (select date::date from stock_picking where id = """+str(temp.id)+""")
                                order by ef_date desc limit 1
                        """)
                    if temp.type == 'out':
                        cr.execute("""
                            select case when kw.sub_total is null then kw.product_price else kw.sub_total end

                            from product_supplierinfo ps
                            inner join kw_product_price kw on ps.id = kw.supp_info_id
                            and ps.product_id = """+str(temp.product_id.id)+"""

                            and ef_date <= '"""+str(temp.date)+"""' ::date
                            and ps.name = """+str(temp.paying_agent_id.id)+"""
                            and (case when ps.customer_id is null then ps.depot = (select location_id from stock_move where picking_id = """+str(temp.id)+""" limit 1)
                            else case when ps.customer_id is null and ps.depot is null then ps.city_id = """+str(temp.city_id.id)+""" else ps.customer_id = """+str(temp.partner_id.id)+""" end end)
                            order by ef_date desc limit 1
                        """)
                    goods_rate = [x[0] for x in cr.fetchall()]
                    if goods_rate:
                        goods_rate = goods_rate[0]
                        _logger.error('Goods Rate=================: %s', goods_rate)
                        _logger.error('Temp Qty=================: %s', temp.qty)
                        purchase_amount = float(temp.qty * goods_rate)
                        if purchase_amount > 0:
                            cr.execute("update stock_picking set purchase_amount="+str(purchase_amount)+" where id="+str(temp.id))

                    cr.execute("""select id from sub_facilitator
                                    where sub_part_id="""+str(temp.sub_facilitator_id.id)+"""
                                    and '"""+str(temp.date)+"""'::date>= from_date and '"""+str(temp.date)+"""'::date <= to_date
                                """)
                    sub_part_ids = [x[0] for x in cr.fetchall()]
                    if sub_part_ids:
                        sub_part_ids = sub_part_ids[0]
                        sub_part = sub_part_obj.browse(cr, uid, sub_part_ids)
                        if sub_part.total_purchase >= float(1850000):
                            raise osv.except_osv(_('Warning'),_('Total Purcase is exceeded for the selected Sub Facilitator.'))

            if 'move_lines' in vals:
#               if vals['move_lines'][0][2]:
                     
                if not vals['move_lines'][0][2]:
                    if ids:
                        cr.execute("select product_id from stock_move where picking_id=%s",(ids[0],))
                        sp=cr.fetchone()
                        if not sp:
                            raise osv.except_osv(_('Warning'),_('Add one product'))
                else: 
                    if vals['move_lines'][0][2].get('unloaded_qty',False):
                        if vals['move_lines'][0][2]['unloaded_qty']>50:
                            raise osv.except_osv(_('Warning'),_("Enter the Quantity in Metric Tons Eg. if the loaded quantity is 16800 kgs enter 16.800"))                                                  
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
                    goods_rate = []
                    purchase_amount = 0.00
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
                    
            freight=False    
            for case in self.browse(cr, uid, ids):    
                
                if 'gen_freight' in vals:
                        if case.gen_freight and vals['gen_freight' ]==False:
                                raise osv.except_osv(_('Warning'),_('You Cannot Change Pay Freight'))
                if case.partner_id.freight or case.gen_freight:
                    freight=True

                for ln in case.move_lines:
                    rejected_qty=vals.get('rejected_qty',ln.rejected_qty)
                    deduction_amt=vals.get('deduction_amt',ln.deduction_amt)   
                    if rejected_qty>0:
                        if not deduction_amt>0:
                            raise osv.except_osv(_('Warning'),_('Enter Deduction Amount'))
                        
                    if deduction_amt>0:
                        if not rejected_qty>0:
                            raise osv.except_osv(_('Warning'),_('Enter Rejected Qty or Enter Qty as 1 if The Rejected Qty is Unknown'))                                     
                    i=0
                    paying_agent={}
                    paying_agent_id=[]
                    
                    
                    if 'state_id' in vals:
                        if case.paying_agent_id.state_id.id!=vals['state_id']:
                            vals['state_id'] = case.paying_agent_id.state_id.id
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
                                        cr.execute("select id from stock_location where lower(name) like 'stock%'")
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
                                    new_partner=vals.get('paying_agent_id',False)
                                    cr.execute("select id from stock_location where here lower(name) like 'stock%'")
                                    paying_agent=cr.fetchall()
                                    paying_agent=zip(*paying_agent)[0]
                                    cr.execute('UPDATE stock_move SET location_id = %s WHERE picking_id=%s',(paying_agent,case.id,))
                                    paying_agent_obj.location_id=paying_agent
                                    if new_partner and new_partner in king: 
                                        cr.execute("select partner_id from res_company where lower(name) like '%logistics%'")
                                        log_partner=cr.fetchone()
                                        if log_partner:
                                            log_partner=log_partner[0]
                                        if not temp.transporter_id:
                                            pick_obj.write(cr, uid, context['active_ids'],{'transporter_id':log_partner},context = context)                                    
                                    
                                    if new_partner and new_partner not in king:
                                        cr.execute("select id from stock_location where lower(name) like 'supplier%'")
                                        paying_agent_loc=cr.fetchall()
                                        paying_agent_loc=zip(*paying_agent_loc)[0]
                                        
                                        cr.execute('UPDATE stock_move SET location_id = %s WHERE picking_id=%s',(paying_agent_loc,case.id,))                                    
                 
               
                

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
    

    def get_location_inout(self, cr, uid, ids,context = None):
        cr.execute("select id from stock_picking where dest_location_id is null and type='out'")
        loc_ids=cr.fetchall()
        if loc_ids:
            a=0
            for loc in loc_ids:
                for stock in self.browse(cr,uid,[loc[0]]):
                    for temp in stock.move_lines:
                        cr.execute("update stock_picking set dest_location_id = "+str(temp.location_id.id)+" where id = "+str(stock.id))
                        print 'temp.location_id----',temp.location_id.complete_name
                        a=a+1
                        print 'No. ID',len(loc_ids)-a
        loc_ids = []    
        cr.execute("select id from stock_picking where dest_location_id is null and type='in'")
        loc_ids=cr.fetchall()
        if loc_ids:
            a=0
            for loc1 in loc_ids:
                for stock in self.browse(cr,uid,[loc1[0]]):
                    for temp in stock.move_lines:
                        cr.execute("update stock_picking set dest_location_id = "+str(temp.location_dest_id.id)+" where id = "+str(stock.id))
                        print 'temp.location_dest_id ---',temp.location_dest_id.complete_name
                        a=a+1
                        print 'No. ID',len(loc_ids)-a
        return True

    
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
    
    def send_monthly_dispatch_mail(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        if not context:
            context= {}        
        context.update({'summary':True})
        
        print_report = self.send_dispatch_mail(cr,uid,[uid],context)
        return print_report
    
#     def send_daily_dispatch_mail(self, cr, uid, ids, context=None):
    def send_daily_dispatch_mail(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        if not context:
            context= {}
        context.update({'summary': False})
        _logger.info('DC Mail Before==========================> %s',context)

        print_report = self.send_dispatch_mail(cr,uid,[uid],context)
        _logger.info('DC Mail After==========================> %s',context)

        return print_report    
    
    def send_daily_facilitator_mail(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        if not context:
            context= {}
        context.update({'facilitator': True})
        
        print_report = self.send_dispatch_mail(cr,uid,[uid],context)  
        print 'dc_facilitator_daily_mail'      
        return print_report

#     def send_daily_dispatch_in_out_mail(self, cr, uid, ids, context=None):
    def send_daily_dispatch_in_out_mail(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        if not context:
            context= {}
        context.update({'daily_dispatch': True})
        if 'type' in context:
            context.pop('type')
        _logger.info('Befrore Calling Send Dispatch==========================> %s',context)
        print_report = self.send_dispatch_mail(cr,uid,[uid],context)        
        _logger.info('Befrore Calling Send Dispatch==========================> %s',context)
        return print_report


        # Daily Dispatch Report for ADL
    # def send_daily_dispatch_adl_mail(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
    #     if not context:
    #         context= {}
    #     context.update({'adl': True})
    #     if 'type' in context:
    #         context.pop('type')
    #     print_report = self.send_dispatch_mail(cr,uid,[uid],context)
    #     return print_report


    def invoice_facilitator_mail(self, cr, uid, ids,context=None):
        if not context:
            context={}
        start_date = time.strftime('%Y-%m-%d')
        data = {}
        data['ids'] = ids
        id=0
        if ids:
            id=ids[0]
        data['model'] = context.get('active_model', 'ir.ui.menu')            
        rep_obj = self.pool.get('ir.actions.report.xml')
        datas={}
        today = time.strftime('%Y-%m-%d')
        user_obj = self.pool.get('res.users')
        zone = self.pool.get('res.users').browse(cr,uid,uid).tz or 'Asia/Kolkata'
        user = self.pool['res.users'].read(
            cr, uid, [uid], ['tz'], context=context)[0]        
        local_tz = pytz.timezone(zone)         
        today = datetime.strptime(today, '%Y-%m-%d') - relativedelta(days=int(0))
#         ed_dt = datetime.datetime.strptime(today, '%Y-%m-%d %H:%M:%S')
        print 'today',today,"**************************"
        ed_local_dt = local_tz.localize(today, is_dst=None)
        
        ed_utc_dt = ed_local_dt.astimezone(pytz.UTC)

        data['output_type'] = 'xls' 
        
        report_name=  'dc_facilitator_daily_mail'
        shedular_date = str(ed_utc_dt)
        if shedular_date:
            start_date = str(shedular_date[:10])
            a=str(start_date[8:])
            b=str(start_date[5:7])
            c=str(start_date[:4])
            str_date = str(str(a)+"-" + str(b)+"-" + str(c))
            if ids:
                print 'str_date',str_date
                cr.execute("update stock_picking set report_date='"+str(str_date)+"' where id ="+str(ids[0]))
            start_date = str(str(c)+"-" + str(b)+"-" + str(a))
               
        data['variables'] = {

                             'start_date':start_date,

                            }
                 
        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'name' : report_name,
        'datas': data,
            }


    
    def send_dispatch_mail(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        _logger.info('Inside ==========================> %s',context)
        rep_obj = self.pool.get('ir.actions.report.xml')
        today = time.strftime('%Y-%m-%d')      
        wzd_obj = self.pool.get('invoice.group.report')
        mail_obj = self.pool.get('mail.mail')
        email_obj = self.pool.get('email.template')
        user_obj = self.pool.get('res.users')
        mail_compose = self.pool.get('mail.compose.message')
        print_report = True
        partner_obj = self.pool.get('res.partner')
        model_obj = 'stock.picking.out'
        data = context.get('active_res_id', False)
        temp_obj = self.pool.get('email.template')  
        file_name = "dispatches.xls" 
        variables = {}  
        facilitator = context.get('facilitator',False)   
        if uid:
            user_id = user_obj.browse(cr,uid,uid)
        summary = False
        partners = ''
#         context.update({'date':today,'pdf':True})

        if context.get('type'):
            context.pop('type')
        
        summary = context.get('summary',False)
        if today:
            today = datetime.strptime(today, '%Y-%m-%d') - relativedelta(days=int(1))
            today = today.strftime('%Y-%m-%d')
        file_name = "Daily_dispatch_report.xls"

        template = self.pool.get('ir.model.data').get_object(cr, uid, 'kingswood', 'kw_send_mail')
        if summary:
           template = self.pool.get('ir.model.data').get_object(cr, uid, 'kingswood', 'kw_send_monthly_mail')

        _logger.info('Inside the Send Mail Function==========================> %s',context)
# for non dispacth DC        
#         if facilitator:
#            template = self.pool.get('ir.model.data').get_object(cr, uid, 'kingswood', 'kw_facilitator_daily_mail')
#            file_name = "daily_dc_facilitator.xls" 
#         assert template._name == 'email.template'
          # By Praveen
#         if not context.get('adl'):
        cr.execute(""" select ru.partner_id
                        from res_groups_users_rel gu
                        inner join res_groups g on g.id = gu.gid
                        inner join res_users ru on ru.id = gu.uid
                        where g.name = 'KW_Admin'""")
        # By Praveen
        # if context.get('adl'):
        #     cr.execute("select id from res_partner where ref ='ADL'")

        for p in cr.fetchall():
            p = partner_obj.browse(cr, uid,p[0])
            if p.email and p.email not in partners:
                partners += (p.email and p.email or "") + ","
                

        pick = self.search(cr,uid,[('date','<',today),('type','=','out')],order='id desc',limit=1)        
        
        print "DC...................",pick
        if context.get('daily_dispatch', False):
            template = self.pool.get('ir.model.data').get_object(cr, uid, 'kingswood', 'kw_daily_dispatch_in_out')
            file_name = "daily_dispatch_in_out_report.xls"
        
        _logger.info('DC Mail Before==========================> %s',partners[0:-1])
        if partners:
            email_obj.write(cr, uid, [template.id], {'email_to':partners[0:-1]})

        wzd_id=wzd_obj.create(cr,uid,{'from_date':today,'summary':False,},context)
        
        
        if not facilitator:
            if summary:
                file_name = "monthly_dispatch_report.xls"  
                wzd_id=wzd_obj.create(cr,uid,{'from_date':today,'summary':True,},context)
                      
            print_report = wzd_obj.print_monthly_dispatch_report(cr,uid,[wzd_id],context) 
        else:
           print_report = self.invoice_facilitator_mail(cr,uid,pick,context)  
            
        print 'mail_id',template.report_template
        report = print_report['datas']
        
        if report:          
            if 'ids' in report:
                ids = report['ids']
            if not ids and summary:
                ids = pick
            if 'variables' in report:
                variables = report['variables']
            if context.get('daily_dispatch'):
                ids = pick
        print variables 
        if not facilitator and not context.get('daily_dispatch'):       
            report_service = "report." + 'dispatches'
            if summary:
                report_service = "report." + 'monthly_dispatch'
        elif context.get('daily_dispatch'):
            report_service = "report." + 'daily_dispatch_in_out'
#             prev_date = datetime.strptime('2016-06-01', '%Y-%m-%d') - relativedelta(days=int(1))
#             
#             data['variables'] = {
#                                  'from_date':   prev_date,
#                                  'to_date'  :   prev_date,
#                                 }
            
        else:
            report_service = "report." + 'dc_facilitator_daily_mail'
        
        service = netsvc.LocalService(report_service)
        (result, format) = service.create(cr, uid, ids, {'model': 'stock.picking.out','variables':variables}, context)        
        result = base64.b64encode(result)
        if ids:
            for case in self.browse(cr,uid,[ids[0]]):            
    #                 (result, format) = service.create(cr, uid, ids, {'model': 'stock.picking.out'}, context)        
    #                 result = base64.b64encode(result)            
                attach_ids = self.pool.get('ir.attachment').create(cr, uid,
                                                          {
                                                           'name': file_name,
                                                           'datas': result,
                                                           'datas_fname': file_name,
                                                           'res_model': 'stock.picking.out',
                                                           'res_id': case.id,
                                                           'type': 'binary'
                                                          },
                                                          context=context)        
        
                           
                temp_obj.dispatch_mail(cr,uid,[template.id],attach_ids,context)
            print "template ......",template.id
            mail_id = self.pool.get('email.template').send_mail(cr, uid, template.id, case.id, True, context=context)
            mail_state = mail_obj.read(cr, uid, mail_id, ['state'], context=context)
            # try:
            #     if mail_state and mail_state['state'] == 'exception':
            #         mail_state=mail_state
            # except:
            #     pass
            _logger.info('mail_state==========================> %s',mail_state)
        cr.execute("delete from email_template_attachment_rel where email_template_id="+str(template.id))  
        cr.execute("delete from ir_attachment where lower(datas_fname) like '%dispatch%'")        
#         attachment_ids = [(4, attach_ids)]
#         temp_obj.write(cr,uid,[mail_id],{'lang':'Eng'})
        return print_report
    
    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels the moves and if all moves are cancelled it cancels the picking.
        @return: True
        """
        voucher_obj=self.pool.get('account.voucher')
        res = super(stock_picking_out,self).action_cancel(cr, uid, ids,context=context)
        for case in self.browse(cr,uid,ids):
                voucher=voucher_obj.search(cr,uid,[('state','=','draft'),('reference','=',case.name)])
                if voucher:
                    voucher_obj.unlink(cr, uid, voucher,context = context)
                
                voucher_done=voucher_obj.search(cr,uid,[('state','=','posted'),('reference','=',case.name)])
                if voucher_done:
                    state=case.dc_state
                    raise osv.except_osv(_('Warning'),_('Voucher Posted, Cannot Change The Status'))                    
        return res
    
    # for decaptcha the captcha image
    def get_captcha(self, cr, uid, ids, browser, context=None):
        """ Captcha Image Reading using PIL 
        """
        
        #case = self.browse(cr, uid, ids)[0]
        
        img = browser.find_element_by_xpath('//td[@valign="middle"]/div/img')
        src = img.get_attribute('src')
        urllib.urlretrieve(src, '/tmp/captcha.jpg')
         
        img = Image.open('/tmp/captcha.jpg')
        img = img.convert("RGBA")
        pixdata = img.load()
        print "pixdata[x, y]",pixdata
        
        # Make the letters bolder for easier recognition
#         for y in xrange(img.size[1]):
#             for x in xrange(img.size[0]):
#                 if pixdata[x, y][0] < 90: #90
#                     pixdata[x, y] = (0, 0, 0, 255)
#                     
        for y in xrange(img.size[1]):
         for x in xrange(img.size[0]):
             if pixdata[x, y][1] < 50: #136
                pixdata[x, y] = (0, 0, 0, 255)
                
#         for y in xrange(img.size[1]):
#             for x in xrange(img.size[0]):
#                 if pixdata[x, y][2] > 0:
#                     pixdata[x, y] = (255, 255, 255, 255)
        
        img.save("/tmp/new_captcha.jpg")
        
        #   Make the image bigger (needed for OCR)
        #img = img.resize((1000, 500))
        #img.save("/home/serveradmin/Desktop/esugam/new_"+case.driver_name+".jpg")
        data = pytesseract.image_to_string(Image.open('/tmp/new_captcha.jpg'))
        print data
        return data.replace(' ', '')
        
        return True    
                   
stock_picking_out()


class stock_picking(osv.osv):
    _inherit='stock.picking' 
    
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        user = self.pool.get('res.users').browse(cr,uid,uid)
        
        if context is None:context = {}
        res = super(stock_picking, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        doc = etree.XML(res['arch'])
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
                    
                
                if view_type == 'form':
                    if context.get('type', 'out') in ('out'):
                        for node in doc.xpath("//field[@name='partner_id']"):
                            node.set('options', '{"no_open":True}')
              
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
    
    def _get_default_user_partner(self, cr, uid, context=None):
        res ={}
        g_ids = []
        users=self.pool.get('res.users')
        user_id=users.browse(cr, uid, uid)
        res=user_id.partner_id.id                 
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
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        company=cr.fetchone()
        if company:
            company=company[0]
        if u_id:
            uid=u_id
#         cr.execute("select login from res_users where id  ="+str(uid))
#         user=cr.fetchone()[0]
        product_change = False
        for case in self.browse(cr, uid, ids):
            d=case.id
            if case.type=='out':
                for temp in case.move_lines:
                    txt=''
#                     if case.product_id.product_change:
#                        product_change= case.product_id.product_change
#                     self.write(cr, uid, [case.id],{'product_change':case.product_id.product_change},context = context)
#                         
                    
                    res[case.id] = {'product': " ",'cft1':0.0,'cft2':0.0,'deduction_amt':0.0, 'amt_txt':'','qty':0.000,'transporter':" ",'rej_quantity':0.000,'price_unit':0.0,'users':'' ,'freight':False,'del_quantity':0.000}
#                     res[case.id]['product']  = temp.product_id.name
                    res[case.id]['qty']  = temp.product_qty
                    res[case.id]['product_id']= temp.product_id.id
                    res[case.id]['price_unit'] = temp.price_unit
                    res[case.id]['del_quantity'] = temp.unloaded_qty
                    res[case.id]['rej_quantity'] = temp.rejected_qty
                    res[case.id]['deduction_amt'] = temp.deduction_amt
                    res[case.id]['cft1'] = temp.cft1
                    res[case.id]['cft2'] = temp.cft2
                    case.product_id.id=temp.product_id.id
                    
                    if case.freight_balance>0:
                        txt += amount_to_text_softapps._100000000_to_text(int(round(case.freight_balance)))        
                        res[case.id]['amt_txt'] = txt
                        
                    if case.partner_id.freight or case.gen_freight:
                        cr.execute("UPDATE stock_picking SET dc_company =%s where id=%s", (company,case.id))
                    else:
                        cr.execute("UPDATE stock_picking SET dc_company =%s where id=%s", (case.company_id.id,case.id))
#                     res[case.id]['location_id']=temp.location_id.id
                    cr.execute("select create_uid from stock_picking where id="+str(case.id))
                    create_uid=cr.fetchone()[0]
                    cr.execute("select login from res_users where id  ="+str(create_uid))
                    user=cr.fetchone()[0]
                    res[case.id]['users']=user
                    if case.partner_id.freight or case.gen_freight:
                        res[case.id]['freight']=True
 
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
    
    
    def _get_user(self, cr, uid, ids, args, field_name, context = None):
        res ={}
        g_ids = []
        user_obj = self.pool.get('res.users')
        u_id=context.get('uid')
        if u_id:
            uid=u_id
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'partner' : '', 'user_log':''}       
            if case.partner_id:
                if uid!=1:
                    res[case.id]['partner']=case.partner_id.ref     
            if case.type=='out':
                
                cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
                gid = cr.dictfetchall()
                for x in gid:
                    g_ids.append(x['gid'])
                for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
    #                 if g.name == 'KW_Freight':
    #                     res[case.id] = False
                    if g.name == 'KW_Supplier':
                        res[case.id]['user_log'] = 'KW_Supplier'
    #                     for temp in case.move_lines:
    #                           res[case.paying_agent_id]=temp.supplier_id
                         
                    if g.name == 'KW_Customer':
                        res[case.id]['user_log'] = 'KW_Customer'
                    if g.name == 'KW_Depot':
                        res[case.id]['user_log'] = 'KW_Depot'   
                    if g.name == 'KW_Admin':
                        res[case.id]['user_log'] = 'KW_Admin'
#                         cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (case.state_id.id,d))3
                    if g.name == 'KW_Freight':
                        res[case.id]['user_log'] = 'kw_freight'
                       
                    if res[case.id]['user_log']=='KW_Depot' or res[case.id]['user_log'] == 'KW_Admin':
                        
                        user = user_obj.browse(cr, uid, [uid])[0]
                        
                        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
                        paying_agent=cr.fetchall()
                        paying_agent=zip(*paying_agent)[0]
                        if res[case.id]['user_log'] !='KW_Admin':
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
                            cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (case.paying_agent_id.state_id.id,case.id))
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
            if g.name == 'KW_Freight':
                res = 'kw_freight'        
                    
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
        dealers_obj=self.pool.get('goods.dealers')
        res = {}
        truck=False
        
        for case in self.browse(cr, uid, ids):
            date=case.date_function
            truck=dealers_obj.search(cr,uid,[('name','=',case.truck_id.id),('date','<=',date)])
            truck_id=dealers_obj.browse(cr,uid,truck)
            if truck_id:
                truck_id=truck_id[0]
            if case.type=='out':
                res[case.id] = {'freight_deduction': 0.00, 'freight_total':0.00}
                total = 0.00
                deduction = 0.00
                tol_qty = 0.00
                tol_rate = 0
#                 freight_charge=0
                for ln in case.move_lines:
#                     for temp in ln.product_id.customer_ids:
#                         if temp.name.id==case.partner_id.id:
#                             
#                             case.freight_charge=temp.transport_rate
#                             cr.execute('UPDATE stock_picking SET freight_charge = %s WHERE id=%s',(temp.transport_rate,case.id,))
                    if case.freight_charge > 0:
                        total += (case.freight_charge * ln.unloaded_qty)
                        
                        for partner in case.partner_id.dealers_ids:
                            if case.truck_id.id==partner.name.id and partner.date <= date:
                                if tol_qty==0 and tol_rate==0:
                                    tol_qty=partner.tol_qty
                                    tol_rate=partner.tol_rate
                                
                                
                        # Picking Qty > Product Qty
                        if case.truck_id and ln.unloaded_qty> 0.00:
                              if ln.unloaded_qty < ln.product_qty and (ln.product_qty  - ln.unloaded_qty) > (tol_qty/1000):
                                  deduction += ((ln.product_qty - (tol_qty/1000)) - ln.unloaded_qty) *1000 * tol_rate
#                             if ((ln.product_qty - ln.unloaded_qty) * 1000) > (ln.product_qty * truck_id.tol_qty) :
#                                 deduction += (((ln.product_qty - ln.unloaded_qty)*1000) - (ln.product_qty * tol_qty)) * tol_rate

                res[case.id]['freight_deduction'] = round(deduction)
                res[case.id]['freight_total'] = total
#                 self.get_freight_balance(cr, uid, ids, context)
#                 if case.freight_charge > 0:
#                     res[case.id]['freight_balance'] = total - deduction - case.freight_advance
        return res

    
    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels the moves and if all moves are cancelled it cancels the picking.
        @return: True
        """
        voucher_obj=self.pool.get('account.voucher')
        res = super(stock_picking,self).action_cancel(cr, uid, ids,context=context)
        for case in self.browse(cr,uid,ids):
                voucher=voucher_obj.search(cr,uid,[('state','=','draft'),('reference','=',case.name)])
                if voucher:
                    voucher_obj.unlink(cr, uid, voucher,context = context)
                
                voucher_done=voucher_obj.search(cr,uid,[('state','=','posted'),('reference','=',case.name)])
                if voucher_done:
                    raise osv.except_osv(_('Warning'),_('Voucher Posted, Cannot Change The Status'))                      
        return res
    
    
    def kw_pay_freight(self, cr, uid, ids, context = None):
#         if context.get('type', '') == 'out':
        cur_date = time.strftime('%Y-%m-%d')
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
                    if case.partner_id.freight or case.gen_freight:
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
                        
                        if case.partner_id.freight or case.gen_freight:
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
                        if case.partner_id.freight or case.gen_freight:
                            context.update({'freight':freight})
                        self.write(cr, uid, ids, {'state':'freight_paid','frtpaid_date':cur_date})
                        #TODO: Remove the functionlity of posting the entries
                        #voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                    
                    
                     
        #             if (user_id.role == 'depot' or user_id.role =='admin') and case.freight_balance >0:
        #                 if user_id == supplier_id:
        #                     partner = case.transporter_id
        #                 else:
        #                     partner = supplier_id.partner_id
                        
                            
                    else:
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
                            if case.partner_id.freight or case.gen_freight:
                                context.update({'freight':freight})
                            #TODO: Remove the functionlity of posting the entries
                            #voucher_obj.proforma_voucher(cr, uid,[vid],context=context)
                            self.write(cr, uid, ids, {'state':'freight_paid','frtpaid_date':cur_date})
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
        cinv_ids=[]
        sinv_ids=[]
        Iinv_ids=[]
        for case in self.browse(cr, uid, ids):
            res[case.id] = {'cust_invoice' : False, 'sup_invoice':False}
            cr.execute("""SELECT dr.invoice_id FROM delivery_invoice_rel dr inner 
            join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id=%s and ac.state <>'cancel'""",(str(case.id),)) 
            cinv_ids = [x[0] for x in cr.fetchall()]
            if cinv_ids:
                res[case.id]['cust_invoice'] = True
            cr.execute("""SELECT dr.invoice_id FROM supp_delivery_invoice_rel dr inner 
            join account_invoice ac on ac.id=dr.invoice_id WHERE dr.del_ord_id=%s and ac.state <>'cancel'""",(str(case.id),))
            sinv_ids = [x[0] for x in cr.fetchall()]
            cr.execute("""SELECT dr.invoice_id FROM incoming_shipment_invoice_rel dr inner 
            join account_invoice ac on ac.id=dr.invoice_id WHERE dr.in_shipment_id=%s and ac.state <>'cancel'""",(str(case.id),))
            Iinv_ids = [x[0] for x in cr.fetchall()]
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
               'partner_id': fields.many2one('res.partner', 'Partner', track_visibility='onchange',states={'done':[('readonly', True)], 'cancel':[('readonly',True)],'freight_paid':[('readonly',True)]}, select=True),
              # New:
               
               'work_order'    :   fields.function(get_workorder,store=True,type="char",string='Work Order Number',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
               'truck_no'      :   fields.char('Vehicle No',size=20, states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
               'esugam_no'     :   fields.char('E-Sugam No.',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
               'distance'      :   fields.integer("Approximate Distance(KM)"),
               'state'         :   fields.selection([('draft','Draft'),('in_transit','In Transit'),('auto', 'Waiting Another Operation'),
                                                      ('confirmed', 'Waiting Availability'),
                                                      ('assigned', 'Ready to Deliver'),
                                                      ('done', 'Delivered'),
                                                      ('cancel', 'Cancelled'),('freight_paid','Freight Paid')],'Status', readonly=True, select=True,),
                                                      
              'freight_charge' : fields.float('Freight Charge',digits=(0,2),states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'freight_advance': fields.float('Freight Advance',digits=(0,2),states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'driver_name'    : fields.char('Driver Name',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'diver_contact'  : fields.char('Driver Contact',size=20,states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              
              
              'freight_total'    : fields.function(_get_freight_amount, type='float', string='Freight Total', store=True, multi="tot",track_visibility='onchange'),
              'freight_deduction': fields.function(_get_freight_amount, type='float', string='Freight Deduction', store=True, multi="tot",track_visibility='onchange'),                 
#               'freight_balance'  : fields.function(_get_freight_amount, type='float', string='Freight Balance', store=True, multi="tot"),
              'city_id'          : fields.many2one('kw.city','From', select=True),
              'transporter_id'   : fields.many2one('res.partner','Transporter', select=True),
              'date_function'   : fields.function(_get_new_date,type='date',string="Creation Date",store=True,multi="date"),
              'delivery_date_function'   : fields.function(_get_new_date,type='date',string="Delivery Date",store=True,multi="date",track_visibility='onchange'),    
               'user_log'        : fields.function(_get_user,type='char',method=True,string="Permission", store=False,multi='user'),
              'paying_agent_id'     : fields.many2one('res.partner','Paying Agent',track_visibility='onchange', select=True),
#                                                       states={'in_transit': [('readonly', True)],'done': [('readonly', True)],'freight_paid': [('readonly', True)]}),
              'paying_agent'    : fields.function(_get_paying_agent,type='char',method=True,string="paying_agent", store=True),        
#               'customer_list'   : fields.function(_get_customer, type='text', string='Customers List' ,store=True),
            'product'         : fields.function(_get_move_lines,type="char", size=30, string="Product",store=True, multi="move_lines"),
            'qty'             : fields.function(_get_move_lines,type="float", digits=(0,3),string="Quantity in Mts",store=True, multi="move_lines"),
            'del_quantity'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string="Delivered Quantity",store=True, multi="move_lines",track_visibility='onchange'),
            'rej_quantity'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string="Rejected Quantity",store=True, multi="move_lines",track_visibility='onchange'),
             'deduction_amt'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string="Deduction",store=True, multi="move_lines",track_visibility='onchange'),
            'transporter'     : fields.function(_get_move_lines,type="char", size=30,string="Transporter",store=True,multi="move_lines"),
            'price_unit'      : fields.function(_get_move_lines,type="float",string="Unit Price",store=True,multi="move_lines"),

            'product_id'       : fields.many2one('product.product', 'Products',track_visibility='onchange', select=True),
            'freight_balance' :fields.float('Freight Balance',digits=(0,2),track_visibility='onchange'),
             'state_id'        : fields.many2one('res.country.state','State', select=True),
            'move_lines'        : fields.one2many('stock.move', 'picking_id', 'Internal Moves', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},track_visibility='onchange'),
            
            'truck_id'           : fields.many2one('goods.trucks','Trucks', select=True),
            
            'cft1'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string='CFT Size1',multi="move_lines",track_visibility='onchange',
                                         store=True),
            'cft2'    :  fields.function(_get_move_lines,type="float", digits=(0,3),string='CFT Size2',multi="move_lines",track_visibility='onchange',
                                         store=True),              
             #FOR VIEW PURPOSE
               
               'year': fields.char('Year', size=6, readonly=True),
              'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                                            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
                                            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
              'day': fields.char('Day', size=128, readonly=True),
        
            #for reporting purpose
            'dc_company' : fields.many2one('res.company','company'),
             'amt_txt'         :   fields.function(_get_move_lines,type="char",string="Amount in Words",store=True,multi="move_lines"),
              'invoice_line_id'    : fields.many2one('account.invoice.line', 'invoice line'),
              'finvoice_line_id'    : fields.many2one('account.invoice.line', 'Freight invoice line'),
              'oinvoice_line_id'    : fields.many2one('account.invoice.line', 'Other Facilitator invoice line'),
               'purchase_id': fields.many2one('purchase.order', 'Purchase Order',
                                             ondelete='set null', select=True),
              'location_id'     : fields.function(_get_move_lines,type="integer",string="location_id",store=True,multi="move_lines", select=True),
             
              'users'           : fields.function(_get_move_lines,type="char", string="User",store=True, multi="move_lines"), 
              'freight'         : fields.function(_get_move_lines,type="boolean",string="freight",store=True,multi="move_lines"),
              
              'transit_date'    : fields.datetime('Transit Date'),
              
            #invoice Purpose
#              'cust_invoice'    :   fields.boolean('Customer Invoice'),
#               'sup_invoice'    :   fields.boolean('Facilitator Invoice'), 
#             
              'cust_invoice'    :   fields.function(_get_inv_status, multi = "all",type="boolean",string ='Customer Invoice',store=True),
              'sup_invoice'     :   fields.function(_get_inv_status, multi = "all",type="boolean",string ='Facilitator Invoice',store=True),
              
            #for search view
              'date_from':fields.function(lambda *a,**k:{}, method=True, type='date',string="From"),
              'date_to':fields.function(lambda *a,**k:{}, method=True, type='date',string="To"),
            
              #esugam, for specific users
              'gen_esugam'   : fields.boolean("Generate E-sugam"),
              'show_esugam'  : fields.related('partner_id','show_esugam',type='boolean',store=False),
              
              #Freight for specific users
              'show_freight'  : fields.related('partner_id','show_freight',type='boolean',store=False),
              'gen_freight'   : fields.boolean("Generate Freight"),
               'pay_freight'   : fields.related('partner_id','pay_freight',type='boolean',store=True,string="Pay Freight"),
               'report'   : fields.related('partner_id','report',type='boolean',store=True,string="DC-LR Report"),
               'wc_number':fields.char('W.C. Number',size=20),
               'wc_num'        : fields.related('partner_id','wc_num',type='boolean',store=True,string="WC Num"),
               'attachment'   : fields.related('company_id','attachment',type='binary',store=False,string="APMC Attachment"),
               'amc_attachment'        :   fields.related('partner_id','amc_attachment',type='boolean',store=False,string="APMC Attachment",readonly=True), 
                'filename'   :   fields.char('File Name',size=100),
                'billing_cycle'        :   fields.related('partner_id','billing_cycle',type='boolean',store=False,string="Billing Cycle",readonly=True),
                
                'user_partner_id': fields.many2one('res.partner', 'Partner'),  
                'w_report'        : fields.related('partner_id','w_report',type='boolean',store=True,string="Weighment Slip Report"),
                'dc_report'        : fields.related('partner_id','dc_report',type='boolean',store=True,string="DC Report"),                    
               'partner'       :   fields.function(_get_user,type='char',method=True,string="Partner", store=False,multi='user'),
               'dest_location_id'        : fields.many2one('stock.location','Location'),
               'report_date'  :       fields.char('Date'), 
               'hide_fields'    : fields.function(_get_permission,type='boolean',method=True,string="Permission", store=True),
               'farmer_declaration' : fields.related('company_id','farmer_declaration', string="Farmer Declaration", type='binary', store=False),
               'is_farm_decl' : fields.related('partner_id','is_farm_decl',string="Is Farmer Declaration", type="boolean", store=False),
               'fd_filename'   :   fields.char('File Name',size=100),
               'transit_pass'     : fields.related('partner_id','transit_pass',type='boolean',store=True,string="Transit Pass"),

              # Bank details
                'bank_name'     :   fields.char("Bank Name", size=100),
                'ifsc_code'     :   fields.char("IFSC Code", size=11),
                'ac_holder'     :   fields.char("Beneficiary Name", size=100),
                'ac_number'     :   fields.char("Account Number", size=30),
                'bank_addr'     :   fields.text("Bank Address"),
                'ac_holder_mob' :   fields.char("Mobile Number", size=10),
                'ac_holder_pan' :   fields.char("Pan Number", size=20),
                'bene_code'     :   fields.char("Beneficiary Code", size=30),

                #esugam, for specific users
                'gen_jjform'   : fields.boolean("Generate JJform"),
                'show_jjform'  : fields.related('partner_id','show_jjform',type='boolean',store=False),
                'jjform_no'    : fields.char("JJform Number", size=50),

                'es_active'    : fields.related('partner_id','es_active',type='boolean',store=False),

                # For Bank Account Details Report
                'frtpaid_date'   : fields.date("Freight Paid Date", select=True),
                'is_bank_submit' : fields.boolean("Is Online Bank Submit", select=True),
                'frieght_paid'   : fields.boolean("Is Freight Paid", select=True),

                'sub_facilitator_id'    :   fields.many2one("res.partner", "Sub Facilitator"),
                'purchase_amount'       :   fields.float("Purchase Amount", digits=(16,2)),
                'is_sub_facilitator'    :   fields.boolean("Is Sub Facilitator"),

                'hnl_attachment'            :   fields.related('company_id','hnl_attachment',type='binary',store=False,string="HNL Attachment"),
                'is_hnl_attachment'        :   fields.related('partner_id','is_hnl_attachment',type='boolean',store=False,string="HNL Attachment",readonly=True),
                'hnl_filename'          :   fields.char("File Name", size=30),
                'po_hnl_attachment'     :   fields.related('company_id','hnl_po_attachment',type='binary',store=False,string="HNL Attachment"),
                'hnl_po_filename'          :   fields.char("File Name", size=30),

              }
    _order = 'date desc'
    _defaults={
               
                'paying_agent_id':_get_default_paying_agent_id,
               'esugam_no'    :'0',
#                'purchase_id': False,
#                'hide_fields' : True
#                 'date_function': _get_default_new_date,
                 'user_log'     :_get_default_user,
                'paying_agent' :_get_default_paying_agent,
                'state_id'     : _get_default_state,
                'freight': False,
                'cust_invoice' : False, 
                'sup_invoice':False,
                'delivery_date_function':lambda *a: time.strftime('%Y-%m-%d'),
                'date_function': lambda *a: time.strftime('%Y-%m-%d'),
                    'filename'      :"APMC_CESS.pdf" ,
                    'fd_filename'   : "Farmer Declaration.pdf",
                    'user_partner_id':_get_default_user_partner, 
                'hide_fields' : _get_default_permission,   
                'transit_pass' : False,
                'is_bank_submit' : False,
                'frieght_paid'  : False,
                'hnl_filename'  :   "HNL-Letter to DFO.pdf",
                'hnl_po_filename' : "HNL PO File.pdf"
               }

    # Actions

    def open_tax_link(self, cr, uid, ids, context=None):
        ''' Open the website page with the Tax form '''
        trail = ""
        context = dict(context or {}, relative_url=True)
#         if 'survey_token' in context:
#             trail = "/" + context['survey_token']
        case = self.browse(cr, uid, ids)
#         if case.partner_id.tax_link:
        print "Link..........",case.partner_id.tax_link
            
        return {
            'type': 'ir.actions.act_url',
            'name': "Start Survey",
            'target': 'self',
            'url': case.partner_id.tax_link#self.read(cr, uid, ids, ['public_url'], context=context)[0]['public_url'] + trail
        }    

    def onchange_partner_in(self, cr, uid, ids, partner_id=None, context=None):
#         res=super(stock_picking,self).onchange_partner_in(cr, uid, ids,partner_id=False,context=None)
        res={}
        dom = {}
        partner_obj=self.pool.get('res.partner')
        partner_ids=partner_obj.search(cr,uid,[('id','=',partner_id)])
        for i in partner_obj.browse(cr,uid,partner_ids):
            if i.work_order:
                res['work_order']=i.work_order
            else:
                res['work_order']=False
            if 'associate' in i.name.lower():
                res['partner']=i.ref
            if i.sub_facilitator_ids:
                cr.execute("select sub_part_id from sub_facilitator where main_facilitator_id="+str(i.id))
                sub_facilitator_id = [x[0] for x in cr.fetchall()]
                if sub_facilitator_id:
                    dom.update({'sub_facilitator_id':  [('id','in',sub_facilitator_id )]})
                    res.update({'is_sub_facilitator': True})
        return {'value':res,'domain':dom}
    
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
    
#     def write(self, cr, uid, ids, vals, context = None): 
#         res = super(stock_picking,self).write(cr, uid, ids, vals, context)
#         
#         type=context.get('default_type',False)
#         if type=='in':
#             in_p_id=False
#             if 'move_lines' in vals: 
#                 in_p_id=vals['move_lines'][0][2].get('product_id',False)
#                 if in_p_id:
#                     vals['product_id']=in_p_id
#             else:
#                 for case in self.browse(cr, uid, ids):
#                     for temp in case.move_lines:  
#                         vals['product_id']=temp.product_id.id
#         return res
    #Dispatch 
    def send_dispatch_mail(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
        today = time.strftime('%Y-%m-%d %H:%M:%S')      
        print 'context',context          
        return res
    
        
stock_picking()



class stock_move(osv.osv):
    _inherit='stock.move'
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        
        user = self.pool.get('res.users').browse(cr,uid,uid)
        
        if context is None:context = {}
        res = super(stock_move, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        doc = etree.XML(res['arch'])
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
                
                if view_type == 'tree':
                    if context.get('picking_type', 'out') in ('out'):
                        for node in doc.xpath("//field[@name='product_id']"):
                            node.set('options', '{"no_open":True}')

        return res
    

    def _get_permission(self, cr, uid, ids, args, field_name, context = None):
        stock_obj=self.pool.get('stock.picking.out')
        res ={}
        g_ids = []
        freight=False
        cft=False
        origin=' '
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        user_partner=user.partner_id.id
        for case in self.browse(cr, uid, ids):
            partner_id=case.picking_id.partner_id
            if partner_id:
                if 'associate' in partner_id.name:
                    cr.execute("UPDATE stock_move SET origin ='ADL' where id=%s", (str(case.id),))            
            cft=case.product_id.cft
            if cft:
                self.write(cr,uid,ids,{'cft':cft})
            picking_id=case.picking_id.id
            if case.picking_id.partner_id.id and uid!=1:
                origin=case.picking_id.partner_id.ref
                if origin:
                    cr.execute("UPDATE stock_move SET partner =%s where id=%s", (origin,case.id))
            if uid==1:
                cr.execute("UPDATE stock_move SET partner =%s where id=%s", (origin,case.id))
                    
            stock_id=stock_obj.search(cr,uid,[('id','=',picking_id)])
            if user_partner:
                cr.execute("UPDATE stock_picking SET user_partner_id =%s where id=%s", (user_partner,picking_id))
            res[case.id] = True
            cr.execute("select gid from res_groups_users_rel where uid ="+str(uid))
            gid = cr.dictfetchall()
            for x in gid:
                g_ids.append(x['gid'])
            for g in self.pool.get('res.groups').browse(cr, uid, g_ids):
#                 cr.execute("select complete_name from stock_location where id = (select location_id from stock_move where picking_id="+str(picking_id)+")")
#                 sr_location_id=cr.fetchone()
#                 if sr_location_id:
#                     sr_location_id = sr_location_id[0]
#                     cr.execute("UPDATE stock_picking SET source_location_id = '"+str(sr_location_id)+"' where id="+str(picking_id)) 
#                 pay_freight=False
                report=False
#                 cr.execute("select pay_freight from res_partner where id="+str(partner_id))
#                 pay_freight=cr.fetchone()[0]
#                 cr.execute("UPDATE stock_picking SET pay_freight =%s where id=%s", (pay_freight,picking_id))  
#                 cr.execute("select dc_report from res_partner where id="+str(partner_id.id))
#                 report=cr.fetchone()[0]
#                 if report:
#                     cr.execute("UPDATE stock_picking SET dc_report =%s where id=%s", (report,picking_id)) 
#                 else:
#                     stock_obj.write(cr,uid,stock_id,{'dc_report':False})
#                 cr.execute("select wc_num from res_partner where id="+str(partner_id))
#                 wc_num=cr.fetchone()[0]  
#                 if wc_num:              
#                     cr.execute("UPDATE stock_picking SET wc_num =%s where id=%s", (report,picking_id))  
#                 else:
#                     stock_obj.write(cr,uid,stock_id,{'wc_num':False})   
#                     
#                 cr.execute("select w_report from res_partner where id="+str(partner_id))
#                 wc_num=cr.fetchone()[0]  
#                 if wc_num:              
#                     cr.execute("UPDATE stock_picking SET w_report =%s where id=%s", (report,picking_id))  
#                 else:
#                     stock_obj.write(cr,uid,stock_id,{'w_report':False})                                    
#                 stock_obj.write(cr,uid,[picking_id],{'pay_freight':pay_freight},context=context)              
                if g.name == 'KW_Supplier':
                    res[case.id] = False
                if g.name == 'KW_Depot':
                    res[case.id] = False
                if g.name == 'KW_Customer':
                    res[case.id] = True
                    
#                     cr.execute("select partner_id from res_users where id="+str(uid))
#                     partner_id=cr.fetchone()[0]
                    cr.execute("select product_change from res_partner where id="+str(partner_id.id))
                    partner=cr.fetchone()[0]
                    if not partner:
                        partner=False
                    cr.execute("UPDATE stock_move SET product_change =%s where id=%s", (partner,case.id))
                    
#                     cr.execute("UPDATE stock_move SET location_dest_id =%s where id=%s", (case.location_dest_id.id,case.id))
                if g.name == 'KW_Admin': 
                    res[case.id] = False
                    if case.picking_id.state != 'in_transit':
#                         
#     
#                         cr.execute("select partner_id from stock_picking where id="+str(picking_id))
#                         partner_id=cr.fetchone()[0]
#                         
#                         cr.execute("select product_change from res_partner where id="+str(partner_id))
#                         partner=cr.fetchone()[0]
#                         if not partner:
#                             partner=False
#                         cr.execute("UPDATE stock_move SET product_change =%s where id=%s", (partner,case.id))  
#                         if case.state=='done':
#                             res[case.id] = False
# 
#                         
#                             cr.execute("select product_change from res_partner where id="+str(partner_id))
#                             partner=cr.fetchone()[0]
#                         paying_agent=[]
#                         
#                         cr.execute("select freight from res_partner where id="+str(partner_id))
#                         freight=cr.fetchone()[0]
#                         if not freight:
#                             cr.execute("select gen_freight from stock_picking where id="+str(picking_id))
#                             freight=cr.fetchone()[0]
#                             
#                         cr.execute("UPDATE stock_picking SET freight =%s where id=%s", (freight,picking_id))
#                            
#                         cr.execute("select paying_agent_id from stock_picking where id="+str(picking_id))
#                         paying_agent_id=cr.fetchone()[0]
#                         cr.execute("select transporter_id from stock_picking where id="+str(picking_id))
#                         transporter_id=cr.fetchone()[0]
#                         
#                         cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
#                         paying_agent=cr.fetchall()
#                         paying_agent=zip(*paying_agent)[0]
#                         if paying_agent_id in paying_agent:                                                   
#                             cr.execute("select id from res_partner where lower(name) like 'others'")
#                             transport=cr.fetchall()
#                             transport=zip(*transport)[0]
#                             if transport:
#                                 if transporter_id in transport:
#                                     cr.execute('UPDATE stock_picking SET paying_agent = %s WHERE id=%s',("representative",picking_id,))
#                                 else:
#                                     cr.execute('UPDATE stock_picking SET paying_agent = %s WHERE id=%s',("kingswood",picking_id,))
#                         else:
#                             cr.execute('UPDATE stock_picking SET paying_agent = %s WHERE id=%s',("not",picking_id,))
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
                elif context.get('address_in_id', False) and paying_agent_id:
                    context.update({'address_in_id':paying_agent_id})
                    part_obj_add = self.pool.get('res.partner').browse(cr, uid, context.get('address_in_id', []), context=context)
                    if part_obj_add and part_obj_add.property_stock_supplier:
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
        if "picking_type" in context:
            if context['picking_type'] == 'internal' or context['picking_type'] =='in' :
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
                            print user.location_id.name
                        else:
                            raise osv.except_osv(_('Warning'),_('Check Location for the logged in User "%s" ')% (user.log))
        return location_dest_id
 
    
    _columns={
              'unloaded_qty'    :   fields.float('Delivered Quantity (MT)',digits=(0,3),track_visibility='onchange'),
              'rejected_qty'    :   fields.float('Rejected Quantity (MT)',digits=(0,3),track_visibility='onchange'),
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
              'deduction_amt'   : fields.float('Deduction Amount',digits=(0,2),track_visibility='onchange'),
              'location'        : fields.function(_get_location,type='char',method=True,string="Source Location"),
              'delivery_date'   : fields.date('Delivery Date',required=True,track_visibility='onchange'),
              'product_change'  : fields.boolean("Allow Product Change"), 
              'cft1'            : fields.float('CFT Size1',digits=(0,2),track_visibility='onchange'),
              'cft2'            : fields.float('CFT Size2',digits=(0,2),track_visibility='onchange'),
              'cft'             : fields.related('product_id','cft',type='boolean',store=False,string="CFT",readonly=True),
              'partner'         : fields.char('Partner')
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
                'partner':'',
#                 'location_dest_id': _default_location_destination,
                
              }
    
    
    
    
    
    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
                            loc_dest_id=False, partner_id=False,paying_agent_id=False,type=False,date=False, context=None):
        """ On change of product id, if finds UoM, UoS, quantity and UoS quantity.
        @param prod_id: Changed Product id
        @param loc_id: Source location id
        @param loc_dest_id: Destination location id
        @param partner_id: Address id of partner
        @return: Dictionary of values
        """
        if not context:
            context={}
        if not type:
            type='in'
        warning=''
        res={}
        price=0.0
        update=0
        proforma_price=0.0

        res=super(stock_move,self).onchange_product_id(cr, uid, ids, prod_id=prod_id, loc_id=loc_id,loc_dest_id=loc_dest_id, partner_id=partner_id)
        cft=False
                  
           
        if partner_id:
              
            if prod_id and paying_agent_id and type=='out':
                product = self.pool.get('product.product').browse(cr, uid, [prod_id], context={})[0]
                price=product.list_price
                if product.cft:
                    cft=product.cft
                res['value']['cft']=cft
                for i in product.customer_ids:
                    if i.name.id==partner_id:
                        
                        res['value']['price_unit']=i.proforma_price
                        proforma_price=i.proforma_price
                if proforma_price==0:
                    res['value']['price_unit']=product.list_price
                if price==0.0 and proforma_price==0:    
                       raise osv.except_osv(_('Warning'),_('Check Goods Price, Selected Customer Do Not Have Rate In The Goods Master'))
                 
#         if res.get('value',''):
#             del res['value']['product_qty']
        return res
    
    def onchange_delivey_date(self, cr, uid, ids, delivery_date,partner_id, paying_agent_id, type):
        res = {}
        if not partner_id and type=='out':
            raise osv.except_osv(_('Warning'),_('Before Choosing a Product,Select a Customer in the DC Form.'))

        if not paying_agent_id:
             if type!='out':
                 if not partner_id:
                     raise osv.except_osv(_('Warning'),_('Before Choosing a Product,Select a Facilitator in the form.'))
                    
             else:
                raise osv.except_osv(_('Warning'),_('Before Choosing a Product,Select a Facilitator in the DC form.'))
                               
        return {'value' : res}

            
     
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
        res['pay_freight']=False
        for i in partner_obj.browse(cr,uid,partner_ids):
            res['partner'] = ''
            if 'associate' in i.name.lower():
                if uid!=1:
                    res['partner']=i.ref
            if i.sub_facilitator_ids:
                cr.execute("select sub_part_id from sub_facilitator where main_facilitator_id="+str(i.id))
                sub_facilitator_id = [x[0] for x in cr.fetchall()]
                if sub_facilitator_id:
                    dom.update({'sub_facilitator_id':  [('id','in',sub_facilitator_id )]})
                    res.update({'is_sub_facilitator': True})
            else:
                    dom.update({'sub_facilitator_id':  [('id','in',0)]})
                    res.update({'is_sub_facilitator': False})
        return {'value':res, 'domain':dom}
            
        
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
    
    def get_user_qty(self, cr, uid, ids,context = None):
        self.get_day_date(cr,uid,ids)
        cr.execute("select id from stock_picking where type ='in' and qty is null or users is null or location_id is null or year is null")
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
                
                for case in self.browse(cr, uid, [n]):
                    if case.type=='in':
                        if not case.location_id: 
                            for temp in case.move_lines:
                                cr.execute("update stock_picking set location_id=%s where id=%s",(temp.location_dest_id.id,case.id,))
                                cr.execute("UPDATE stock_picking SET product_id =%s where id=%s", (temp.product_id.id,case.id,))
            
                cr.execute("select to_char(s.date, 'YYYY') as year,to_char(s.date, 'MM') as month,to_char(s.date, 'YYYY-MM-DD') as day from stock_picking s where id =%s",(i,))
                date=cr.fetchall()[0]
                if date:
  
                    cr.execute("UPDATE stock_picking SET year =%s where id=%s", (date[0],i))
                    cr.execute("UPDATE stock_picking SET month =%s where id=%s", (date[1],i))
                    cr.execute("UPDATE stock_picking SET day =%s where id=%s", (date[2],i))
                
        return True
    
    def _get_move_lines(self, cr, uid, ids, args, field_name, context = None):
        if not context:
            context={}
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
                prod_id=temp.product_id
                res[case.id] = {'product': " ", 'qty':0.00,'location_id':0,'users':''}
                res[case.id]['product']  = temp.product_id.name
                if prod_id:
                    cr.execute("UPDATE stock_picking SET product_id =%s where id=%s", (prod_id.id,case.id))
                res[case.id]['qty']  = temp.product_qty  
                res[case.id]['location_id']=temp.location_dest_id.id
                if temp.location_dest_id:
                    cr.execute("UPDATE stock_picking SET dest_location_id ="+str(temp.location_dest_id.id)+" where id="+str(case.id))
                cr.execute("select create_uid from stock_picking where id="+str(case.id))
                create_uid=cr.fetchone()[0]
                cr.execute("select login from res_users where id  ="+str(create_uid))
                user=cr.fetchone()[0]
                res[case.id]['users']=user
                d=case.id
#                 print "case.paying_agent_id.state_id.id", case.paying_agent_id.state_id.name
#                 cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (case.paying_agent_id.state_id.id,d)) 
                
            if case.date_function!=case.date:
                        cr.execute("UPDATE stock_picking SET date_function =%s where id=%s", (case.date,d))
            if case.year=='':
                cr.execute("select to_char(s.date, 'YYYY') as year,to_char(s.date, 'MM') as month,to_char(s.date, 'YYYY-MM-DD') as day from stock_picking s where id =%s",(d,))
                date=cr.fetchall()[0]
                if date:
  
                    cr.execute("UPDATE stock_picking SET year =%s where id=%s", (date[0],d))
                    cr.execute("UPDATE stock_picking SET month =%s where id=%s", (date[1],d))
                    cr.execute("UPDATE stock_picking SET day =%s where id=%s", (date[2],d))
#                 cr.execute("UPDATE stock_picking SET state_id =%s where id=%s", (case.paying_agent_id.state_id.id,d))  
                cr.execute("select product_id from stock_move where picking_id=%s",(d,))
                product_id=cr.fetchone()[0]
                cr.execute("UPDATE stock_picking SET product_id =%s where id=%s", (product_id,d))
#             self.get_user_qty(cr, uid, ids, context)
        return res
    
    
    
    def _get_inv_status(self, cr, uid, ids, field_name, args, context = None):
        res = {}
        for case in self.browse(cr, uid, ids):
            cr.execute("""select id from account_invoice where state != 'cancel'
                and id in (select invoice_id from incoming_shipment_invoice_rel where in_shipment_id = """+str(case.id)+""" )
            """)
            Iinv_ids = cr.fetchall()
            if Iinv_ids:
                res[case.id] = True
            else:
                res[case.id] = False
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

              'location_id'     : fields.function(_get_move_lines,type="many2one",relation = 'stock.location',string="Stock Location",store=True,multi="move_lines"),
           'dest_location_id'        : fields.many2one('stock.location','Location'),
              'product_id'      : fields.many2one('product.product', 'Products',track_visibility='onchange'),
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
             'sup_invoice'    :   fields.function(_get_inv_status, type="boolean",string ='Facilitator Invoice', store=True),
              
               #for search view
              'date_from':fields.function(lambda *a,**k:{}, method=True, type='date',string="From"),
              'date_to':fields.function(lambda *a,**k:{}, method=True, type='date',string="To"),
              'freight_balance' :fields.float('Freight Balance',digits=(0,2),track_visibility='onchange'),
              'state'         :   fields.selection([('draft','Draft'),('in_transit','In Transit'),('auto', 'Waiting Another Operation'),
                                                      ('confirmed', 'Waiting Availability'),
                                                      ('assigned', 'Ready to Deliver'),
                                                      ('done', 'Delivered'),
                                                      ('cancel', 'Cancelled'),('freight_paid','Freight Paid')],'Status', readonly=True, select=True,), 
                   
               # Bank details
                'bank_name'     :   fields.char("Bank Name", size=100),
                'ifsc_code'     :   fields.char("IFSC Cde", size=11),
                'ac_holder'     :   fields.char("Beneficiary Name", size=100),
                'ac_number'     :   fields.char("Account Number", size=30),
                'bank_addr'     :   fields.text("Bank Address"),
                'ac_holder_mob' :   fields.char("Mobile Number", size=10),
                'ac_holder_pan' :   fields.char("Pan Number", size=20),
                'bene_code'     :   fields.char("Beneficiary Code", size=30),

                'sub_facilitator_id'    :   fields.many2one("res.partner", "Sub Facilitator"),
                'purchase_amount'       :   fields.float("Purchase Amount", digits=(16,2)),
                'is_sub_facilitator'    :   fields.boolean("Is Sub Facilitator")


              }
    
    _order = 'date desc'
    

    _defaults={
                 'purchase_id': False,
                 'location_id': get_location,
                 'type'       : 'in',
                 'sup_invoice':False,
              }
 
    # Mail,IF no product rate while creating facilitator invoice by schedular
    def send_mail_prod_rate(self,cr,uid,ids,context=None):
        res={}
        if not context:
            context = {}
        state = context.get('state',False)
        print 'context',context
        type = context.get('type','')
        partners = ''
        mail_obj = self.pool.get('mail.mail')
        partner_obj = self.pool.get('res.partner')
        email_obj = self.pool.get('email.template')
        prod_obj = self.pool.get('product.product')
        if type == 'in':
            template = self.pool.get('ir.model.data').get_object(cr, uid,'kingswood', 'kw_send_mail_prod_rate_ship')
        else:
            template = self.pool.get('ir.model.data').get_object(cr, uid,'kingswood', 'kw_send_mail_prod_rate')
        assert template._name == 'email.template'
        
        for case in self.browse(cr,uid,ids):
            
            cr.execute(""" select distinct rp.email 
                            from res_groups_users_rel gu 
                            inner join res_groups g on g.id = gu.gid
                            inner join res_users ru on ru.id = gu.uid
                            inner join res_partner rp on rp.id = ru.partner_id  
                            where g.name = 'KW_Admin' and rp.email is not null""")
            for p in cr.fetchall():
#                 p = partner_obj.browse(cr, uid,p[0])
                partners += (p and p[0] or "") + ","
            if partners:
                print partners
                email_obj.write(cr, uid, [template.id], {'email_to':partners[0:-1]})
                        
            mail_id = self.pool.get('email.template').send_mail(cr, uid, template.id, case.id, True, context=context)
            mail_state = mail_obj.read(cr, uid, mail_id, ['state'], context=context)
            if mail_state and mail_state['state'] == 'exception':
                raise osv.except_osv(_("Cannot send email(date): no outgoing email server configured.\nYou can configure it under Settings/General Settings."), case.delivery_manager_id.partner_id.name)
            prod_obj.write(cr,uid,[case.product_id.id],{'product_rate':True,'dc_state':state})
            print "--------------STOP No Rate__________",case.name
        return True

    def get_supplier_rate(self,cr,uid,ids,freight,context=None):
        journal_obj = self.pool.get('account.journal')
        schedular = context.get('schedular',False)
        today = time.strftime('%Y-%m-%d')
        schedular_state = context.get('state',False) 
        run_schedular = True       
        print "incoming shiipment", ids
        product_groups = {}
        delivery_orders = {}
        date_groups={}
        inv_obj = self.pool.get('account.invoice')
        kwprod_obj=self.pool.get('kw.product.price')
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
        in_invoices = []
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
        back_date = False
        frt=0
#         journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase')])[0]
        prod_obj=self.pool.get('kw.product.price')
        kw_prod_obj = self.pool.get('product.product')
        sup_freight_ids=kw_prod_obj.search(cr, uid, [('name_template','=','Freight')])
        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
        kw_paying_agent=cr.fetchall()
        kw_paying_agent=zip(*kw_paying_agent)[0]        
        order_id = []
        company=cr.fetchone()
        if company:
            company=company[0]
        log_user={}
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        g_ids = []
        if user.role!='admin':
                raise osv.except_osv(_('Warning'),_('You Cannot Create Invoice For The Incoming Shipments'))

        if schedular:
            back_date = True
            for stock in self.browse(cr, uid, ids):
                if stock.partner_id.id in kw_paying_agent:
                    ids.remove(stock.id)
                stock_type = stock.type
                price1 = 0.0
#                 if stock.paying_agent_id.id not in kw_paying_agent:
                for line in stock.move_lines:

                        location = line.location_dest_id.id

                        cr.execute("""select 
                                kw.id,
                                kw.product_price,
                                kw.sub_total,
                                kw.handling_charge,
                                kw.transport_price 
                            from product_supplierinfo ps
                            inner join kw_product_price kw on ps.id = kw.supp_info_id
                            and ps.product_id = %s
                            and ps.depot = %s
                            and ef_date <='%s'
                            and ps.name = %s
                            order by ef_date desc limit 1""" % (line.product_id.id, location,stock.date,stock.partner_id.id ))
                         
                        prod_ids = [x[0] for x in cr.fetchall()]
                    
                for js in kwprod_obj.browse(cr,uid,prod_ids):
                        price1 = js.product_price + js.transport_price
                        freight_price = js.transport_price                        
                         
                if price1 == 0 :     
                    context.update({'DC':stock.name,'product':line.product_id.name,'date':line.delivery_date,'return_inv':True,'type':stock.type})
                    print "Failed",stock.name
                    self.send_mail_prod_rate(cr,uid,[stock.id],context)
                    run_schedular = False
                    return False
        return True

        
    def get_invoice(self,cr,uid,ids,freight,context=None):
        journal_obj = self.pool.get('account.journal')
        schedular = context.get('schedular',False)
        today = time.strftime('%Y-%m-%d')
        schedular_state = context.get('state',False) 
        run_schedular = True       
        print "incoming shipment", ids
        product_groups = {}
        delivery_orders = {}
        account_expense_sup = []
        date_groups={}
        inv_obj = self.pool.get('account.invoice')
        kwprod_obj=self.pool.get('kw.product.price')
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
        in_invoices = []
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
        tx_ids = []
        partner_name=''
        s_id={}
        s_parent_id=False
        back_date = False
        frt=0
        c_account_parent=self.pool.get('account.account')
#         journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase')])[0]
        prod_obj=self.pool.get('kw.product.price')
        kw_prod_obj = self.pool.get('product.product')

        cr.execute("select id from res_company where lower(name) like '%logistics%'")
        cr.execute("select id from res_partner where lower(name) like 'kingswood%'")
        kw_paying_agent=cr.fetchall()
        kw_paying_agent=zip(*kw_paying_agent)[0]        
        order_id = []
        company=cr.fetchone()
        if company:
            company=company[0]
        log_user={}
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, [uid])[0]
        g_ids = []
        if user.role!='admin':
                raise osv.except_osv(_('Warning'),_('You Cannot Create Invoice For The Incoming Shipments'))

#         if schedular:
#             back_date = True
#             for stock in self.browse(cr, uid, ids):
#                 if stock.partner_id.id in kw_paying_agent:
#                     ids.remove(stock.id)
#                 stock_type = stock.type
#                 price1 = 0.0
# #                 if stock.paying_agent_id.id not in kw_paying_agent:
#                 for line in stock.move_lines:
# 
#                         location = line.location_dest_id.id
# 
#                         cr.execute("""select 
#                                 kw.id,
#                                 kw.product_price,
#                                 kw.sub_total,
#                                 kw.handling_charge,
#                                 kw.transport_price 
#                             from product_supplierinfo ps
#                             inner join kw_product_price kw on ps.id = kw.supp_info_id
#                             and ps.product_id = %s
#                             and ps.depot = %s
#                             and ef_date <='%s'
#                             and ps.name = %s
#                             order by ef_date desc limit 1""" % (line.product_id.id, location,stock.date,stock.partner_id.id ))
#                          
#                         prod_ids = [x[0] for x in cr.fetchall()]
#                     
#                 for js in kwprod_obj.browse(cr,uid,prod_ids):
#                         price1 = js.product_price + js.transport_price
#                         freight_price = js.transport_price                        
#                          
#                 if price1 == 0 :     
#                     context.update({'DC':stock.name,'product':line.product_id.name,'date':line.delivery_date,'return_inv':True,'type':stock.type})
#                     print "Failed",stock.name
#                     self.send_mail_prod_rate(cr,uid,[stock.id],context)
#                     run_schedular = False
#                     return False
            
        if ids:
            print "incoming", len(ids)
            print ids
            cr.execute("""SELECT dr.in_shipment_id FROM incoming_shipment_invoice_rel dr inner join account_invoice ac on ac.id=dr.invoice_id WHERE dr.in_shipment_id  IN %s and ac.state <>'cancel'""",(tuple(ids),))             
#             cr.execute("SELECT in_shipment_id FROM incoming_shipment_invoice_rel WHERE in_shipment_id IN %s ",(tuple(ids),))
            order_id = cr.fetchall()
        
        if order_id:
            raise osv.except_osv(_('Warning'),_('Invoice Already Created for the Incoming Shipments'))
        if run_schedular:
           
            for case in self.browse(cr, uid, ids):
                cr.execute("select id from stock_picking where delivery_date_function >= '2017-07-01 00:00:00' and id ="+str(case.id))
                pk_ids = [x[0] for x in cr.fetchall()]
                if pk_ids:
                    sup_freight_ids=kw_prod_obj.search(cr, uid, [('name_template','=','HC')])
                else:
                    sup_freight_ids=kw_prod_obj.search(cr, uid, [('name_template','=','Freight')])

                # Updating Tax
                if pk_ids:
                        if case.state_id and case.state_id.id == case.paying_agent_id.state_id.id:
                           cr.execute("select id from account_tax where gst_categ='intra' ")
                           intra_tax_id= [x[0] for x in cr.fetchall()]
                           intra_tax_id = tuple(intra_tax_id)
                           if intra_tax_id:
                               cr.execute("select tax_id from product_supplier_taxes_rel where prod_id=%s and tax_id in %s",(case.product_id.id,intra_tax_id))
                               tx_ids = [x[0] for x in cr.fetchall()]
                           else:
                               raise osv.except_osv(_('Warning'),_('Map proper Taxes for Intra State'))

                        else:
                           cr.execute("select id from account_tax where gst_categ='inter' ")
                           inter_tax_id= [x[0] for x in cr.fetchall()]
                           inter_tax_id = tuple(inter_tax_id)
                           if inter_tax_id:
                               cr.execute("select tax_id from product_supplier_taxes_rel where prod_id=%s and tax_id in %s",(case.product_id.id,inter_tax_id))
                               tx_ids = [x[0] for x in cr.fetchall()]
                           else:
                               raise osv.except_osv(_('Warning'),_('Map proper Taxes for Inter State'))
                        _logger.info('Supplier Tax Ids==========================> %s',tx_ids)
                print "incominng", case.name
                journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase'),('company_id','=',case.company_id.id)])[0]
    #             handling_journal_id = journal_obj.search(cr, uid, [('type', '=', 'purchase'),('company_id','=',company)])[0]
                type=case.type
                if case.state in ('done','freight_paid') and type=='in':
                    a=""
                    loaded_qty = 0
                    rejected_qty = 0
                    loc=0
                    for ln in case.move_lines:
                        
                                    
                        vals['product_id']          = ln.product_id.id
                        vals['name']                = ln.name
                        vals['quantity']            = ln.product_qty
                        vals['uos_id']              = ln.product_uom.id
                        vals['price_unit']          = 0
                        vals['invoice_line_tax_id'] = [(6, 0, tx_ids)]
                        
                        
                        
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
                        if 'Firewood' in str(ln.product_id.name):
                            if case.partner_id.state_id.code == "KA":
                                account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of FW-Local')])
                            else:
                                   account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of FW-Interstate')])
#                                    
#                             if case.partner_id.state_id.code == "TN":
#                                     account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of FW-Interstate-TN')])
#                             if case.partner_id.state_id.code == "AP":
#                                     account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of FW-Interstate-AP')]) 
                        else:
                            if case.partner_id.state_id.code == "KA":
                                   account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Local')])
                            else:
                                   account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Interstate')])
                                        
#                             if case.partner_id.state_id.code == "TN":
#                                 if case.partner_id.state_id.id == case.paying_agent_id.state_id.id:
#                                     account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Local-TN')])
#                                 else: 
#                                     account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Interstate-TN')])
#                             if case.partner_id.state_id.code == "AP":
#                                 if case.partner_id.state_id.id == case.paying_agent_id.state_id.id:
#                                     account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Local-AP')])
#                                 else: 
#                                     account_expense_sup = c_account_parent.search(cr,uid,[('company_id','=',case.company_id.id),('name','=','Purchase of wood-Interstate-AP')])
                                                            
                        if account_expense:
                            handling_vals['account_id'] = account_expense[0]
                            vals['account_id'] = account_expense[0]
                        if account_expense_sup:    
                            vals['account_id'] = account_expense_sup[0]
                        
                        for i in ln.product_id.seller_ids:
                             if case.partner_id.id == i.name.id:
                                 if ln.location_dest_id.id == i.depot.id:
                                    
                                    loc=1;
                                    prod_ids=prod_obj.search(cr, uid, [('ef_date','<=',case.date),('supp_info_id','=',i.id)],limit=1, order='ef_date desc')
                                    for j in prod_obj.browse(cr,uid,prod_ids):
                                        price1 = j.sub_total or (j.product_price +j.transport_price)
                                        
                                        vals['price_unit']  = price1
                                        freight_price = j.transport_price
                                        partner = j.partner_id
                                        partner_name = j.partner_id.name
                                        handling_vals['price_unit'] = j.handling_charge or 0
                                        qty = ln.product_qty
                                        if partner:
                                            s_parent_id = j.partner_id.property_account_payable and j.partner_id.property_account_payable.id or False
                                            s_id.update({partner.id:s_parent_id})
                                        if price1>0:    
                                            cr.execute("update stock_picking set sup_invoice=True where id=%s ",(case.id,))
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
                                                                    'partner_id'     :  partner and partner.id,
                                                                    'date_invoice'   :  case.date_function,
                                                                    'type'           :  'in_invoice',
                                                                    'journal_id'     :  journal_id,
                                                                    'back_date'      :  back_date,
                                                                    'freight'        :  False,
                                                                    'origin'         :  'IN',
                                                                    'branch_state'   :  partner.state_id.id,
                                                                }
                                 
                                 
                                 handling_invoices_lines[handling_key] = [(handling_vals.copy())]
                             else:
                                 
                                  handling_invoices_lines[handling_key][0]['quantity'] += ln.product_qty
                                  handling_del_orders[handling_key].append(case.id)                        
                        
                              
                        if loc==0:
                            if not schedular:
                                raise osv.except_osv(_('Warning'),_('Check Loccation, %s  for the Selected Supplier "%s" Not Found in Goods Master for "%s"')% 
                                                 (ln.location_dest_id.complete_name,case.partner_id.name,ln.product_id.name ))   
                        if price1==0:
                            if not schedular:
                                raise osv.except_osv(_('Warning'),_('Check Goods Price, Selected Supplier "%s" Do Not Have Rate for "%s" In The Goods Master')% (case.partner_id.name,ln.product_id.name ))
    #                     else:
    #                         cr.execute("update stock_picking set sup_invoice=True where id=%s ",(case.id,))
    
    
    #                     #check for the key
                        if case.sub_facilitator_id:
                            supp_key = case.sub_facilitator_id.id,case.date_function
                            product_key =case.sub_facilitator_id.id,ln.product_id.id,ln.price_unit
                        else:
                            supp_key = case.partner_id.id,case.date_function
                            product_key =case.partner_id.id,ln.product_id.id,ln.price_unit
                        if supp_key not in supp_inv_group:
                            supp_del_orders[supp_key] =[case.id]
                            supp_inv_group[supp_key] = {'partner_id'   : case.sub_facilitator_id and case.sub_facilitator_id.id or case.partner_id.id,
                                                         'origin'   :   'IN',
                                                         'date_invoice': case.date_function,
                                                         'type':   'in_invoice',
                                                         'freight'      : False,
                                                         'journal_id' : journal_id,
                                                         'branch_state'    : case.partner_id.state_id.id,
                                                         'back_date'      :back_date,
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
                print "line_vals.........",line_vals
                sup_inv_vals.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_invoice', supp_inv_group[inv]['partner_id'])['value'])
                # Updating Tax for the Supllier Invoice Creating from Incomingshipment
                line_vals[inv][0][2].update({"invoice_line_tax_id":[(6, 0, tx_ids)]})
                sup_inv_vals.update(supp_inv_group[inv])
                sup_inv_vals.update({
                                                
                                    'invoice_line': line_vals[inv],
                                    'incoming_shipment_ids': [(6, 0, supp_del_orders[inv])],
                                })
                
    #             if ln.location_id.name == "Suppliers":
                context.update({'type':'in_invoice'})
                inv1 = inv_obj.create(cr, uid, sup_inv_vals,context=context) 
                if inv1:
                    inv_obj.button_reset_taxes(cr, uid, [inv1], {})
                    in_invoices.append(inv1)
                
            context.update({'in_invoices':in_invoices}) 
            print 'incoming_context',context
            #Handing Charges invoice
            for handling_inv in handling_invoices_lines:
                handling_invoices.update(inv_obj.onchange_partner_id(cr, uid, ids,'in_invoice', handling_group[handling_inv]['partner_id'])['value'])
                handling_invoices.update(handling_group[handling_inv])
                handling_invoices.update({
                                                                    
                                            'incoming_shipment_ids' : [(6, 0, handling_del_orders[handling_inv])],
                                            'invoice_line'          : [(0,0,handling_invoices_lines[handling_inv][0])],
                                            'handling_charges'      : True
                                                                                                                                        
                                         }) 
                  
             
                if s_parent_id:
                       
                    context.update({'type':'in_invoice'})
                    #to create freight invoice for supplier
                    handl_inv_id = inv_obj.create(cr, uid, handling_invoices)
                    cr.execute("update account_invoice set handling_charges=true where id="+str(handl_inv_id))
        return True
    

    
#     # TODO: commented for testing 
    def create(self,cr,uid,vals,context=None):
        seq_code=False
        move_lines=[]
        today = time.strftime('%Y-%m-%d') 
        user = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        sub_part_obj = self.pool.get("sub.facilitator")
         
        # for creating the sequence code
         
                 
        cr.execute("select code from account_fiscalyear where date_start <= '"+today+"' and date_stop >='" +today+"'")
        seq_code = cr.fetchone()
        if not seq_code:
            raise osv.except_osv(_('Warning'),_('Please Create Fiscal Year For "%s"')%(today))
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
        res=  super(stock_picking_in,self).create(cr, uid, vals, context)
        if res:
            for temp in self.browse(cr, uid, [res]):
                # Purchase Amount Calculation
                if temp.sub_facilitator_id and temp.sub_facilitator_id.id:
                    if temp.type == 'in':
                        cr.execute("""
                            select case when kw.sub_total is null then kw.product_price else kw.sub_total end

                                from product_supplierinfo ps
                                inner join kw_product_price kw on ps.id = kw.supp_info_id
                                and ps.product_id = (select product_id from stock_picking where id ="""+str(temp.id)+""")
                                and ps.name = (select partner_id from stock_picking where id = """+str(temp.id)+""")
                                and ef_date <= (select date::date from stock_picking where id = """+str(temp.id)+""")
                                order by ef_date desc limit 1
                        """)
                    if temp.type == 'out':
                        cr.execute("""
                            select case when kw.sub_total is null then kw.product_price else kw.sub_total end

                            from product_supplierinfo ps
                            inner join kw_product_price kw on ps.id = kw.supp_info_id
                            and ps.product_id = """+str(temp.product_id.id)+"""

                            and ef_date <= '"""+str(temp.date)+"""' ::date
                            and ps.name = """+str(temp.paying_agent_id.id)+"""
                            and (case when ps.customer_id is null then ps.depot = (select location_id from stock_move where picking_id = """+str(temp.id)+""" limit 1)
                            else case when ps.customer_id is null and ps.depot is null then ps.city_id = """+str(temp.city_id.id)+""" else ps.customer_id = """+str(temp.partner_id.id)+""" end end)
                            order by ef_date desc limit 1
                        """)
                    goods_rate = [x[0] for x in cr.fetchall()]
                    if goods_rate:
                        goods_rate = goods_rate[0]
                        _logger.error('Goods Rate=================: %s', goods_rate)
                        _logger.error('Temp Qty=================: %s', temp.qty)
                        purchase_amount = float(temp.qty * goods_rate)
                        if purchase_amount > 0:
                            cr.execute("update stock_picking set purchase_amount="+str(purchase_amount)+" where id="+str(temp.id))

                    cr.execute("""select id from sub_facilitator
                                    where sub_part_id="""+str(temp.sub_facilitator_id.id)+"""
                                    and '"""+str(temp.date)+"""'::date>= from_date and '"""+str(temp.date)+"""'::date <= to_date
                                """)
                    sub_part_ids = [x[0] for x in cr.fetchall()]
                    if sub_part_ids:
                        sub_part_ids = sub_part_ids[0]
                        sub_part = sub_part_obj.browse(cr, uid, sub_part_ids)
                        if sub_part.total_purchase >= float(1850000):
                            raise osv.except_osv(_('Warning'),_('Total Purcase is exceeded for the selected Sub Facilitator.'))
        return res

#     def write(self, cr, uid, ids, vals, context = None): 
#         res = super(stock_picking_in,self).write(cr, uid, ids, vals, context)
#         in_p_id=False
#         type=context.get('default_type',False)
#         if type=='in':
#             
#             if 'move_lines' in vals: 
#                 in_p_id=vals['move_lines'][0][2].get('product_id',False)
#                 if in_p_id:
#                     vals['product_id']=in_p_id
#             else:
#                 for case in self.browse(cr, uid, ids):
#                     in_p_id=temp.product_id.id
#                     for temp in case.move_lines:  
#                         vals['product_id']=temp.product_id.id
#         return res
    
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
    
    def kw_pay_freight(self, cr, uid, ids, context = None):
        pick_obj = self.pool.get('stock.picking.out')
        return pick_obj.kw_pay_freight(cr, uid, ids, context)


    def write(self, cr, uid, ids, vals, context):
        if not context:
            contxet = {}
        sub_part_obj = self.pool.get("sub.facilitator")
        res = super(stock_picking_in, self).write(cr, uid, ids, vals, context=context)
        for temp in self.browse(cr, uid, ids):

            # Purchase Amount Calculation
            if temp.sub_facilitator_id and temp.sub_facilitator_id.id:
                if temp.type == 'in':
                    cr.execute("""
                        select case when kw.sub_total is null then kw.product_price else kw.sub_total end

                            from product_supplierinfo ps
                            inner join kw_product_price kw on ps.id = kw.supp_info_id
                            and ps.product_id = (select product_id from stock_picking where id ="""+str(temp.id)+""")
                            and ps.name = (select partner_id from stock_picking where id = """+str(temp.id)+""")
                            and ef_date <= (select date::date from stock_picking where id = """+str(temp.id)+""")
                            order by ef_date desc limit 1
                    """)
                if temp.type == 'out':
                    cr.execute("""
                        select case when kw.sub_total is null then kw.product_price else kw.sub_total end

                        from product_supplierinfo ps
                        inner join kw_product_price kw on ps.id = kw.supp_info_id
                        and ps.product_id = """+str(temp.product_id.id)+"""

                        and ef_date <= '"""+str(temp.date)+"""' ::date
                        and ps.name = """+str(temp.paying_agent_id.id)+"""
                        and (case when ps.customer_id is null then ps.depot = (select location_id from stock_move where picking_id = """+str(temp.id)+""" limit 1)
                        else case when ps.customer_id is null and ps.depot is null then ps.city_id = """+str(temp.city_id.id)+""" else ps.customer_id = """+str(temp.partner_id.id)+""" end end)
                        order by ef_date desc limit 1
                    """)
                goods_rate = [x[0] for x in cr.fetchall()]
                if goods_rate:
                    goods_rate = goods_rate[0]
                    _logger.error('Goods Rate=================: %s', goods_rate)
                    _logger.error('Temp Qty=================: %s', temp.qty)
                    purchase_amount = float(temp.qty * goods_rate)
                    if purchase_amount > 0:
                        cr.execute("update stock_picking set purchase_amount="+str(purchase_amount)+" where id="+str(temp.id))

                cr.execute("""select id from sub_facilitator
                                where sub_part_id="""+str(temp.sub_facilitator_id.id)+"""
                                and '"""+str(temp.date)+"""'::date>= from_date and '"""+str(temp.date)+"""'::date <= to_date
                            """)
                sub_part_ids = [x[0] for x in cr.fetchall()]
                if sub_part_ids:
                    sub_part_ids = sub_part_ids[0]
                    sub_part = sub_part_obj.browse(cr, uid, sub_part_ids)
                    if sub_part.total_purchase >= float(1850000):
                        raise osv.except_osv(_('Warning'),_('Total Purcase is exceeded for the selected Sub Facilitator.'))
        return res


stock_picking_in()



