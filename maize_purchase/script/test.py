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

from osv import osv, fields
from datetime import datetime
import logging
import os
_logger = logging.getLogger("Import Journal Entry")

MAPPING = {
    "MOVELINE" : {
        "name": "Beneficiary Name1",
        "date": "Value Date",
        "account_id": "Debit Account Number",
        "ref": "Customer Reference No",
        "move_id": "Move",
        "debit": "Amount",
        "partner_id": "Beneficiary Name",
    },
}

class import_journal_entries(osv.osv_memory):
    """This is OpenERP AbstractModel Which will helper for Importing data after 
    reading from some expected source
    """   
    _name = "import.journal.entry"


    def _read_text_data(self, cr, uid, path, context=None):
        """
            Reads Text from given path and Return list of dict with Mapping text
        """
        f = open(path, "r")
        lines = f.readlines()
        # Read the column names from the first line of the file
        fields = lines[0].split('\t')
        data_lines = []
        for row in lines[1:]:
            row1 = row.split('\t')
            items = dict(zip(fields, row1))
            data_lines.append(items)
        f.close()
        return fields,data_lines


    def _get_field_mapping(self, cr, uid, values, mapping):
        """
        Final Field Mapper for the Preparing Data for the Import Data
        """
        fields=[]
        data_lst = []
        for key,val in mapping.items():
            if key not in fields and values:
                fields.append(key)
                value = values.get(val)
                data_lst.append(value)
        return fields, data_lst

    def _write_bounced_partner(self, cr, uid, file_path, file_head, bounced_detail, context):
        if not file_head:
            _logger.warning("Can not Export bounced(Rejected) Partner detail to the file. ")
            return False
        try:
            dtm = datetime.today().strftime("%Y%m%d%H%M%S")
            fname = "BOUNCED_CUSTOMER-" + dtm + ".txt"
            _logger.info("Opening file '%s' for logging the bounced partner detail."%(fname))
            file = open(file_head+"/"+fname, "wb")
            f = open(file_path, "r")
            lines = f.readlines()
            # Read the column names from the first line of the file
            file.write(lines[0])
            data_lines = []
            for partner in bounced_detail:
                for row in lines[1:]:
                    row1 = row.split('\t')
                    if partner in row1:
                        file.write(row)
            f.close()
            file.close()
            _logger.info("Successfully exported the bounced partner detail to the file %s."%(fname))
            return True
        except Exception, e:
            print e
            _logger.warning("Can not Export bounced(Rejected) Partner detail to the file. ")
            return False

    def _do_import(self, cr, uid, file_path, bounch_folder, context=None):
        """
        This Function is call by scheduler. it read the source file and process 
        the data the prepare the account move and account move line entry. 
        """
        if not file_path or file_path == "":
            _logger.warning("Import can not be started. Configure your schedule Actions.")
            return True
        fields = data_lines = False
        try:
            fields, data_lines = self._read_text_data(cr, uid, file_path, context)
        except:
            _logger.warning("Can not read source file(txt) '%s', Invalid file path or File not reachable on file system."%(file_path))
            return True
        if not data_lines:
            _logger.info("File '%s' has not data or it has been already imported, please update the file."%(file_path))
            return True
        _logger.info("Starting Import Journal Entry Process from file '%s'."%(file_path))
        #NOTE: 
        
        bounced_partner = []
        for data in data_lines:
            pname = data['ITEMCODE']
            data['ITEMCODE'] = pname
            field, value = self._get_field_mapping(cr, uid, data, MAPPING['MOVELINE'])
            product_pool.create(cr, uid, dict(zip(field, value)), context)
            else:
                reject = pname
                if reject not in bounced_partner:
                    bounced_partner.append(pname)

        try:
            cross_val = {'name' : 'Customer Payment',
                         'credit' : total,
                         'account_id': parent_id[0],
                         'move_id': move_id[0],
                         'date': datetime.strptime(data_lines[0]['Value Date'], "%Y%m%d").strftime("%Y-%m-%d")}
#                         'date': datetime.today().strftime("%Y-%m-%d %H:%M:%S")}
            move_line_pool.create(cr, uid, cross_val, context)
        except:
            move_pool.unlink(cr, uid, move_id, context)
            _logger.warning("Can not Complete import process, unexpected error encountered.", exc_info=True)
#
        self._write_bounced_partner(cr, uid, file_path, bounch_folder, bounced_partner, context)
        file = open(file_path, "wb")
        _logger.info("Writing back empty source file to avoid re-import.")
        file.write('\t'.join(fields))
        file.close()
        _logger.info("Successfully completed import journal Entry process.")
        return True

import_journal_entries()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
