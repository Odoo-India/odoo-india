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

import math
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
from openerp import netsvc
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.osv.orm import browse_record, browse_null
from lxml import etree
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

SERIES = [
    ('repair', 'Repair'),
    ('purchase', 'Purchase'),
    ('store', 'Store')
]
class stock_picking_in(osv.osv):
    _inherit = "stock.picking.in"
    _order = "id desc"
    _columns = {
        'lr_no': fields.char("LR No",size=64),
        'lr_date': fields.date("LR Date"),
        'transporter':fields.char("Transporter",size=256),
        'hpressure':fields.integer("HPressure"),
        'dest_from': fields.char("Destination From",size=64),
        'dest_to': fields.char("Destination To",size=64),
        'lab_no':fields.integer("Lab No"),
        'gp_no': fields.integer("Gate Pass No"),
        'gp_year': fields.char("GP Year",size=64),
        'series_id':fields.selection(SERIES, 'Series'),
        'remark1': fields.char("Remark1",size=256),
        'remark2': fields.char("remark2",size=256),
        'case_code': fields.boolean("Cash Code"),
        'challan_no': fields.char("Challan Number",size=256),
        'despatch_mode': fields.selection([('person','By Person'),
                                           ('scooter','By Scooter'),
                                           ('tanker','By Tanker'),
                                           ('truck','By Truck'),
                                           ('auto_rickshaw','By Auto Rickshaw'),
                                           ('loading_rickshaw','By Loading Rickshaw'),
                                           ('tempo','By Tempo'),
                                           ('metador','By Metador'),
                                           ('rickshaw_tempo','By Rickshaw Tempo'),
                                           ('cart','By Cart'),
                                           ('cycle','By Cycle'),
                                           ('pedal_rickshaw','By Pedal Rickshaw'),
                                           ('car','By Car'),
                                           ('post_parcel','By Post Parcel'),
                                           ('courier','By Courier'),
                                           ('tractor','By Tractor'),
                                           ('hand_cart','By Hand Cart'),
                                           ('camel_cart','By Camel Cart'),
                                           ('others','Others'),],"Despatch Mode"),
        'other_dispatch': fields.char("Other Dispatch",size=256),
        'maize_in': fields.char('Maize', size=256, readonly=True)
    }
    _defaults = {
        'dest_to' : 'Kathwada'
    }
    
    def receipt_tree_view(self, cr, uid, ids, context):
        mod_obj = self.pool.get('ir.model.data')
        action_model, action_id = tuple(mod_obj.get_object_reference(cr, uid, 'maize_purchase', 'action_picking_tree4_receipt'))
        action = self.pool.get(action_model).read(cr, uid, action_id, context=context)
        ctx = eval(action['context'])
        ctx.update({
            'search_default_inward_id': ids,
        })
        action.update({'context': ctx,})
        return action

    def create(self, cr, uid, vals, context=None):
        vals['name'] = False
        return super(stock_picking_in, self).create(cr, uid, vals, context=context)

stock_picking_in()

class stock_picking_out(osv.Model):
    _inherit = 'stock.picking.out'

    def create(self, cr, uid, vals, context=None):
        vals['name'] = False
        return super(stock_picking_out, self).create(cr, uid, vals, context=context)

stock_picking_out()

