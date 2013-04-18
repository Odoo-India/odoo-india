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

class import_indent_data(osv.osv_memory):
    _name = "import.indent.data"
    
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
    
    def do_import_indent_data(self, cr, uid,ids, context=None):
        
        file_path = "/home/ashvin/Desktop/script/INDENTHEADER.csv"
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
        indent_pool =self.pool.get('indent.indent')
        indent = []
        for data in data_lines:
            try:
                if data['APRVID'] == 'Y':
                    wf_service = netsvc.LocalService('workflow')
                    indent = self.pool.get('indent.indent').search(cr,uid,[('maize','=',data["INDENTNO"])])[0]
                    print "indentindentindent", indent, data["INDENTNO"]
                    wf_service.trg_validate(uid, 'indent.indent', indent, 'indent_confirm', cr)
                    wf_service.trg_validate(uid, 'indent.indent', indent, 'indent_inprogress', cr)
#                print "data111111111111111111111111", data["INDENTOR"]
#                inderntor = self.pool.get('res.users').search(cr,uid,[('user_code','=',data["INDENTOR"])])[0]
#                print ">>>>>>>>>>>>>>>>>>>>", inderntor
#                emp_obj = self.pool.get('hr.employee')
#                emp = emp_obj.search(cr, uid, [('user_id', '=', inderntor)], context=context)[0]
#                if data["DEPTCODE"]:
#                    department = self.pool.get('stock.location').search(cr,uid,[('code','=',data["DEPTCODE"])])[0]
#                else:
#                    department = False
#                if data["ITEMREQ"] =='U':
#                    req = 'urgent'
#                else:
#                    req = 'ordinary'
#                    
#                if data["INDTYPE"] =='New':
#                    type = 'new'
#                else:
#                    type = 'existing'
#                if data["ITEMFOR"] =='S':
#                    item_for = 'store'
#                else:
#                    item_for = 'capital'
#
#                if data["INDDATE"] == 'NULL' or data["INDDATE"] == '' or data["INDDATE"] == '00:00.0' or data["INDDATE"] == '  ':
#                    indent_date = ''
#                else:
#                    indent_date=datetime.datetime.strptime(data["INDDATE"], '%d/%m/%y').strftime("%Y-%m-%d 00:00:00")
#
#                if data["REQDATE"] == 'NULL' or data["REQDATE"] == '' or data["REQDATE"] == '00:00.0' or data["REQDATE"] == '  ':
#                    req_date = ''
#                else:
#                    req_date = datetime.datetime.strptime(data["REQDATE"], '%d/%m/%y').strftime("%Y-%m-%d 00:00:00")
#
#                data['indent'] = indent_pool.create(cr, uid, {'name':data["INDENTNO"],
#                                                              'indentor_id':inderntor,
#                                                              'employee_id':emp,
#                                                              'indent_date': indent_date,
#                                                              'required_date':data["REQDATE"],
#                                                              'requirement': req,
#                                                              'type':type,
#                                                              'department_id': department,
#                                                              'item_for':item_for,
#                                                   }, context)


            except:
                print "data['INDENTNO']", data['INDENTNO']
                _logger.warning("Skipping Record with Indent code '%s'."%(data['INDENTNO']), exc_info=True)
                continue
        print "indentindentindentindent",indent
        
        _logger.info("Successfully completed import journal process.")
        return True
import_indent_data()