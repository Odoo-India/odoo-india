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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    def _total_dealer_disc(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in invoice.invoice_line:
                total += ((line.price_unit - line.price_dealer) * line.quantity)
            res[invoice.id] = total
        return res

    def _get_lines(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    _columns = {
        'dealer_id': fields.many2one('res.partner', 'Dealer', readonly=True, states={'draft':[('readonly',False)]}),
        'dealer_pricelist_id': fields.many2one('product.pricelist', 'Dealer Pricelist', domain=[('type','=','sale')]),
        'total_dealer_disc': fields.function(_total_dealer_disc, digits_compute=dp.get_precision('Account'), string='Total Dealer Disc.',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['dealer_pricelist_id', 'invoice_line'], 10),
                'account.invoice.line': (_get_lines, ['price_unit', 'price_dealer', 'product_uom_qty'], 10),
                },
            ),
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

class account_invoice_line(osv.Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'price_dealer': fields.float('Dealer Price'),
        'dealer_discount': fields.float('Dealer Discount'),
        'dealer_discount_per': fields.float('Dealer Discount (%)')
    }
    
    def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):
        res = {'value':{}}
        if product:
            res = super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom_id, qty, name, type, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id, context=context, company_id=company_id)
            
            pricelist_pool = self.pool.get('product.pricelist')
            
            dealer_id = context.get('dealer_id')
            dealer_pricelist_id = context.get('dealer_pricelist_id')
            
            if dealer_id and dealer_pricelist_id:
                dealer_res = pricelist_pool.price_get(cr, uid, [dealer_pricelist_id], product, qty, dealer_id)
                
                price_unit = res['value']['price_unit']
                price_dealer = dealer_res.get(dealer_pricelist_id)
                dealer_discount = price_unit - price_dealer
                
                res['value']['price_dealer'] = price_dealer * qty
                res['value']['dealer_discount'] = dealer_discount * qty
                res['value']['dealer_discount_per'] = (dealer_discount * 100) / price_unit
            
        return res
account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

