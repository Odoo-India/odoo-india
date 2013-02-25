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
from openerp.osv import osv
from openerp import pooler

class indent(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        self.sr_no = 0
        self.cr = cr
        self.uid = uid
        super(indent, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
              'time': time, 
              'total_amount': self._get_total, 
              'project_name': self._project_code_name, 
              'last_supplier': self._last_supplier_code_name,
              'indent_no': self._indent_no,
              'sequence': self._serial_no,
              'last_issue': self._last_issue,
              })
        self.context = context

    def _serial_no(self, line):
        self.sr_no += 1
        return self.sr_no
    
    def _last_issue(self, product_id, date):
        res = {}
        picking_obj = self.pool.get('stock.move')
        picking_id = picking_obj.search(self.cr, self.uid, [('product_id', '=', product_id.id), ('state', '=', 'done'), ('create_date', '<=', date)])
        picking_id = sorted(picking_id,reverse=True)
        if picking_id and len(picking_id) >= 2:
            pick = picking_obj.browse(self.cr, self.uid, picking_id[1])
            res.update({'date': pick.picking_id.date.split(' ')[0], 'department' : pick.location_dest_id.name})
        elif picking_id:
            pick = picking_obj.browse(self.cr, self.uid, picking_id[0])
            res.update({'date': pick.picking_id.date.split(' ')[0], 'department' : pick.location_dest_id.name})
        return res

    def _indent_no(self, name):
        no = name.split('/')
        return no[len(no)-1]

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
    
    def _last_supplier_code_name(self, id):
        code = ''
        if id:
            code = (id.ref or '')+' '+ id.name or ''
        return code

report_sxw.report_sxw('report.indent.indent','indent.indent','addons/indent/report/indent.rml',parser=indent, header='internal landscape')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

