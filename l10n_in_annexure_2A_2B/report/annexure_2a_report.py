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

from openerp import tools
from openerp.osv import fields, osv
from openerp.addons.decimal_precision import decimal_precision as dp

class annexure_2a_report(osv.osv):
    _name = "annexure.2a.report"
    _description = "Annexure 2A Report"
    _auto = False

    _columns = {
        'id': fields.integer('ID'),
        'account_id': fields.many2one('account.account', 'Tax Account'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'tin_no': fields.char('Tin No.', size=64),
        'date':fields.date('Date'),
        'base': fields.float('Base', digits_compute=dp.get_precision('Account')),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'base_code_id': fields.many2one('account.tax.code', 'Base Code'),
        'base_amount': fields.float('Base Code Amount', digits_compute=dp.get_precision('Account')),
        'tax_code_id': fields.many2one('account.tax.code', 'Tax Code'),
        'tax_amount': fields.float('Tax Code Amount', digits_compute=dp.get_precision('Account')),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'annexure_2a_report')
        cr.execute("""CREATE OR REPLACE view annexure_2a_report AS (
            select
                row_number() OVER () AS id,
                ai.date_invoice AS date,
                ai.partner_id as partner_id,
                rp.tin_no as tin_no,
                ait.invoice_id as invoice_id,
                ait.account_id as account_id,
                ait.base as base,
                ait.amount as amount,
                ait.base_code_id as base_code_id,
                ait.base_amount as base_amount,
                ait.tax_code_id as tax_code_id,
                ait.tax_amount as tax_amount

            FROM 
                account_invoice_line ail
                LEFT JOIN account_invoice ai ON (ail.invoice_id = ai.id)
                LEFT JOIN account_invoice_tax ait ON (ait.invoice_id = ai.id)
                LEFT JOIN res_partner rp ON (ai.partner_id = rp.id)

                WHERE ai.type = 'in_invoice'
                GROUP BY ail.id,
                ai.date_invoice,
                ai.partner_id,
                rp.tin_no,
                ail.account_id,
                ait.invoice_id,
                ait.account_id,
                ait.base,
                ait.amount,
                ait.base_amount,
                ait.tax_amount,
                ait.base_code_id,
                ait.tax_code_id
                )""")

annexure_2a_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
