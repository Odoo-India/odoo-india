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

class comparison_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        self.cr = cr
        self.uid = uid
        self.get_value ={}
        super(comparison_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time,
                                  'tax': self._tax,
                                  'get_value': self._get_value,})
        self.context = context
    
    def _tax(self,order):
        tax_obj = self.pool.get('account.tax')
        excise_tax = vat_tax = ''
        for exc in order.excies_ids:
            if exc.price_include:
                excise_tax += 'Include in Price' + ' '
            else:
                excise_tax += exc.name + ' '
        for vat in order.vat_ids:
            if vat.price_include:
                vat_tax += 'Include in Price' + ' '
            else:
                vat_tax += vat.name + ' '
        return self.get_value.update({'excise': excise_tax, 'vat': vat_tax})
    
    def _get_value(self):
        return self.get_value
    
    def set_context(self, objects, data, ids, report_type=None):
        return super(comparison_report, self).set_context(objects, data, ids, report_type=report_type)
        
report_sxw.report_sxw('report.Rate_Comparison','purchase.requisition','addons/maize_purchase/report/comparison_report.rml',parser=comparison_report, header='internal landscape')