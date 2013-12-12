# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
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
# from openerp.osv import osv
# from openerp import pooler

class picking_402(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(picking_402, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_tax_names':self._get_tax_names,
            'get_quantity': self._get_quantity,
        })

    def _get_tax_names(self, id):
        stock_picking_obj = self.pool.get('stock.picking.out')
        tax_values = stock_picking_obj._get_tax_names(self.cr, self.uid, self.ids)
        return tax_values
    
    def _get_quantity(self, id):
        stock_picking_obj = self.pool.get('stock.picking.out')
        tot_qty = stock_picking_obj._get_tot_qty(self.cr, self.uid, self.ids)
        return int(tot_qty)
    
report_sxw.report_sxw('report.stock.picking.form_402', 'stock.picking.out', 'addons/l10n_in_form_402/report/picking_form_402.rml', parser=picking_402, header=None)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
