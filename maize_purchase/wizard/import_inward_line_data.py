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
    
    
    def do_import_inward_data(self, cr, uid,ids, context=None):
        
        file_path = "/home/kuldeep/Desktop/inwardtr20132014.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            

        _logger.info("Starting Import PO Process from file '%s'."%(file_path))
        move_pool =self.pool.get('stock.move')
        picking_pool =self.pool.get('stock.picking.in')
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
        for data in data_lines:
            try:
                name = inwrd_num = ''
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
                if data["CHLNQTY"]:
                    chlnqty = data["CHLNQTY"]
                if data["INWYEAR"]:
                    indyear = data["INWYEAR"] 
                
                po_name = data["POSERIES"]+'/'+data["PONO"]
                maize_name = data["INWARDNO"]
                new_picking_id = False
                purchase_date = ''
                date_start = self._get_start_end_date_from_year(cr,uid,indyear)['start']
                date_end = self._get_start_end_date_from_year(cr,uid,indyear)['end']
                date_start_po = self._get_start_end_date_from_year(cr,uid,poyear)['start']
                date_end_po = self._get_start_end_date_from_year(cr,uid,poyear)['end']

                indent_id=False
                indentor_id=False
                fiscalyear = self.pool.get('account.fiscalyear').search(cr,uid,[('name','=',data['INDYEAR'].strip())])
                if data["INDENTNO"] and fiscalyear:
                    try:
                        indent = self.pool.get('indent.indent').search(cr,uid,[('maize','=',data["INDENTNO"]), ('fiscalyear','=',fiscalyear[0])])
                        indent_id = indent[0]
                    except:
                        indent_not_found.append(data["INDENTNO"]+'/'+data['INDYEAR'])
                    
                if data["INDENTOR"]:
                    indentor = self.pool.get('res.users').search(cr,uid,[('user_code','=',data["INDENTOR"])])
                    indentor_id = indentor and indentor[0] or ''

                
                if po_name:
                    exist_picking_po = self.pool.get('stock.picking.in').search(cr,uid,[('maize_in','=',maize_name),('date_done','>=',date_start),('date_done','<=',date_end)])
                    exist_picking_po1 = self.pool.get('stock.picking.in').browse(cr,uid,exist_picking_po[0])
                    if not  exist_picking_po1.purchase_id:
                        try:
                            purchase_id = self.pool.get('purchase.order').search(cr,uid,[('maize','=',data["POSERIES"]+'/'+data["PONO"]),('date_order','>=',date_start_po),('date_order','<=',date_end_po)])[0]
                            if purchase_id:
                                purchase_date = self.pool.get('purchase.order').browse(cr,uid,purchase_id).date_order
                                new_picking_id = self.pool.get('stock.picking.in').search(cr,uid,[('maize_in', '=', maize_name),('date_done','>=',date_start),('date_done','<=',date_end)])[0]
                                self.pool.get('stock.picking.in').write(cr,uid,new_picking_id,{'purchase_id':purchase_id})
                                new_vals = {
                                        'product_id': product,
                                        'name':po_name,
                                        'picking_id': new_picking_id,
                                        'challan_qty':chlnqty,
                                        'product_qty': rqty,
                                        'product_uom': self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                                        'location_id': supplier_location[0],
                                        'location_dest_id': 299,#input location fix
                                        'state': 'draft',
                                        'price_unit':float(rate),
                                        'company_id':1,
                                        'date':purchase_date or '',
                                        'indent':indent_id,
                                        'indentor':indentor_id,
                                        }
                                move_pool.create(cr, uid, new_vals, context)                                
                        except:
                            po_not_found.append(data["POSERIES"]+'/'+data["PONO"]+'/'+data["POYEAR"])
                        
                    else:
                        try:
                            if data['PONO'] == '99999':
                                purchase_id = 17970
                            else:
                                purchase_id = self.pool.get('purchase.order').search(cr,uid,[('maize','=',data["POSERIES"]+'/'+data["PONO"]),('date_order','>=',date_start_po),('date_order','<=',date_end_po)])[0]
                            purchase_date = self.pool.get('purchase.order').browse(cr,uid,purchase_id).date_order
                            if purchase_id != exist_picking_po1.purchase_id.id:
                                pp = self.pool.get('stock.picking.in').create(cr,uid,
                                                                              {'partner_id':exist_picking_po1.partner_id.id,
                                                                               'purchase_id':purchase_id,
                                                                               'date_done':exist_picking_po1.date_done,
                                                                               'lr_no':exist_picking_po1.lr_no,
                                                                               'lab_no':exist_picking_po1.lab_no,
                                                                               'case_code':exist_picking_po1.case_code,
                                                                               'lr_date':exist_picking_po1.lr_date,
                                                                               'dest_from':exist_picking_po1.dest_from,
                                                                               'challan_no':exist_picking_po1.challan_no,
                                                                               'hpressure':exist_picking_po1.hpressure,
                                                                               'despatch_mode':exist_picking_po1.despatch_mode,
                                                                               'dest_to':exist_picking_po1.dest_to,
                                                                               'transporter':exist_picking_po1.transporter,
                                                                               'maize_in':exist_picking_po1.maize_in,
                                                                               'other_dispatch':exist_picking_po1.other_dispatch,
                                                                               'gp_year':exist_picking_po1.gp_year,
                                                                               'series_id':exist_picking_po1.series_id,
                                                                               'gate_pass_id':exist_picking_po1.gate_pass_id.id,
                                                                               })
                                new_vals = {
                                        'product_id': product,
                                        'name':po_name,
                                        'picking_id': pp,
                                        'challan_qty':chlnqty,
                                        'product_qty': rqty,
                                        'product_uom': self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                                        'location_id': supplier_location[0],
                                        'location_dest_id': 299,#input location fix
                                        'state': 'draft',
                                        'price_unit':float(rate),
                                        'company_id':1,
                                        'date':purchase_date or '',
                                        'indent':indent_id,
                                       'indentor':indentor_id,
                                }
                            else:
                                new_vals = {
                                        'product_id': product,
                                        'name':po_name,
                                        'picking_id': exist_picking_po1.id,
                                        'challan_qty':chlnqty,
                                        'product_qty': rqty,
                                        'product_uom': self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                                        'location_id': supplier_location[0],
                                        'location_dest_id': 299,#input location fix
                                        'state': 'draft',
                                        'price_unit':float(rate),
                                        'company_id':1,
                                        'date':purchase_date or '',
                                        'indent':indent_id,
                                       'indentor':indentor_id,
                                }
                            move_pool.create(cr, uid, new_vals, context)
                        except:
                            po_not_found.append(data["POSERIES"]+'/'+data["PONO"]+'/'+data["POYEAR"])
            except:
                rejected.append(data['INWARDNO'])
                _logger.warning("Skipping Record with Inward code '%s'."%(data['INWARDNO']), exc_info=True)
                continue
        print "rejectedrejectedrejected", rejected
        print "po_not_foundpo_not_foundpo_not_foundpo_not_found>>>>>>>>>>", po_not_found
        print "po_not_foundpo_not_foundpo_not_foundpo_not_found>>>>>>>>>>", indent_not_found
        _logger.info("Successfully completed import Inward process.")
        return True
    
import_inward_line_data()