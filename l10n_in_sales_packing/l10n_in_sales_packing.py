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

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    _columns = {
        'packaging_cost': fields.float('Packing Cost'),
    }

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line=line, account_id=account_id, context=context)
        res = dict(res, packaging_cost=line.packaging_cost)
        return res

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
                raise osv.except_osv(_('Warning!'), _('Unable to compute packaging cost as you have not define product on box %s' % (package.ul.name)))
        
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
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'packaging_cost'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty', 'packaging_cost'], 10),
            },
            multi='sums', help="The tax amount."),
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

    def _get_default_values(self, cr, uid, preline, context=None):
        res = super(sale_order, self)._get_default_values(cr, uid, preline=preline, context=context)
        res = dict(res,
          packaging_cost=-preline.packaging_cost
        )
        return res

    def _make_invoice(self, cr, uid, order, lines, context=None):
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        if context is None:
            context = {}
        invoiced_sale_line_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', order.id), ('invoiced', '=', True)], context=context)
        from_line_invoice_ids = []
        for invoiced_sale_line_id in self.pool.get('sale.order.line').browse(cr, uid, invoiced_sale_line_ids, context=context):
            for invoice_line_id in invoiced_sale_line_id.invoice_lines:
                if invoice_line_id.invoice_id.id not in from_line_invoice_ids:
                    from_line_invoice_ids.append(invoice_line_id.invoice_id.id)
        for preinv in order.invoice_ids:
            if preinv.state not in ('cancel',) and preinv.id not in from_line_invoice_ids:
                for preline in preinv.invoice_line:
                    res = self._get_default_values(cr, uid, preline, context=context)
                    inv_line_id = obj_invoice_line.copy(cr, uid, preline.id, res, context=context)
                    lines.append(inv_line_id)
        inv = self._prepare_invoice(cr, uid, order, lines, context=context)
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], inv['payment_term'], time.strftime(DEFAULT_SERVER_DATE_FORMAT))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id

    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        res = super(sale_order, self)._prepare_order_line_move(cr, uid, order=order, line=line, picking_id=picking_id, date_planned=date_planned, context=context)
        res = dict(res, packaging_cost=line.packaging_cost / line.product_uom_qty)
        return res

sale_order()

class sale_advance_payment_inv(osv.osv_memory):
    _inherit = 'sale.advance.payment.inv'
    
    # TODO: improve this method need to call super
    def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        result = super(sale_advance_payment_inv, self)._prepare_advance_invoice_vals(cr, uid, ids, context)
        
        sale_obj = self.pool.get('sale.order')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])
        
        update_val = {}
        for sale in sale_obj.browse(cr, uid, sale_ids, context=context):
            res = {}
            if wizard.advance_payment_method == 'percentage':
                packing_amount = sale.amount_packing * wizard.amount / 100
            else:
                inv_amount = wizard.amount
                percent = inv_amount / sale.amount_total
                packing_amount = sale.amount_packing * percent / 100
            
            res = {
             'packaging_cost': packing_amount
            }
            update_val[sale.id] = res
        
        #TODO: Need to re-implement it in best way
        for line in result:
            line[1].get('invoice_line')[0][2].update(update_val.get(line[0]))
    
        return result
    
sale_advance_payment_inv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
