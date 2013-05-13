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
        'maize_in': fields.char('Maize', size=256, readonly=True),
            
    }
stock_picking_in()

class purchase_order_line(osv.Model):
    _inherit = 'purchase.order.line'
    
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = super(purchase_order_line, self)._amount_line(cr, uid, ids, prop, arg, context=context)
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        child = []
        res = dict([(id, {'price_subtotal': 0.0, 'po_excise':0.0,'po_st':0.0,'po_cess':0.0,'line_advance':0.0}) for id in ids])
        for line in self.browse(cr, uid, ids, context=context):
            price_discount = line.price_unit
            if line.discount != 0:
                price_discount = (line.price_unit * (1 - (line.discount / 100)))
            
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, price_discount, line.product_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
            res[line.id]['line_advance']= (res[line.id]['price_subtotal'] * line.advance_percentage) / 100
            for tax in taxes['taxes']:
                if not tax.get('parent_tax', False):
                    res[line.id]['po_excise'] = tax.get('amount', 0)
                elif tax.get('price_unit') in child:
                    res[line.id]['po_st'] = tax.get('amount', 0)
                else:
                    res[line.id]['po_cess'] = tax.get('amount', 0)
                    child.append(tax.get('price_unit'))
        return res
    
    def _received_amount(self, cr, uid, ids, prop, arg, context=None):
        res = dict([(id, {'received_amount': 0.0, 'pending_amount':0.0}) for id in ids])
        picking_in_obj = self.pool.get('stock.picking.in')
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
    
    _columns = {
        'discount': fields.float('Discount (%)'),
        'price_subtotal': fields.function(_amount_line, multi="tax", string='Subtotal', digits_compute= dp.get_precision('Account'),store=True),
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
        'po_delivery': fields.related('order_id', 'delivey', type="char", relation="purchase.order",string="Mill Delivery/Ex-Godown",store=True),
        'po_indentor_id': fields.related('order_id', 'indentor_id', type="many2one", relation="res.users", string="Indentor",store=True),
        'po_excise': fields.function(_amount_line, multi="tax", string='Excise', digits_compute= dp.get_precision('Account'),store=True),
        'po_cess': fields.function(_amount_line, multi="tax",string='Cess', digits_compute= dp.get_precision('Account'),store=True),
        'po_st': fields.function(_amount_line, multi="tax",string='ST', digits_compute= dp.get_precision('Account'),store=True),
        'line_advance': fields.function(_amount_line, multi="tax", string="Advance", digits_compute= dp.get_precision('Account'),store=True),
        'received_amount': fields.function(_received_amount, multi="amount", string="Received", digits_compute= dp.get_precision('Account'),store=True),
        'pending_amount': fields.function(_received_amount, multi="amount", string="Pending", digits_compute= dp.get_precision('Account'),store=True),
        'last_month_consumption': fields.function(_last_consumption, string="Last Month Consumption", digits_compute= dp.get_precision('Account'),store=True),
      }
purchase_order_line()

