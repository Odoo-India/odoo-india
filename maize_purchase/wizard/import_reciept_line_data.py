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

class import_receipt_line_data(osv.osv_memory):
    _name = "import.receipt.line.data"
    
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

    def import_receipt_line_data(self, cr, uid,ids, context=None):
        file_path = "/home/ron/Desktop/MAIZE/RECEIPTTRANS.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True

        _logger.info("Starting Import PO Process from file '%s'."%(file_path))
        reciept_pool =self.pool.get('stock.picking.receipt')
        move_pool = self.pool.get('stock.move')
        indent = []
        rejected =[]
        exist_picking = []
        for data in data_lines:
            try:
                # All lines values
                maze_name = data["RECPTNO"]
                bill_date = False
                price_unit = data['RATE'] or 0.0
                rec_qty = data['RECVQTY'] or 0.0
                bill_no = data['BILLNO'] or ''
                excies = data['EXCISE'] or 0.0
                high_exice_cess = data['EXCISEHCESS'] or 0.0
                excies_cess = data['EXCISECESS'] or 0.0
                cenvat = data['CENVAT'] or 0.0
                vat_cess = data['CENVATCESS'] or 0.0
                high_vat_cess = data['CENVATHCESS'] or 0.0
                imp_duty = data['IMPDUTY'] or 0.0
                if data["ITEMCODE"]:
                    product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["ITEMCODE"])])[0]
                if data["BILLDATE"]:
                    if data["BILLDATE"] == 'NULL' or data["BILLDATE"] == '' or data["BILLDATE"] == '00:00.0' or data["BILLDATE"] == '  ':
                        bill_date = False
                    else:
                        bill_date=datetime.datetime.strptime(data["BILLDATE"], '%d-%m-%y').strftime("%Y-%m-%d")
                # Create dictionary at once.
                product_data = self.pool.get('product.product').browse(cr,uid,product)
                vals = {
                        'name':product_data.uom_id.name,
                        'rate': price_unit,
                        'product_id': product,
                        'product_qty': rec_qty,
                        'product_uom': product_data.uom_id.id,
                        'date': '03/29/2013',
                        'location_id': 12,
                        'location_dest_id': 12,
                        'state': 'draft',
                        'price_unit':float(price_unit),
                        'company_id':1,
                        'bill_no': bill_no,
                        'bill_date': bill_date,
                        'excies': excies,
                        'cess': excies_cess,
                        'high_cess': high_exice_cess,
                        'import_duty': imp_duty,
                        'cenvat': cenvat,
                        'c_cess': vat_cess,
                        'c_high_cess': high_vat_cess
                }
                #First time go into the not exist loop because of Header already Imported ;)
                if not maze_name in exist_picking:
                    receipt_id = self.pool.get('stock.picking').search(cr,1,[('maize_receipt','=',maze_name)])[0]
                    vals.update({'picking_id':receipt_id})
                    move_pool.create(cr, uid, vals, context)
                    exist_picking.append(maze_name)
                #Otherwise create new receipt and attached vals with it.
                else:
                    picking_id = self.pool.get('stock.picking').search(cr,1,[('maize_receipt','=',maze_name)])[0]
                    picking_data = reciept_pool.browse(cr, uid, picking_id,context) 
                    pick_vals = {
                            'maize_receipt':picking_data.maize_receipt,
                            'date':picking_data.date,
                            'purchase_id':picking_data.purchase_id.id,
                            'origin':picking_data.origin or '',
                            'partner_id': picking_data.partner_id.id,
                            'excisable_item': picking_data.excisable_item,
                            'gp_received': picking_data.gp_received,
                            'gp_date': picking_data.gp_date,
                            'inward_id': picking_data.inward_id and picking_data.inward_id.id,
                            'inward_date':picking_data.inward_date,
                            'tr_code': picking_data.tr_code,
                            'note':picking_data.note,
                        }
                    new_receipt = reciept_pool.create(cr, uid, pick_vals, context)
                    vals.update({'picking_id':new_receipt})
                    move_pool.create(cr, uid, vals, context)
            except:
                rejected.append(data['RECPTNO'])
                _logger.warning("Skipping Record with reciept code '%s'."%(data['RECPTNO']), exc_info=True)
                continue
        print "REJECTED RECIEPTS", rejected
        _logger.info("Successfully completed import RECIEPT HEADER process.")
        return True

import_receipt_line_data()