class purchase_order_line(osv.Model):
    _inherit = 'purchase.order.line'
    
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = super(purchase_order_line, self)._amount_line(cr, uid, ids, prop, arg, context=context)
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        child = []
        val1 = amount_untaxed = packing_and_forwading = total_discount = freight = excise_tax = vat_tax = other_tax = service_tax = other_charge = total_qty = 0.0
        for line in self.browse(cr, uid, ids, context=context):
            res [line.id] = {'price_subtotal': 0.0, 'po_excise':0.0,'po_st':0.0,'po_cess':0.0,
                          'line_advance':0.0, 'amount_total': 0.0, 'packing_amount':0.0, 
                          'insurance_amount':0.0, 'freight_amount':0.0, 'new_price':0.0,
                          'vat_amount':0.0,'vat_unit':0.0,'packing_unit':0.0,'insurance_unit':0.0,'freight_unit':0.0}
            for old_line in line.order_id.order_line:
                total_qty += old_line.product_qty
            if line.order_id.packing_type == 'per_unit':
                packing_and_forwading += line.order_id.package_and_forwording * line.product_qty
            if line.order_id.freight_type == 'per_unit':
                freight += line.order_id.freight * line.product_qty
            price_discount = line.price_unit
            if line.discount != 0:
                price_discount = (line.price_unit * (1 - (line.discount / 100)))
            
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, price_discount, line.product_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
            val1 = res[line.id]['price_subtotal']
            res[line.id]['line_advance']= (res[line.id]['price_subtotal'] * line.advance_percentage) / 100
            for tax in taxes['taxes']:
                if not tax.get('parent_tax', False):
                    res[line.id]['po_excise'] += tax.get('amount', 0)
                elif tax.get('price_unit') in child:
                    res[line.id]['po_st'] = tax.get('amount', 0)
                else:
                    res[line.id]['po_cess'] = tax.get('amount', 0)
                    child.append(tax.get('price_unit'))
            amount_untaxed += res[line.id]['price_subtotal'] + res[line.id]['po_cess'] + res[line.id]['po_excise'] + res[line.id]['po_st']
            for vat in tax_obj.compute_all(cr, uid, line.order_id.vat_ids, line.order_id.excise_total, 1, line.product_id, line.order_id.partner_id)['taxes']:
                res[line.id]['vat_amount'] += vat.get('amount',0) / total_qty * line.product_qty
            res[line.id]['vat_unit']= res[line.id]['vat_amount'] / line.product_qty
            if line.order_id.packing_type == 'per_unit':
                res[line.id]['packing_amount'] = packing_and_forwading  - line.order_id.commission
                res[line.id]['packing_unit'] = res[line.id]['packing_amount'] / line.product_qty
            elif line.order_id.packing_type == 'percentage':
                res[line.id]['packing_amount'] = ((line.order_id.package_and_forwording * val1) / 100 -line.order_id.commission)
                res[line.id]['packing_unit'] = res[line.id]['packing_amount'] / line.product_qty
            elif line.order_id.packing_type == 'include':
                res[line.id]['packing_amount'] = line.order_id.package_and_forwording  - line.order_id.commission
                res[line.id]['packing_unit'] = res[line.id]['packing_amount'] / line.product_qty
            else:
                res[line.id]['packing_amount'] = (line.order_id.package_and_forwording  - line.order_id.commission) / total_qty * line.product_qty
                res[line.id]['packing_unit'] = res[line.id]['packing_amount'] / line.product_qty
            
            if line.order_id.insurance_type == line.order_id.freight_type:
                if line.order_id.insurance_type == 'fix':
                    res[line.id]['insurance_amount'] = line.order_id.insurance / total_qty * line.product_qty
                    res[line.id]['freight_amount'] = line.order_id.freight / total_qty * line.product_qty
                    res[line.id]['insurance_unit'] = res[line.id]['insurance_amount'] / line.product_qty
                    res[line.id]['freight_unit'] = res[line.id]['freight_amount'] / line.product_qty
                    amount_untaxed += res[line.id]['insurance_amount'] + res[line.id]['freight_amount']
            else:
                if line.order_id.insurance_type == 'fix':
                    res[line.id]['insurance_amount'] = line.order_id.insurance / total_qty * line.product_qty
                    res[line.id]['insurance_unit'] = res[line.id]['insurance_amount'] / line.product_qty
                    amount_untaxed += res[line.id]['insurance_amount']
                    if line.order_id.freight_type == 'per_unit':
                        res[line.id]['freight_amount'] = freight
                        res[line.id]['freight_unit'] = res[line.id]['freight_amount'] / line.product_qty
                        amount_untaxed += res[line.id]['freight_amount']
                    elif line.order_id.freight != 0:
                        res[line.id]['freight_amount'] = ((amount_untaxed * line.order_id.freight) / 100) / total_qty * line.product_qty 
                        res[line.id]['freight_unit'] = res[line.id]['freight_amount'] / line.product_qty
                        amount_untaxed += res[line.id]['freight_amount']
                elif line.order_id.insurance_type == 'include':
                    if line.order_id.freight_type == 'percentage':
                        res[line.id]['freight_amount'] = ((amount_untaxed * line.order_id.freight) / 100)
                        res[line.id]['freight_unit'] = res[line.id]['freight_amount'] / line.product_qty
                        amount_untaxed += res[line.id]['freight_amount']
                    elif line.order_id.freight_type == 'per_unit':
                        res[line.id]['freight_amount'] = freight
                        res[line.id]['freight_unit'] = res[line.id]['freight_amount'] / line.product_qty
                        amount_untaxed += res[line.id]['freight_amount']
                    else:
                        res[line.id]['freight_amount'] = line.order_id.freight / total_qty * line.product_qty
                        res[line.id]['freight_unit'] = res[line.id]['freight_amount'] / line.product_qty
                        amount_untaxed += res[line.id]['freight_amount']
                elif line.order_id.freight_type == 'include' or line.order_id.freight_type == 'extra':
                    if line.order_id.insurance_type == 'percentage':
                        res[line.id]['insurance_amount'] = ((amount_untaxed * line.order_id.insurance) / 100)
                        res[line.id]['insurance_unit'] = res[line.id]['insurance_amount'] / line.product_qty
                        amount_untaxed += res[line.id]['insurance_amount']
                    else:
                        res[line.id]['insurance_amount'] = line.order_id.insurance / total_qty * line.product_qty
                        res[line.id]['insurance_unit'] = res[line.id]['insurance_amount'] / line.product_qty
                        amount_untaxed += res[line.id]['insurance_amount']
                elif line.order_id.insurance_type == 'percentage' and line.order_id.insurance != 0:
                    res[line.id]['insurance_amount'] = ((amount_untaxed * line.order_id.insurance) / 100)
                    res[line.id]['insurance_unit'] = res[line.id]['insurance_amount'] / line.product_qty
                    amount_untaxed += res[line.id]['insurance_amount']
                    if line.order_id.freight_type == 'per_unit':
                        res[line.id]['freight_amount'] = freight
                        res[line.id]['freight_unit'] = res[line.id]['freight_amount'] / line.product_qty
                        amount_untaxed += res[line.id]['freight_amount']
                    else:
                        res[line.id]['freight_amount'] = line.order_id.freight / total_qty * line.product_qty
                        res[line.id]['freight_unit'] = res[line.id]['freight_amount'] / line.product_qty
                        amount_untaxed += res[line.id]['freight_amount']
                else:
                    if line.order_id.insurance != 0:
                        res[line.id]['insurance_amount'] = ((amount_untaxed * line.order_id.insurance) / 100) / total_qty * line.product_qty
                        res[line.id]['insurance_unit'] = res[line.id]['insurance_amount'] / line.product_qty
                        amount_untaxed += res[line.id]['insurance_amount']
                    res[line.id]['freight_amount'] = line.order_id.freight / total_qty * line.product_qty
                    res[line.id]['freight_unit'] = res[line.id]['freight_amount'] / line.product_qty
                    amount_untaxed += res[line.id]['freight_amount']
                
            total_discount = line.order_id.other_discount
            if line.order_id.discount_percentage != 0:
                total_discount += ((amount_untaxed + res[line.id]['packing_amount']) * line.order_id.discount_percentage)/ 100
            res[line.id]['amount_total'] += amount_untaxed + res[line.id]['packing_amount'] - total_discount
            for other in self.pool.get('account.tax').compute_all(cr, uid, line.order_id.other_tax_ids, 1, res[line.id]['amount_total'], line.product_id, line.order_id.partner_id)['taxes']:
                other_tax += other.get('amount',0.0)
            res[line.id]['amount_total'] += other_tax
            res [line.id]['new_price'] = res[line.id]['amount_total'] / line.product_qty
        return res
    
    def _received_amount(self, cr, uid, ids, prop, arg, context=None):
        res = dict([(id, {'received_amount': 0.0, 'pending_amount':0.0}) for id in ids])
        move_obj = self.pool.get('stock.move')
        for po_line in self.browse(cr, uid, ids, context=context):
            move_id = move_obj.search(cr, uid, [('type', '=', 'in'), ('origin', '=', po_line.order_id.name), ('state', '=', 'done')])
            if move_id:
                move = move_obj.browse(cr, uid, move_id[0])
                amount = move.product_qty * po_line.price_subtotal
                res[po_line.id]['received_amount'] = amount
                res[po_line.id]['pending_amount'] = po_line.price_subtotal - amount
        return res
    
    def _last_consumption(self, cr, uid, ids, prop, arg, context=None):
        last_month = str(datetime.now() - relativedelta(months=1)).split('-')[1]
        current_year = str(datetime.now()).split('-')[0]
        def last_day_of_month(any_day):
            next_month = any_day.replace(day=28) + relativedelta(days=4)  # this will never fail
            return next_month - relativedelta(days=next_month.day)
        last_day = str(last_day_of_month(datetime.today()- relativedelta(months=1))).split(' ')[0]
        res = {}
        consume_amount = 0.0
        list = []
        stock_obj = self.pool.get('stock.move')
        for line in self.browse(cr, uid, ids, context=context):
            stock_id = stock_obj.search(cr, uid, [('product_id', '=', line.product_id.id), ('type', '=', 'internal'),('state', '=', 'done'), ('create_date', '<=', last_day),('create_date', '>=', last_month+'-1-'+current_year)])
            if stock_id:
                for id in stock_id:
                    if id not in list:
                        stock_data = stock_obj.browse(cr, uid, id)
                        consume_amount += stock_data.product_qty * line.price_unit
                    list.append(id)
                res[line.id] =  consume_amount
            else:
                res[line.id] = 0.0
        return res
        
    def _get_advance_percentage(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        for po_line in self.browse(cr, uid, ids, context=context):
            if po_line.advance_amount and po_line.po_amount:
                res[po_line.id] = (po_line.advance_amount * 100) / po_line.po_amount
            else:
                res[po_line.id] = 0
        return res
    
    # Need To Fix (if product is change twice and uom is different than in 7.0 give warning of different category)
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        res = super(purchase_order_line,self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order, fiscal_position_id, date_planned,
            name, price_unit, context=context)
        if not product_id:
            return res
        product_product = self.pool.get('product.product')
        product = product_product.browse(cr, uid, product_id, context=context)
        if product.description_purchase:
            res['value'].update({'name': product.description_purchase})
        else:
            res['value'].update({'name': ''})
        return res
    
    def _get_po_order(self, cr, uid, ids, context=None):
        result = {}
#         for line in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
#             result[line.id] = True
        return result

    _columns = {
        # 'purchase.order.line'
        'indent_id': fields.many2one('indent.indent', 'Indent'),
        'indentor_id':fields.related('indent_id', 'indentor_id', relation='res.users', string='Indentor', type='many2one', store=True, readonly=True),        
        'department_id': fields.related('indent_id', 'department_id', relation='stock.location', string='Department', type='many2one', store=True, readonly=True), 

        'discount': fields.float('Discount (%)'),
        'price_subtotal': fields.function(_amount_line, multi="tax", string='Subtotal', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'person': fields.integer('Person',help="Number of Person work for this task"),
        'contract': fields.related('order_id', 'contract', type='boolean', relation='purchase.order', string='Contract', store=True, readonly=True),
        'po_name': fields.related('order_id', 'name', type='char', size=64, relation='purchase.order', string='PO No', store=True, readonly=True),
        'po_date': fields.related('order_id', 'date_order', type='date', relation='purchase.order', string='PO Date', store=True, readonly=True),
        'po_supplier_id': fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', string='Supplier Name', store=True, readonly=True),
        'po_amount': fields.related('order_id', 'amount_total', type='float', relation='purchase.order', string='Approx. Value', store=True, readonly=True),
        'advance_no': fields.related('order_id', 'voucher_id', 'id', type='integer', relation='account.voucher', string='Advance Note No', store=True, readonly=True),
        'advance_amount': fields.related('order_id', 'voucher_id', 'amount', type='float', relation='account.voucher', string='Advance Amount', store=True, readonly=True),
        'advance_date': fields.related('order_id', 'voucher_id', 'date', type='date', relation='account.voucher', string="Date",store=True),
        'advance_percentage': fields.function(_get_advance_percentage, string="(%)", digits_compute= dp.get_precision('Account'),store=True),
        'po_series_id': fields.related('order_id', 'po_series_id', type="many2one", relation="product.order.series", string="PO Sr", store=True),
        'po_payment_term_id': fields.related('order_id', 'payment_term_id', type="many2one", relation='account.payment.term', string="Payment Term", store=True),
        'po_delivery': fields.related('order_id', 'delivey', type="many2one", relation="purchase.delivery",string="Mill Delivery/Ex-Godown",store=True),

#        'po_indentor_id': fields.related('indent_id', 'indentor_id', type="many2one", relation="res.users", string="Indentor",store=True),
        
        'po_excise': fields.function(_amount_line, multi="tax", string='Excise', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'po_cess': fields.function(_amount_line, multi="tax",string='Cess', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'po_st': fields.function(_amount_line, multi="tax",string='ST', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'line_advance': fields.function(_amount_line, multi="tax", string="Advance", digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'received_amount': fields.function(_received_amount, multi="amount", string="Received", digits_compute= dp.get_precision('Account'),store=True),
        'pending_amount': fields.function(_received_amount, multi="amount", string="Pending", digits_compute= dp.get_precision('Account'),store=True),
        'last_month_consumption': fields.function(_last_consumption, string="Last Month Consumption", digits_compute= dp.get_precision('Account'),store=True),
        'name': fields.text('Description'),
        'amount_total': fields.function(_amount_line, multi="tax",string='Total Amount', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'packing_amount': fields.function(_amount_line, multi="tax",string='Packing Amount', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'insurance_amount': fields.function(_amount_line, multi="tax",string='Insurance Amount', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'freight_amount': fields.function(_amount_line, multi="tax",string='Freight Amount', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'new_price': fields.function(_amount_line, multi="tax",string='Price (include all tax)',digits_compute= dp.get_precision('Payment Term'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'vat_amount': fields.function(_amount_line, multi="tax",string='Total VAT Amount', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'vat_unit': fields.function(_amount_line, multi="tax",string='VAT Unit', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'packing_unit': fields.function(_amount_line, multi="tax",string='Packing Unit', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'insurance_unit': fields.function(_amount_line, multi="tax",string='Insurance Unit', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
        'freight_unit': fields.function(_amount_line, multi="tax",string='Freight Unit', digits_compute= dp.get_precision('Account'),
            store={
                'purchase.order': (_get_po_order, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, None, 10),
            }),
      }
    
    def action_confirm(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('product.product')
        current_year = str(datetime.now()).split('-')[0]
        next_year = str(datetime.now() + relativedelta(years=1)).split('-')[0]
        res = super(purchase_order_line,self).action_confirm(cr, uid, ids,context)
        for order in self.browse(cr, uid, ids, context):
            product = product_obj.write(cr, uid, order.product_id.id, {'last_po_no': order.order_id and order.order_id.id, 'last_supplier_rate': order.price_unit,'last_po_year':current_year+next_year})
        return res
purchase_order_line()

class purchase_requisition(osv.osv):
    _inherit = "purchase.requisition"
    _order = "name desc"
    
    def _get_indent(self, cr, uid, ids, name, args, context=None):
        result = {}
        indent_obj = self.pool.get('indent.indent')
        for requisition in self.browse(cr, uid, ids, context=context):
            indent_id = False
            if requisition.origin:
                indent_ids = indent_obj.search(cr, uid, [('name', '=', requisition.origin)], context=context)
                indent_id = indent_ids and indent_ids[0] or False
            result[requisition.id] = indent_id
        return result

    _columns = {
        'indent_id': fields.function(_get_indent, relation='indent.indent', type="many2one", string='Indent', store=True),
        'indentor_id': fields.related('indent_id', 'indentor_id', type='many2one', relation='res.users', string='Indentor', store=True, readonly=True),
        'department_id': fields.related('indent_id', 'department_id', relation='stock.location', string='Department', type='many2one', store=True, readonly=True), 
        
        'indent_date': fields.related('indent_id', 'indent_date', type='datetime', relation='indent.indent', string='Indent Date', store=True, readonly=True),
        'maize': fields.char('Maize', size=256, readonly=True),
        'purchase_ids' : fields.many2many('purchase.order','purchase_requisition_rel11','requisition_id','purchase_id','Latest Requisition')
    }
    _defaults = {
        'exclusive': 'exclusive',
    }
    
    def make_purchase_order(self, cr, uid, ids, partner_id, context=None):
        """
        Create New RFQ for Supplier
        """
        if context is None:
            context = {}
        assert partner_id, 'Supplier should be specified'
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        fiscal_position = self.pool.get('account.fiscal.position')
        supplier = res_partner.browse(cr, uid, partner_id, context=context)
        supplier_pricelist = supplier.property_product_pricelist_purchase or False
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            if supplier.id in filter(lambda x: x, [rfq.state <> 'cancel' and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
                raise osv.except_osv(_('Warning!'), _('You have already one %s purchase order for this partner, you must cancel this purchase order to create a new quotation.') % rfq.state)
            location_id = requisition.warehouse_id.lot_input_id.id
            purchase_id = purchase_order.create(cr, uid, {
                        'origin': requisition.origin,
                        'partner_id': supplier.id,
                        'pricelist_id': supplier_pricelist.id,
                        'location_id': location_id,
                        'company_id': requisition.company_id.id,
                        'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
                        'requisition_id':requisition.id,
                        'notes':requisition.description,
                        'warehouse_id':requisition.warehouse_id.id,
            }, context=context)
            res[requisition.id] = purchase_id
            for line in requisition.line_ids:
                product = line.product_id
                seller_price, qty, default_uom_po_id, date_planned = self._seller_details(cr, uid, line, supplier, context=context)
                taxes_ids = product.supplier_taxes_id
                taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
                purchase_order_line.create(cr, uid, {
                    'order_id': purchase_id,
                    'name': product.partner_ref,
                    'product_qty': qty,
                    'product_id': product.id,
                    'product_uom': default_uom_po_id,
                    'price_unit': seller_price,
                    'date_planned': date_planned,
                    'taxes_id': [(6, 0, taxes)],
                }, context=context)
            self.pool.get('purchase.requisition').write(cr, uid, requisition.id, {'purchase_ids':[(4, purchase_id)]})
        return res
    
    def request_all_supplier(self, cr, uid, ids, context=None):
        """
       Create New RFQ for List of Supplier in Product
        """
        if context is None:
            context = {}
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            for line in requisition.line_ids:
                for product_supplier in line.product_id.seller_ids:
                    purchase_id = False
                    assert product_supplier.name.id, 'Supplier should be specified'
                    if product_supplier.name.id in filter(lambda x: x, [rfq.state <> 'cancel' and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
                        purchase_id = sorted(filter(lambda x: x, [rfq.id or False for rfq in requisition.purchase_ids]),reverse=True)
                    if not purchase_id:
                        res = self.make_purchase_order(cr, uid, ids, product_supplier.name.id, context=context)
        return res

purchase_requisition()

class purchase_dispatch(osv.Model):
    _name = 'purchase.dispatch'
    _description = 'Purchase Dispatch'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=32, required=True),
    }

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of the dispatch must be unique!')
    ]

purchase_dispatch()

class purchase_delivery(osv.Model):
    _name = 'purchase.delivery'
    _description = 'Purchase Delivery'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=32, required=True),
    }

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of the dispatch must be unique!')
    ]

purchase_delivery()

class purchase_requisition_partner(osv.osv_memory):
    _inherit = "purchase.requisition.partner"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """
        @ Set domain into partner_id
        """
        context = context or {}
        res = super(purchase_requisition_partner, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if context.get('active_id'):
            cr.execute(""" SELECT psinfo.name FROM purchase_requisition_line prl,purchase_requisition pr,product_supplierinfo psinfo  
                            WHERE pr.id = %s
                            AND pr.id = prl.requisition_id
                            AND psinfo.product_id = prl.product_id """, (context['active_id'],))

            domain = "[('id', 'in', "+str([x[0] for x in cr.fetchall()])+")]"
            nodes = doc.xpath("//field[@name='partner_id']")
            for node in nodes:
                node.set('domain', domain)
        res['arch'] = etree.tostring(doc)
        return res

    _columns = {
        'po_series_id': fields.many2one('product.order.series', 'PO Series'),
    }
    def create_order(self, cr, uid, ids, context=None):
        active_ids = context and context.get('active_ids', [])
        data =  self.browse(cr, uid, ids, context=context)[0]
        context.update({'po_order_series':data.po_series_id or False})
        qu_id = self.pool.get('purchase.requisition').make_purchase_order(cr, uid, active_ids, data.partner_id.id, context=context)
        if qu_id:
            self.pool.get('purchase.order').write(cr,uid,qu_id[active_ids[0]],{'po_series_id':data.po_series_id.id or False})
        return {'type': 'ir.actions.act_window_close'}    
purchase_requisition_partner()

class purchase_order(osv.Model):
    _inherit = 'purchase.order'
    _order = 'id desc'
    
    def _get_number_of_days(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""

        DATETIME_FORMAT = "%Y-%m-%d"
        from_dt = datetime.strptime(date_from, DATETIME_FORMAT)
        to_dt = datetime.strptime(date_to, DATETIME_FORMAT)
        timedelta = to_dt - from_dt
        diff_day = timedelta.days + float(timedelta.seconds) / 86400
        return diff_day

    def onchange_compute_days1(self, cr, uid, ids, date_from, date_to,d1=0,d2=0,d3=0):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            result['value']['no_of_days1'] = 0
            result['value']['total_days'] = d1+d2+d3

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['no_of_days1'] = round(math.floor(diff_day))+1
            result['value']['total_days'] = d1+d2+round(math.floor(diff_day))+1+d3
        else:
            result['value']['no_of_days1'] = 0

        return result
    
    def onchange_compute_days2(self, cr, uid, ids, date_from, date_to,d1=0,d2=0,d3=0):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            result['value']['no_of_days2'] = 0
            result['value']['total_days'] = d1+d2+d3

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['no_of_days2'] = round(math.floor(diff_day))+1
            result['value']['total_days'] = round(math.floor(diff_day))+1+d1+d2+d3
        else:
            result['value']['no_of_days2'] = 0

        return result

    def onchange_compute_days3(self, cr, uid, ids, date_from, date_to,d1=0,d2=0,d3=0):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            result['value']['no_of_days3'] = 0
            result['value']['total_days'] = d1+d2+d3

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['no_of_days3'] = round(math.floor(diff_day))+1
            result['value']['total_days'] = round(math.floor(diff_day))+1+d1+d2+d3
        else:
            result['value']['no_of_days3'] = 0

        return result       

    def onchange_compute_days4(self, cr, uid, ids, date_from, date_to,d1=0,d2=0,d3=0):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            result['value']['no_of_days4'] = 0
            result['value']['total_days'] = d1+d2+d3

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['no_of_days4'] = round(math.floor(diff_day))+1
            result['value']['total_days'] = round(math.floor(diff_day))+1+d1+d2+d3
        else:
            result['value']['no_of_days4'] = 0

        return result
    
    def wkf_send_rfq(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        res = super(purchase_order, self).wkf_send_rfq(cr, uid, ids, context=context)
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'maize_purchase', 'email_template_edi_purchase')[1]
            if template_id:
                res['context']['default_template_id'] = template_id
        except ValueError:
            template_id = False
        return res

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'is_template':False})
        return super(purchase_order, self).copy(cr, uid, id, default, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for purchase in self.browse(cr, uid, ids, context=context):
            if purchase.voucher_id:
                if purchase.voucher_id.state not in ('draft', 'cancel'):
                    raise osv.except_osv(
                        _('Unable to cancel this purchase order.'),
                        _('First cancel an advance payment related to this purchase order.'))
                else:
                    wf_service.trg_validate(uid, 'account.voucher', purchase.voucher_id.id, 'cancel_voucher', cr)

        return super(purchase_order, self).action_cancel(cr, uid, ids, context=context)

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        amount_untaxed = 0
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'other_charges': 0.0,
                'excise_amount': 0.0,
                'excise_total': 0.0,
                'vat_amount': 0.0,
                'vat_total': 0.0,
            }
            val = val1 = packing_and_forwading = freight = excise_tax = vat_tax = other_tax = service_tax= 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                amount_untaxed = val1
                vat_tax = 0.0
                price_discount = line.price_unit
                if line.discount != 0:
                    price_discount = (line.price_unit * (1 - (line.discount / 100)))
                if order.packing_type == 'per_unit':
                    packing_and_forwading += order.package_and_forwording * line.product_qty
                if order.freight_type == 'per_unit':
                    freight += order.freight * line.product_qty
                #for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, price_discount, line.product_qty, line.product_id, order.partner_id)['taxes']:
                    #val += c.get('amount', 0.0)
                for exices in self.pool.get('account.tax').compute_all(cr, uid, order.excies_ids, price_discount, line.product_qty, line.product_id, order.partner_id)['taxes']:
                    excise_tax += exices.get('amount', 0.0)
                res[order.id]['excise_amount'] = excise_tax
                val = excise_tax+val1
                res[order.id]['excise_total'] = val
                for vat in self.pool.get('account.tax').compute_all(cr, uid, order.vat_ids, val, 1, line.product_id, order.partner_id)['taxes']:
                    vat_tax += vat.get('amount', 0.0)
                res[order.id]['vat_amount'] = vat_tax
                val += vat_tax
                for service in self.pool.get('account.tax').compute_all(cr, uid, order.service_ids, val, 1, line.product_id, order.partner_id)['taxes']:
                    service_tax = service.get('amount', 0.0)
                val += service_tax
                res[order.id]['vat_total'] = val
            if order.packing_type == 'per_unit':    
                other_charge = packing_and_forwading  - order.commission
            elif order.packing_type == 'percentage':
                other_charge = (order.package_and_forwording * val1) / 100 -order.commission
            elif order.packing_type == 'include':
                other_charge = order.package_and_forwording  - order.commission
            else:
                other_charge = order.package_and_forwording  - order.commission
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['other_charges'] = cur_obj.round(cr, uid, cur, other_charge)
            amount_untaxed = res[order.id]['vat_total']
            if order.insurance_type == order.freight_type:
                if order.insurance_type == 'fix':
                    amount_untaxed += order.insurance
                    amount_untaxed += order.freight
                #else:
                    #if order.insurance != 0:
                        #amount_untaxed += (amount_untaxed * order.insurance) / 100
                    #if order.freight != 0:
                        #amount_untaxed += (amount_untaxed * order.freight) / 100
            else:
                if order.insurance_type == 'fix': 
                    amount_untaxed += order.insurance
                    if order.freight_type == 'per_unit':
                        amount_untaxed += freight
                    elif order.freight != 0:
                        amount_untaxed += (amount_untaxed * order.freight) / 100
                elif order.insurance_type == 'include':
                    if order.freight_type == 'percentage':
                        amount_untaxed += (amount_untaxed * order.freight) / 100
                    elif order.freight_type == 'per_unit':
                        amount_untaxed += freight
                    else:
                        amount_untaxed += order.freight
                elif order.freight_type == 'include' or order.freight_type == 'extra':
                    if order.insurance_type == 'percentage':
                        amount_untaxed += (amount_untaxed * order.insurance) / 100
                    else:
                        amount_untaxed += order.insurance
                elif order.insurance_type == 'percentage' and order.insurance != 0:
                    amount_untaxed += (amount_untaxed * order.insurance) / 100
                    if order.freight_type == 'per_unit':
                        amount_untaxed += freight
                    else:
                        amount_untaxed += order.freight
                else:
                    if order.insurance != 0:
                        amount_untaxed += (amount_untaxed * order.insurance) / 100
                    amount_untaxed += order.freight
            
            total_discount = order.other_discount
            if order.discount_percentage != 0:
                total_discount += ((amount_untaxed + res[order.id]['other_charges']) * order.discount_percentage)/ 100
            res[order.id]['amount_total'] = amount_untaxed + res[order.id]['other_charges'] - total_discount
            for other in self.pool.get('account.tax').compute_all(cr, uid, order.other_tax_ids, 1, res[order.id]['amount_total'], order.product_id, order.partner_id)['taxes']:
                other_tax += other.get('amount',0.0)
            res[order.id]['amount_total'] += other_tax
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    def po_genrate(self, cr, uid, ids, context=None):
        default = {}
        default.update({
            'is_template': False,
            'is_copy': True,
        })
        return super(purchase_order, self).copy(cr, uid, ids[0], default, context=context)
    
    def _get_indent(self, cr, uid, ids, name, args, context=None):
        result = {}
        indent_obj = self.pool.get('indent.indent')
        for order in self.browse(cr, uid, ids, context=context):
            indent_id = False
            if order.origin:
                indent_ids = indent_obj.search(cr, uid, [('name', '=', order.origin)], context=context)
                indent_id = indent_ids and indent_ids[0] or False
            result[order.id] = indent_id
        return result

    def _prepare_order_picking(self, cr, uid, order, context=None):
        return {
            'name': False,
            'origin': order.name + ((order.origin and (':' + order.origin)) or ''),
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'partner_id': order.dest_address_id.id or order.partner_id.id,
            'invoice_state': '2binvoiced' if order.invoice_method == 'picking' else 'none',
            'type': 'in',
            'partner_id': order.dest_address_id.id or order.partner_id.id,
            'purchase_id': order.id,
            'company_id': order.company_id.id,
            'move_lines' : [],
            'voucher_id': order.voucher_id.id,
        }
        
    def _get_indent_ids(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for po in self.browse(cr, uid, ids, context):
            for line in po.line_ids:
                print line 
        
        return res

    _columns = {
        'indent_id': fields.related('order_line','indent_id', type='many2one', relation='indent.indent', string='Indents'),

        #fields from contract
        'contract': fields.boolean('Contract'),
        
        'no_of_days1': fields.integer("No of Days1", help="Calculate number of days for contracts"),
        'no_of_days2': fields.integer("No of Days2", help="Calculate Extended number of days 1st time for contracts"),
        'no_of_days3': fields.integer("No of Days3", help="Calculate Extended number of days 2nd time for contracts"),
        'no_of_days4': fields.integer("No of Days4", help="Calculate Extended number of days 2nd time for contracts"),
        'total_days': fields.integer("Total Days", help="Calculate Total number of days for contracts"),
        'date_from': fields.date('From Date', required=True),
        'date_to': fields.date('To Date'),
        'extended_date_from1': fields.date('Extended From'),
        'extended_date_from2': fields.date('Extended From'),
        'extended_date_from3': fields.date('Extended From'),
        'extended_date_to1': fields.date('Extended Upto'),
        'extended_date_to2': fields.date('Extended Upto'),
        'extended_date_to3': fields.date('Extended Upto'),
        'retention': fields.selection([('leived', 'CONTRACTOR\'S RETENTION TO BE LEIVED'),('not_leived', 'CONTRACTOR\'S RETENTION NOT TO BE LEIVED')], "Retention Type"),

        #fields from indent
        'maize': fields.char('Maize PO Number', size=256, readonly=True),
        'contract_name': fields.char('Contract Name', size=256, readonly=True),
        'voucher_id': fields.many2one('account.voucher', 'Payment'),
        
        'package_and_forwording': fields.float('Packing & Forwarding', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'insurance': fields.float('Insurance',  states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'commission': fields.float('Commission', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'delivey': fields.many2one('purchase.delivery', 'Ex. GoDown / Mill Delivey', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'po_series_id': fields.many2one('product.order.series', 'Series', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total amount"),
        'other_charges': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Other Charges',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="Other Charges(computed as Packing & Forwarding - (Commission + Other Discount))"),
        'excise_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Excise Amount',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total excise amount"),
        'excise_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Excise Total',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total after excise"),
        'vat_amount': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='VAT Amount',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total VAT amount"),
        'vat_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='VAT Total',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['service_ids','other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total after VAT"),
        'excies_ids': fields.many2many('account.tax', 'purchase_order_exices', 'exices_id', 'tax_id', 'Excise', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'vat_ids': fields.many2many('account.tax', 'purchase_order_vat', 'vat_id', 'tax_id', 'VAT', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'freight': fields.float('Freight', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'insurance_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage (%)'), ('include', 'Include in price')], 'Insurance Type', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'freight_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage (%)'), ('per_unit', 'Per Unit'), ('extra', 'EXTRA'),('include', 'Include in price')], 'Freight Type', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'packing_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage (%)'), ('per_unit', 'Per Unit'), ('include', 'Include in price')], 'Packing & Forwarding Type', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'payment_term_id': fields.many2one('account.payment.term', 'Payment Term', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'service_ids': fields.many2many('account.tax', 'purchase_order_service', 'service_id', 'tax_id', 'Service Tax', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'voucher_id': fields.many2one('account.voucher', 'Payment', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'contract_id': fields.many2one('product.order.series', 'Contract Series'),
        'supplier_code': fields.related('partner_id', 'supp_code', type='char', string='Supplier Code', store=True, readonly=True),
#        'indentor_code': fields.related('indentor_id', 'login', type='char', string='Indentor Code', store=True, readonly=True),
        'dispatch_id': fields.many2one('purchase.dispatch', 'Dispatch', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'other_discount': fields.float('Discount / Round Off', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}, help="Discount in fix amount", track_visibility='always'),
        'discount_percentage':  fields.float('Discount (%)', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}, help="Discount in %", track_visibility='always'),
        'discount_amount':  fields.float('Discount (%)', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}, help="Discount in %", track_visibility='always'),
        'requisition_ids' : fields.many2many('purchase.requisition','purchase_requisition_rel11','purchase_id','requisition_id','Latest Requisition'),
        'warehouse_id': fields.many2one('stock.warehouse', 'Destination Warehouse', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'our_ref': fields.char('Our Reference',size=250, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'your_ref': fields.char('Your Reference',size=250, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'other_tax_ids': fields.many2many('account.tax', 'purchase_order_other', 'other_tax_id', 'tax_id', 'Other Tax', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'is_template': fields.boolean('Is Template', help="If it's check means this PO is template and use for recreate same PO from it."),
        'is_copy': fields.boolean('Is Copy', help="If it's check means this PO is Copy from Template"),
    }

    _defaults = {
        'insurance_type': 'fix',
        'freight_type': 'fix',
        'packing_type': 'fix',
        'date_from': lambda *a: datetime.now().strftime('%Y-%m-%d'),
     }
    
#     def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
#         if order is None:
#             self._order = 'amount_total'
#         else:
#             self._order = 'name DESC'
#         return super(purchase_order, self).search(cr, user, args, offset, limit, order, context, count)

    def write(self, cr, uid, ids, vals, context=None):
        orders = self.browse(cr, uid, ids, context=context)
        res = super(purchase_order, self).write(cr, uid, ids, vals, context=context)
        
        line_obj = self.pool.get('purchase.order.line')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for order in orders:
            excies_ids = [excies_id.id for excies_id in order.excies_ids]
            vat_ids = [vat_id.id for vat_id in order.vat_ids]
            service_ids = [service_id.id for service_id in order.service_ids]
            if ('excies_ids' in vals) and ('vat_ids' in vals):
                excies_ids = vals.get('excies_ids') and vals.get('excies_ids')[0][2] or []
                vat_ids = vals.get('vat_ids') and vals.get('vat_ids')[0][2] or []
            if 'excies_ids' in vals and 'vat_ids' not in vals:
                excies_ids = vals.get('excies_ids') and vals.get('excies_ids')[0][2] or []
                vat_ids = [vat_id.id for vat_id in order.vat_ids]
            if 'vat_ids' in vals and 'excies_ids' not in vals:
                excies_ids = [excies_id.id for excies_id in order.excies_ids]
                vat_ids = vals.get('vat_ids') and vals.get('vat_ids')[0][2] or []
            if 'service_ids' in vals:
                service_ids = vals.get('service_ids') and vals.get('service_ids')[0][2] or []
            
            for line in order.order_line:
                line_obj.write(cr, uid, [line.id], {'taxes_id': [(6, 0, excies_ids + vat_ids+ service_ids)]}, context=context)
        return res

    def onchange_reset(self, cr, uid, ids, insurance_type, freight_type,packing_type):
        dict = {}
        if insurance_type == 'include':
            dict.update({'insurance': 0.0})
        if freight_type == 'include' or freight_type == 'extra':
            dict.update({'freight': 0.0})
        if packing_type == 'include':
            dict.update({'package_and_forwording': 0.0})
        return {'value': dict}

    def action_invoice_create(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get('account.invoice')
        invoice_id = super(purchase_order, self).action_invoice_create(cr, uid, ids, context=context)
        order = self.browse(cr, uid, ids[0], context=context)
        invoice_obj.write(cr, uid, [invoice_id], {'freight':order.freight, 'insurance':order.insurance, 'other_charges':order.other_charges,'book_series_id':order.po_series_id.id }, context=context)
        invoice_obj.button_compute(cr, uid, [invoice_id], context=context, set_total=True)
        return invoice_id

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        res = super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)
        proc_obj = self.pool.get('procurement.order')
        series_obj = self.pool.get('product.order.series')
        seq_obj = self.pool.get('ir.sequence')
        payment_term_obj = self.pool.get('account.payment.term')
        voucher_obj = self.pool.get('account.voucher')
        for po in self.browse(cr, uid, ids, context=context):
            sequence = po.name
            
#             if po.indent_id and po.indent_id.contract and not po.maize:
#                 if not po.contract_id:
#                     raise osv.except_osv(_("Warning !"),_('Please select a contract series.'))
#                 
#                 contract_seq = series_obj.browse(cr, uid, po.contract_id.id, context=context).seq_id.code
#                 sequence = seq_obj.get(cr, uid, contract_seq)
#             if not po.maize:
#                 if not po.po_series_id:
#                     raise osv.except_osv(_("Warning !"), _('Please select a purchase order series.'))
#                 seq = series_obj.browse(cr, uid, po.po_series_id.id, context=context).seq_id.code
#                 sequence = seq_obj.get(cr, uid, seq)
            
            voucher_id = False
            totlines = []
            total_amt = 0.0
            flag = False
            if po.payment_term_id and po.payment_term_id.line_ids:
                totlines = payment_term_obj.compute(cr, uid, po.payment_term_id.id, po.amount_untaxed, po.date_order or False, context=context)
            
                journal_ids = self.pool.get('account.journal').search(cr, uid, [('code', '=', 'BNK2')], context=context)
                journal_id = journal_ids and journal_ids[0] or False
            
                if po.payment_term_id and not journal_id:
                    raise osv.except_osv(_("Warning !"),_('Bank journal not defined, You must define a bank journal to process an advance payment.'))
        
                journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
                account_id = journal.default_credit_account_id or journal.default_debit_account_id or False
                if not account_id:
                    raise osv.except_osv(_("Warning !"),_('You must define a default debit and credit account for a journal.'))
                for line in totlines:
                    today = fields.date.context_today(self, cr, uid, context=context)
                    if line[0] == today:
                        total_amt += line[1]
                        flag = True
                if flag:
                    note = '''An advance payment of rupees: %s\n\nREFERENCES:\nPurchase order: %s\nIndent: %s''' %(total_amt, sequence, po.indent_id.name or '',)
                    voucher_id = voucher_obj.create(cr, uid, {'partner_id': po.partner_id.id, 'date': today, 'amount': total_amt, 'reference': sequence, 'type': 'payment', 'journal_id': journal_id, 'account_id': account_id.id, 'narration': note}, context=context)
                self.write(cr, uid, [po.id], {'name': sequence, 'voucher_id': voucher_id}, context=context)
            
            for pp in po.requisition_ids:
                if pp.exclusive=='exclusive':
                    for order in pp.purchase_ids:
                        if order.id != po.id:
                            proc_ids = proc_obj.search(cr, uid, [('purchase_id', '=', order.id)])
                            if proc_ids and po.state=='confirmed':
                                proc_obj.write(cr, uid, proc_ids, {'purchase_id': po.id})
                            wf_service = netsvc.LocalService("workflow")
                            wf_service.trg_validate(uid, 'purchase.order', order.id, 'purchase_cancel', cr)

                pp.tender_done(context=context)
        return res

    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
        res = super(purchase_order, self)._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context)
        res = dict(res, indent_id = order_line.indent_id.id)
        return res

    def open_advance_payment(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display advance payment of given purchase order ids.
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        voucher_id = self.browse(cr, uid, ids[0], context=context).voucher_id.id
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_payment_form')
        result = {
            'name': _('Advance Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': res and res[1] or False,
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': voucher_id,
        }
        return result

    def do_merge(self, cr, uid, ids, context=None):
        """ Copy the original do_merge method for set po_series_id field for new Purchase Order
        """
        #TOFIX: merged order line should be unlink
        wf_service = netsvc.LocalService("workflow")
        def make_key(br, fields):
            list_key = []
            for field in fields:
                field_val = getattr(br, field)
                if field in ('product_id', 'move_dest_id', 'account_analytic_id'):
                    if not field_val:
                        field_val = False
                if isinstance(field_val, browse_record):
                    field_val = field_val.id
                elif isinstance(field_val, browse_null):
                    field_val = False
                elif isinstance(field_val, list):
                    field_val = ((6, 0, tuple([v.id for v in field_val])),)
                list_key.append((field, field_val))
            list_key.sort()
            return tuple(list_key)

        # Compute what the new orders should contain

        new_orders = {}
        tander_ids = []

        for porder in [order for order in self.browse(cr, uid, ids, context=context) if order.state == 'draft']:
            if porder.requisition_ids:
                for tid in porder.requisition_ids:
                    tander_ids += [tid.id]
            
            order_key = make_key(porder, ('partner_id', 'location_id', 'pricelist_id'))
            new_order = new_orders.setdefault(order_key, ({}, []))
            new_order[1].append(porder.id)
            order_infos = new_order[0]
            
            if not order_infos:
                order_infos.update({
                    'origin': porder.origin,
                    'po_series_id': porder.po_series_id and porder.po_series_id.id or False,
                    'payment_term_id':porder.payment_term_id and porder.payment_term_id.id or False,
                    'date_order': porder.date_order,
                    'partner_id': porder.partner_id and porder.partner_id.id or False,
                    'dest_address_id': porder.dest_address_id and porder.dest_address_id.id or False,
                    'warehouse_id': porder.warehouse_id and porder.warehouse_id.id or False,
                    'location_id': porder.location_id and porder.location_id.id or False,
                    'pricelist_id': porder.pricelist_id and porder.pricelist_id.id or False,
                    'state': 'draft',
                    'order_line': {},
                    'notes': '%s' % (porder.notes or '',),
                    'fiscal_position': porder.fiscal_position and porder.fiscal_position.id or False,                    
                    'package_and_forwording':porder.package_and_forwording or 0.0,
                    'commission':porder.commission or 0.0,
                    'delivey':porder.delivey.id or '',
                    'dispatch_id':porder.dispatch_id and porder.dispatch_id.id or False,
                    'excies_ids':[(6,0, [excies.id for excies in porder.excies_ids])],
                    'vat_ids':[(6,0, [vat.id for vat in porder.vat_ids])],
                    'insurance':porder.insurance,
                    'insurance_type':porder.insurance_type,
                    'freight':porder.freight,
                    'freight_type':porder.freight_type,
                    'other_discount': porder.other_discount,
                    'discount_percentage':porder.discount_percentage
                })
            else:
                if porder.date_order < order_infos['date_order']:
                    order_infos['date_order'] = porder.date_order
                if porder.notes:
                    order_infos['notes'] = (order_infos['notes'] or '') + ('\n%s' % (porder.notes,))
                if porder.origin:
                    order_infos['origin'] = (order_infos['origin'] or '')# + ' ' + porder.origin

            for order_line in porder.order_line:
                line_key = make_key(order_line, ('name', 'date_planned', 'taxes_id', 'price_unit', 'product_id', 'move_dest_id', 'account_analytic_id', 'indent_id', 'indentor_id', 'department_id', 'account_analytic_id'))
                o_line = order_infos['order_line'].setdefault(line_key, {})
                if o_line:
                    # merge the line with an existing line
                    o_line['product_qty'] += order_line.product_qty * order_line.product_uom.factor / o_line['uom_factor']
                else:
                    # append a new "standalone" line
                    for field in ('product_qty', 'product_uom'):
                        field_val = getattr(order_line, field)
                        if isinstance(field_val, browse_record):
                            field_val = field_val.id
                        o_line[field] = field_val
                    o_line['uom_factor'] = order_line.product_uom and order_line.product_uom.factor or 1.0
            
        allorders = []
        orders_info = {}
        for order_key, (order_data, old_ids) in new_orders.iteritems():
            # skip merges with only one order
            if len(old_ids) < 2:
                allorders += (old_ids or [])
                continue

            # cleanup order line data
            for key, value in order_data['order_line'].iteritems():
                del value['uom_factor']
                value.update(dict(key))
            order_data['order_line'] = [(0, 0, value) for value in order_data['order_line'].itervalues()]
            order_data.update({'requisition_ids':[(6, 0, tander_ids)]})

            # create the new order
            neworder_id = self.create(cr, uid, order_data)
            orders_info.update({neworder_id: old_ids})
            allorders.append(neworder_id)

            # make triggers pointing to the old orders point to the new order
            for old_id in old_ids:
                wf_service.trg_redirect(uid, 'purchase.order', old_id, neworder_id, cr)
                wf_service.trg_validate(uid, 'purchase.order', old_id, 'purchase_cancel', cr)
        return orders_info

purchase_order()

class stock_picking(osv.Model):
    _inherit = "stock.picking"
    _order = "id desc"
    _columns = {
        'type': fields.selection([('out', 'Sending Goods'), ('receipt', 'Receipt'),('in', 'Getting Goods'), ('internal', 'Internal')], 'Shipping Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
        'ac_code_id': fields.many2one('ac.code', 'AC Code', help="AC Code"),
        
#        'mc_code_id': fields.related('indent_id','analytic_account_id', relation='account.analytic.account', type='many2one', string="Project"),

        'tr_code_id': fields.many2one('tr.code', 'TR Code', help="TR Code"),
        'cylinder': fields.char('Cylinder Number', size=50),
        'excisable_item': fields.boolean('Excisable Item'),
        'warehouse_id': fields.related('purchase_id', 'warehouse_id', type='many2one', relation='stock.warehouse', string='Destination Warehouse'),
        'voucher_id': fields.many2one('account.voucher', 'Payment'),
    }

    def create(self, cr, uid, vals, context=None):
        vals['name'] = False
        return super(stock_picking, self).create(cr, uid, vals, context=context)

    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        res = super(stock_picking, self)._prepare_invoice(cr, uid, picking=picking, partner=partner, inv_type=inv_type, journal_id=journal_id, context=context)
        freight = insurance = package_and_forwording = vat_amount = advance_amount = 0.0
        if picking.voucher_id and picking.voucher_id.state == 'posted':
            advance_amount = picking.voucher_id and picking.voucher_id.amount or 0.0
        for move in picking.move_lines:
            freight += move.freight_unit * move.product_qty
            insurance += move.insurance_unit * move.product_qty
            package_and_forwording += move.packing_unit * move.product_qty
            vat_amount += move.vat_unit * move.product_qty
        res = dict(res, freight = freight, insurance = insurance, package_and_forwording = package_and_forwording, vat_amount = vat_amount, voucher_id = picking.voucher_id.id, advance_amount = advance_amount)
        return res

    def _get_taxes_invoice(self, cr, uid, move_line, type):
        account_tax_obj =  self.pool.get('account.tax')
        
        old_tax_ids = super(stock_picking, self)._get_taxes_invoice(cr, uid, move_line, type)
        tax_ids = []
        if move_line.tax_cal != 0.0 or (move_line.excies and move_line.cess == 0 and move_line.high_cess == 0):
            for tax in account_tax_obj.browse(cr, uid, old_tax_ids):
                if tax.tax_type != 'excise':
                    tax_ids.append(tax.id)

            tax_amount = round(move_line.excies / move_line.product_qty, 3)
            name = str(tax_amount)+' per unit (Edu.cess 2% + H.Edu cess 1%)'
            excise_ids = account_tax_obj.search(cr, uid, [('tax_type','=', 'excise'),('amount','=', tax_amount)])
            if excise_ids:
                tax_ids += excise_ids
            else:
                new_tax_vals = {
                    'name': name, 
                    'tax_type': 'excise', 
                    'amount': tax_amount, 
                    'type':'fixed',
                    'sequence': 1,
                    'include_base_amount': True
                }
                if move_line.excies and move_line.cess != 0 and move_line.high_cess != 0:
                    child_tax = account_tax_obj.onchange_tax_type(cr, uid, False, str(tax_amount),'excise')
                new_tax_vals.update(child_tax.get('value'))
                tax_id = account_tax_obj.create(cr, uid, new_tax_vals)
                tax_ids.append(tax_id)
               
        else:
            tax_ids = old_tax_ids

        return tax_ids

    def action_invoice_create(self, cr, uid, ids, journal_id=False,
            group=False, type='out_invoice', context=None):
        type = 'in_invoice'
        res = super(stock_picking, self).action_invoice_create(cr, uid, ids, journal_id=journal_id, group=group, type=type, context=context)
        return res

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        receipt_obj = self.pool.get('stock.picking.receipt')
        stock_move = self.pool.get('stock.move')
        warehouse_obj = self.pool.get('stock.warehouse')
        res = super(stock_picking,self).do_partial(cr, uid, ids, partial_datas, context=context)
        vals = {}
        if context.get('default_type') == 'in':
            move_line = []
            for pick in self.browse(cr, uid, ids, context=context):
                if not pick.purchase_id:
                    raise osv.except_osv(_('Configuration Error!'), _('Inward Not create without any Puchase Order'))
                warehouse_dict = warehouse_obj.read(cr, uid, pick.warehouse_id.id, ['lot_input_id','lot_stock_id'], context=context)
                if pick.state == 'done':
                    for move in pick.move_lines:
                        dict = stock_move.onchange_amount(cr, uid, [move.id], pick.purchase_id.id, move.product_id.id,0,0,0,0,0, context)
                        dict['value'].update({'location_id': warehouse_dict.get('lot_input_id', False)[0], 'location_dest_id': warehouse_dict.get('lot_stock_id',False)[0]})
                        move_line.append(stock_move.copy(cr,uid,move.id, dict['value'],context=context))
                        if move.product_id and move.product_id.ex_chapter:
                            vals.update({'excisable_item': True})
                    vals.update({'inward_id': pick.id or False})
                else:
                    for move in pick.backorder_id.move_lines:
                        dict = stock_move.onchange_amount(cr, uid, [move.id], pick.purchase_id.id, move.product_id.id,0,0,0,0,0, context)
                        dict['value'].update({'location_id': warehouse_dict.get('lot_input_id', False)[0], 'location_dest_id': warehouse_dict.get('lot_stock_id',False)[0]})
                        move_line.append(stock_move.copy(cr,uid,move.id, dict['value'],context=context))
                        for move in pick.move_lines:
                            stock_move.write(cr, uid, [move.id], {'challan_qty':0.0})
                        if move.product_id and move.product_id.ex_chapter:
                            vals.update({'excisable_item': True})
                    vals.update({'inward_id': pick.backorder_id and pick.backorder_id.id or False})
                
                vals.update({'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.receipt'),
                    'partner_id': pick.partner_id.id,
                    'stock_journal_id': pick.stock_journal_id or False,
                    'origin': pick.origin or False,
                    'type': 'receipt',
                    'inward_date': datetime.today().strftime('%m-%d-%Y'),
                    'purchase_id': pick.purchase_id.id or False,
                    'voucher_id': pick.voucher_id.id,
                    'move_lines': [(6,0, move_line)]
                })
            receipt_obj.create(cr, uid, vals, context=context)
        else:
            for pick in self.browse(cr, uid, ids, context=context):
                if context.get('default_type') == 'receipt':
                    for move in pick.move_lines:
                        dict = stock_move.onchange_amount(cr, uid, [move.id], pick.purchase_id.id, move.product_id.id,move.diff,move.less_diff,move.new_rate,move.import_duty,move.tax_cal, context)
                        stock_move.write(cr, uid, [move.id], dict['value'])
                    if res[pick.id]['delivered_picking']:
                        for new_pick in self.browse(cr, uid, [res[pick.id]['delivered_picking']], context=context):
                            for move in new_pick.move_lines:
                                dict = stock_move.onchange_amount(cr, uid, [move.id], pick.purchase_id.id, move.product_id.id,move.diff,move.less_diff,move.new_rate,move.import_duty,move.tax_cal, context)
                                stock_move.write(cr, uid, [move.id], dict['value'])
                        receipt_obj.write(cr,uid,[res[pick.id]['delivered_picking']], {})
                    receipt_obj.write(cr,uid,ids, {})
        return res

    def action_done(self, cr, uid, ids, context=None):
        seq_obj = self.pool.get('ir.sequence')
        for picking in self.browse(cr, uid, ids, context=context):
            seq_name = 'stock.picking'
            if picking.type == 'in':
                seq_name = 'stock.picking.in'
            elif picking.type == 'out':
                seq_name = 'stock.picking.out'
            elif picking.type == 'receipt':
                seq_name = 'stock.picking.receipt'
            name = seq_obj.get(cr, uid, seq_name)
            self.write(cr, uid, [picking.id], {'name': name, 'state': 'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        return True

stock_picking()

class stock_picking_receipt(osv.Model):
    _name = "stock.picking.receipt"
    _inherit = "stock.picking"
    _table = "stock_picking"
    _order = "id desc"
    _description = "Receipt"

    def check_access_rights(self, cr, uid, operation, raise_exception=True):
        #override in order to redirect the check of acces rights on the stock.picking object
        return self.pool.get('stock.picking').check_access_rights(cr, uid, operation, raise_exception=raise_exception)

    def check_access_rule(self, cr, uid, ids, operation, context=None):
        #override in order to redirect the check of acces rules on the stock.picking object
        return self.pool.get('stock.picking').check_access_rule(cr, uid, ids, operation, context=context)

    def _workflow_trigger(self, cr, uid, ids, trigger, context=None):
        #override in order to trigger the workflow of stock.picking at the end of create, write and unlink operation
        #instead of it's own workflow (which is not existing)
        return self.pool.get('stock.picking')._workflow_trigger(cr, uid, ids, trigger, context=context)

    def _workflow_signal(self, cr, uid, ids, signal, context=None):
        #override in order to fire the workflow signal on given stock.picking workflow instance
        #instead of it's own workflow (which is not existing)
        return self.pool.get('stock.picking')._workflow_signal(cr, uid, ids, signal, context=context)
    
    def purchase_amount(self, cr, uid, purchase_id,product_id, context=None):
        po_field = ['other_tax_ids','excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','packing_type','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line']
        res = {}
        line_price = 0.0
        purchase_line_obj = self.pool.get('purchase.order.line')
        line_id = purchase_line_obj.search(cr, uid, [('order_id', '=', purchase_id), ('product_id', '=', product_id)])
        if not line_id:
            res.update({'new_price':0.0})
            return res
        for line in purchase_line_obj.browse(cr, uid, line_id, context=context):
            line_price  = line.new_price
            res.update({'new_price': line_price,'order': line.order_id})
        return res
    
    def _total_amount(self, cr, uid, ids, name, args, context=None):
        result = dict([(id, {'amount_total':0.0,'total_diff':0.0,'amount_subtotal':0.0, 'import_duty':0.0}) for id in ids])
        for receipt in self.browse(cr, uid, ids, context=context):
            total = 0.0
            diff = 0.0
            import_duty = 0.0
            for line in receipt.move_lines:
                po_dict = self.purchase_amount(cr, uid, receipt.purchase_id.id, line.product_id.id, context=context)
                diff += line.diff_amount
                total += po_dict['new_price'] * line.product_qty
                import_duty += line.import_duty
            result[receipt.id]['total_diff'] = diff
            result[receipt.id]['import_duty'] = import_duty
            result[receipt.id]['amount_subtotal'] = total
            result[receipt.id]['amount_total'] = total + ( diff + import_duty)
        return result
    
    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def onchange_bill_date(self, cr, uid, ids, bill_no, bill_date=False, context=None):
        stock_move = self.pool.get('stock.move')
        picking = self.browse(cr,uid,ids,context=context)
        if picking:
            for move in picking[0].move_lines:
                stock_move.write(cr,uid,move.id,{'bill_no':bill_no,'bill_date':bill_date})
        return True

    _columns = {
        'purchase_id': fields.many2one('purchase.order', 'Purchase Order',ondelete='set null', select=True),
        'inward_id': fields.many2one('stock.picking.in', 'Inward',ondelete='set null'),
        'inward_date': fields.date('Inward Date'),
        'challan_no': fields.char("Challan Number",size=256),
        'tr_code': fields.integer('TR Code'),
        'excisable_item': fields.boolean('Excisable Item'),
        'gp_received': fields.boolean('GP Received'),
        'gp_date': fields.date('GP Received Date'),
        'state': fields.selection(
            [('draft', 'Draft'),
            ('approved', 'Approved'), 
            ('auto', 'Waiting Another Operation'),
            ('confirmed', 'Waiting Availability'),
            ('assigned', 'Ready to Receive'),
            ('done', 'Received'),
            ('cancel', 'Cancelled'),],
            'Status', readonly=True, select=True,
            help="""* Draft: not confirmed yet and will not be scheduled until confirmed\n
                 * Approved: waiting for manager approval to proceed further\n
                 * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
                 * Waiting Availability: still waiting for the availability of products\n
                 * Ready to Receive: products reserved, simply waiting for confirmation.\n
                 * Received: has been processed, can't be modified or cancelled anymore\n
                 * Cancelled: has been cancelled, can't be confirmed anymore"""),
        'party_id': fields.many2one('res.partner', 'Excisable Party Name'),
        'amount_total': fields.function(_total_amount, multi="cal",type="float", string='Total', store=True),
        'total_diff': fields.function(_total_amount, multi="cal", type="float", string='Total Diff', help="Total Diff", store=True),
        'amount_subtotal': fields.function(_total_amount, multi="cal", type="float", string='Total Amount', help="Total Amount(computed as (Total - Total Diff))", store=True),

#        'department_id': fields.related('purchase_id', 'indent_id', 'department_id', type="many2one", relation="stock.location", store=True),
        
        'maize_receipt': fields.char('Maize', size=256, readonly=True),
        'import_duty': fields.function(_total_amount, multi="cal", type="float", string='Import Duty', help="Total Import Duty", store=True),
        'voucher_id': fields.many2one('account.voucher', 'Payment'),
        'bill_no': fields.integer('Bill No'),
        'bill_date': fields.date('Bill Date'),
    }
    _defaults = {
        'type': 'receipt',
        'invoice_state': '2binvoiced',
    }
stock_picking_receipt()

class stock_location(osv.osv):
    _inherit = 'stock.location'

    _columns = {
        'chained_picking_type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal'), ('receipt', 'Receipt')], 'Shipping Type', help="Shipping Type of the Picking List that will contain the chained move (leave empty to automatically detect the type based on the source and destination locations)."),
    }

    def _check_code(self, cr, uid, ids, context=None):
        for location in self.browse(cr, uid, ids, context=context):
            if location.code and len(location.code) != 3:
                return False
        return True

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of the stock location must be unique!')
    ]

    _constraints = [
        (_check_code, 'Error ! Code must be of 3 digit.', ['code']),
    ]

stock_location()

class stock_move(osv.osv):
    _inherit = "stock.move"
    
    def _get_year(self, cr, uid, ids, name, args, context=None):
        res = dict([(id, {'inward_year':'','puchase_year':'','indent_year':''}) for id in ids])
#         move_year = po_year = indent_year = ''
#         for move in self.browse(cr, uid, ids, context=context):
#             move_date = datetime.strptime(move.create_date,'%Y-%m-%d %H:%M:%S').year
#             move_year=str(move_date-1)+''+str(move_date)
#             res[move.id]['inward_year'] = move_year
#             if move.picking_id and move.picking_id.purchase_id:
#                 po_date = datetime.strptime(move.picking_id.purchase_id.date_order,'%Y-%m-%d').year
#                 po_year=str(po_date-1)+''+str(po_date)
#                 if move.picking_id.purchase_id.indent_date:
#                     indent_date = datetime.strptime(move.picking_id.purchase_id.indent_date,'%Y-%m-%d %H:%M:%S').year
#                     indent_year=str(indent_date-1)+''+str(indent_date)
#                 res[move.id]['puchase_year'] = po_year 
#                 res[move.id]['indent_year'] = indent_year
        return res
    
    def _get_stock(self, cr, uid, ids, name, args, context=None):
        res = {}
        product_obj = self.pool.get('product.product')
        for move in self.browse(cr, uid, ids, context=context):
            product = product_obj.browse(cr, uid, [move.product_id.id])[0]
            res[move.id] = product and product.qty_available or 0.0
        return res 
    
    def _get_today(self,cr, uid, ids, name, args, context=None):
        res = {}
        for move in self.browse(cr, uid, ids, context=context):
            res[move.id] = time.strftime('%d/%m/%Y')
        return res
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """
        @ Set Challan_qty String on the base of picking type
        """
        context = context or {}
        res = super(stock_move, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        eview = etree.fromstring(res['arch'])
        node = eview.xpath("//field[@name='challan_qty']") and eview.xpath("//field[@name='challan_qty']")[0]
        if context.get('picking_type') == 'internal':
            if 'challan_qty' in res['fields'].keys():
                node.set('string', _('Issue Quantity'))
        if context.get('picking_type') == 'out' and node in eview:
            location = eview.xpath("//field[@name='location_id']") and eview.xpath("//field[@name='location_id']")[0] 
            location.set('modifiers', '{"invisible":false}')
            eview.remove(node)
        if context.get('picking_type') == 'internal':
            stock = eview.xpath("//field[@name='qty_available']") and eview.xpath("//field[@name='qty_available']")[0]
            stock.set('modifiers', '{"invisible":false,"readonly":true}')
        res['arch'] = etree.tostring(eview)
        return res
    
    _columns = {
        'type': fields.related('picking_id', 'type', type='selection', selection=[('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal'),('receipt', 'receipt')], string='Shipping Type',store=True),
        'rate': fields.float('Rate', digits_compute= dp.get_precision('Account'), help="Rate for the product which is related to Purchase order"),
        'new_rate': fields.float('Rate', help="Rate for the product which is calculate after adding all tax"),
        'diff': fields.float('Add (%)', digits_compute= dp.get_precision('Account'), help="Amount to be add"),
        'less_diff': fields.float('Less (%)', digits_compute= dp.get_precision('Account'), help="Amount to be less"),
        'diff_amount': fields.float('Diff amount',digits_compute= dp.get_precision('Account'), help="Difference Amount"),
        'amount': fields.float('Amount.', digits_compute= dp.get_precision('Account'), help="Total Amount"),
        'bill_no': fields.integer('Bill No'),
        'bill_date': fields.date('Bill Date'),
        'excies': fields.float('Excies.', digits_compute= dp.get_precision('Account')),
        'cess': fields.float('Cess.', digits_compute= dp.get_precision('Account')),
        'high_cess': fields.float('High cess.', digits_compute= dp.get_precision('Account')),
        'import_duty': fields.float('Import Duty.', digits_compute= dp.get_precision('Account')),
        'import_duty1': fields.float('Import Duty.', digits_compute= dp.get_precision('Account')),
        'cenvat': fields.float('CenVAT.', digits_compute= dp.get_precision('Account')),
        'c_cess': fields.float('Cess.', digits_compute= dp.get_precision('Account')),
        'c_high_cess': fields.float('High Cess.', digits_compute= dp.get_precision('Account')),
        'tax_cal': fields.float('Tax Cal', digits_compute= dp.get_precision('Account')),
        'supplier_id': fields.related('picking_id', 'purchase_id', 'partner_id', type='many2one', relation='res.partner', string="Supplier", store=True),
        'po_name': fields.related('picking_id', 'purchase_id','name', type="char", size=64, relation='puchase.order', string="PO Number", store=True),
        'payment_id': fields.related('picking_id', 'purchase_id', 'payment_term_id','name', type="char", size=64, relation='account.payment.term',string="Payment", store=True),
        'po_series_id': fields.related('picking_id', 'purchase_id', 'po_series_id', type="many2one", relation='product.order.series', string="PO series", store=True),
        
        'inward_year':fields.function(_get_year, multi="year", string="Inward Year",store=True),
        'puchase_year':fields.function(_get_year, multi="year", string="Puchase Year", store=True),
        'indent_year':fields.function(_get_year, multi="year", string="Puchase Year", store=True),
        'excisable_item': fields.related('picking_id', 'excisable_item', type="boolean", relation='stock.picking', string="Excisable Item", store=True),
        'today': fields.function(_get_today, string="Today Date",type="date"),
        'name': fields.char('Description', select=True),
        'challan_qty': fields.float('Challan Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),states={'done': [('readonly', True)]},help="This Quntity is used for backorder and actual received quntity"),
        'qty_available': fields.function(_get_stock, string="Stock", type="float"),
        'vat_unit': fields.float('VAT Unit', digits_compute= dp.get_precision('Account')),
        'packing_unit': fields.float('Packing Unit', digits_compute= dp.get_precision('Account')),
        'insurance_unit': fields.float('Insurance Unit', digits_compute= dp.get_precision('Account')),
        'freight_unit': fields.float('Freight Unit', digits_compute= dp.get_precision('Account')),
    }

    def onchange_amount(self, cr, uid, ids, purchase_id, product_id, add_diff, less_diff,rate, import_duty, tax_cal, context=None):
        tax = ''
        child_tax = 0
        if not context:
            context = {}

        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        account_tax_obj = self.pool.get('account.tax')
        line_id = purchase_line_obj.search(cr, uid, [('order_id', '=', purchase_id), ('product_id', '=', product_id)])
        line_id = line_id and line_id[0] or False
        if not line_id:
            return {'value':{}}
            #raise osv.except_osv(_('Configuration Error!'), _('Puchase Order don\'t  have line'))
        line = purchase_line_obj.browse(cr, uid, line_id, context=context)
        move = [move for move in self.browse(cr, uid, ids,context=context) if move.id][0]

        order = purchase_obj.browse(cr, uid, purchase_id, context)
        amount = rate * move.product_qty if rate != 0.0 else line.new_price * move.product_qty
        diff_amount =  amount * add_diff / 100 if add_diff != 0.0 else -(amount * less_diff / 100)
        if order.excies_ids:
            tax = order.excies_ids[0]
#        else:
#            tax = tax_obj.search(cr, uid, [('amount', '=', '0.12'), ('tax_type','=', 'excise')])
#            if not tax:
#                raise osv.except_osv(_('Configuration Error!'), _('Please define Excise @ 12.36% (Edu Cess 2% + H. Edu Cess 1%) tax properly !'))
#                tax = tax[0]
#           tax = tax_obj.browse(cr, uid, tax, context=context)

        if not tax:
            return {'value': {'amount': amount + diff_amount,'rate': line.new_price,'new_rate': rate if rate != 0.0 else line.new_price,'diff_amount': diff_amount,'vat_unit': line.vat_unit,
                              'insurance_unit': line.insurance_unit,'freight_unit':line.freight_unit,'packing_unit':line.packing_unit}}

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
            tax_main = (line.price_unit* move.product_qty) * base_tax if tax.type not in ['fixed'] else move.product_qty * base_tax
        else:
            tax_main = (tax_cal * base_tax ) / total_tax
        new_tax.update({'excies':tax_main, 'cenvat':tax_main})

        for ctax in tax.child_ids:
            cess = tax_main * ctax.amount
            child_tax += cess
            if ctax.tax_type == 'cess':
                new_tax.update({'cess':cess, 'c_cess':cess})
            if ctax.tax_type == 'hedu_cess':
                new_tax.update({'high_cess':cess, 'c_high_cess':cess})
        if tax_cal == 0:
            new_tax.update({'amount': amount + diff_amount,'rate': line.price_unit, 'new_rate': rate if rate != 0.0 else line.new_price,'diff_amount': diff_amount,'vat_unit': line.vat_unit,
                            'insurance_unit': line.insurance_unit,'freight_unit':line.freight_unit,'packing_unit':line.packing_unit})
        new_tax.update({'amount': amount + diff_amount,'rate': line.price_unit, 'new_rate': rate if rate != 0.0 else line.new_price,'diff_amount': diff_amount,'vat_unit': line.vat_unit,
                        'insurance_unit': line.insurance_unit,'freight_unit':line.freight_unit,'packing_unit':line.packing_unit})
        return {'value': new_tax}
    
    def onchange_rate(self,cr, uid, ids, product_qty, price, add_diff, less_diff, context=None):
        amount = (product_qty * price)
        diff =  amount * add_diff / 100 if add_diff != 0 else -amount * less_diff / 100
        if not diff:
            return {'value': {'amount': amount}}
        return {'value': {'amount': amount + diff}}
    
    def onchange_excise(self, cr, uid, ids, excise, cess, high_cess,import_duty, context=None):
        return {'value': {'excise': excise or 0.0, 'cenvat':excise or 0.0, 'cess': cess or 0.0, 'c_cess': cess or 0.0, 'high_cess': high_cess or 0.0, 'c_high_cess': high_cess or 0.0, 'import_duty': import_duty or 0.0, 'import_duty1': import_duty or 0.0}}

    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
                            loc_dest_id=False, partner_id=False):
        res = super(stock_move,self).onchange_product_id(cr, uid, ids, prod_id, loc_id, loc_dest_id, partner_id)
        product = self.pool.get('product.product').browse(cr, uid, [prod_id])[0]
        res['value'].update({'qty_available': product and product.qty_available or 0.0})
        return res

stock_move()

class ac_code(osv.Model):
    _name = 'ac.code'
    _rec_name = 'code'
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for pckg in self.browse(cr, uid, ids, context=context):
            p_name = pckg.code and '[' + pckg.code + '] ' or ''
            p_name += pckg.name
            res.append((pckg.id,p_name))
        return res 
    
    _columns = {
        'name': fields.char('Name',size=256),
        'code': fields.char('Code', size=64)
        }

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique!')
    ]

ac_code()

class tr_code(osv.Model):
    _name = 'tr.code'
    _rec_name = 'code'
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for pckg in self.browse(cr, uid, ids, context=context):
            p_name = pckg.code and '[' + pckg.code + '] ' or ''
            p_name += pckg.name
            res.append((pckg.id,p_name))
        return res 
    
    _columns = {
        'name': fields.char('Name',size=256),
        'code': fields.char('Code', size=64)
        }

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique!')
    ]
tr_code()

class stock_invoice_onshipping(osv.osv_memory):
    _inherit = 'stock.invoice.onshipping'

    def open_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice_ids = []
        data_pool = self.pool.get('ir.model.data')
        res = self.create_invoice(cr, uid, ids, context=context)
        invoice_ids += res.values()
        inv_type = 'in_invoice'
        action_model = False
        action = {}
        if not invoice_ids:
            raise osv.except_osv(_('Error!'), _('Please create Invoices.'))
        if inv_type == "out_invoice":
            action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree1")
        elif inv_type == "in_invoice":
            action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree2")
        elif inv_type == "out_refund":
            action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree3")
        elif inv_type == "in_refund":
            action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree4")
        if action_model:
            action_pool = self.pool.get(action_model)
            action = action_pool.read(cr, uid, action_id, context=context)
            action['domain'] = "[('id','in', ["+','.join(map(str,invoice_ids))+"])]"
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: