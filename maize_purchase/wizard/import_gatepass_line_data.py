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
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv
import csv
import logging
from openerp import netsvc
_logger = logging.getLogger("Indent Indent")

class import_gatepass_line_data(osv.osv_memory):
    _name = "import.gatepass.line.data"
    
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
    def _get_start_end_date_from_year(self,cr,uid,year):
        po_year_start=''
        po_year_end=''
        if year =='20132014':
            po_year_start = '2013-04-01'
            po_year_end = '2014-03-31'
        elif year =='20122013':
            po_year_start = '2012-04-01'
            po_year_end = '2013-03-31'
        elif year =='20112012':
            po_year_start = '2011-04-01'
            po_year_end = '2012-03-31'
        elif year =='20102011':
            po_year_start = '2010-04-01'
            po_year_end = '2011-03-31'
        elif year =='20092010':
            po_year_start = '2009-04-01'
            po_year_end = '2010-03-31'
        elif year =='20082009':
            po_year_start = '2008-04-01'
            po_year_end = '2009-03-31'
        elif year =='20072008':
            po_year_start = '2007-04-01'
            po_year_end = '2008-03-31'
        elif year =='20062007':
            po_year_start = '2006-04-01'
            po_year_end = '2007-03-31'                                
        elif year =='20052006':
            po_year_start = '2005-04-01'
            po_year_end = '2006-03-31'
        elif year =='20042005':
            po_year_start = '2004-04-01'
            po_year_end = '2005-03-31'
        elif year =='20032004':
            po_year_start = '2003-04-01'
            po_year_end = '2004-03-31'
        elif year =='20022003':
            po_year_start = '2002-04-01'
            po_year_end = '2003-03-31'
        elif year =='20012002':
            po_year_start = '2001-04-01'
            po_year_end = '2002-03-31'
        elif year =='20002001':
            po_year_start = '2000-04-01'
            po_year_end = '2001-03-31'
        return {'start':po_year_start,'end':po_year_end}                                
    
    
    def do_import_gatepass_data(self, cr, uid,ids, context=None):
        file_path = "/home/jir/Desktop/transaction.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            

        _logger.info("Starting Import Gate Pass Line Process from file '%s'."%(file_path))
        move_pool =self.pool.get('stock.move')
        picking_pool =self.pool.get('stock.picking.out')
        supplier_location = self.pool.get('stock.location').search(cr, uid, [('name','ilike','Suppliers')])
        if not supplier_location:
            raise osv.except_osv(_('Warning!'), _('Please define Supplier location in the database')) 
        indent = []
        rejected =[]
        exist_po = []
        po_picking_key = {}
        po_exist = []
        picking_exist = []
        exist_picking = []
        po_not_found = []
        indent_not_found = []
        reject = []
        print "Script Executed...."
        for data in data_lines:
            name = inwrd_num = ''
            gps_ser=''
            gps_type = ''
            gpsyr = ''
            note = ''
            if data["GPS_SER"]:
                if data["GPS_SER"] == "REP":
                    gps_ser = 'repair'
                elif data["GPS_SER"] == "PUR":
                    gps_ser = 'purchase'
                elif data["GPS_SER"] == "STR":
                    gps_ser = 'store'
            if data["GPS_TYPE"]:
                if data["GPS_TYPE"] in 'F.O.C.':
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
            if data["GPS_ITEM_CODE"]:
                product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["GPS_ITEM_CODE"]),])[0]
            if data["GPS_YEAR"]:
                gpsyr = data["GPS_YEAR"]
            if data["GPS_NO"] and gps_ser:
                search = data["GPS_NO"]+'/'+gpsyr
                picking_id = self.pool.get('stock.picking.out').search(cr,uid,[('maize_out','=',search),('series','=',gps_ser),('gate_pass_type','=',gps_type)])
                picking_id = picking_id[0]
            if data["INWARDNO"] and data["INWYEAR"]:
                search = data["INWARDNO"]+'/'+data["INWYEAR"]
                inward_id = self.pool.get('stock.picking.in').search(cr,uid,[('maize_in','=',search)])
            if data["GPS_IND_YEAR"]:
                indent_year = data["GPS_IND_YEAR"]
            if data["GPS_IND_QTY"]:
                rqty = data["GPS_IND_QTY"]
            if data["GPS_APP_RATE"]:
                rate = data["GPS_APP_RATE"]
            if data["POYEAR"]:
                poyear = data["POYEAR"]
            if data["GPS_IND_PURPOSE"] or data["GPS_IND_REMARK"]:
                note= data["GPS_IND_PURPOSE"] +'\n'+ data["GPS_IND_REMARK"]
            new_vals = {
                    'product_id': product,
                    'picking_id': picking_id,
                    'product_qty': rqty,
                    'product_uom': self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                    'location_id': 12,
                    'location_dest_id': 297,#input location fix
                    'state': 'draft',
                    'price_unit':float(rate),
                    'company_id':1,
                    'note':note,
                    }
            try:
                move_pool.create(cr, uid, new_vals,context)
                print "GPS line .. Created .....",data["GPS_NO"]+'/'+gpsyr
            except:
                reject.append(data["GPS_NO"])
                continue
        _logger.info("Successfully completed import Inward process.")
        return True
    
