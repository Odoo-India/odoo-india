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

from openerp import tools
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class indent_purchase_report(osv.osv):
    _name = "indent.purchase.report"
    _description = "Indent Purchase Statistics"
    _auto = False
 
    def amount_tax(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'excise_tax': 0.0,
                'cess_tax': 0.0,
                'st_tax': 0.0,
                'insurance': 0.0,
                'pending_value':0.0,
            }
            tax = ''
            vat = ''
            insurance_tax = ''
            child_tax = 0
            if not context:
                context = {}
    
            purchase_obj = self.pool.get('purchase.order')
            purchase_line_obj = self.pool.get('purchase.order.line')
            line_id = purchase_line_obj.search(cr, uid, [('order_id', '=', order.purchase_id.id), ('product_id', '=', order.product_id.id)])
            line_id = line_id and line_id[0] or False
            if not line_id:
                raise osv.except_osv(_('Configuration Error!'), _('Puchase Order don\'t  have line'))
            line = purchase_line_obj.browse(cr, uid, line_id, context=context)

            if order.purchase_id.excies_ids:
                tax = order.purchase_id.excies_ids[0]
    #        else:
    #            tax = tax_obj.search(cr, uid, [('amount', '=', '0.12'), ('tax_type','=', 'excise')])
    #            if not tax:
    #                raise osv.except_osv(_('Configuration Error!'), _('Please define Excise @ 12.36% (Edu Cess 2% + H. Edu Cess 1%) tax properly !'))
    #                tax = tax[0]
    #           tax = tax_obj.browse(cr, uid, tax, context=context)
    
            def vat_cal(val,vat_id, context=None):
                if vat_id:
                    vat = vat_id[0]
                    vat_tax = val * vat.amount
                    res[order.id]['st_tax'] += vat.amount * 100
                    for ctax in vat.child_ids:
                        cess = val * ctax.amount
                        res[order.id]['st_tax'] += ctax.amount * 100
                        vat_tax += cess
                    res[order.id]['pending_value'] = val+ vat_tax
                    return res
                else:
                    res[order.id]['pending_value'] = val
                    return res
            
            if not tax:
                res[order.id]['pending_value'] = ( (line.price_unit - (line.price_unit * line.discount / 100))  *order.pending_qty)
                return vat_cal(res[order.id]['pending_value'], order.purchase_id.vat_ids or order.purchase_id.service_ids)
            
            base_tax = tax.amount
            total_tax = base_tax
            for ctax in tax.child_ids:
                total_tax = total_tax + (base_tax * ctax.amount)
            tax_main = ( (line.price_unit - (line.price_unit * line.discount / 100)) * order.pending_qty * base_tax )
            res[order.id]['excise_tax'] = base_tax * 100
    
            for ctax in tax.child_ids:
                cess = tax_main * ctax.amount
                child_tax += cess
                if ctax.tax_type == 'cess':
                    res[order.id]['cess_tax'] += ctax.amount *100
                if ctax.tax_type == 'hedu_cess':
                    res[order.id]['cess_tax'] += ctax.amount *100
            res[order.id]['pending_value'] = ( (line.price_unit - (line.price_unit * line.discount / 100)) * order.pending_qty) + tax_main+child_tax
            if tax:
                vat_cal(res[order.id]['pending_value'], order.purchase_id.vat_ids or order.purchase_id.service_ids)
            if order.purchase_id.insurance_type == 'percentage':
                insurance_tax = round((res[order.id]['pending_value'] * order.purchase_id.insurance) / 100,2)
            else:
                insurance_tax = order.purchase_id.insurance
            res[order.id]['insurance'] =  insurance_tax
            res[order.id]['pending_value'] += insurance_tax
        return res

    _columns = {
        'contract_id': fields.many2one('product.order.series', 'Contract Series'),
        'purchase_maize_id': fields.char('Maize PO Number', size=256, readonly=True),
        'indent_maize_id': fields.char('Maize Indent No', size=256, readonly=True),
        'purchase_date': fields.date('PO Date', readonly=True),
        'date': fields.date('Date of Indent', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
        'day': fields.char('Day', size=128, readonly=True),
        'contract': fields.boolean('Contract'),
        'department_id': fields.many2one('stock.location', 'Department', readonly=True),
        'requirement': fields.selection([('ordinary','Ordinary'), ('urgent','Urgent')], 'Requirement', readonly=True),
        'type': fields.selection([('new','New'), ('existing','Existing')], 'Type', readonly=True),
        'item_for': fields.selection([('store', 'Store'), ('capital', 'Capital')], 'Item For', readonly=True),
        'purchase_id': fields.many2one('purchase.order', 'PO Number', readonly=True),
        'indent_id': fields.many2one('indent.indent', 'Indent', readonly=True),
        'indentor_id': fields.many2one('res.users', 'Indentor', readonly=True),
        'nbr': fields.integer('# of Lines', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'date_planned' : fields.date('Delivery Date', readonly=True),
        'delivey' : fields.many2one('purchase.delivery', 'Ex. GoDown / Mill Delivey'),
        'po_series_id': fields.char('PO Series', size=64, readonly=True),
        'state':fields.selection([
            ('draft','Draft'),
            ('confirm','Confirm'),
            ('waiting_approval','Waiting For Approval'),
            ('inprogress','Inprogress'),
            ('received','Received'),
            ('reject','Rejected')
            ], 'State', readonly=True),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Project', readonly=True),
        'product_uom_qty': fields.float('Qty', readonly=True),
        'price_unit': fields.float('Rate', readonly=True),
        'price_total': fields.float('Untax', readonly=True),
        'puchase_total': fields.float('Total', readonly=True),
        'advance_amount': fields.float('Advance Amount', readonly=True),
        'product_uom': fields.many2one('product.uom', 'Unit'),
        'partner_id':fields.many2one('res.partner', 'Supplier', readonly=True),
        'payment_term_id':fields.many2one('account.payment.term', 'Payment Term'),
        'pending_qty': fields.float('Pending Qty', readonly=True),
        'discount': fields.float('Disc %', readonly=True),
        'excise_tax': fields.function(amount_tax, digits_compute= dp.get_precision('Account'), string='Excise', type="float", multi="tax",help="Excise Tax"),
        'cess_tax': fields.function(amount_tax, digits_compute= dp.get_precision('Account'), string='Cess', type="float", multi="tax",help="Cess Tax"),
        'service_tax': fields.function(amount_tax, digits_compute= dp.get_precision('Account'), string='ST', type="float", multi="tax",help="Serivce Tax"),
        'insurance': fields.function(amount_tax, digits_compute= dp.get_precision('Account'), string='Insurance', type="float", multi="tax",help="Insuance Amount"),
        'pending_value': fields.function(amount_tax, digits_compute= dp.get_precision('Account'), string='Pending Value', type="float", multi="tax",help="Pending Value"),
        'st_tax': fields.function(amount_tax, digits_compute= dp.get_precision('Account'), string='ST', type="float", multi="tax",help="ST"),
    }
    _order = 'date desc'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'indent_purchase_report')
        cr.execute("""
            create or replace view indent_purchase_report as (
                select
                    min(po.id) as id,
                    i.id as indent_id,
                    i.maize as indent_maize_id,
                    i.contract as contract,
                    i.department_id as department_id,
                    po.id as purchase_id,
                    l.product_qty as product_uom_qty,
                    l.price_unit as price_unit,
                    l.product_uom as product_uom,
                    l.discount as discount,
                    po.amount_untaxed as price_total,
                    po.maize as purchase_maize_id,
                    po.partner_id as partner_id,
                    po.amount_total as puchase_total,
                    l.advance_amount as advance_amount,
                    po.delivey as delivey,
                    l.date_planned as date_planned,
                    po.date_order as purchase_date,
                    i.requirement as requirement,
                    i.type as type,
                    i.item_for as item_for,
                    1 as nbr,
                    i.indent_date as date,
                    l.product_id as product_id,
                    to_char(i.indent_date, 'YYYY') as year,
                    to_char(i.indent_date, 'MM') as month,
                    to_char(i.indent_date, 'YYYY-MM-DD') as day,
                    i.indentor_id as indentor_id,
                    ps.name as po_series_id,
                    i.state,
                    i.analytic_account_id as analytic_account_id,
                    po.contract_id as contract_id,
                    CASE WHEN po.state = 'draft' or sm.state != 'done' or po.contract = True THEN
                        sum(l.product_qty) 
                    ELSE
                        l.product_qty - sum(sm.product_qty)
                    END AS pending_qty,
                    po.payment_term_id as payment_term_id
                from
                    indent_indent i
                    left join purchase_order po on (i.id=po.indent_id and po.state != 'cancel')
                    left join stock_location sl on (sl.id=i.department_id)
                    left join purchase_order_line l on (l.order_id = po.id)
                    left join product_product p on (l.product_id=p.id)
                    left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_order_series ps on (po.po_series_id = ps.id)
                    left join stock_move sm on (sm.indent=i.id and sm.type='receipt' and sm.product_id=p.id)
                where po.indent_id is not null and l.product_id is not null
                group by
                    po.id,
                    i.id,
                    i.name,
                    i.contract,
                    po.name,
                    po.maize,
                    po.amount_untaxed,
                    po.amount_total,
                    l.advance_amount,
                    po.date_order,
                    po.delivey,
                    i.department_id,
                    i.requirement,
                    i.type,
                    i.item_for,
                    i.indent_date,
                    i.indentor_id,
                    i.state,
                    i.analytic_account_id,
                    l.product_id,
                    ps.name,
                    l.product_qty,
                    l.price_unit,
                    l.product_uom,
                    l.discount,
                    l.date_planned,
                    po.partner_id,
                    i.analytic_account_id,
                    po.contract_id,
                    po.contract,
                    sm.state,
                    sm.type,
                    payment_term_id
            )
        """)
indent_purchase_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
