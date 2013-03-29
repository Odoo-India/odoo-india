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
        excise_tax = vat_tax = val1 = 0.0
        excise_name = vat_name = ''
        for line in order.order_line:
            freight_tax = order.freight
            insurance_tax = order.insurance
            val1 += line.price_subtotal
            for exices in self.pool.get('account.tax').compute_all(self.cr, self.uid, order.excies_ids, line.price_subtotal, 1, line.product_id, order.partner_id)['taxes']:
                excise_tax += exices.get('amount', 0.0)
            val1 += excise_tax
            for vat in self.pool.get('account.tax').compute_all(self.cr, self.uid, order.vat_ids, val1, 1, line.product_id, order.partner_id)['taxes']:
                vat_tax += vat.get('amount', 0.0)
            val1 += vat_tax
        if order.insurance_type == 'percentage':
            insurance_tax = round((val1 * order.insurance) / 100,2)
        val1 += insurance_tax
        if order.freight_type == 'percentage':
            freight_tax = round(( val1 * order.freight) / 100,2)
        self._get_value
        for exices in order.excies_ids:
            excise_name = exices.name
        for vat in order.vat_ids:
            vat_name = vat.name
        return self.get_value.update({'excise': excise_tax, 'vat': vat_tax, 'freight': freight_tax,'insurance': insurance_tax, 'excise_name': excise_name, 'vat_name': vat_name})
    
    def _get_value(self):
        return self.get_value
    
    def set_context(self, objects, data, ids, report_type=None):
        return super(comparison_report, self).set_context(objects, data, ids, report_type=report_type)
        
report_sxw.report_sxw('report.Rate_Comparison','purchase.requisition','addons/maize_purchase/report/comparison_report.rml',parser=comparison_report, header='internal landscape')