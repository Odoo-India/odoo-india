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

class import_po_data(osv.osv_memory):
    _name = "import.po.data"
    
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
    
    def do_import_po_data(self, cr, uid,ids, context=None):
        
        file_path = "/home/ashvin/Desktop/script/POHEADER.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            

        _logger.info("Starting Import PO Process from file '%s'."%(file_path))
        po_pool =self.pool.get('purchase.order')
        indent = []
        rejected =[]
        for data in data_lines:
            try:
#                if data['APRVID'] == 'Y':
#                    wf_service = netsvc.LocalService('workflow')
#                    indent = self.pool.get('indent.indent').search(cr,uid,[('name','=',data["INDENTNO"])])[0]
#                    wf_service.trg_validate(uid, 'indent.indent', indent, 'indent_inprogress', cr)
#                print "data111111111111111111111111", data["INDENTOR"]

                if data["PONO"]:
                    name = data["PONO"]
                if data["PONO"] and data["POSERIES"]:
                    old_id = data["POSERIES"] + '/' +data["PONO"]

                if data["POSERIES"]:
                    po_series = self.pool.get('product.order.series').search(cr,uid,[('code','=',data["POSERIES"])])[0]
                    
                if data["PODATE"]:
                    if data["PODATE"] == 'NULL' or data["PODATE"] == '' or data["PODATE"] == '00:00.0' or data["PODATE"] == '  ':
                        value = ''
                    else:
                        value=datetime.datetime.strptime(data["PODATE"], '%d-%m-%y').strftime("%Y-%m-%d")
                    podate = value
                    
                if data["SUPPCODE"]:
                    partner = self.pool.get('res.partner').search(cr,uid,[('supp_code','=',data["SUPPCODE"])])[0]

                if data["MILDELIV"]:
                    delivey = data["MILDELIV"]

                if data["INSURANCE"]:
                    ins = 0.0
                if data["INSAMOUNT"]:
                    ins_type = 'fix'
                    
                if data["EXCISE"]:
                    data["EXCISE"] = int(data["EXCISE"])
                    if data["EXCISE"] == 0:
                        excies = self.pool.get("account.tax").search(cr,uid,[('name','like','No Excise')])
                    elif data["EXCISE"] == 1:
                        excies = self.pool.get("account.tax").search(cr,uid,[('name','like','Excise Duty paid')])
                    elif data["EXCISE"] == 2:
                        excies = self.pool.get("account.tax").search(cr,uid,[('name','like','Excise 12%')])
                    elif data["EXCISE"] == 3:
                        excies = self.pool.get("account.tax").search(cr,uid,[('name','like','Exise Rate per unit')])
                    excies_ids = [(6,0,excies)]

                if data["SALETAX"]:
                    data["SALETAX"] = int(data["SALETAX"])
                    if data["SALETAX"] == 0:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','like','Tax Paid')])
                    elif data["SALETAX"] == 1:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','like','VAT 4% (1% Add Tax)')])
                    elif data["SALETAX"] == 2:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','like',"C.S.T")])
                    elif data["SALETAX"] == 3:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','like',"'C' form to be Issued")])
                    elif data["SALETAX"] == 4:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','like',"Tax Extra")])
                    elif data["SALETAX"] == 5:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','like',"'H' form to be Issued")])
                    elif data["SALETAX"] == 6:
                        vat = self.pool.get("account.tax").search(cr,uid,[('name','like',"VAT 12% (2.5% VAT)")])
                    vat_ids = [(6,0,vat)]
                    
                if data["REMARK1"] or data["REMARK2"] or data["REMARK3"] or data["REMARK4"]:
                    note= data["REMARK1"] +'\n'+ data["REMARK2"] +'\n'+ data["REMARK3"] +'\n'+ data["REMARK4"]


                vals = {'name':name,
                        'maize':old_id,
                        'po_series_id':po_series,
                        'date_order':podate,
                        'partner_id': partner,
                        'delivey':delivey,
                        'location_id':12,
                        'pricelist_id':2,
                        'insurance':ins,
                        'insurance_type':ins_type,
                        'excies_ids':excies_ids,
                        'vat_ids':vat_ids,
                        'notes':note,
                                                   }
                data['po'] = po_pool.create(cr, uid, vals, context)
            
            except:
                rejected.append(data['PONO'])
                _logger.warning("Skipping Record with Indent code '%s'."%(data['PONO']), exc_info=True)
                continue
        print "rejectedrejectedrejected", rejected
        _logger.info("Successfully completed import journal process.")
        return True
    
    def po_line_create(self,cr,uid,ids):
        file_path = "/home/ashvin/Desktop/script/POTRANS.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            

        _logger.info("Starting Import PO LINE Process from file '%s'."%(file_path))
        pol_pool =self.pool.get('purchase.order.line')
        indent = []
        rejected =[]
        for data in data_lines:
            try:
                if data["PONO"] and data['POSERIES']:
                    po = self.pool.get('purchase.order').search(cr,uid,[('name','=',data['POSERIES']+'0'+data["PONO"])])

                if data["ITEMCODE"]:
                    product = self.pool.get('product.product').search(cr,uid,[('code','=',data["ITEMCODE"])])[0]
                    
                if data["PORATE"]:
                    rate = data["PORATE"]
                    
                if data["DISCPER"]:
                    discount = data["DISCPER"]


                vals = {'order_id':po,
                        'product_id':product,
                        'rate':rate,
                        'discount': discount,
                        'name':'test',
                        'product_uom':self.pool.get('product.product').browse(cr,uid,product).uom_id.id,
                        'date_planned':'03/29/2013'
                       }
                data['po'] = po_pool.create(cr, uid, vals, context)
            
            except:
                rejected.append(data['PONO'])
                _logger.warning("Skipping Record with Indent code '%s'."%(data['PONO']), exc_info=True)
                continue
import_po_data()