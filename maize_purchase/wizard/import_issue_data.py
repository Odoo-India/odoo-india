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
import os
import logging
from openerp import netsvc
_logger = logging.getLogger("Indent Indent")

class import_issue_data(osv.osv_memory):
    _name = "import.issue.data"
    _columns = {
       'file_path': fields.char('File Path', required=True, size=256),
    }
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

    def _write_bounced_issue(self, cr, uid, file_head, bounced_detail, context):
        if not file_head:
            _logger.warning("Can not Export bounced(Rejected) filllllllleee Inward detail to the file. ")
            return False
        try:
            dtm = datetime.datetime.today().strftime("%Y%m%d%H%M%S")
            fname = "BOUNCED_INWARD_HEADER"+dtm+".csv"
            _logger.info("Opening file '%s' for logging the bounced inward detail."%(fname))
            fl= csv.writer(open(file_head+"/"+fname, 'wb'))
            for ln in  bounced_detail:
                fl.writerow(ln)
            _logger.info("Successfully exported the bounced inward detail to the file %s."%(fname))
            return True
        except Exception, e:
            print e
            _logger.warning("Can not Export bounced(Rejected) Inward detail to the file. ")
            return False

    #TODO:FIX ME TO FIND INDENT
    def import_isuue_data(self, cr, uid,ids, context=None):
        print "yeppppppppppppppppppppiiiiiiiiiiiiiiiiiiiiiiiiiii"
        data = self.read(cr, uid, ids)[0]
        file_path = data['file_path']
        fields = data_lines = False
        try:
            fields, data_lines = self._read_csv_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(csv) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True

        _logger.info("Starting Import Issue Process from file '%s'."%(file_path))
        issue_pool =self.pool.get('stock.picking')
        indent = []
        rejected =[]
        bounced_issue = [tuple(fields)]
        for data in data_lines:
            try:
                if data['ISUYEAR'] and data['ISSUENO']:
                    maize = data['ISUYEAR'] +'/'+data['ISSUENO']
                tr_code = data["TRCODE"]
                department_code = data["DEPTCODE"] or ''
                issue_date = data["ISUDATE"]
                indentor = data["INDENTOR"]
                dept_code = data["DEPTCODE"]
                partner_id = False
                tr = False
                if indentor:
                    user = self.pool.get('res.users').search(cr, uid, [('user_code','=',indentor)])
                    if user:
                        partner_id = self.pool.get('res.users').browse(cr, uid, user[0]).partner_id.id
                if tr_code:
                    tr_code = "R"+tr_code
                    tr = self.pool.get('tr.code').search(cr, uid, [('code','=',tr_code)])

                vals = {
                        #All fields depends on indent_id(maize)
                        #Just write maize number (indent_id) to origin field.
                        #origin: 
                        'partner_id': partner_id or False,
                        'tr_code_id':tr and tr[0] or False,
                        'maize':maize,
                        'date':issue_date,
                        'company_id':1,
                        'remark1':department_code,
                        'note':dept_code
                        }
                issue_pool.create(cr, uid, vals, context)
            except:
                rejected.append(data['ISSUENO'])
                reject = [ data.get(f, '') for f in fields]
                bounced_issue.append(reject)
                _logger.warning("Skipping Record with reciept code '%s'."%(data['ISSUENO']), exc_info=True)
                continue
        print "REJECTED RECIEPTS", rejected
        head, tail = os.path.split(file_path)
        self._write_bounced_issue(cr, uid, head, bounced_issue, context)        
        _logger.info("Successfully completed import RECIEPT HEADER process.")
        return True

import_issue_data()