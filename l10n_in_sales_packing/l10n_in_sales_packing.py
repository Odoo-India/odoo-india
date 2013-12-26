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

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            total = taxes['total'] + line.packaging_cost
            res[line.id] = cur_obj.round(cr, uid, cur, total)
        return res

    _columns = {
        'packaging_cost': fields.float('Packing Cost'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
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
