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

import datetime
from openerp.osv import fields, osv
from openerp import netsvc
import openerp.addons.decimal_precision as dp

class purchase_order_line(osv.Model):
    _inherit = 'purchase.order.line'
    
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = super(purchase_order_line, self)._amount_line(cr, uid, ids, prop, arg, context=context)
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] -= line.discount
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, res[line.id], 1, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    _columns = {
        'discount': fields.float('Discount'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
                }
purchase_order_line()
class purchase_requisition(osv.osv):
    _inherit = "purchase.requisition"
    _order = "name desc"
    _defaults = {
                 'exclusive': 'exclusive',
    }
purchase_requisition()

class purchase_requisition_partner(osv.osv_memory):
    _inherit = "purchase.requisition.partner"
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
                for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_subtotal, 1, line.product_id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)
            other_charge = order.package_and_forwording  - order.commission
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['other_charges'] = cur_obj.round(cr, uid, cur, other_charge)
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
            res[order.id]['amount_total']= amount_untaxed + res[order.id]['amount_tax'] + res[order.id]['other_charges']
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    _columns = {
        'package_and_forwording': fields.float('Packing & Forwarding'),
        'insurance': fields.float('Insurance'),
        'commission': fields.float('Commission'),
        'other_charge': fields.float('Other Charges'),
        'other_discount': fields.float('Other Discount'),
        'delivey': fields.char('Ex. GoDown / Mill Delivey',size=50),
        'po_series_id': fields.many2one('product.order.series', 'PO Series'),
        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total amount"),
        'other_charges': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Other Charges',
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['excies_ids', 'vat_ids', 'insurance', 'insurance_type', 'freight_type','freight'], 10),
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The other charge"),
        'excies_ids': fields.many2many('account.tax', 'purchase_order_exices', 'exices_id', 'tax_id', 'Excise'),
        'vat_ids': fields.many2many('account.tax', 'purchase_order_vat', 'vat_id', 'tax_id', 'VAT'),
        'freight': fields.float('Freight'),
        'insurance_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage (%)'), ('include', 'Include in price')], 'Type', required=True),
        'freight_type': fields.selection([('fix', 'Fix Amount'), ('percentage', 'Percentage (%)'), ('include', 'Include in price')], 'Type', required=True),
    }

    _defaults = {
        'insurance_type': 'fix',
        'freight_type': 'fix'
     }

    def write(self, cr, uid, ids, vals, context=None):
        line_obj = self.pool.get('purchase.order.line')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for order in self.browse(cr, uid, ids, context=context):
            excies_ids = [excies_id.id for excies_id in order.excies_ids]
            vat_ids = [vat_id.id for vat_id in order.vat_ids]
            if ('excies_ids' in vals) and ('vat_ids' in vals):
                excies_ids = vals.get('excies_ids') and vals.get('excies_ids')[0][2] or []
                vat_ids = vals.get('vat_ids') and vals.get('vat_ids')[0][2] or []
            if 'excies_ids' in vals and 'vat_ids' not in vals:
                excies_ids = vals.get('excies_ids') and vals.get('excies_ids')[0][2] or []
                vat_ids = [vat_id.id for vat_id in order.vat_ids]
            if 'vat_ids' in vals and 'excies_ids' not in vals:
                excies_ids = [excies_id.id for excies_id in order.excies_ids]
                vat_ids = vals.get('vat_ids') and vals.get('vat_ids')[0][2] or []
            for line in order.order_line:
                line_obj.write(cr, uid, [line.id], {'taxes_id': [(6, 0, excies_ids + vat_ids)]}, context=context)
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
        for po in self.browse(cr, uid, ids, context=context):
            if po.requisition_id and (po.requisition_id.exclusive=='exclusive'):
                for order in po.requisition_id.purchase_ids:
                    if order.id != po.id:
                        proc_ids = proc_obj.search(cr, uid, [('purchase_id', '=', order.id)])
                        if proc_ids and po.state=='confirmed':
                            proc_obj.write(cr, uid, proc_ids, {'purchase_id': po.id})
                        wf_service = netsvc.LocalService("workflow")
                        wf_service.trg_validate(uid, 'purchase.order', order.id, 'purchase_cancel', cr)
                    
                    for line in order.order_line:
                        today = order.date_order
                        year = datetime.datetime.today().year
                        month = datetime.datetime.today().month
                        if month<4:
                            po_year=str(datetime.datetime.today().year-1)+'-'+str(datetime.datetime.today().year)
                        else:
                            po_year=str(datetime.datetime.today().year)+'-'+str(datetime.datetime.today().year+1)
                        self.pool.get('product.product').write(cr,uid,line.product_id.id,{
                                                                                              'last_supplier_rate': line.price_unit,
                                                                                              'last_po_no':order.id,
                                                                                              'last_po_series':order.po_series_id.id,
                                                                                              'last_supplier_code':order.partner_id.id,
                                                                                              'last_po_date':order.date_order,
                                                                                              'last_po_year':po_year
                                                                                          },context=context)
                po.requisition_id.tender_done(context=context)
        return res    
purchase_order()
