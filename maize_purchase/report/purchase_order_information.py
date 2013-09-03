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

class purchase_order_information_report(osv.osv):
    _name = "purchase.order.information.report"
    _description = "Indent Purchase Statistics"
    _auto = False
    
    def calc_inward_qty(self, cr, uid, ids, field_name, arg, context=None):
        stock_move_obj = self.pool.get('stock.move')
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        inward_name = ''
        res = {}
        ids = list(set(ids))
        for id in ids:
            inward_qty = 0.0
            res[id] = {
                       'inward_qty_func': 0.0,
                      }
            move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id', '=', id), ('type', '=', 'in'), ('state','=','done')], context=context)
            for move_id in move_ids:
                inward_name = stock_move_obj.browse(cr, uid, move_id, context=context).picking_id.name
                delivery_date = stock_move_obj.browse(cr, uid, move_id, context=context).picking_id.date_done
                inward_qty += stock_move_obj.browse(cr, uid, move_id, context=context).product_qty
                res[id]['delivery_date'] = delivery_date
                res[id]['inward_name'] = inward_name    
            res[id]['inward_qty_func'] = inward_qty
        return res
    
    def calc_receipt_pending_qty(self, cr, uid, ids, field_name, arg, context=None):
        stock_move_obj = self.pool.get('stock.move')
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        receipt_name = ''
        res = {}
        ids = list(set(ids))
        for id in ids:
            receipt_qty = 0.0
            res[id] = {
                       'receipt_qty_func': 0.0,
                       'pending_qty_func': 0.0
                      }
            tot_qty = purchase_order_line_obj.browse(cr, uid, id, context=context).product_qty
            move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id', '=', id), ('type', '=', 'receipt'), ('state','=','done')], context=context)
            for move_id in move_ids:
                receipt_name = stock_move_obj.browse(cr, uid, move_id, context=context).picking_id.name
                receipt_qty += stock_move_obj.browse(cr, uid, move_id, context=context).product_qty
                res[id]['receipt_name'] = receipt_name
            res[id]['receipt_qty_func'] = receipt_qty
            res[id]['pending_qty_func'] = tot_qty - receipt_qty
        return res

    _columns = {
        'contract_id': fields.many2one('product.order.series', 'Contract Series'),
        'purchase_maize_id': fields.char('Maize PO Number', size=256, readonly=True),
        'indent_maize_id': fields.char('Maize Indent No', size=256, readonly=True),
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
        'po_series_id': fields.many2one('product.order.series', 'PO Series', readonly=True),
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
        'product_uom': fields.many2one('product.uom', 'Unit'),
        'partner_id':fields.many2one('res.partner', 'Supplier', readonly=True),
        'supplier_code':fields.char('Supplier Code', size=10, readonly=True),
        'payment_term_id':fields.many2one('account.payment.term', 'Payment Term'),
        'discount': fields.float('Disc %', readonly=True),
        'purchase_year': fields.char('Purchase Year', size=10, readonly=True),
        'indent_year': fields.char('Indent Year', size=10, readonly=True),
        'inward_qty_func': fields.function(calc_inward_qty, digits_compute= dp.get_precision('Account'), string='Inward Qty', type="float", multi='sums1'),
        'receipt_qty_func': fields.function(calc_receipt_pending_qty, digits_compute= dp.get_precision('Account'), string='Receipt Qty', type="float", multi='sums'),
        'pending_qty_func': fields.function(calc_receipt_pending_qty, digits_compute= dp.get_precision('Account'), string='Pending Qty', type="float", multi='sums'),
        'default_code': fields.char('Indent Year', size=10, readonly=True),
        'date_order': fields.date('Purchase Date', readonly=True),
        'inward_name': fields.function(calc_inward_qty, string='Inward Name', type='char', size=10, readonly=True, multi='sums1'),
        'receipt_name': fields.function(calc_receipt_pending_qty, string='Receipt Name', type='char', size=10, readonly=True, multi='sums'),
        'delivery_date': fields.function(calc_inward_qty, string='Delivery Date', type='date', readonly=True, multi='sums1')
    }
    _order = 'date desc'
        
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'purchase_order_information_report')
        cr.execute("""
            create or replace view purchase_order_information_report as (
               select
                    min(al.id) as id,
                    al.indent_id as indent_id,
                    al.name as name,
                    al.indent_maize_id as indent_maize_id,
                    al.contract as contract,
                    al.department_id as department_id,
                    al.purchase_id as purchase_id,
                    al.product_uom_qty as product_uom_qty,
                    al.price_unit as price_unit,
                    al.product_uom as product_uom,
                    al.discount as discount,
                    al.price_total as price_total,
                    al.purchase_maize_id as purchase_maize_id,
                    al.partner_id as partner_id,
                    al.supplier_code as supplier_code,
                    al.puchase_total as puchase_total,
                    al.requirement as requirement,
                    al.type as type,
                    al.item_for as item_for,
                    1 as nbr,
                    al.date as date,
                    al.product_id as product_id,
                    al.year as year,
                    al.month as month,
                    al.day as day,
                    al.indentor_id as indentor_id,
                    al.po_series_id as po_series_id,
                    al.state,
                    al.analytic_account_id as analytic_account_id,
                    al.contract_id as contract_id,
                    al.payment_term_id as payment_term_id,
                    al.indent_year as indent_year,
                    al.purchase_year as purchase_year,
                    al.inward_qty as inward_qty,
                    al.receipt_qty as receipt_qty,
                    al.pending_qty as pending_qty,
                    al.default_code as default_code,
                    al.date_order 
                from
                (select distinct(l.id) as id,
            l.product_qty as product_uom_qty,
            CASE WHEN sm.type = 'in' THEN
                sum(sm.product_qty)
                ELSE 0.0
                END AS inward_qty,
            CASE WHEN sm.type = 'receipt' THEN
                sum(sm.product_qty)
                ELSE 0.0
                END AS receipt_qty,
                    CASE WHEN sm.type in ('in') and min(sm.product_qty) !=0.0 THEN
                        l.product_qty - sum(sm.product_qty)
                        WHEN sm.type in ('in') THEN
                        l.product_qty
                        END AS pending_qty,
                    i.id as indent_id,
                    i.name as name,
                    i.maize as indent_maize_id,
                    i.contract as contract,
                    i.department_id as department_id,
                    po.id as purchase_id,
                    l.price_unit as price_unit,
                    l.product_uom as product_uom,
                    l.discount as discount,
                    po.amount_untaxed as price_total,
                    po.maize as purchase_maize_id,
                    po.partner_id as partner_id,
                    po.supplier_code as supplier_code,
                    po.amount_total as puchase_total,
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
                    ps.id as po_series_id,
                    i.state,
                    i.analytic_account_id as analytic_account_id,
                    po.contract_id as contract_id,
                    po.payment_term_id as payment_term_id,
                    sm.indent_year as indent_year,
                    sm.puchase_year as purchase_year,
                    p.default_code as default_code,
                    po.date_order as date_order
            from indent_indent i
            left join purchase_order_line l on (i.id=l.indent_id)
            left join purchase_order po on (l.order_id=po.id)
                    left join stock_location sl on (sl.id=i.department_id)
                    left join product_product p on (l.product_id=p.id)
                    left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_order_series ps on (po.po_series_id = ps.id)
                    left join stock_move sm on (sm.indent=i.id)
                where po.state != 'cancel' and po.contract != True and sm.product_id=p.id and sm.indent=i.id and sm.state = 'done'
                and sm.product_id=p.id and sm.state = 'done' and sm.type not in ('out', 'internal')
                group by po.id,sm.type,sm.state,po.id,
                    i.id,
                    i.name,
                    i.contract,
                    po.name,
                    po.maize,
                    po.amount_untaxed,
                    po.amount_total,
                    i.department_id,
                    i.requirement,
                    i.type,
                    i.item_for,
                    i.indent_date,
                    i.indentor_id,
                    i.state,
                    i.analytic_account_id,
                    l.id,
                    l.product_id,
                    ps.id,
                    l.product_qty,
                    l.price_unit,
                    l.product_uom,
                    l.discount,
                    po.partner_id,
                    po.supplier_code,
                    i.analytic_account_id,
                    po.contract_id,
                    po.contract,
                    sm.state,
                    sm.type,
                    sm.indent_year,
                    sm.puchase_year,
                    p.default_code,
                    po.date_order,
                    payment_term_id)
                AS al 
                group by
                    al.id,
                    al.name,
                    al.contract,
                    al.name,
                    al.purchase_maize_id,
                    al.price_total,
                    al.puchase_total,
                    al.department_id,
                    al.requirement,
                    al.type,
                    al.item_for,
                    al.date,
                    al.indentor_id,
                    al.state,
                    al.analytic_account_id,
                    al.product_id,
                    al.product_uom_qty,
                    al.price_unit,
                    al.product_uom,
                    al.discount,
                    al.partner_id,
                    al.supplier_code,
                    al.analytic_account_id,
                    al.contract_id,
                    al.contract,
                    al.indent_year,
                    al.purchase_year,
                    al.payment_term_id,
                    al.indent_id,
                    al.indent_maize_id,
                    al.purchase_id,
                    al.year,
                    al.month,
                    al.day,
                    al.po_series_id,
                    al.inward_qty,
                    al.receipt_qty,
                    al.pending_qty,
                    al.default_code,
                    al.date_order
                    )
        """)
        
purchase_order_information_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
