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
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    _columns = {
        'packaging_cost': fields.float('Packing Cost'),
    }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        '''
        The purpose of this function to get value of price unit, list price, packing amount on product change.
        :return: return this value list price , price unit, packing amount.
        :rtype: dictionary
        '''
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

        product_pool = self.pool.get('product.product')
        package_pool = self.pool.get('product.packaging')
        
        if not packaging:
            packaging = res.get('value', {}).get('product_packaging', False)

        package_product = False
        qty_factor = 0
        if product:
            package = product_pool.browse(cr, uid, product)
            if package.container_id:
                package_product = package.container_id
                qty_factor = qty

        if not package_product and packaging:
            package = package_pool.browse(cr, uid, packaging)
            if package.ul.container_id:
                package_product = package.ul.container_id
                qty_factor = round(qty / package.qty)
            else:
                raise osv.except_osv(_('Warning!'),_('Unable to compute packaging cost as you have not define product on box %s' % (package.ul.name)))
        
        if package_product:
            packing_res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, package_product.id, qty=1,
                            uom=package_product.uom_id.id, partner_id=partner_id, lang=lang, fiscal_position=fiscal_position, flag=flag, context=context)
            res['value']['packaging_cost'] = qty_factor * packing_res['value']['price_unit']
        else:
            res['value']['packaging_cost'] = 0.0
        return res

class sale_order(osv.Model):
    _inherit = 'sale.order'

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'amount_packing': 0.0,
            }
            val = val1 = val2 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
                val2 += line.packaging_cost
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_packing'] = cur_obj.round(cr, uid, cur, val2)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + res[order.id]['amount_packing'] + order.round_off
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'round_off'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'packaging_cost'], 10),
            },
            multi='sums', help="The total amount."),
        'amount_packing': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Packing Cost',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'packaging_cost'], 10),
            },
            multi='sums', help="The total amount."),
        'round_off': fields.float('Round Off', help="Round Off Amount"),
    }

sale_order()

class account_invoice_line(osv.Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'packaging_cost': fields.float('Packing Cost'),
    }

account_invoice_line()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'amount_packing': 0.0,
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
                res[invoice.id]['amount_packing'] += line.packaging_cost
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] + res[invoice.id]['amount_packing'] + invoice.round_off
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

    _columns = {
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'round_off'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id', 'packaging_cost'], 20),
            },
            multi='sums', help="The total amount."),
        'amount_packing': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Packing Cost',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id', 'packaging_cost'], 20),
            },
            multi='sums', help="The total packing amount."),
        'round_off': fields.float('Round Off', help="Round Off Amount"),
    }

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
