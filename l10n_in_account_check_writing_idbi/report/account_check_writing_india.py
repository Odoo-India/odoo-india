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
from openerp.tools import amount_to_text_en
import datetime

class report_print_check_india(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_check_india, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'get_date': self.get_date,
            'amount_to_text': self._amount_to_text,
        })
    def get_date(self):
        todays_date = datetime.datetime.now()
        date = todays_date.strftime("%d")
        month = todays_date.strftime("%m")
        year = todays_date.strftime("%Y")
        format_date = date + month + year
        return format_date
    
    def _amount_to_text(self, amount, currency):
        account_invoice_obj = self.pool.get('account.invoice')
        val = account_invoice_obj.amount_to_text(amount, currency)
        return val

report_sxw.report_sxw(
    'report.account.print.check.india.idbi',
    'account.voucher',
    'addons/l10n_in_account_check_writing_idbi/report/account_check_writing_india.rml',
    parser=report_print_check_india, header=False
)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
