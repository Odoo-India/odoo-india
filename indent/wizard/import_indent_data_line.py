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

class import_indent_data_line(osv.osv_memory):
    _name = "import.indent.data.line"
    
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
    
    def _write_bounced_pos(self, cr, uid, file_head, bounced_detail, context):
        if not file_head:
            _logger.warning("Can not Export bounced(Rejected) Partner detail to the file. ")
            return False
        try:
            dtm = datetime.datetime.today().strftime("%Y%m%d%H%M%S")
            fname = "BOUNCED_POS_NOT_FOUND"+dtm+".csv"
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
        
    def do_import_indent_data_line(self, cr, uid,ids, context=None):
        file_path = "/home/ara/Desktop/intest.csv"
        if not file_path or file_path == "":
            _logger.warning("Import can not be started. Configure your schedule Actions.")
            return True
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True            
        if not data_lines:
            _logger.info("File '%s' has not data or it has been already imported, please update the file."%(file_path))
            return True
        _logger.info("Starting Import Journal Process from file '%s'."%(file_path))
        indent_line_pool =self.pool.get('indent.product.lines')
        indent_pool=self.pool.get('indent.indent')
        
        indent = []
        c_po=[]
        not_po = []
        cn_po=[]
        item_list= []
# "product_uom": "ITEMCODE",
        
        for data in data_lines:
            fiscalyear = self.pool.get('account.fiscalyear').search(cr,uid,[('name','=',data['INDYEAR'])])[0]
            try:
                indent = indent_pool.search(cr,uid,[('name','=', data["INDENTNO"].strip()),('fiscalyear','=',fiscalyear)])[0]
                indent_line = indent_line_pool.search(cr,uid,[('indent_id','=',indent)])
                
                if data["ITEMCODE"] and not indent_line:
                    try:
                        product = self.pool.get('product.product').search(cr,uid,[('default_code','=','0'+data["ITEMCODE"])])[0]
                        product_uom = self.pool.get('product.product').browse(cr,uid,product).uom_id.id
                        sqty = data['SQTY']
                        name = data['PURPOSE']
                        specification = data['REMARK']
                        price_unit = data['AP_RATE']
                        
                        indent_f = indent_line_pool.create(cr, uid, {'indent_id':indent,
                                                                   'product_id':product,
                                                                   'product_uom_qty':sqty,
                                                                   'name':name,
                                                                   'specification':specification,
                                                                   'price_unit':price_unit,
                                                                   'product_uom':product_uom,
                                                                           
                                                           }, context)
                        print "indet>>>>>>>>>>>>>>created", indent,indent_f
                        
                    except:
                        item_list.append(data["ITEMCODE"])
            except:
                print "data['INDENTNO']", data['INDENTNO']
                cn_po.append(data['INDENTNO'])
                _logger.warning("Skipping Record with Indent code '%s'."%(data['INDENTNO']), exc_info=True)
                continue
        print "indentindentindentindent>>>>>>>>>>>>>>>>>>>>>>>with po",c_po
        print "indentindentindentindent>>>>>>>>>>>>>>>>>>>>>>>>>>>with not po",not_po
        print "indentindentindentindent>>>>>>>>>>>>>>>>>>>>>>>>>>>canvel",item_list
        
        _logger.info("Successfully completed import journal process.")
        return True
import_indent_data_line()