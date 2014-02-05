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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class account_invoice(osv.osv):
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = super(account_invoice, self)._amount_all(cr, uid, ids, name, args, context=context)
        for invoice,data in res.items():
            res[invoice].update({'amount_total': data.get('amount_total',0.0) + self.browse(cr, uid, invoice).variation_amount or 0.0})
        return res

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    _inherit = "account.invoice"
    _columns = {
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','variation_amount'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'variation_amount': fields.float('Variation Amount(±)', digits_compute=dp.get_precision('Account'), readonly=False, states={'paid':[('readonly',True)]}),
    }
account_invoice()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    _columns = {
        'pur_line_qty': fields.float('Purchase Quantity'),
        'pur_line_uom_id':  fields.many2one('product.uom', 'Purchase UoM'),
    }

account_invoice_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: