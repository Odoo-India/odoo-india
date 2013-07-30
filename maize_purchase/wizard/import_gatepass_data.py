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

class import_gatepass_data(osv.osv_memory):
    _name = "import.gatepass.data"
    
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
    
    def do_import_gatepass_data(self, cr, uid,ids, context=None):
        
        file_path = "/home/jir/Desktop/header.csv"
        print "CALLED JACKY ONE >>>>>>>>>>>>>>>>>>>>>>>>"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            

        _logger.info("Starting Import PO Process from file '%s'."%(file_path))
        delivery_pool =self.pool.get('stock.picking.out')
        indent_pool =self.pool.get('indent.indent')
        indent = []
        rejected =[]
        
        for data in data_lines:
            try:
                if data["GPS_DATE"]:
                    if data["GPS_DATE"] == 'NULL' or data["GPS_DATE"] == '' or data["GPS_DATE"] == '00:00.0' or data["GPS_DATE"] == '  ':
                        value = ''
                    else:
                        value=datetime.datetime.strptime(data["GPS_DATE"], '%Y-%m-%d 00:00:00.000').strftime("%Y-%m-%d 00:00:00")
                gps_date = value
                gpsno = ''
                gpyr = ''
                note = ''
                gps_type=''
                if data["GPS_ACTION_DATE"]:
                    if data["GPS_ACTION_DATE"] == 'NULL' or data["GPS_ACTION_DATE"] == '' or data["GPS_ACTION_DATE"] == '00:00.0' or data["GPS_ACTION_DATE"] == '  ':
                        value = ''
                    else:
                        value=datetime.datetime.strptime(data["GPS_ACTION_DATE"], '%Y-%m-%d 00:00:00.000').strftime("%Y-%m-%d 00:00:00")
                action_date = value
                if data["GPS_YEAR"]:
                    gpyr = data["GPS_YEAR"]
                if data["GPS_NO"]:
                    gpsno = data["GPS_NO"]+'/'+gpyr

                gps_ser=''
                if data["GPS_SER"]:
                    if data["GPS_SER"] == "REP":
                        gps_ser = 'repair'
                    elif data["GPS_SER"] == "PUR":
                        gps_ser = 'purchase'
                    elif data["GPS_SER"] == "STR":
                        gps_ser = 'store'
                if data["GPS_SUPPCODE"]:
                    partner = self.pool.get('res.partner').search(cr,uid,[('supp_code','=',data["GPS_SUPPCODE"])])
                    un_define = self.pool.get('res.partner').search(cr,uid,[('supp_code','=','1111111')])
                    if partner:
                        partner = partner[0]
                    else:
                        partner = un_define[0]

                if data["GPS_TYPE"]:
                    if data["GPS_TYPE"] in 'F.O.C.':
                        print "CALLED"
                        gps_type = 'foc'
                    elif data["GPS_TYPE"] == 'Chargeable':
                        gps_type = 'chargeable'
                    elif data["GPS_TYPE"] == 'Sample':
                        gps_type = 'sample'
                    elif data["GPS_TYPE"] == 'Loan':
                        gps_type = 'Loan'
                    elif data["GPS_TYPE"] == 'Contract':
                        gps_type = 'contract'
                    elif data["GPS_TYPE"] == 'Cash':
                        gps_type = 'cash'
                          
                if data["GPS_IND_NO"]:
                    indent_id = indent_pool.search(cr,uid,[('maize','=',data["GPS_IND_NO"])])
                if data["GPS_REMARK1"] or data["GPS_REMARK"]:
                    note= data["GPS_REMARK"] +'\n'+ data["GPS_REMARK1"] 
                vals = {
                        'maize_out':gpsno,
                        'date':gps_date,
                        'date_done':action_date,
                        'partner_id': partner,
                        'gate_pass_type': gps_type,
                        'note':note,
                        'series':gps_ser,
                        'indent':indent_id and indent_id[0],

                }
                create_id = delivery_pool.create(cr, uid, vals, context)
            except:
                rejected.append(data['GPS_NO'])
                _logger.warning("Skipping Record with GPS code '%s'."%(data['GPS_NO']), exc_info=True)
                continue
        print "BRO REJECTED", rejected
        _logger.info("Successfully completed import Delevary Order process.")
        return True
    
import_gatepass_data()
