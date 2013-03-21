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
from openerp.report import report_sxw

class contract(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        self.sr_no = 0
        self.cr = cr
        self.uid = uid
        self.get_value ={}
        super(contract, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
              'time': time, 
              'total_amount': self._get_total, 
              'project_name': self._project_code_name, 
              'sequence': self._serial_no,
              'get_value': self._get_value,
              'type': self._type,
              })
        self.context = context

    def _serial_no(self, line):
        self.sr_no += 1
        return self.sr_no
    
    def _type(self, order, retenstion_type):
        text = 'CONTRACTOR\'S RETENTION NOT TO BE LEIVED'
        if str(retenstion_type) == 'leived':
            text = 'CONTRACTOR\'S RETENTION TO BE LEIVED'
        return text
    
    def _get_value(self):
        return self.get_value

    def _get_total(self, id):
        total =  0.0
        for line in id.product_lines:
            if line.product_id and line.product_id.last_supplier_rate:
                total += (line.product_uom_qty * line.product_id.last_supplier_rate )
            else:
                total += 0.0
        return total

    def _project_code_name(self, project_id):
        code = ''
        if project_id:
            code = (project_id.code or '') +'  '+ project_id.name or ''
        return code

report_sxw.report_sxw('report.contract.new','purchase.order','addons/maize_contract/report/contract.rml',parser=contract, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