class purchase_requisition(osv.osv):
    _inherit = "purchase.requisition"
    _order = "name desc"
    _columns = {
        #'purchase_ids' : fields.one2many('purchase.order','requisition_id','Purchase Orders',states={'done': [('readonly', True)]}),
        #'purchase_ids' : fields.many2many('purchase.order','purchase_requisition_rel11','requisition_id','purchase_id','Latest Requisition',states={'done': [('readonly', True)]}),
        'purchase_ids' : fields.many2many('purchase.order','purchase_requisition_rel11','requisition_id','purchase_id','Latest Requisition')
        }
    _defaults = {
                 'exclusive': 'exclusive',
    }
    
    def _seller_detail(self, cr, uid, requisition_line, supplier, product_supplier, context=None):
        product_uom = self.pool.get('product.uom')
        pricelist = self.pool.get('product.pricelist')
        supplier_info = self.pool.get("product.supplierinfo")
        product = requisition_line.product_id
        default_uom_po_id = product.uom_po_id.id
        qty = product_uom._compute_qty(cr, uid, requisition_line.product_uom_id.id, requisition_line.product_qty, default_uom_po_id)
        seller_delay = 0.0
        seller_price = False
        seller_qty = False
        if supplier.id ==  product_supplier.name and qty >= product_supplier.qty:
            seller_delay = product_supplier.delay
            seller_qty = product_supplier.qty
        supplier_pricelist = supplier.property_product_pricelist_purchase or False
        seller_price = pricelist.price_get(cr, uid, [supplier_pricelist.id], product.id, qty, False, {'uom': default_uom_po_id})[supplier_pricelist.id]
        if seller_qty:
            qty = max(qty,seller_qty)
        date_planned = self._planned_date(requisition_line.requisition_id, seller_delay)
        return seller_price, qty, default_uom_po_id, date_planned
    
    def request_all_supplier(self, cr, uid, ids, context=None):
        """
       Create New RFQ for Supplier
        """
        if context is None:
            context = {}
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        fiscal_position = self.pool.get('account.fiscal.position')
        purchase_list = []
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            location_id = requisition.warehouse_id.lot_input_id.id
            for line in requisition.line_ids:
                for product_supplier in line.product_id.seller_ids:
                    assert product_supplier.name.id, 'Supplier should be specified'
                    if product_supplier.name.id in filter(lambda x: x, [rfq.state <> 'cancel' and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
                         raise osv.except_osv(_('Warning!'), _('You have already one %s purchase order for this partner, you must cancel this purchase order to create a new quotation.') % rfq.state)
                    supplier_pricelist = product_supplier.name.property_product_pricelist_purchase or False
                    purchase_id = purchase_order.create(cr, uid, {
                                'origin': requisition.name,
                                'partner_id': product_supplier.name.id,
                                'pricelist_id': supplier_pricelist.id,
                                'location_id': location_id,
                                'company_id': requisition.company_id.id,
                                'fiscal_position': product_supplier.name.property_account_position and product_supplier.name.property_account_position.id or False,
                                'requisition_id':requisition.id,
                                'notes':requisition.description,
                                'warehouse_id':requisition.warehouse_id.id ,
                    })
                    res[requisition.id] = purchase_id
                    purchase_list.append(purchase_id)
                    product = line.product_id
                    seller_price, qty, default_uom_po_id, date_planned = self._seller_detail(cr, uid, line, product_supplier.name, product_supplier, context=context)
                    taxes_ids = product.supplier_taxes_id
                    taxes = fiscal_position.map_tax(cr, uid, product_supplier.name.property_account_position, taxes_ids)
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
        # Update the stored value (fields.function), so we write to trigger recompute
        purchase_order.write(cr, uid, purchase_list, {}, context=context)
        return self.write(cr, uid, [requisition.id], {'purchase_ids':[(6,0,purchase_list)]})

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
    def action_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for purchase in self.browse(cr, uid, ids, context=context):
            for pick in purchase.picking_ids:
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
            for inv in purchase.invoice_ids:
                if inv and inv.state not in ('cancel','draft'):
                    raise osv.except_osv(
                        _('Unable to cancel this purchase order.'),
                        _('You must first cancel all receptions related to this purchase order.'))
                if inv:
                    wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
        self.write(cr,uid,ids,{'state':'cancel'})

        for (id, name) in self.name_get(cr, uid, ids):
            wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_cancel', cr)
        return True
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
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                amount_untaxed = val1
                for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)

            other_charge = order.package_and_forwording  - order.commission
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['other_charges'] = cur_obj.round(cr, uid, cur, other_charge)
            amount_untaxed = res[order.id]['amount_tax'] + res[order.id]['amount_untaxed']
            if order.insurance_type == order.freight_type:
                if order.insurance_type == 'fix':
                    amount_untaxed += order.insurance
                    amount_untaxed += order.freight
                else:
                    if order.insurance != 0:
                        amount_untaxed += (amount_untaxed * order.insurance) / 100
                    if order.freight != 0:
                        amount_untaxed += (amount_untaxed * order.freight) / 100
            else:
                if order.insurance_type == 'fix' and order.freight_type == 'percentage':
                    amount_untaxed += order.insurance
                    if order.freight != 0:
                        amount_untaxed += (amount_untaxed * order.freight) / 100
                elif order.insurance_type == 'include':
                    if order.freight_type == 'percentage':
                        amount_untaxed += (amount_untaxed * order.freight) / 100
                    else:
                        amount_untaxed += order.freight
                elif order.freight_type == 'include':
                    if order.insurance_type == 'percentage':
                        amount_untaxed += (amount_untaxed * order.insurance) / 100
                    else:
                        amount_untaxed += order.insurance
                else:
                    if order.insurance != 0:
                        amount_untaxed += (amount_untaxed * order.insurance) / 100
                    amount_untaxed += order.freight
            
            total_discount = order.other_discount
            if order.discount_percentage != 0:
                total_discount += ((amount_untaxed + res[order.id]['other_charges']) * order.discount_percentage)/ 100
            res[order.id]['amount_total'] = amount_untaxed + res[order.id]['other_charges'] - total_discount
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    _columns = {
        'package_and_forwording': fields.float('Packing & Forwarding', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'insurance': fields.float('Insurance',  states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'commission': fields.float('Commission', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'delivey': fields.char('Ex. GoDown / Mill Delivey',size=50, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'po_series_id': fields.many2one('product.order.series', 'Series', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total amount"),
        'other_charges': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Other Charges',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight','package_and_forwording','commission','other_discount', 'discount_percentage', 'order_line'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="Other Charges(computed as Packing & Forwarding - (Commission + Other Discount))"),
        'excies_ids': fields.many2many('account.tax', 'purchase_order_exices', 'exices_id', 'tax_id', 'Excise', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'vat_ids': fields.many2many('account.tax', 'purchase_order_vat', 'vat_id', 'tax_id', 'VAT', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'freight': fields.float('Freight', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'insurance_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage (%)'), ('include', 'Include in price')], 'Insurance Type', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'freight_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage (%)'), ('include', 'Include in price')], 'Freight Type', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'payment_term_id': fields.many2one('account.payment.term', 'Payment Term', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'service_ids': fields.many2many('account.tax', 'purchase_order_service', 'service_id', 'tax_id', 'Service Tax', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'voucher_id': fields.many2one('account.voucher', 'Payment', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
        'contract_id': fields.many2one('product.order.series', 'Contract Series'),
        'supplier_code': fields.related('partner_id', 'supp_code', type='char', string='Supplier Code', store=True, readonly=True),
        'indentor_code': fields.related('indentor_id', 'login', type='char', string='Indentor Code', store=True, readonly=True),
        'dispatch_id': fields.many2one('purchase.dispatch', 'Dispatch'),
        'other_discount': fields.float('Discount / Round Off', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}, help="Discount in fix amount", track_visibility='always'),
        'discount_percentage':  fields.float('Discount (%)', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}, help="Discount in %", track_visibility='always'),
        'discount_amount':  fields.float('Discount (%)', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}, help="Discount in %", track_visibility='always'),
        'requisition_ids' : fields.many2many('purchase.requisition','purchase_requisition_rel11','purchase_id','requisition_id','Latest Requisition') 
    }

    _defaults = {
        'insurance_type': 'fix',
        'freight_type': 'fix'
     }
    
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        if order is None:
            self._order = 'amount_total'
        else:
            self._order = 'name DESC'
        return super(purchase_order, self).search(cr, user, args, offset, limit, order, context, count)

    def write(self, cr, uid, ids, vals, context=None):
        line_obj = self.pool.get('purchase.order.line')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for order in self.browse(cr, uid, ids, context=context):
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
                vat_ids = vals.get('service_ids') and vals.get('service_ids')[0][2] or []
            for line in order.order_line:
                line_obj.write(cr, uid, [line.id], {'taxes_id': [(6, 0, excies_ids + vat_ids+ service_ids)]}, context=context)
        return super(purchase_order, self).write(cr, uid, ids, vals, context=context)

    def onchange_reset(self, cr, uid, ids, insurance_type, freight_type):
        dict = {}
        if insurance_type == 'include':
            dict.update({'insurance': 0.0})
        if freight_type == 'include':
            dict.update({'freight': 0.0})
        return {'value': dict}

    def action_invoice_create(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get('account.invoice')
        invoice_id = super(purchase_order, self).action_invoice_create(cr, uid, ids, context=context)
        order = self.browse(cr, uid, ids[0], context=context)
        invoice_obj.write(cr, uid, [invoice_id], {'freight':order.freight, 'insurance':order.insurance, 'other_charges':order.other_charges}, context=context)
        invoice_obj.button_compute(cr, uid, [invoice_id], context=context, set_total=True)
        return invoice_id

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        res = super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)
        proc_obj = self.pool.get('procurement.order')
        series_obj = self.pool.get('product.order.series')
        seq_obj = self.pool.get('ir.sequence')
        for po in self.browse(cr, uid, ids, context=context):
            if not po.po_series_id:
                raise osv.except_osv(_("Warning !"),_('You cannot confirm a purchase order without any purchase order series.'))
            seq = series_obj.browse(cr, uid, po.po_series_id.id, context=context).seq_id.code
            contract_name = False
            if po.indent_id.contract:
                if not po.contract_id:
                    raise osv.except_osv(_("Warning !"),_('Please select contract series.'))
                contract_seq = series_obj.browse(cr, uid, po.contract_id.id, context=context).seq_id.code
                contract_name = seq_obj.get(cr, uid, contract_seq)
            self.write(cr, uid, [po.id], {'name': seq_obj.get(cr, uid, seq), 'contract_name': contract_name}, context=context)
            for pp in po.requisition_ids:
                if pp.exclusive=='exclusive':
                    for order in pp.purchase_ids:
                        print "order.id != po.id", order.id, po.id
                        if order.id != po.id:
                            proc_ids = proc_obj.search(cr, uid, [('purchase_id', '=', order.id)])
                            if proc_ids and po.state=='confirmed':
                                proc_obj.write(cr, uid, proc_ids, {'purchase_id': po.id})
                            wf_service = netsvc.LocalService("workflow")
                            wf_service.trg_validate(uid, 'purchase.order', order.id, 'purchase_cancel', cr)

                pp.tender_done(context=context)
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

        for porder in [order for order in self.browse(cr, uid, ids, context=context) if order.state == 'draft']:
            order_key = make_key(porder, ('partner_id', 'location_id', 'pricelist_id'))
            new_order = new_orders.setdefault(order_key, ({}, []))
            new_order[1].append(porder.id)
            order_infos = new_order[0]
            print "porder.origin", porder.origin
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
                    'delivey':porder.delivey or '',
                    'dispatch_id':porder.dispatch_id and porder.dispatch_id.id or False,
                    'excies_ids':[(6,0, [excies.id for excies in porder.excies_ids])],
                    'vat_ids':[(6,0, [vat.id for vat in porder.vat_ids])],
                    'insurance':porder.insurance,
                    'insurance_type':porder.insurance_type,
                    'freight':porder.freight,
                    'freight_type':porder.freight_type,
                    'other_discount': porder.other_discount,
                    'discount_percentage':porder.discount_percentage,                    
                })
                print "order_infos", order_infos
            else:
                if porder.date_order < order_infos['date_order']:
                    order_infos['date_order'] = porder.date_order
                if porder.notes:
                    order_infos['notes'] = (order_infos['notes'] or '') + ('\n%s' % (porder.notes,))
                if porder.origin:
                    order_infos['origin'] = (order_infos['origin'] or '')# + ' ' + porder.origin

            for order_line in porder.order_line:
                line_key = make_key(order_line, ('name', 'date_planned', 'taxes_id', 'price_unit', 'product_id', 'move_dest_id', 'account_analytic_id'))
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
    _columns = {
            'type': fields.selection([('out', 'Sending Goods'), ('receipt', 'Receipt'),('in', 'Getting Goods'), ('internal', 'Internal')], 'Shipping Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
            'ac_code_id': fields.many2one('ac.code', 'AC Code', help="AC Code"),
            'mc_code_id': fields.related('indent_id','analytic_account_id', relation='account.analytic.account', type='many2one', string="Project"),
            'tr_code_id': fields.many2one('tr.code', 'TR Code', help="TR Code"),
            'cylinder': fields.char('Cylinder Number', size=50),
            'excisable_item': fields.boolean('Excisable Item'),
                }
    
    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        receipt_obj = self.pool.get('stock.picking.receipt')
        stock_move = self.pool.get('stock.move')
        res = super(stock_picking,self).do_partial(cr, uid, ids, partial_datas, context=context)
        vals = {}
        if context.get('default_type') == 'in':
            move_line = []
            for pick in self.browse(cr, uid, ids, context=context):
                if not pick.purchase_id:
                    raise osv.except_osv(_('Configuration Error!'), _('Inward Not create without any Puchase Order'))
                if pick.state == 'done':
                    for move in pick.move_lines:
                        dict = stock_move.onchange_amount(cr, uid, [move.id], pick.purchase_id.id, move.product_id.id,0,0,0, context)
                        move_line.append(stock_move.copy(cr,uid,move.id, dict['value'],context=context))
                    vals= {'inward_id': pick.id or False}
                    if move.product_id and move.product_id.ex_chapter:
                        vals.update({'excisable_item': True})
                else:
                    for move in pick.backorder_id.move_lines:
                        dict = stock_move.onchange_amount(cr, uid, [move.id], pick.purchase_id.id, move.product_id.id,0,0,0, context)
                        move_line.append(stock_move.copy(cr,uid,move.id, dict['value'],context=context))
                    vals= {'inward_id': pick.backorder_id and pick.backorder_id.id or False}
                    if move.product_id and move.product_id.ex_chapter:
                        vals.update({'excisable_item': True})
                vals.update({'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.receipt'),
                        'partner_id': pick.partner_id.id,
                        'stock_journal_id': pick.stock_journal_id or False,
                        'origin': pick.origin or False,
                        'type': 'receipt',
                        'inward_date': datetime.today().strftime('%m-%d-%Y'),
                        'purchase_id': pick.purchase_id.id or False,
                        'move_lines': [(6,0, move_line)]

                        })
            receipt_id = receipt_obj.create(cr, uid, vals, context=context)
        return res
stock_picking()

class stock_picking_receipt(osv.Model):
    _name = "stock.picking.receipt"
    _inherit = "stock.picking"
    _table = "stock_picking"
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

    def _total_amount(self, cr, uid, ids, name, args, context=None):
        result = dict([(id, {'amount_total':0.0,'total_diff':0.0,'amount_subtotal':0.0}) for id in ids])
        for receipt in self.browse(cr, uid, ids, context=context):
            total = 0.0
            diff = 0.0
            import_duty = 0.0
            for line in receipt.move_lines:
                diff += line.diff
                total += line.amount
                import_duty += line.import_duty
            result[receipt.id]['total_diff'] = diff + import_duty
            result[receipt.id]['amount_subtotal'] = total
            result[receipt.id]['amount_total'] = total - ( diff + import_duty)
        return result
    
    def button_dummy(self, cr, uid, ids, context=None):
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
        'party_id': fields.many2one('res.partner', 'Party Name'),
        'amount_total': fields.function(_total_amount, multi="cal",type="float", string='Total', store=True),
        'total_diff': fields.function(_total_amount, multi="cal", type="float", string='Total Diff', help="Total Diff(computed as (Diff + Import Duty))", store=True),
        'amount_subtotal': fields.function(_total_amount, multi="cal", type="float", string='Total Amount', help="Total Amount(computed as (Total - Total Diff))", store=True),
        'department_id': fields.related('purchase_id', 'indent_id', 'department_id', type="many2one", relation="stock.location", store=True),
        'maize_receipt': fields.char('Maize', size=256, readonly=True),
    }
    _defaults = {
        'type': 'receipt',
    }

stock_picking_receipt()
#----------------------------------------------------------
# Stock Location
#----------------------------------------------------------
class stock_location(osv.osv):
    _inherit = "stock.location"
    _columns = {
            'chained_picking_type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal'),('receipt', 'Receipt')], 'Shipping Type', help="Shipping Type of the Picking List that will contain the chained move (leave empty to automatically detect the type based on the source and destination locations)."),
                }

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of the stock location must be unique!')
    ]

