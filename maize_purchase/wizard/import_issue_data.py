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

class import_issue_data(osv.osv_memory):
    _name = "import.issue.data"

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

    #TODO:FIX ME TO FIND INDENT
    def import_isuue_data(self, cr, uid,ids, context=None):
        file_path = "/home/ashvin/Desktop/script/ISSUEHEADER.csv"
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True

        _logger.info("Starting Import PO Process from file '%s'."%(file_path))
        issue_pool =self.pool.get('stock.picking')
        indent = []
        rejected =[]
        for data in data_lines:
            try:
                maize = data["ISSUENO"]
                tr_code = data["TRCODE"]
                department_code = data["DEPTCODE"]
                create_date = data["ISUDATE"]
                indentor = data["INDENTOR"]
                partner_id = False
                tr = False
                if indentor:
                    user = self.pool.get('res.users').search(cr, uid, [('user_code','=',indentor)])
                    if user:
                        partner_id = self.pool.get('res.users').browse(cr, uid, user[0]).partner_id.id
                if tr_code:
                    tr_code = "R"+tr_code
                    tr = self.pool.get('tr.code').search(cr, uid, [('code','=',tr_code)])
                if create_date == 'NULL' or create_date == '' or create_date == '00:00.0' or create_date == '  ':
                    create_date = ''
                else:
                    create_date=datetime.datetime.strptime(create_date, '%d-%m-%y').strftime("%Y-%m-%d")
                vals = {
                        #All fields depends on indent_id(maize)
                        #Just write maize number (indent_id) to origin field.
                        #origin: 
                        'partner_id': partner_id or False,
                        'tr_code_id':tr and tr[0] or False,
                        'maize':maize,
                        'date':create_date,
                        'company_id':1,
                        }
                issue_pool.create(cr, uid, vals, context)
            except:
                rejected.append(data['ISSUENO'])
                _logger.warning("Skipping Record with reciept code '%s'."%(data['ISSUENO']), exc_info=True)
                continue
        print "REJECTED RECIEPTS", rejected
        _logger.info("Successfully completed import RECIEPT HEADER process.")
        return True

import_issue_data()