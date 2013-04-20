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

class import_inward_line_data(osv.osv_memory):
    _name = "import.inward.line.data"
    
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
    
    def do_import_inward_data(self, cr, uid,ids, context=None):
        
        file_path = "/home/ashvin/Desktop/script/INWARDTRANS.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            

        _logger.info("Starting Import PO Process from file '%s'."%(file_path))
        move_pool =self.pool.get('stock.move')
        picking_pool =self.pool.get('stock.picking.in')
        indent = []
        rejected =[]
        exist_po = []
        po_picking_key = {}
        po_exist = []
        picking_exist = []
        exist_picking = []
        for data in data_lines:
            try:
                maze_name = data["INWARDNO"]
                if not maze_name in exist_picking:
                    name = ''
                    purchase_id = False
                    if data["ITEMCODE"]:
                        product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["ITEMCODE"])])[0]
                    if data["INDENTOR"]:
                        inwrd_num = data["INDENTOR"]
                    if data["INDENTNO"]:
                        maize_no = data["INDENTNO"]
                    if data["INWARDNO"]:
                        search_picking = data["INWARDNO"]
                        picking_id = self.pool.get('stock.picking').search(cr,1,[('maize_in','=',search_picking)])[0]
                    if data["RECVQTY"]:
                        rqty = data["RECVQTY"]
                    if data["INWRATE"]:
                        rate = data["INWRATE"]
                    if data["POYEAR"]:
                        poyear = data["POYEAR"]
                    if data["POSERIES"]:
                        poseries = data["POSERIES"]
                        name += poseries
                    if data["PONO"]:
                        pono = '/'+data["PONO"]
                        name += pono
                    if name:
                        purchase_id = self.pool.get('purchase.order').search(cr,1,[('maize','=',name)])
                    vals = {
                            'name':name,
                            'picking_id': picking_id,
                            'product_id': product,
                            'product_qty': rqty,
                            'product_uom': self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                            'date': '03/29/2013',
                            'location_id': 12,
                            'location_dest_id': 12,
                            'state': 'draft',
                            'price_unit':float(rate),
                            'company_id':1,
                    }
                    move_pool.create(cr, uid, vals, context)
                    exist_picking.append(maze_name)
                    if purchase_id:
                        pur_data = self.pool.get('purchase.order').browse(cr, uid, purchase_id[0],context)
                        picking_pool.write(cr, uid, picking_id, {'purchase_id': purchase_id[0], 'origin': pur_data.name})
                else:
                    picking_id = self.pool.get('stock.picking').search(cr,1,[('maize_in','=',maze_name)])[0]
                    picking_data = self.pool.get('stock.picking').browse(cr, uid, picking_id,context) 
                    pick_vals = {
                            'maize_in':picking_data.maize_in,
                            'date':picking_data.date,
                            'purchase_id':picking_data.purchase_id.id,
                            'origin':picking_data.origin or '',
                            'partner_id': picking_data.partner_id.id,
                            'gp_year':picking_data.gp_year,
                            'gp_no':picking_data.gp_no,
                            'lr_no':picking_data.lr_no,
                            'lr_date':picking_data.lr_date,
                            'dest_from':picking_data.dest_from,
                            'dest_to':picking_data.dest_to,
                            'despatch_mode':picking_data.despatch_mode,
                            'note':picking_data.note,
                        }
                    
                    new_picking_id = self.pool.get('stock.picking.in').create(cr, uid, pick_vals,context)

                    if data["ITEMCODE"]:
                        product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["ITEMCODE"])])[0]
                    if data["INDENTOR"]:
                        inwrd_num = data["INDENTOR"]
                    if data["INDENTNO"]:
                        maize_no = data["INDENTNO"]
                    if data["INWARDNO"]:
                        search_picking = data["INWARDNO"]
                        picking_id = self.pool.get('stock.picking').search(cr,1,[('maize_in','=',search_picking)])[0]
                    if data["RECVQTY"]:
                        rqty = data["RECVQTY"]
                    if data["INWRATE"]:
                        rate = data["INWRATE"]
                    if data["POYEAR"]:
                        poyear = data["POYEAR"]
                    if data["POSERIES"]:
                        poseries = data["POSERIES"]
                        name += poseries
                    if data["PONO"]:
                        pono = '/'+data["PONO"]
                        name += pono
                    if name:
                        purchase_id = self.pool.get('purchase.order').search(cr,1,[('maize','=',name)])
                    new_vals = {
                            'name':name,
                            'picking_id': new_picking_id,
                            'product_id': product,
                            'product_qty': rqty,
                            'product_uom': self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                            'date': '03/29/2013',
                            'location_id': 12,
                            'location_dest_id': 12,
                            'state': 'draft',
                            'price_unit':float(rate),
                            'company_id':1,
                    }
                    move_pool.create(cr, uid, new_vals, context)
            except:
                rejected.append(data['INWARDNO'])
                _logger.warning("Skipping Record with Inward code '%s'."%(data['INWARDNO']), exc_info=True)
                continue
        print "rejectedrejectedrejected", rejected
        _logger.info("Successfully completed import Inward process.")
        return True
    
import_inward_line_data()