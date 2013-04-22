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

class import_inward_data(osv.osv_memory):
    _name = "import.inward.data"
    
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
        
        file_path = "/home/ashvin/Desktop/script/INWARDHEADER.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            

        _logger.info("Starting Import PO Process from file '%s'."%(file_path))
        inward_pool =self.pool.get('stock.picking.in')
        indent = []
        rejected =[]
        for data in data_lines:
            try:
                if data["INWARDNO"]:
                    name = data["INWARDNO"]
                if data["INWDATE"]:
                    if data["INWDATE"] == 'NULL' or data["INWDATE"] == '' or data["INWDATE"] == '00:00.0' or data["INWDATE"] == '  ':
                        value = ''
                    else:
                        value=datetime.datetime.strptime(data["INWDATE"], '%d-%m-%y').strftime("%Y-%m-%d 00:00:00")
                    indate = value
                gpsno = ''
                gpyr = ''
                lrno = ''
                frdesti = ''
                todesti = ''
                labno = ''
                note = ''
                if data["GPS_NO"]:
                    gpsno = data["GPS_NO"]
                if data["GPS_YEAR"]:
                    gpyr = data["GPS_YEAR"]
                    
                if data["CHALLAN"]:
                    challan = data["CHALLAN"] 
                    
                if data["SUPPCODE"]:
                    partner = self.pool.get('res.partner').search(cr,uid,[('supp_code','=',data["SUPPCODE"])])[0]

                if data["LRNO"]:
                    lrno = data["LRNO"]
                    
                if data["LRDATE"]:
                    if data["LRDATE"] == 'NULL' or data["LRDATE"] == '' or data["LRDATE"] == '00:00.0' or data["LRDATE"] == '  ':
                        value1 = False
                    else:
                        value1=datetime.datetime.strptime(data["LRDATE"], '%d-%m-%y').strftime("%Y-%m-%d")
                    lrdate = value1

                if data["FRDESTI"]:
                    frdesti = data["FRDESTI"]
                if data["TODESTI"]:
                    todesti = data["TODESTI"]

                if data["DESPATCH"]:
                    if data["DESPATCH"] == 'By tempo':
                        despatch = 'tempo'
                    elif data["DESPATCH"] == 'By truck':
                        despatch = 'truck'
                    elif data["DESPATCH"] == 'By scooter':
                        despatch = 'scooter'
                    elif data["DESPATCH"] == 'By person':
                        despatch = 'person'
                    elif data["DESPATCH"] == 'By auto rickshaw':
                        despatch = 'auto_rickshaw'
                    elif data["DESPATCH"] == 'By cycle':
                        despatch = 'cycle'
                    elif data["DESPATCH"] == 'By pedal rickshaw':
                        despatch = 'pedal_rickshaw'
                    elif data["DESPATCH"] == 'By tanker':
                        despatch = 'tanker'
                    elif data["DESPATCH"] == 'By courier':
                        despatch = 'courier'
                    elif data["DESPATCH"] == 'By loading rickshaw':
                        despatch = 'loading_rickshaw'
                    elif data["DESPATCH"] == 'By car':
                        despatch = 'car'
                    else:
                        despatch = ''
                if data["LABNO"]:
                    labno = data["LABNO"]
                    
                if data["REMARK2"]:
                    note = data["REMARK2"]                     
#                if data["REMARK1"] or data["REMARK2"] or data["REMARK3"] or data["REMARK4"]:
#                    note= data["REMARK1"] +'\n'+ data["REMARK2"] +'\n'+ data["REMARK3"] +'\n'+ data["REMARK4"]
                vals = {
                        'maize_in':name,
                        'date':indate,
                        'partner_id': partner,
                        'gp_year':gpyr,
                        'gp_no':gpsno,
                        'challan_no':challan,
                        'lr_no':lrno,
                        'lr_date':lrdate,
                        'dest_from':frdesti,
                        'dest_to':todesti,
                        'dest_to':todesti,
                        'despatch_mode':despatch,
                        'note':note,

                }
                ok = inward_pool.create(cr, uid, vals, context)
            except:
                rejected.append(data['INWARDNO'])
                _logger.warning("Skipping Record with Inward code '%s'."%(data['INWARDNO']), exc_info=True)
                continue
        print "rejectedrejectedrejected", rejected
        _logger.info("Successfully completed import Inward process.")
        return True
    
import_inward_data()