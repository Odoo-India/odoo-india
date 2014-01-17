# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today Tiny SPRL (<http://tiny.be>).
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

from osv import fields, osv
from tools import config
import decimal_precision as dp

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    _columns = {
        'buyer_order_no': fields.char('Buyer Order No.', size=64),
        'bill_entry': fields.char('Bill of Entry', size=64),
        'address_id_del': fields.many2one('res.partner', 'Delivery Address', help="Address of Customer"),
        'date_delivery': fields.date('Delivery Date', readonly=True, states={'draft':[('readonly',False)]}, select=True, help="Keep empty to use the current date"),
    }

account_invoice()

class stock_picking(osv.osv):
    _inherit = "stock.picking"

    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        sale_obj = self.pool.get('sale.order')
        res = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
        if picking.sale_id:
            res.update(
                {
#                     'is_cst_register': picking.sale_id.is_cst_register,
#                     'cst_tax_id': picking.sale_id.cst_tax_id and picking.sale_id.cst_tax_id.id or False,
                    'buyer_order_no': picking.sale_id.client_order_ref or '',
                    'date_delivery': picking.date_done,
                    'address_id_del':picking.partner_id.id or False,
                    'bill_entry': picking.move_lines[0].prodlot_id and picking.move_lines[0].prodlot_id.name or ''
                }
            )
        return res

    def _prepare_invoice_group(self, cr, uid, picking, partner, invoice, context=None):
        res = super(stock_picking, self)._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
        if picking.sale_id:
            res.update(
                {
#                     'is_cst_register': picking.sale_id.is_cst_register,
#                     'cst_tax_id': picking.sale_id.cst_tax_id and picking.sale_id.cst_tax_id.id or False,
                    'buyer_order_no': picking.sale_id.client_order_ref or '',
                    'date_delivery': picking.date_done,
                    'address_id_del':picking.partner_id.id or False,
                    'bill_entry': picking.move_lines[0].prodlot_id and picking.move_lines[0].prodlot_id.name or ''
                }
            )
        return res
stock_picking()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: