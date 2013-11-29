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
        'inward_id': fields.many2one('stock.picking.in', 'Inward', ondelete='set null', domain=[('type','=','in'), ('date_done','>','2013-04-01')]),
        'inward_date': fields.related('inward_id', 'date_done', type='datetime', string='Inward Date', readonly=True, store=True),
        'tr_code': fields.integer('TR Code'),
        'excisable_item': fields.boolean('Excisable Item', track_visibility='onchange'),
        'amount_total': fields.function(_total_amount, multi="cal", type="float", string='Total', store=True),
        'total_diff': fields.function(_total_amount, multi="cal", type="float", string='Total Diff', help="Total Diff", store=True),
        'amount_subtotal': fields.function(_total_amount, multi="cal", type="float", string='Total Amount', help="Total Amount(computed as (Total - Total Diff))", store=True),
        'import_duty': fields.function(_total_amount, multi="cal", type="float", string='Import Duty', help="Total Import Duty", store=True),
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
        'date_done': fields.datetime('Date of Transfer', help="Date of Completion", track_visibility='onchange'),
    }

    _defaults = {
        'type': 'receipt',
        'invoice_state': '2binvoiced',
    }
stock_picking_receipt()

class stock_move(osv.osv):
    _inherit = "stock.move"

    def _get_stock(self, cr, uid, ids, name, args, context=None):
        res = {}
        product_obj = self.pool.get('product.product')
        for move in self.browse(cr, uid, ids, context=context):
            product = product_obj.browse(cr, uid, [move.product_id.id])[0]
            res[move.id] = product and product.qty_available or 0.0
        return res 

    _columns = {
        #Fields to check with development team
        'rate': fields.float('Rate', digits_compute=dp.get_precision('Account'), help="Rate for the product which is related to Purchase order"),
        'supplier_id': fields.related('picking_id', 'purchase_id', 'partner_id', type='many2one', relation='res.partner', string="Supplier", store=True),
        'payment_id': fields.related('picking_id', 'purchase_id', 'payment_term_id', 'name', type="char", size=64, relation='account.payment.term', string="Payment", store=True),
#        'name': fields.char('Description', select=True),
        'avg_price': fields.float('Average Price', digits_compute=dp.get_precision('Account')),

        #Fields required for all Stock movement 
        'type': fields.related('picking_id', 'type', type='selection', selection=[('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal'), ('receipt', 'Receipt'), ('opening', 'Opening')], string='Shipping Type', store=True),
        'amount': fields.float('Amount.', digits_compute=dp.get_precision('Stock Picking Receipt'), help="Total Amount"),
        'qty_available': fields.float("Stock"),

        #Fields required for Receipts
        'bill_no': fields.char('Bill No', size=256),
        'bill_date': fields.date('Bill Date'),
        'new_rate': fields.float('Rate', help="Rate for the product which is calculate after adding all tax"),
        'diff': fields.float('Add (%)', digits_compute=dp.get_precision('Account'), help="Amount to be add"),
        'less_diff': fields.float('Less (%)', digits_compute=dp.get_precision('Account'), help="Amount to be less"),
        'diff_amount': fields.float('Diff amount', digits_compute=dp.get_precision('Account'), help="Difference Amount"),
        'excies': fields.float('Excies.', digits_compute=dp.get_precision('Stock Picking Receipt')),
        'cess': fields.float('Cess.', digits_compute=dp.get_precision('Stock Picking Receipt')),
        'high_cess': fields.float('High cess.', digits_compute=dp.get_precision('Stock Picking Receipt')),
        'import_duty': fields.float('Import Duty.', digits_compute=dp.get_precision('Stock Picking Receipt')),
        'import_duty1': fields.float('Import Duty.', digits_compute=dp.get_precision('Stock Picking Receipt')),
        'cenvat': fields.float('CenVAT.', digits_compute=dp.get_precision('Stock Picking Receipt')),
        'c_cess': fields.float('Cess.', digits_compute=dp.get_precision('Stock Picking Receipt')),
        'c_high_cess': fields.float('High Cess.', digits_compute=dp.get_precision('Stock Picking Receipt')),
        'tax_cal': fields.float('Tax Cal', digits_compute=dp.get_precision('Stock Picking Receipt')),

        'total_cost': fields.float('Total', digits_compute=dp.get_precision('Account')),

        #'excisable_item': fields.related('picking_id', 'excisable_item', type="boolean", relation='stock.picking', string="Excisable Item", store=True),
        'vat_unit': fields.float('VAT Unit', digits_compute=dp.get_precision('Account')),
        'packing_unit': fields.float('Packing Unit', digits_compute=dp.get_precision('Account')),
        'insurance_unit': fields.float('Insurance Unit', digits_compute=dp.get_precision('Account')),
        'freight_unit': fields.float('Freight Unit', digits_compute=dp.get_precision('Account')),
        'retention_unit': fields.float('Retention Unit', digits_compute=dp.get_precision('Account')),
        'analytic_account_id':fields.many2one('account.analytic.account','M/C Code'),
        'cylinder':fields.char('Cylinder', size=256),
        'advance_adjustment': fields.float('Advance Adjustment', digits_compute=dp.get_precision('Stock Picking Receipt')),
        'name': fields.char('Description'),
        'discount': fields.float('Discount'),
        #Fields required for Issue
    }

    def onchange_amount(self, cr, uid, ids, purchase_id, product_id, add_diff, less_diff, rate, import_duty, tax_cal, context=None):
        tax = ''
        child_tax = 0
        if not context:
            context = {}

        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        line_id = purchase_line_obj.search(cr, uid, [('order_id', '=', purchase_id), ('product_id', '=', product_id)])
        line_id = line_id and line_id[0] or False
        if not line_id:
            return {'value':{}}
            # raise osv.except_osv(_('Configuration Error!'), _('Puchase Order don\'t  have line'))
        line = purchase_line_obj.browse(cr, uid, line_id, context=context)
        move = [move for move in self.browse(cr, uid, ids, context=context) if move.id][0]

        order = purchase_obj.browse(cr, uid, purchase_id, context)
        amount = rate * move.product_qty if rate != 0.0 else line.new_price * move.product_qty
        diff_amount = amount * add_diff / 100 if add_diff != 0.0 else -(amount * less_diff / 100)
        if order.excies_ids:
            tax = order.excies_ids[0]

        if not tax:
            return {'value': {'amount': amount + diff_amount, 'rate': line.new_price, 'new_rate': rate if rate != 0.0 else line.new_price, 'diff_amount': diff_amount, 'vat_unit': line.vat_unit,
                              'insurance_unit': line.insurance_unit, 'freight_unit':line.freight_unit, 'packing_unit':line.packing_unit}}

        base_tax = tax.amount
        total_tax = base_tax
        for ctax in tax.child_ids:
            total_tax = total_tax + (base_tax * ctax.amount)

        new_tax = { 
            'excies':0.0,
            'cess': 0.0,
            'high_cess': 0.0,
            'cenvat':0.0,
            'c_cess': 0.0,
            'c_high_cess': 0.0,
        }

        if tax_cal == 0:
            tax_main = (line.price_unit * move.product_qty) * base_tax if tax.type not in ['fixed'] else move.product_qty * base_tax
        else:
            tax_main = (tax_cal * base_tax) / total_tax
        new_tax.update({'excies':tax_main, 'cenvat':tax_main})

        for ctax in tax.child_ids:
            cess = tax_main * ctax.amount
            child_tax += cess
            if ctax.tax_type == 'cess':
                new_tax.update({'cess':cess, 'c_cess':cess})
            if ctax.tax_type == 'hedu_cess':
                new_tax.update({'high_cess':cess, 'c_high_cess':cess})
        if tax_cal == 0:
            new_tax.update({'amount': amount + diff_amount, 'rate': line.price_unit, 'new_rate': rate if rate != 0.0 else line.new_price, 'diff_amount': diff_amount, 'vat_unit': line.vat_unit,
                            'insurance_unit': line.insurance_unit, 'freight_unit':line.freight_unit, 'packing_unit':line.packing_unit})
        new_tax.update({'amount': amount + diff_amount, 'rate': line.price_unit, 'new_rate': rate if rate != 0.0 else line.new_price, 'diff_amount': diff_amount, 'vat_unit': line.vat_unit,
                        'insurance_unit': line.insurance_unit, 'freight_unit':line.freight_unit, 'packing_unit':line.packing_unit})
        return {'value': new_tax}

    def onchange_quantity(self, cr, uid, ids, product_id, product_qty, product_uom, product_uos):
        res = super(stock_move, self).onchange_quantity(cr, uid, ids, product_id, product_qty, product_uom, product_uos)
        res['value'].update({'challan_qty':product_qty})
        return res

    def onchange_rate(self, cr, uid, ids, product_qty, price, add_diff, less_diff, context=None):
        amount = (product_qty * price)
        diff = amount * add_diff / 100 if add_diff != 0 else -amount * less_diff / 100
        if not diff:
            return {'value': {'amount': amount}}
        return {'value': {'amount': amount + diff}}

    def onchange_excise(self, cr, uid, ids, excise, cess, high_cess, import_duty, context=None):
        return {'value': {'excise': excise or 0.0, 'cenvat':excise or 0.0, 'cess': cess or 0.0, 'c_cess': cess or 0.0, 'high_cess': high_cess or 0.0, 'c_high_cess': high_cess or 0.0, 'import_duty': import_duty or 0.0, 'import_duty1': import_duty or 0.0}}

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
