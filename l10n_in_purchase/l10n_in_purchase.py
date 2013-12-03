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
from openerp import netsvc
import openerp.addons.decimal_precision as dp

class purchase_order(osv.Model):
    _inherit = 'purchase.order'
    _order = 'id desc'

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        untax_amount = 0
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'other_charges':0.0,
            }
            val = val1 = freight = package_and_forwording = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                untax_amount = val1
                for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)
                
                if order.package_and_forwording_type == 'per_unit':
                    package_and_forwording += order.package_and_forwording * line.product_qty
                if order.freight_type == 'per_unit':
                    freight += order.freight * line.product_qty
            #adding package and forwarding to Untax ammount
            if order.package_and_forwording_type == 'fix':
                untax_amount += order.package_and_forwording
            elif order.package_and_forwording_type == 'per_unit':
                untax_amount += package_and_forwording
            elif order.package_and_forwording_type == 'percentage':
                untax_amount += (val1 * order.package_and_forwording) / 100

            #adding Freight to Untax ammount
            if order.freight_type == 'fix':
                untax_amount += order.freight
            elif order.freight_type == 'per_unit':
                untax_amount += freight
            elif order.freight_type == 'percentage':
                untax_amount += (val1 * order.freight) / 100

            #adding insurance to Untax ammount
            if order.insurance_type == 'fix':
                untax_amount += order.insurance
            elif order.insurance_type == 'percentage':
                untax_amount += (val1 * order.insurance) / 100

            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total']= res[order.id]['amount_tax']+untax_amount+order.round_off
            res[order.id]['other_charges']= res[order.id]['amount_total']-res[order.id]['amount_untaxed']-res[order.id]['amount_tax']-order.round_off
        return res
    
    _columns = {
        'package_and_forwording_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage'), ('per_unit', 'Per Unit'), ('actual', 'At actual'),('include', 'Include in Price')], 'Packaging & Forwarding Type', states={'confirmed':[('readonly', True)], 'approved':[('readonly', True)], 'done':[('readonly', True)]}),
        'package_and_forwording': fields.float('Packaging & Forwarding', states={'confirmed':[('readonly', True)], 'approved':[('readonly', True)], 'done':[('readonly', True)]}),
        'insurance_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage'), ('include', 'Include in Price')], 'Insurance Type', states={'confirmed':[('readonly', True)], 'approved':[('readonly', True)], 'done':[('readonly', True)]}),  
        'insurance': fields.float('Insurance', states={'confirmed':[('readonly', True)], 'approved':[('readonly', True)], 'done':[('readonly', True)]}),
        'delivery_id': fields.many2one('mill.delivery', 'Mill Delivery', states={'confirmed':[('readonly', True)], 'approved':[('readonly', True)], 'done':[('readonly', True)]}),
        'freight': fields.float('Freight', states={'confirmed':[('readonly', True)], 'approved':[('readonly', True)], 'done':[('readonly', True)]}),
        'freight_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage'), ('per_unit', 'Per Unit'),('actual', 'At actual'), ('include', 'Include in Price')], 'Freight Type', states={'confirmed':[('readonly', True)], 'approved':[('readonly', True)], 'done':[('readonly', True)]}),
        'round_off': fields.float('Round Off', states={'confirmed':[('readonly', True)], 'approved':[('readonly', True)], 'done':[('readonly', True)]}, help="Round Off Amount"),
        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
            store={
                   'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['round_off','insurance', 'insurance_type', 'freight_type', 'freight', 'package_and_forwording_type', 'package_and_forwording', 'order_line'], 11),
                   'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['round_off','insurance', 'insurance_type', 'freight_type', 'freight', 'package_and_forwording_type', 'package_and_forwording', 'order_line'], 11),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['round_off','insurance', 'insurance_type', 'freight_type', 'freight', 'package_and_forwording_type', 'package_and_forwording', 'order_line'], 11),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total amount"),
        'other_charges': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Other Charges',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['round_off','insurance', 'insurance_type', 'freight_type', 'freight', 'package_and_forwording_type', 'package_and_forwording', 'order_line'], 11),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="Computed as Packing & Forwarding + Freight + Insurance"),
    }
    
    _defaults = {
        'package_and_forwording_type':'fix',
        'insurance_type':'fix',
        'freight_type':'fix'
    }
    
    def onchange_reset(self, cr, uid, ids, insurance_type, freight_type, packing_type):
        res = {}
        if insurance_type in ('include',False):
            res.update({'insurance': 0.0})
        elif freight_type == 'actual':
            res.update({'freight': 0.0})
        elif packing_type == 'actual':
            res.update({'package_and_forwording': 0.0})
        return {'value': res}
    
purchase_order()
class mill_delivery(osv.Model):
    _name = 'mill.delivery'
    _description = 'Mill Delivery'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=32, required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the mill delivery without removing it."),
    }
    
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of the mill delivery must be unique!')
    ]

mill_delivery()

class purchase_order_line(osv.Model):
    _inherit = 'purchase.order.line'

    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        cur_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        total_qty = package_amount = insurance_amount =packing_and_forwading= freight_amount =freight= 0.0
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                'pkg_frwrd':0.0,
                'insurance':0.0,
                'freight':0.0,
                'price_subtotal':0.0
            }
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
            
            val1 = res[line.id]['price_subtotal']
            if line.order_id.package_and_forwording_type == 'per_unit':
                res[line.id]['pkg_frwrd'] = line.order_id.package_and_forwording
            elif line.order_id.package_and_forwording_type == 'percentage':
                package_amount = ((line.order_id.package_and_forwording * val1) / 100)
                res[line.id]['pkg_frwrd'] = package_amount / line.product_qty
            elif line.order_id.package_and_forwording_type == 'fix' and line.order_id.amount_untaxed > 0:
                package_amount = ((line.order_id.package_and_forwording)*res[line.id]['price_subtotal'])/line.order_id.amount_untaxed
                res[line.id]['pkg_frwrd'] = package_amount
        return res

    def _get_po_order(self, cr, uid, ids, context=None):
        cr.execute("""SELECT DISTINCT pol.id FROM purchase_order_line pol JOIN
                                                  purchase_order po ON (pol.order_id = %s)
                                    """, (tuple(ids),))
        return [i[0] for i in cr.fetchall()]
    
    _columns = {
        'discount': fields.float('Discount (%)'),
        'pkg_frwrd': fields.function(_amount_line, multi="pkg", string='Packing Unit', digits_compute=dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['round_off','insurance', 'insurance_type', 'freight_type', 'freight', 'package_and_forwording_type', 'package_and_forwording',], 11),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, [], 10),
            }),
        'insurance': fields.function(_amount_line, multi="pkg", string='Insurance Unit', digits_compute=dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['round_off','insurance', 'insurance_type', 'freight_type', 'freight', 'package_and_forwording_type', 'package_and_forwording',], 11),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'freight': fields.function(_amount_line, multi="pkg", string='Freight Unit', digits_compute=dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['round_off','insurance', 'insurance_type', 'freight_type', 'freight', 'package_and_forwording_type', 'package_and_forwording',], 11),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'price_subtotal': fields.function(_amount_line, multi="pkg", store={
                'purchase.order': (_get_po_order, ['round_off','insurance', 'insurance_type', 'freight_type', 'freight', 'package_and_forwording_type', 'package_and_forwording',], 11),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }, string='Subtotal', digits_compute= dp.get_precision('Account')),
        }