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

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    _columns = {
        'price_dealer': fields.float('Dealer Price'),
        'dealer_discount': fields.float('Dealer Discount'),
        'dealer_discount_per': fields.float('Dealer Discount (%)')
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
        
        dealer_id = context.get('dealer_id')
        dealer_pricelist_id = context.get('dealer_pricelist_id')
        
        if dealer_id and dealer_pricelist_id:
            dealer_res = super(sale_order_line, self).product_id_change(cr, uid, ids, dealer_pricelist_id, product, qty=qty,
                uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=dealer_id,
                lang=lang, update_tax=False, date_order=date_order, packaging=False, fiscal_position=fiscal_position, flag=flag, context=context)
            
            price_unit = res['value']['price_unit']
            price_dealer = dealer_res['value']['price_unit']
            dealer_discount = price_unit - price_dealer
            
            res['value']['price_dealer'] = price_dealer
            res['value']['dealer_discount'] = dealer_discount
            res['value']['dealer_discount_per'] = (dealer_discount * 100) / price_unit
            
        return res
    
sale_order_line()

class sale_order(osv.Model):
    _inherit = 'sale.order'

    _columns = {
        'dealer_id': fields.many2one('res.partner', 'Dealer'),
        'dealer_pricelist_id': fields.many2one('product.pricelist', 'Dealer Pricelist', domain=[('type','=','sale')])
    }

    
    def onchange_dealer_id(self, cr, uid, ids, part, context=None):
        if not part:
            return {'value': {'dealer_pricelist_id': False}}
        
        val = {}
        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False

        if pricelist:
            val['dealer_pricelist_id'] = pricelist
        return {'value': val}
sale_order()
