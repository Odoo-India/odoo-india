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
        'price_dealer': fields.float('Dealer Price', readonly=True, select=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'dealer_discount': fields.float('Dealer Discount', readonly=True, select=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'dealer_discount_per': fields.float('Dealer Discount (%)', readonly=True, select=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    }
    
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line=line, account_id=account_id, context=context)
        res = dict(res, price_dealer=line.price_dealer * line.product_uom_qty, dealer_discount=line.dealer_discount * line.product_uom_qty, dealer_discount_per=line.dealer_discount_per/100)
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

class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    _columns = {
        'dealer_id': fields.many2one('res.partner', 'Dealer', readonly=True, states={'draft':[('readonly',False)]})
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

account_invoice()

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

    def _get_default_values(self, cr, uid, preline, context=None):
        res = super(sale_order, self)._get_default_values(cr, uid, preline=preline, context=context)
        res = dict(res,
            price_dealer = -preline.price_dealer, 
            dealer_discount = -preline.dealer_discount,
            dealer_discount_per = -preline.dealer_discount_per
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
        inv.update({
            'dealer_id':order.dealer_id.id
        })
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], inv['payment_term'], time.strftime(DEFAULT_SERVER_DATE_FORMAT))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id

    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        res = super(sale_order, self)._prepare_order_line_move(cr, uid, order=order, line=line, picking_id=picking_id, date_planned=date_planned, context=context)
        res = dict(res, price_dealer = line.price_dealer, dealer_discount=line.dealer_discount, dealer_discount_per=line.dealer_discount_per)
        return res

sale_order()

class account_invoice_line(osv.Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'price_dealer': fields.float('Dealer Price'),
        'dealer_discount': fields.float('Dealer Discount'),
        'dealer_discount_per': fields.float('Dealer Discount (%)')
    }
account_invoice_line()

class sale_advance_payment_inv(osv.osv_memory):
    _inherit = 'sale.advance.payment.inv'

    def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        result = super(sale_advance_payment_inv, self)._prepare_advance_invoice_vals(cr, uid, ids, context)
        
        sale_obj = self.pool.get('sale.order')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])
        
        update_val = {}
        for sale in sale_obj.browse(cr, uid, sale_ids, context=context):
            total_price_dealer = total_dealer_discount = 0.0
            price_dealer = dealer_discount = 0.0
            for line in sale.order_line:
                total_price_dealer += line.price_dealer * line.product_uom_qty
                total_dealer_discount += line.dealer_discount * line.product_uom_qty
            
            res = {}
            total_amount = 0.0
            if wizard.advance_payment_method == 'percentage':
                price_dealer = total_price_dealer * (wizard.amount / 100)
                dealer_discount = total_dealer_discount * (wizard.amount / 100)
                total_amount = (sale.amount_total * wizard.amount) / 100
            else:
                inv_amount = wizard.amount
                percent = inv_amount / sale.amount_total
                total_amount = inv_amount
                price_dealer = total_price_dealer * percent
                dealer_discount = total_dealer_discount * percent
            
            res['price_dealer'] = price_dealer
            res['dealer_discount'] = dealer_discount
            res['dealer_discount_per'] =  dealer_discount / total_amount

            update_val[sale.id] = res

        #TODO: Need to re-implement it in best way
        for line in result:
            line[1].get('invoice_line')[0][2].update(update_val.get(line[0]))
        
        return result

sale_advance_payment_inv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