stock_location()

class stock_move(osv.osv):
    _inherit = "stock.move"
    
    def _get_year(self, cr, uid, ids, name, args, context=None):
        res = dict([(id, {'inward_year':'','puchase_year':'','indent_year':''}) for id in ids])
        move_year = po_year = indent_year = ''
        for move in self.browse(cr, uid, ids, context=context):
            move_date = datetime.strptime(move.create_date,'%Y-%m-%d %H:%M:%S').year
            move_year=str(move_date-1)+''+str(move_date)
            res[move.id]['inward_year'] = move_year
            if move.picking_id and move.picking_id.purchase_id:
                po_date = datetime.strptime(move.picking_id.purchase_id.date_order,'%Y-%m-%d').year
                po_year=str(po_date-1)+''+str(po_date)
                if move.picking_id.purchase_id.indent_date:
                    indent_date = datetime.strptime(move.picking_id.purchase_id.indent_date,'%Y-%m-%d %H:%M:%S').year
                    indent_year=str(indent_date-1)+''+str(indent_date)
                res[move.id]['puchase_year'] = po_year 
                res[move.id]['indent_year'] = indent_year
        return res
    _columns = {
            'type': fields.related('picking_id', 'type', type='selection', selection=[('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal'),('receipt', 'receipt')], string='Shipping Type',store=True),
            'rate': fields.float('Rate', digits_compute= dp.get_precision('Account'), help="Rate for the product which is related to Purchase order"),
            'diff': fields.float('Diff.', digits_compute= dp.get_precision('Account'), help="Amount to be add or less"),
            'amount': fields.float('Amount.', digits_compute= dp.get_precision('Account'), help="Total Amount"),
            'bill_no': fields.integer('Bill No'),
            'bill_date': fields.date('Bill Date'),
            'excies': fields.float('Excies.', digits_compute= dp.get_precision('Account')),
            'cess': fields.float('Cess.', digits_compute= dp.get_precision('Account')),
            'high_cess': fields.float('High cess.', digits_compute= dp.get_precision('Account')),
            'import_duty': fields.float('Import Duty.', digits_compute= dp.get_precision('Account')),
            'cenvat': fields.float('CenVAT.', digits_compute= dp.get_precision('Account')),
            'c_cess': fields.float('Cess.', digits_compute= dp.get_precision('Account')),
            'c_high_cess': fields.float('High Cess.', digits_compute= dp.get_precision('Account')),
            'tax_cal': fields.float('Tax Cal', digits_compute= dp.get_precision('Account')),
            'supplier_id': fields.related('picking_id', 'purchase_id', 'partner_id', type='many2one', relation='res.partner', string="Supplier", store=True),
            'po_name': fields.related('picking_id', 'purchase_id','name', type="char", size=64, relation='puchase.order', string="PO Number", store=True),
            'payment_id': fields.related('picking_id', 'purchase_id', 'payment_term_id','name', type="char", size=64, relation='account.payment.term',string="Payment", store=True),
            'indentor_id': fields.related('picking_id', 'purchase_id', 'indentor_id', type="many2one", relation='res.users', string="Indentor", store=True),
            'po_series_id': fields.related('picking_id', 'purchase_id', 'po_series_id', type="many2one", relation='product.order.series', string="PO series", store=True),
            'indent_id': fields.related('picking_id', 'purchase_id', 'indent_id', type="many2one", relation='indent.indent', string="Indent", store=True),
            'inward_year':fields.function(_get_year, multi="year", string="Inward Year",store=True),
            'puchase_year':fields.function(_get_year, multi="year", string="Puchase Year", store=True),
            'indent_year':fields.function(_get_year, multi="year", string="Puchase Year", store=True),
            'excisable_item': fields.related('picking_id', 'excisable_item', type="boolean", relation='stock.picking', string="Excisable Item", store=True),
            #'gate_pass_id': fields.related('picking_id', 'gp_no', type="many2one", relation='gate.pass', string="Gate Pass No", store=True),
            #'despatch_mode': fields.related('picking_id', 'despatch_mode', type="selection", relation='stock.picking', string="Mode of Despatch", store=True),
                }

    def onchange_amount(self, cr, uid, ids, purchase_id, product_id, diff, import_duty, tax_cal, context=None):
        res = {}
        tax = ''
        child_tax = 0
        if not context:
            context = {}

        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        line_id = purchase_line_obj.search(cr, uid, [('order_id', '=', purchase_id), ('product_id', '=', product_id)])
        line_id = line_id and line_id[0] or False
        if not line_id:
            raise osv.except_osv(_('Configuration Error!'), _('Puchase Order don\'t  have line'))
        line = purchase_line_obj.browse(cr, uid, line_id, context=context)
        move = [move for move in self.browse(cr, uid, ids,context=context) if move.id][0]
        tax_obj = self.pool.get('account.tax')

        order = purchase_obj.browse(cr, uid, purchase_id, context)
        if order.excies_ids:
            tax = order.excies_ids[0]
