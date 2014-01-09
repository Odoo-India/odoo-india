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

class excice_cum_tax_invoice(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(excice_cum_tax_invoice, self).__init__(cr, uid, name, context=context)
        self.context = context
        self.x = 0.0
        self.localcontext.update({
            'time': time,
            'amount_to_text': self._amount_to_text,
            'get_quantity': self._get_quantity,
            'get_excise': self._get_excise_cess,
            'convert_int': self._convert_int,
        })

    def _amount_to_text(self, amount, currency):
        account_invoice_obj = self.pool.get('account.invoice')
        val = account_invoice_obj.amount_to_text(amount, currency)
        return val

    def _get_quantity(self, id):
        account_invoice_obj = self.pool.get('account.invoice')
        val = account_invoice_obj._get_qty_total(self.cr, self.uid, self.ids)
        return int(val.values()[0])

    def _get_excise_cess(self, ids):
        cess_excise_amount = []
        account_invoice_obj = self.pool.get('account.invoice')
        excise_amount = 0.0
        cess_amount = 0.0
        for invoice in account_invoice_obj.browse(self.cr, self.uid, self.ids):
            currency = invoice.company_id.currency_id.name
            for line in invoice.tax_line:
                if line.tax_categ == 'excise':
                    excise_amount += line.amount
#                    val = account_invoice_obj.amount_to_text(excise_amount)
#                    cess_excise_amount.append(val)
                if line.tax_categ == 'cess':
                    cess_amount += line.amount
#                    val = account_invoice_obj.amount_to_text(cess_amount)
#                    cess_excise_amount.append(val)
            val = account_invoice_obj.amount_to_text(excise_amount, currency)
            cess_excise_amount.append(val)
            val = account_invoice_obj.amount_to_text(cess_amount, currency)
            cess_excise_amount.append(val)
        self.x += self.x
        return cess_excise_amount 

    def excise_total(self):
        return self.x

    def _convert_int(self, amount):
        amount = int(amount)
        return amount

report_sxw.report_sxw('report.account.invoice.excise', 'account.invoice', 'addons/l10n_in_excise_invoice/report/excise_cum_tax_invoice.rml', parser=excice_cum_tax_invoice, header='internal')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
