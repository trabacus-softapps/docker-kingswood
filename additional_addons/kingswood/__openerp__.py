{
    'name'          :   'Kingswood',
    'version'       :   '1.0',
    'category'      :   'kingswood',
    'sequence'      :   2,
    'description'   :   """kingswood """,
    'author'        :   'softappsit',
    'website'       :   'http://www.softappsit.com',
    'depends'       :   ['base','sale','product','stock','purchase','account','account_voucher','account_invoice_merge'],
    'data'          :   [
                          'security/security.xml',
                          'wizard/kw_product_rate.xml', 
                          'kw_product.xml',
                         'kw_partner.xml',
                          'wizard/kw_stock_wizard.xml',
                           
                          'kw_uom_data.xml',
                          'wizard/kw_refund.xml',
                          'wizard/kw_product_qty_view.xml', 
                          
                        'kw_stock.xml',
                        
                            
#                          'stock_test.xml',
                          #'test_stock.xml',
                         'kw_sequence.xml',
                         'kw_weighment.xml',
                         
                         'security/ir.model.access.csv',
                         'security/security_rules.xml',
                         'wizard/kw_freight.xml',                         
                        'kw_account_invoice.xml',

                         'kw_invoice.xml',
                         'wizard/kw_freight.xml',
                         
#                          'wizard/invoice_group_merge.xml',
                         'kw_config.xml',
                        'kw_account_invoice_workflow.xml',
                         'kw_default.xml' , 
                         'wizard/kw_mail_compose.xml',
                                             
                         
                         ],
    'css' : ['static/src/css/style.css'],
    'js'  : ['static/src/js/kingswood.js'],
    'qweb': ['static/src/xml/kingswood.xml'],
    'installable'   :   True,
    'application'   :   True,
    'auto_install'  :   False


}