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


from openerp.osv import fields, osv
from openerp.tools.amount_to_text_en import amount_to_text

class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    def amount_to_text(self, amount, currency):
        '''
        The purpose of this function is to use payment amount change in word
        @param amount: pass Total payment of amount
        @param currency: pass which currency to pay
        @return: return amount in word
        @rtype : string
        '''
        amount_in_word = amount_to_text(amount)
        if currency == 'INR':
            amount_in_word = amount_in_word.replace("euro", "Rupees").replace("Cents", "Paise").replace("Cent", "Paise")
        return amount_in_word
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({
            'delivery_order_id':False,
            'delivery_address_id': False,
            'carrier_id': False,
            'date': False,
            'delivery_name': False,
            'delivery_date': False,
            'sale_id': False,
            'dispatch_doc_no': False,
            'dispatch_doc_date': False,
        })
        return super(account_invoice, self).copy(cr, uid, id, default, context)

    _columns = {
        'delivery_order_id': fields.many2one('stock.picking', 'Delivery Order', readonly="True"),
        'delivery_address_id': fields.many2one('res.partner', 'Delivery Address'),
        'date': fields.date('Sales Date'),
        'carrier_id': fields.many2one('delivery.carrier', 'Carrier'),
        'delivery_name': fields.char('Delivery Name'),
        'delivery_date': fields.datetime('Delivery Date'),
        'sale_id': fields.many2one('sale.order', 'Sale Order ID', readonly="True"),
        'dispatch_doc_no': fields.char('Dispatch Document No.', size=16),
        'dispatch_doc_date': fields.date('Dispatch Document Date'),
        'consignee_account': fields.char('Consignee Account', size=32, help="Account Name, applies when there is customer for consignee."),
        'freight_charge': fields.float('Inward Freight'),
        'freight_allowed': fields.boolean('Freight Allowed'),
    }

    _defaults = {
        'freight_allowed': lambda self, cr, uid, context: self.pool.get('res.company').browse(cr, uid, uid, context=context).freight,
     }

account_invoice()

class account_invoice_line(osv.Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'lst_price': fields.float('Dealers Price', help='Dealers Price'),
        'packing_amount': fields.float('Packing Cost'),
    }

account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
