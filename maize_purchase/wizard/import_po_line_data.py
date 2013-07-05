# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import datetime
from openerp.osv import fields, osv
import csv
import logging
from openerp import netsvc
_logger = logging.getLogger("Indent Indent")

class import_po_line_data(osv.osv_memory):
    _name = "import.po.line.data"
    
    def _read_csv_data(self, cr, uid, path, context=None):
        """
            Reads CSV from given path and Return list of dict with Mapping
        """
        data = csv.reader(open(path))
        # Read the column names from the first line of the file
        fields = data.next()
        data_lines = []
        for row in data:
            items = dict(zip(fields, row))
            data_lines.append(items)
        return fields,data_lines
    
    def po_line_create(self,cr,uid,ids,context=None):
        file_path = "/home/ara/Desktop/script/po/po_tra.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            

        _logger.info("Starting Import PO LINE Process from file '%s'."%(file_path))
        pol_pool =self.pool.get('purchase.order.line')
        po_order = self.pool.get('purchase.order')
        indent = []
        rejected =[]
        exist_line=[]
        indent_not_found_list = []
        for data in data_lines:
            try:
                maize_name = data['POSERIES']+'/'+data["PONO"]
                if data["PONO"] and data['POSERIES']:
                    po = self.pool.get('purchase.order').search(cr,uid,[('maize','=',maize_name)])
                if data["ITEMCODE"]:
                    product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["ITEMCODE"])])[0]
                    prod_name1 = self.pool.get('product.product').read(cr, uid, product,['name'])['name']
                    prod_name2 = self.pool.get('product.product').read(cr, uid, product,['desc2'])['desc2']
                    prod_name3 = self.pool.get('product.product').read(cr, uid, product,['desc2'])['desc2']
                    prod_name4 = self.pool.get('product.product').read(cr, uid, product,['desc3'])['desc3']
                if data["PORATE"]:
                    rate = data["PORATE"]
                department=False
                if data["DEPTCODE"].strip():
                    print ">>>>>>>>>>departmrt", data["DEPTCODE"].strip()
                    if len(data["DEPTCODE"].strip()) == 1:
                        dept = '00'+data["DEPTCODE"].strip()
                    elif len(data["DEPTCODE"].strip()) == 2:
                        dept = '0'+data["DEPTCODE"].strip()
                    elif len(data["DEPTCODE"].strip()) == 3:
                        dept = data["DEPTCODE"].strip()
                    department = self.pool.get('stock.location').search(cr, uid,[('code','=',dept)])[0]
                mach=data["MACHCODE"].strip()
                project=False
                if mach:
                    project = self.pool.get('account.analytic.account').search(cr,uid,[('code','=',mach)])[0]                      
                if data["DISCPER"]:
                    discount = data["DISCPER"]
                    #self.pool.get('purchase.order').write(cr,uid,po[0],{'discount_percentage':discount})

                ind_name = ''
                ind = self.pool.get('indent.indent').search(cr,uid,[('maize','=',data["INDENTNO"])])
                
                indent_id=False
                indentor_id=False
                if data["INDENTNO"]:
                    indent = self.pool.get('indent.indent').search(cr,uid,[('maize','=',data["INDENTNO"])])
                    print "AAAAAAAAAAAAAAAAAAAAAAAAA", indent
                    indent_id = indent and indent[0] or False
                    print "BBBBBBBBBBBBBBBBBBBBBBBBBBB", indent_id
                if data["INDENTOR"]:
                    indentor = self.pool.get('res.users').search(cr,uid,[('user_code','=',data["INDENTOR"])])
                    indentor_id = indentor and indentor[0] or ''
                if data["SQTY"]:
                    qty = data["SQTY"]
                    
                if data["DLVDATE"]:
                    if data["DLVDATE"] == 'NULL' or data["DLVDATE"] == '' or data["DLVDATE"] == '00:00.0' or data["DLVDATE"] == '  ':
                        dlv_date = ''
                    else:
                        dlv_date=datetime.datetime.strptime(data["DLVDATE"], '%Y-%m-%d 00:00:00.000').strftime("%Y-%m-%d")
                vals = {'order_id':po[0],
                        'product_id':product,
                        'price_unit':rate,
                        #'discount': discount,
                        'name':prod_name1 or ''+'\n'+prod_name2 or ''+'\n'+prod_name3 or ''+'\n'+prod_name4 or '',
                        'product_qty':qty,
                        'product_uom':self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                        'date_planned':dlv_date,
                        #'freight':freight_rs,
                        'indent_id':indent_id and int(indent_id) or '',
                        'indentor_id':indentor_id and int(indentor_id) or '',
                        'department_id':department or '',
                        'account_analytic_id':project or '',
                        'discount':discount
                       }
                print ">>>>>>>>>>>>>>>>>>>>>>>>", vals
                exist_line.append(maize_name)
                po = pol_pool.create(cr, uid, vals, context)
