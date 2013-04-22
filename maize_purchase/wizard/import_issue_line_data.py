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

class import_issue_line_data(osv.osv_memory):
    _name = "import.issue.line.data"
    
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

    #TODO: FIX ME FOR LOCATION and DESTINATION LOCATION
    def import_issue_line_data(self, cr, uid,ids, context=None):
        file_path = "/home/ashvin/Desktop/script/ISSUETRANS.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True

        _logger.info("Starting Import Issue Line Process from file '%s'."%(file_path))
        issue_pool =self.pool.get('stock.picking')
        move_pool = self.pool.get('stock.move')
        indent = []
        rejected =[]
        exist_picking = []
        for data in data_lines:
            try:
                # All lines values
                maze_name = data["ISSUENO"]
                if data["ITEMCODE"]:
                    product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["ITEMCODE"])])[0]
                rec_qty = data['ISUQTY'] or 0.0
                cylinder_number = data['CYLNDRNO'] or ''
                price_unit = data['ISUVALUE'] or 0.0
                act_code = data['ACTCODE'] or False
                act_c = False
                if act_code:
                    act_c = self.pool.get('ac.code').search(cr, uid, [('code','=',act_code)])
                product_data = self.pool.get('product.product').browse(cr,uid,product)
                vals = {
                        'name':product_data.name,
                        'product_id': product,
                        'product_qty': rec_qty,
                        'product_uom': product_data.uom_id.id,
                        'location_id': 12,
                        'location_dest_id': 12,# Temporarly purpose
                        'state': 'draft',
                        'price_unit':float(price_unit),
                        'company_id':1,
                }
                #First time go into the not exist loop because of Header already Imported ;)
                if not maze_name in exist_picking:
                    issue_id = issue_pool.search(cr,1,[('maize','=',maze_name)])[0]
                    isuue_rec = issue_pool.browse(cr, uid, issue_id,context)
                    dep_code = isuue_rec.remark1
                    if dep_code:
                        search_ids = self.pool.get('stock.location').search(cr, uid, [('code','=',dep_code)])
                        if search_ids:
                            vals.update({'location_dest_id': search_ids[0]})
                    vals.update({'picking_id':issue_id})
                    move_pool.create(cr, uid, vals, context)
                    issue_pool.write(cr, uid, issue_id, {'ac_code_id':act_c and act_c[0] or False,'cylinder':cylinder_number})
                    exist_picking.append(maze_name)
                #Otherwise create new issue and attached vals with it.
                else:
                    picking_id = issue_pool.search(cr,1,[('maize','=',maze_name)])[0]
                    picking_data = issue_pool.browse(cr, uid, picking_id,context) 
                    pick_vals = {
                            'maize':picking_data.maize,
                            'date':picking_data.date,
                            'purchase_id':picking_data.purchase_id.id,
                            'origin':picking_data.origin or '',
                            'partner_id': picking_data.partner_id.id,
                            'note':picking_data.note,
                            'ac_code_id':act_c and act_c[0] or False,
                            'cylinder':cylinder_number
                        }
                    new_issue = issue_pool.create(cr, uid, pick_vals, context)
                    search_ids = self.pool.get('stock.location').search(cr, uid, [('code','=',picking_data.remark1)])
                    if search_ids:
                        vals.update({'location_dest_id': search_ids[0]})
                    vals.update({'picking_id':new_issue})
                    move_pool.create(cr, uid, vals, context)
            except:
                rejected.append(data['ISSUENO'])
                _logger.warning("Skipping Record with reciept code '%s'."%(data['ISSUENO']), exc_info=True)
                continue
        print "REJECTED RECIEPTS", rejected
        _logger.info("Successfully completed import Issue Lines process.")
        return True

import_issue_line_data()