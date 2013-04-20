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

class import_receipt_data(osv.osv_memory):
    _name = "import.receipt.data"
    
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
    
    def import_receipt_data(self, cr, uid,ids, context=None):
        file_path = "/home/ashvin/Desktop/script/RECEIPTHEADER.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True

        _logger.info("Starting Import PO Process from file '%s'."%(file_path))
        reciept_pool =self.pool.get('stock.picking.receipt')
        indent = []
        rejected =[]
        for data in data_lines:
            try:
                inword_date,grn_r_date,partner,excisable,recieved,gpdate,purchase_id = False,False,False,False,False,False,False
                trcode = ''
                origin = ''
                Inword_ids = []
                if data["INWARDNO"]:
                    inword_number = data["INWARDNO"]
                    if inword_number:
                        Inword_ids = self.pool.get('stock.picking').search(cr, uid, [('maize_in','=',inword_number)])
                if Inword_ids:
                    inword_data = self.pool.get('stock.picking').browse(cr, uid, Inword_ids[0], context)
                    purchase_id = inword_data.purchase_id and inword_data.purchase_id.id or False
                    origin = inword_data.purchase_id and inword_data.purchase_id.name or ''
                if data["RECPTNO"]: reciept_number = data["RECPTNO"]
                if data["TRCODE"]: trcode = data["TRCODE"]
                #For activation just change first field in picking as a character instead of integer
                if data["CHALLAN"]: challan_number = data["CHALLAN"]

                if data.get("EXCISABLE") and data["EXCISABLE"] == "Y":
                    excisable = True
                if data.get("GPRECEIVED") and data["GPRECEIVED"] == "Y":
                    recieved = True
                if data["SUPPCODE"]:
                    partner = self.pool.get('res.partner').search(cr,uid,[('supp_code','=',data["SUPPCODE"])])
                if data["RCVDATE"]:
                    if data["RCVDATE"] == 'NULL' or data["RCVDATE"] == '' or data["RCVDATE"] == '00:00.0' or data["RCVDATE"] == '  ':
                        grn_r_date = ''
                    else:
                        grn_r_date=datetime.datetime.strptime(data["RCVDATE"], '%d-%m-%y').strftime("%Y-%m-%d")
                if data["INWDATE"]:
                    if data["INWDATE"] == 'NULL' or data["INWDATE"] == '' or data["INWDATE"] == '00:00.0' or data["INWDATE"] == '  ':
                        inword_date = ''
                    else:
                        inword_date=datetime.datetime.strptime(data["INWDATE"], '%d-%m-%y').strftime("%Y-%m-%d")
                if data["GPDATE"]:
                    if data["GPDATE"] == 'NULL' or data["GPDATE"] == '' or data["GPDATE"] == '00:00.0' or data["GPDATE"] == '  ':
                        gpdate = ''
                    else:
                        gpdate=datetime.datetime.strptime(data["GPDATE"], '%d-%m-%y').strftime("%Y-%m-%d")

                vals = {
                        'maize_receipt':reciept_number,
                        'partner_id': partner and partner[0] or False,
                        'purchase_id':purchase_id,
                        'origin':origin,
                        'date':gpdate,
                        'excisable_item': excisable,
                        'gp_received': recieved,
                        'gp_date': grn_r_date,
                        'inward_id': Inword_ids and Inword_ids[0] or False,
                        'inward_date':inword_date,
                        'tr_code': trcode
                }
                ok = reciept_pool.create(cr, uid, vals, context)
            except:
                rejected.append(data['RECPTNO'])
                _logger.warning("Skipping Record with reciept code '%s'."%(data['RECPTNO']), exc_info=True)
                continue
        print "REJECTED RECIEPTS", rejected
        _logger.info("Successfully completed import RECIEPT HEADER process.")
        return True

import_receipt_data()