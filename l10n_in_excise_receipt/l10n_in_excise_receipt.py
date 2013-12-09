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

class stock_picking_receipt(osv.Model):
    _name = "stock.picking.receipt"
    _inherit = "stock.picking"
    _table = "stock_picking"
    _order = "name desc"
    _description = "Receipt"

    def check_access_rights(self, cr, uid, operation, raise_exception=True):
        # override in order to redirect the check of acces rights on the stock.picking object
        return self.pool.get('stock.picking').check_access_rights(cr, uid, operation, raise_exception=raise_exception)

    def check_access_rule(self, cr, uid, ids, operation, context=None):
        # override in order to redirect the check of acces rules on the stock.picking object
        return self.pool.get('stock.picking').check_access_rule(cr, uid, ids, operation, context=context)

    def _workflow_trigger(self, cr, uid, ids, trigger, context=None):
        # override in order to trigger the workflow of stock.picking at the end of create, write and unlink operation
        # instead of it's own workflow (which is not existing)
        return self.pool.get('stock.picking')._workflow_trigger(cr, uid, ids, trigger, context=context)

    def _workflow_signal(self, cr, uid, ids, signal, context=None):
        # override in order to fire the workflow signal on given stock.picking workflow instance
        # instead of it's own workflow (which is not existing)
        return self.pool.get('stock.picking')._workflow_signal(cr, uid, ids, signal, context=context)

    def purchase_amount(self, cr, uid, purchase_id, product_id, context=None):
        res = {}
        line_price = 0.0
        purchase_line_obj = self.pool.get('purchase.order.line')
        line_id = purchase_line_obj.search(cr, uid, [('order_id', '=', purchase_id), ('product_id', '=', product_id)])
        if not line_id:
            res.update({'new_price':0.0})
            return res
        for line in purchase_line_obj.browse(cr, uid, line_id, context=context):
            line_price = line.new_price
            res.update({'new_price': line_price, 'order': line.order_id})
        return res

    def _total_amount(self, cr, uid, ids, name, args, context=None):
        result = dict([(id, {'amount_total':0.0, 'total_diff':0.0, 'amount_subtotal':0.0, 'import_duty':0.0}) for id in ids])
        for receipt in self.browse(cr, uid, ids, context=context):
            total = 0.0
            diff = 0.0
            import_duty = 0.0
            for line in receipt.move_lines:
                po_dict = self.purchase_amount(cr, uid, receipt.purchase_id.id, line.product_id.id, context=context)
                diff += line.diff_amount
                total += round(po_dict['new_price'],2) * line.product_qty
                import_duty += line.import_duty
            result[receipt.id]['total_diff'] = diff
            result[receipt.id]['import_duty'] = import_duty
            result[receipt.id]['amount_subtotal'] = total
            result[receipt.id]['amount_total'] = total + (diff + import_duty)
        return result

    def button_dummy(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        move_obj = self.pool.get('stock.move')
        receipt = self.browse(cr, uid, ids[0], context=context)
        if receipt.freight:
            total = 0.0
            for move in receipt.move_lines:
                total += move.amount
 
            per_unit = receipt.freight / total if total else 1.0
            if receipt.freight > 0:
                for move in receipt.move_lines:
                    diff  = move.amount * per_unit / move.amount if move.amount else 1.0
                    move_obj.write(cr, uid, [move.id], {'diff': diff, 'less_diff': 0}, context=context)
            elif receipt.freight < 0:
                for move in receipt.move_lines:
                    diff  = move.amount * abs(per_unit) / move.amount if move.amount else 1.0
                    move_obj.write(cr, uid, [move.id], {'diff': 0, 'less_diff': diff}, context=context)
        return True

    _columns = {
        'freight':fields.float('Freight', track_visibility='onchange'),
        'product_id': fields.related('move_lines', 'product_id', type='many2one', relation='product.product', string='Products'),
        'inward_id': fields.many2one('stock.picking.in', 'Inward', ondelete='set null', domain=[('type','=','in')]),
        'inward_date': fields.related('inward_id', 'date_done', type='datetime', string='Inward Date', readonly=True, store=True),
#         'amount_total': fields.function(_total_amount, multi="cal", type="float", string='Total', store=True),
        'amount_total': fields.float('Total'),
#         'total_diff': fields.function(_total_amount, multi="cal", type="float", string='Total Diff', help="Total Diff", store=True),
        'total_diff': fields.float('Total Diff'),
#         'amount_subtotal': fields.function(_total_amount, multi="cal", type="float", string='Total Amount', help="Total Amount(computed as (Total - Total Diff))", store=True),
        'amount_subtotal': fields.float('Total Amount'),
#         'import_duty': fields.function(_total_amount, multi="cal", type="float", string='Import Duty', help="Total Import Duty", store=True),
        'import_duty': fields.float('Import Duty'),
        'date_done': fields.datetime('Date of Transfer', help="Date of Completion", track_visibility='onchange'),
        'state': fields.selection([
                ('draft', 'Draft'),
                ('cancel', 'Cancelled'),
                ('auto', 'Waiting Another Operation'),
                ('confirmed', 'Waiting Availability'),
                ('assigned', 'Available'),
                ('done', 'Transferred'),
            ], 'Status', readonly=True, select=True, track_visibility='onchange'
        ),
    }

    _defaults = {
        'type': 'receipt',
        'invoice_state': '2binvoiced',
    }

stock_picking_receipt()

class stock_move(osv.osv):
    _inherit = "stock.move"

    _columns = {
        'rate': fields.float('Rate', digits_compute=dp.get_precision('Account'), help="Rate for the product which is related to Purchase order"),
        'type': fields.related('picking_id', 'type', type='selection', selection=[('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal'), ('receipt', 'Receipt'), ('opening', 'Opening')], string='Shipping Type', store=True),
        'new_rate': fields.float('Rate', help="Rate for the product which is calculate after adding all tax"),
        'excies': fields.float('Excies'),
        'cess': fields.float('Cess'),
        'higher_cess': fields.float('Higher Cess'),
        'import_duty': fields.float('Import Duty'),
        'exe_excies': fields.float('Exempted Excies'),
        'exe_cess': fields.float('Exempted Cess'),
        'exe_higher_cess': fields.float('Exempted Higher Cess'),
        'exe_import_duty': fields.float('Exempted Import Duty'),
        'total_cost': fields.float('Sub Total', digits_compute=dp.get_precision('Account')),
        'package_and_forwording': fields.float('Packing & Forwarding', digits_compute=dp.get_precision('Account')),
        'freight': fields.float('Freight', digits_compute=dp.get_precision('Account')),
        'insurance': fields.float('Insurance', digits_compute=dp.get_precision('Account')),
        'analytic_account_id':fields.many2one('account.analytic.account','Project'),
        'discount': fields.float('Discount'),
    }

    def onchange_excise(self, cr, uid, ids, excise, cess, higher_cess, import_duty, context=None):
        return {'value': {'excise': excise or 0.0, 'exe_excies':excise or 0.0, 'cess': cess or 0.0, 'exe_cess': cess or 0.0, 'higher_cess': higher_cess or 0.0, 'exe_higher_cess': higher_cess or 0.0, 'import_duty': import_duty or 0.0, 'exe_import_duty': import_duty or 0.0}}

stock_move()

class purchase_order(osv.Model):
    _inherit = "purchase.order"

    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
        res = super(purchase_order, self)._prepare_order_line_move(cr, uid, order=order, order_line=order_line, picking_id=picking_id, context=context)
        res = dict(res, package_and_forwording=order_line.package_and_forwording, freight=order_line.freight, insurance=order_line.insurance, discount=order_line.discount)
        return res

purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
