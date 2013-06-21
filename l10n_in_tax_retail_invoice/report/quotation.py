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

class quotation(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):
        super(quotation, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'convert_int': self._convert_int,
        })
    
    def _convert_int(self, amount):
        amount = int(amount)
        return amount
        
report_sxw.report_sxw('report.sale.quotation.india', 'sale.order', 'addons/l10n_in_tax_retail_invoice/report/quotation.rml', parser=quotation, header=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

