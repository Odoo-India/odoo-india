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
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler

class indent(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(indent, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time, 'total_amount': self._get_total})
        self.context = context

    def _get_total(self, id):
        total =  0.0
        for line in id.product_lines:
            if line.product_id and line.product_id.last_supplier_rate:
                total += (line.product_uom_qty * line.product_id.last_supplier_rate )
            else:
                total = 0.0
        return total

report_sxw.report_sxw('report.indent.indent','indent.indent','addons/indent/report/indent.rml',parser=indent, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

