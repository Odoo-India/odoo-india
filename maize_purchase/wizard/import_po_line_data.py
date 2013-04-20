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
        file_path = "/home/ashvin/Desktop/script/POTRANS.csv"
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
        for data in data_lines:
            try:
                maize_name = data['POSERIES']+'/'+data["PONO"]
                if not maize_name in exist_line:
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
                        
                    if data["DISCPER"]:
                        discount = data["DISCPER"]

                    ind_name = ''
                    ind = self.pool.get('indent.indent').search(cr,uid,[('maize','=',data["INDENTNO"])])
                    
                    if ind:
                        ind_name = self.pool.get('indent.indent').read(cr, uid, ind[0],['name'])['name']
                        self.pool.get('purchase.order').write(cr,uid,po[0],{'origin':ind_name})
                    if data["SQTY"]:
                        qty = data["SQTY"]
                        
                    vals = {'order_id':po[0],
                            'product_id':product,
                            'price_unit':rate,
                            'discount': discount,
                            'name':prod_name1+'\n'+prod_name2+'\n'+prod_name3+'\n'+prod_name4,
                            'product_qty':qty,
                            'product_uom':self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                            'date_planned':'03/29/2013'
                           }
                    exist_line.append(maize_name)
                    po = pol_pool.create(cr, uid, vals, context)
                    self.pool.get('purchase.order').write(cr,uid,po,{'commission':0.01})
                    self.pool.get('purchase.order').write(cr,uid,po,{'commission':0.00})
                else:
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
                    if data["SQTY"]:
                        qty = data["SQTY"]
                        
                    if data["DISCPER"]:
                        discount = data["DISCPER"]
    
    
                    vals_line = {
                            'product_id':product,
                            'price_unit':float(rate),
                            'discount': discount,
                            'product_qty':qty,
                            'name':prod_name1+'\n'+prod_name2+'\n'+prod_name3+'\n'+prod_name4,
                            'product_uom':self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                            'date_planned':'03/29/2013',
                           }
                    ind_name = ''
                    ind = self.pool.get('indent.indent').search(cr,uid,[('maize','=',data["INDENTNO"])])
                    
                    if ind:
                        ind_name = self.pool.get('indent.indent').read(cr, uid, ind[0],['name'])['name']
                                            
                    if data["PONO"] and data['POSERIES']:
                        po = po_order.search(cr,uid,[('maize','=',maize_name)])
                        pp = po_order.browse(cr, uid, po[0])
                        po_vals = {
                                'maize':pp.maize,
                                'po_series_id':pp.po_series_id.id,
                                'date_order':pp.date_order,
                                'partner_id': pp.partner_id.id,
                                'delivey':pp.delivey,
                                'origin':ind_name,
                                'location_id':12,
                                'pricelist_id':2,
                                'insurance':pp.insurance,
                                'insurance_type':pp.insurance_type,
                                'excies_ids':[(6,0,[i.id for i in pp.excies_ids])],
                                'vat_ids':[(6,0,[v.id for v in pp.vat_ids])],
                                'order_line':[(0,0,vals_line)],
                                'notes':pp.notes,
                                }
                        pop = po_order.create(cr, uid, po_vals, context)

            except:
                rejected.append(data['PONO'])
                _logger.warning("Skipping Record with Indent code '%s'."%(data['PONO']), exc_info=True)
                continue
        aaa = self.pool.get('purchase.order').search(cr,uid,[])
        self.pool.get('purchase.order').write(cr,uid,aaa,{'commission':0.01})
        self.pool.get('purchase.order').write(cr,uid,aaa,{'commission':0.00})
import_po_line_data()