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
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class report_last_receipt_stock_move(osv.osv):
    _name = "report.last.receipt.stock.move"
    _description = "Moves Statistics"
    _auto = False
    
    def last_receipt_cal(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        stock_move_obj = self.pool.get('stock.move')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = { 
                    'last_receipt_date': '',
                    'last_issue_date': '',
                    'not_moved_months': 0,
                }
            recipt_ids = stock_move_obj.search(cr, uid , [('state', '=', 'done'), ('type', '=', 'receipt'), ('product_id','=',order.product_id.id)], order='date', context=context)
            last_issue_ids = stock_move_obj.search(cr, uid , [('state', '=', 'done'), ('type', '=', 'internal'), ('product_id','=',order.product_id.id)], order='date', context=context)
            receipt_date = ''
            last_isuue_date = ''
            total_months = 0
            current_date = datetime.now()  
            if recipt_ids:
                receipt_date = stock_move_obj.browse(cr, uid, recipt_ids[-1], context=context).date
                receipt_date = datetime.strptime(receipt_date,DEFAULT_SERVER_DATETIME_FORMAT)
                total_months = 12 * (current_date.year-receipt_date.year) + (current_date.month-receipt_date.month)
                total_months = (total_months - 1 if current_date.day < receipt_date.day else total_months)       
            if last_issue_ids:
                last_isuue_date = stock_move_obj.browse(cr, uid, last_issue_ids[-1], context=context).date
            res[order.id]['last_receipt_date']=str(receipt_date)
            res[order.id]['last_issue_date']=last_isuue_date
            res[order.id]['not_moved_months']=total_months
        return res
            
            
    _columns = {
        'date': fields.date('Date', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'day': fields.char('Day', size=128, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
        'product_id':fields.many2one('product.product', 'Product', readonly=True),
        'company_id':fields.many2one('res.company', 'Company', readonly=True),
        'type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('receipt', 'Receipt'), ('internal', 'Internal'), ('other', 'Others')], 'Shipping Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
        'state': fields.selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('confirmed', 'Confirmed'), ('assigned', 'Available'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True),
        'product_qty':fields.integer('Quantity',readonly=True),
        'categ_id': fields.many2one('product.category', 'Product Category', ),
        'value' : fields.float('Total Value', required=True),
        'product_uom': fields.many2one('product.uom', 'UOM'),
        'rate': fields.float('Rate', digits_compute= dp.get_precision('Account'), help="Rate for the product which is related to Purchase order"),
        'receipt_value' : fields.float('Value', required=True),
        'last_receipt_date': fields.function(last_receipt_cal, string='Last Receipt Date',type="date",multi="receipt", readonly=True),
        'last_issue_date': fields.function(last_receipt_cal,string='Last Issue Date', type="date", multi="receipt",readonly=True),
        'not_moved_months': fields.function(last_receipt_cal, string='Not Moved Months',type="integer", multi="receipt",readonly=True)
    }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_last_receipt_stock_move')
        cr.execute("""
            CREATE OR REPLACE view report_last_receipt_stock_move AS (
                                SELECT
                        min(sm_id) as id,
                        al.curr_year as year,
                        al.curr_month as month,
                        al.curr_day as day,
                        al.company_id as company_id,
                        al.product_qty,
                        al.partner_id as partner_id,
                        al.product_id as product_id,
                        al.state as state ,
                        al.rate as rate,
                        al.date as date,
                        al.product_uom as product_uom,
                        al.categ_id as categ_id,
                        coalesce(al.type, 'other') as type,
                        sum(al.in_value - al.out_value) as value,
                        al.receipt_value as receipt_value
                    FROM (SELECT
                        CASE WHEN sp.type in ('out') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor)
                            ELSE 0.0
                            END AS out_qty,
                        CASE WHEN sp.type in ('in') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor)
                            ELSE 0.0
                            END AS in_qty,
                        CASE WHEN sp.type in ('receipt') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor)
                            ELSE 0.0
                            END AS receipt_qty,
                        CASE WHEN sp.type in ('out') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor) * pt.standard_price
                            ELSE 0.0
                            END AS out_value,
                        CASE WHEN sp.type in ('in') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor) * pt.standard_price
                            ELSE 0.0
                            END AS in_value,
                        CASE WHEN sp.type in ('receipt') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor) * sm.rate
                            ELSE 0.0
                            END AS receipt_value,
                        min(sm.id) as sm_id,
                        sm.date as dp,
                        sm.rate as rate,
                        to_char(date_trunc('day',sm.date), 'YYYY') as curr_year,
                        to_char(date_trunc('day',sm.date), 'MM') as curr_month,
                        to_char(date_trunc('day',sm.date), 'YYYY-MM-DD') as curr_day,
                        sum(sm.product_qty) as product_qty,
                        pt.categ_id as categ_id ,
                        sm.supplier_id as partner_id,
                        sm.product_id as product_id,
                            sm.company_id as company_id,
                            sm.state as state,
                            sm.product_uom as product_uom,
                            sp.type as type,
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
                    where sm.type in ('internal','receipt') and sm.state = 'done'
                    GROUP BY
                        sm.id,sp.type, sm.date,sm.supplier_id,
                        sm.product_id,sm.state,sm.product_uom,sm.date_expected,
                        sm.product_id,pt.standard_price, sm.picking_id, sm.product_qty,
                        sm.company_id,pu.factor,pt.categ_id,sm.rate)
                    AS al
                    GROUP BY
                        al.out_qty,al.in_qty,al.curr_year,al.curr_month,al.curr_day,al.categ_id,
                        al.partner_id,al.product_id,al.state,al.product_uom,
                        al.company_id,al.type,al.product_qty,al.receipt_value,al.rate,al.date)
        """)
    
