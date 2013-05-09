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
_logger = logging.getLogger("Product product")
import datetime

class import_product_supp_data(osv.osv_memory):
    _name = "import.product.supp.data"

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

    #TODO:FIX ME TO FIND INDENT
    def import_product_supp_data(self, cr, uid,ids, context=None):
        file_path = "/home/ashvin/Desktop/script/ITEM_MASTER_SUPPLIERWISE.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True

        _logger.info("Starting Import Product Process from file '%s'."%(file_path))
        product_pool =self.pool.get('product.supplierinfo')
        indent = []
        rejected =[]
#        pr = self.pool.get('product.product').search(cr,uid,[('state','=','draft')])
#        print "prprprprprprprprprprprpr", pr
#        self.pool.get('product.product').write(cr,uid,pr,{'state':'done'})
        
        for data in data_lines:
            try:
                default_code = data["ITEMCODE"].strip()
                name=data["LSUPPCODE"].strip()
                if default_code:
                    default_code = '0'+default_code
                    product_lst = self.pool.get('product.product').search(cr,uid,[('default_code','=',default_code)])
                    print "product_lstproduct_lstproduct_lst", product_lst
                    if product_lst:
                        product = product_lst[0]
                if name:
                    print "name", name
                    sp = name[1:]
                    supplier_lst = self.pool.get('res.partner').search(cr,uid,[('supp_code','=',sp)])
                    print "supplier_lstsupplier_lst", supplier_lst
                    if supplier_lst:
                        supplier = supplier_lst[0]
                if product and supplier:
                    vals = {
                            'product_id':product,
                            'name':supplier,
                            'min_qty':0,
                            'delay':1,
                            }
                    prod = self.pool.get('product.product').search(cr,uid,[('id','=',product)])[0]
                    seller = self.pool.get('product.product').browse(cr,uid,prod).seller_ids
                    seller_lst = [i.id for i in seller]
                    print ">>>>>>", seller_lst
                    if supplier not in seller_lst:
                        p = product_pool.create(cr, uid, vals, context)
            except:
                rejected.append(data['ITEMCODE'])
                _logger.warning("Skipping Record with reciept code '%s'."%(data['ITEMCODE']), exc_info=True)
                continue
        print "REJECTED Suppler product", rejected
        _logger.info("Successfully completed import RECIEPT HEADER process.")
        return True

import_product_supp_data()