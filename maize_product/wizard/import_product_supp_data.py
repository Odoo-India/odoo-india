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

from datetime import datetime
from openerp.osv import fields, osv
import csv
import os
import logging
from openerp import netsvc
_logger = logging.getLogger("Product product")

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
    
    def _write_bounced_product_supplier(self, cr, uid, file_head, bounced_detail, context):
        if not file_head:
            _logger.warning("Can not Export bounced(Rejected) Partner detail to the file. ")
            return False
        try:
            dtm = datetime.today().strftime("%Y%m%d%H%M%S")
            fname = "BOUNCED_PRODUCT_SUPPLIER"+dtm+".csv"
            _logger.info("Opening file '%s' for logging the bounced partner detail."%(fname))
            fl= csv.writer(open(file_head+"/"+fname, 'wb'))
            for ln in  bounced_detail:
                fl.writerow(ln)
            _logger.info("Successfully exported the bounced partner detail to the file %s."%(fname))
            return True
        except Exception, e:
            print e
            _logger.warning("Can not Export bounced(Rejected) Partner detail to the file. ")
            return False

    #TODO:FIX ME TO FIND INDENT
    def import_product_supp_data(self, cr, uid,ids, context=None):
        file_path = "/home/maize/data/item_8aug/product_supplier_upto_7_aug.csv"
        
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True

        _logger.info("Starting Import Product Supplier Process from file '%s'."%(file_path))
        product_pool =self.pool.get('product.supplierinfo')
        indent = []
        rejected =[]
        bounced_product_supplier = [tuple(fields)]
#        self.pool.get('product.product').write(cr,uid,pr,{'state':'done'})
        
        for data in data_lines:
            try:
                default_code = data["ITEMCODE"].strip()
                name=data["SUPPCODE"].strip()
                if default_code:
                    default_code = '0'+default_code
                    product_lst = self.pool.get('product.product').search(cr,uid,[('default_code','=',default_code)])
                    if product_lst:
                        product = product_lst[0]
                if name:
                    supplier_lst = self.pool.get('res.partner').search(cr,uid,[('supp_code','=',name)])
                    if supplier_lst:
                        supplier = supplier_lst[0]
                if product and supplier:
                    vals = {
                            'product_id':product,
                            'name':supplier,
                            'min_qty':0,
                            'delay':0,
                            }
                    prod = self.pool.get('product.product').search(cr,uid,[('id','=',product)])[0]
                    seller = self.pool.get('product.product').browse(cr,uid,prod).seller_ids
                    seller_lst = [i.name.id for i in seller]
                    if supplier not in seller_lst:
                        p = product_pool.create(cr, uid, vals, context)
                        print "new creted parnter", p
                    else:
                        print "partner allready exist in this product"
            except:
                rejected.append(data['ITEMCODE'])
                reject = [ data.get(f, '') for f in fields]
                bounced_product_supplier.append(reject)
                _logger.warning("Skipping Record with reciept code '%s'."%(data['ITEMCODE']), exc_info=True)
                continue
        print "REJECTED Suppler product", rejected
        head, tail = os.path.split(file_path)
        self._write_bounced_product_supplier(cr, uid, head, bounced_product_supplier, context) 
        _logger.info("Successfully completed import RECIEPT HEADER process.")
        #set undefine supplier on all product where seller is none
        #prod = self.pool.get('product.product').search(cr,uid,[])
        #for p in prod:
         #   seller = self.pool.get('product.product').browse(cr,uid,p).seller_ids
          #  print "sellersellerseller", seller
          #  if not seller:
          #      s = self.pool.get('res.partner').search(cr,uid,[('supp_code','=','1111111')])[0]
          #      vals = {
          #           'product_id':p,
          #           'name':s,
          #           'min_qty':0,
          #           'delay':0,
          #           }
          #      new_created=product_pool.create(cr, uid, vals, context)
          #      print "new_creatednew_created",new_created        
        return True

import_product_supp_data()
