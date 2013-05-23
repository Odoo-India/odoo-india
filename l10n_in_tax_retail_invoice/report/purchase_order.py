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

from report import report_sxw

class purchase_order(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):
        super(purchase_order, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'amount_to_text': self._amount_to_text,
            'get_quantity': self._get_quantity,
            'convert_int': self._convert_int,
        })
        
    def _amount_to_text(self, amount):
        account_invoice_obj = self.pool.get('account.invoice')
        val = account_invoice_obj.amount_to_text(amount)
        return val
    
    def _get_quantity(self, id):
        purchase_order_obj = self.pool.get('purchase.order')
        val = purchase_order_obj._get_qty_total(self.cr, self.uid, self.ids)
        return int(val[id.id])
    
    def _convert_int(self, amount):
        amount = int(amount)
        return amount

report_sxw.report_sxw('report.purchase.order.india', 'purchase.order', 'addons/l10n_in_tax_retail_invoice/report/purchase_order.rml', parser=purchase_order, header=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