#                 else:
#                     indent_not_found_list.append(data["INDENTNO"])
                
#                else:
#                    if data["PONO"] and data['POSERIES']:
#                        po = self.pool.get('purchase.order').search(cr,uid,[('maize','=',maize_name)])
#                    if data["ITEMCODE"]:
#                        product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["ITEMCODE"])])[0]
#                        prod_name1 = self.pool.get('product.product').read(cr, uid, product,['name'])['name']
#                        prod_name2 = self.pool.get('product.product').read(cr, uid, product,['desc2'])['desc2']
#                        prod_name3 = self.pool.get('product.product').read(cr, uid, product,['desc2'])['desc2']
#                        prod_name4 = self.pool.get('product.product').read(cr, uid, product,['desc3'])['desc3']                        
#                    if data["PORATE"]:
#                        rate = data["PORATE"]
#                    if data["SQTY"]:
#                        qty = data["SQTY"]
#                        
#                    if data["DISCPER"]:
#                        discount = data["DISCPER"]
#                        
#                    if data["DLVDATE"]:
#                        if data["DLVDATE"] == 'NULL' or data["DLVDATE"] == '' or data["DLVDATE"] == '00:00.0' or data["DLVDATE"] == '  ':
#                            dlv_date = ''
#                        else:
#                            dlv_date=datetime.datetime.strptime(data["DLVDATE"], '%d-%m-%y').strftime("%Y-%m-%d")    
#        
#                    vals_line = {
#                            'product_id':product,
#                            'price_unit':float(rate),
#                            #'discount': discount,
#                            'product_qty':qty,
#                            'name':prod_name1 or ''+'\n'+prod_name2 or ''+'\n'+prod_name3 or ''+'\n'+prod_name4 or '',
#                            'product_uom':self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
#                            'date_planned':dlv_date,
#                           }
#                    ind_name = ''
#                    ind = self.pool.get('indent.indent').search(cr,uid,[('maize','=',data["INDENTNO"])])
#                    
#                    if ind:
#                        ind_name = self.pool.get('indent.indent').read(cr, uid, ind[0],['name'])['name']
#                                            
#                    if data["PONO"] and data['POSERIES']:
#                        po = po_order.search(cr,uid,[('maize','=',maize_name)])
#                        pp = po_order.browse(cr, uid, po[0])
#                        po_vals = {
#                                'discount_percentage':discount,
#                                'maize':pp.maize,
#                                'po_series_id':pp.po_series_id.id,
#                                'date_order':pp.date_order,
#                                'partner_id': pp.partner_id.id,
#                                'delivey':pp.delivey,
#                                'origin':ind_name,
#                                'location_id':12,
#                                'pricelist_id':2,
#                                'insurance':pp.insurance,
#                                'insurance_type':pp.insurance_type,
#                                'excies_ids':[(6,0,[i.id for i in pp.excies_ids])],
#                                'vat_ids':[(6,0,[v.id for v in pp.vat_ids])],
#                                'order_line':[(0,0,vals_line)],
#                                'notes':pp.notes,
#                                'payment_term_id':pp.payment_term_id.id,
#                                'freight':pp.freight
#                                }
#                        pop = po_order.create(cr, uid, po_vals, context)
            except:
                rejected.append(maize_name)
                
                _logger.warning("Skipping Record with Indent code '%s'."%(maize_name), exc_info=True)
                continue
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.", rejected
        #aaa = self.pool.get('purchase.order').search(cr,uid,[])
#         self.pool.get('purchase.order').write(cr,uid,aaa,{'commission':0.01})
#         self.pool.get('purchase.order').write(cr,uid,aaa,{'commission':0.00})
        return True
import_po_line_data()
