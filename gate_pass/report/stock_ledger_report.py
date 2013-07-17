# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today Tiny SPRL (<http://tiny.be>).
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
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp


class report_stock_ledger(osv.osv):
    _name = "report.stock.ledger"
    _description = "Stock Ledger Report"
    _auto = False
    
    def closing_qty(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        closing_qty = 0
        for order in self.browse(cr, uid, ids, context=context):
            if order.type == 'receipt':
                closing_qty += order.receipt_qty
            else:
                closing_qty -=order.issue_qty
            res[order.id] = closing_qty
        return res
    
    _columns = {
        'date': fields.date('Date', readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partner', readonly=True),
        'product_id':fields.many2one('product.product', 'Product', readonly=True),
        'picking_id':fields.many2one('stock.picking', 'No', readonly=True),
        'type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('receipt', 'Receipt'), ('internal', 'Internal'), ('other', 'Others')], 'Shipping Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
        'state': fields.selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('confirmed', 'Confirmed'), ('assigned', 'Available'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True),
        'purchase_id': fields.many2one('purchase.order', 'Purchase Order No'),
        'po_series_id': fields.char('Purchase Series'),
        'indent_id': fields.many2one('indent.indent', 'Indent'),
        'indentor_id': fields.many2one('res.users', 'Indentor Name'),
        'rate': fields.float('Rate', digits_compute= dp.get_precision('Account'), help="Rate for the product which is related to Purchase order"),
        'department_id': fields.many2one('stock.location', 'Dept. Code'),
        'ac_code_id': fields.many2one('ac.code', 'AC Code', help="AC Code"),
        'tr_code_id': fields.many2one('tr.code', 'TR Code', help="TR Code"),
        'receipt_qty' : fields.float('Receipt Quantity', digits_compute= dp.get_precision('Account')),
        'receipt_value' : fields.float('Receipt Value', digits_compute= dp.get_precision('Account')),
        'issue_amount' : fields.float('Issue Value', digits_compute= dp.get_precision('Account')),
        'issue_qty' : fields.float('Issue Quantity', digits_compute= dp.get_precision('Account')),
        'closing_qty' : fields.function(closing_qty,string='Closing Quantity',type="float", digits_compute= dp.get_precision('Account')),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_stock_ledger')
        cr.execute("""
            CREATE OR REPLACE view report_stock_ledger AS (
                SELECT
                        min(sm.id) as id,
                        sm.product_id as product_id,
                        sm.picking_id as picking_id,
                        sm.date as dp,
                        sp.tr_code_id as tr_code_id,
                        sm.indent_id as indent_id,
                        sm.indentor_id as indentor_id,
                        ps.name as po_series_id,
                        sp.purchase_id as purchase_id,
                        sm.partner_id as partner_id,
                        CASE WHEN sp.type in ('receipt') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor)
                            ELSE 0.0
                            END AS receipt_qty,
                        sm.rate as rate,
                        CASE WHEN sp.type in ('receipt') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor) * sm.rate
                            ELSE 0.0
                            END AS receipt_value,
                        CASE WHEN sp.type in ('intenal') THEN
                                        sum(sm.product_qty * pu.factor / pu2.factor)
                                        ELSE 0.0
                                        END AS issue_qty,
                        CASE WHEN sp.type in ('internal') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor) * pp.weighted_rate
                            ELSE 0.0
                            END AS issue_amount,
                            sm.state as state,
                            sp.type as type,
                            sp.department_id as department_id,
                            sp.ac_code_id as ac_code_id,
                            to_char(date_trunc('day',sm.date), 'YYYY-MM-DD') as date
                    FROM
                        stock_move sm
                        LEFT JOIN stock_picking sp ON (sm.picking_id=sp.id)
                        LEFT JOIN product_product pp ON (sm.product_id=pp.id)
                        LEFT JOIN product_uom pu ON (sm.product_uom=pu.id)
                        LEFT JOIN product_uom pu2 ON (sm.product_uom=pu2.id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                        LEFT JOIN purchase_order po on (sp.purchase_id=po.id)
                        LEFT JOIN product_order_series ps on (po.po_series_id = ps.id)
                        LEFT JOIN stock_picking spi ON (sp.inward_id =spi.id)
                        where sm.type in ('internal','receipt') and sm.state in ('done')
                    GROUP BY
                        sm.id,sp.type, sm.date,sm.supplier_id,sm.partner_id,
                        sm.product_id,sm.state,sm.date_expected,sm.picking_id,
                        pp.weighted_rate,pu.factor,sm.rate,sp.purchase_id,sp.department_id,ps.name,sm.indent_id,sm.indentor_id,sp.tr_code_id,sp.ac_code_id)
        """)

report_stock_ledger()