#        else:
#            tax = tax_obj.search(cr, uid, [('amount', '=', '0.12'), ('tax_type','=', 'excise')])
#            if not tax:
#                raise osv.except_osv(_('Configuration Error!'), _('Please define Excise @ 12.36% (Edu Cess 2% + H. Edu Cess 1%) tax properly !'))
#                tax = tax[0]
#           tax = tax_obj.browse(cr, uid, tax, context=context)

        if not tax:
            return {'value': {'amount': (line.price_unit* move.product_qty),'rate': line.price_unit}}

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
            tax_main = (line.price_unit* move.product_qty) * base_tax
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
            new_tax.update({'amount': (line.price_unit* move.product_qty) + tax_main+child_tax,'rate': line.price_unit})
        return {'value': new_tax}

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

class stock_partial_picking(osv.osv_memory):
    _name = "stock.partial.picking"
    _inherit = "stock.partial.picking"
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = {}
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not picking_ids or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('stock.picking', 'stock.picking.in', 'stock.picking.out','stock.picking.receipt'), 'Bad context propagation'
        picking_id, = picking_ids
        if 'picking_id' in fields:
            res.update(picking_id=picking_id)
        if 'move_ids' in fields:
            picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
            moves = [self._partial_move_for(cr, uid, m) for m in picking.move_lines if m.state not in ('done','cancel')]
            res.update(move_ids=moves)
        if 'date' in fields:
            res.update(date=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
        return res