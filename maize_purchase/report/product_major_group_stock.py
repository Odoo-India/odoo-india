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

class report_product_major_inventory(osv.osv):
    _name = "report.product.major.inventory"
    _description = "Major Analysis"
    _auto = False
    _columns = {
        'major_name': fields.char('Major Group', size=50),
        'categ_name': fields.char('Category', size=50),
        'year_opening_balance': fields.float('Year_Opening_balance', readonly=True),
        'month_opening_balance': fields.float('Month_Opening_balance', readonly=True),
        'receipt': fields.float('Receipt', readonly=True),
        'consumption': fields.float('Consumption', readonly=True),
        'closing_balance': fields.float('Closing_balance', readonly=True),
        'variance': fields.float('Variance', readonly=True),
        'state': fields.selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('confirmed', 'Confirmed'), ('assigned', 'Available'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True,
              help='When the stock move is created it is in the \'Draft\' state.\n After that it is set to \'Confirmed\' state.\n If stock is available state is set to \'Avaiable\'.\n When the picking it done the state is \'Done\'.\
              \nThe state is \'Waiting\' if the move is waiting for another one.'),
    }
    
    _order = 'major_name'
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_product_major_inventory')
        cr.execute("""
CREATE OR REPLACE view report_product_major_inventory AS (
    (select min(mo.product_id) as id, pm.name as major_name,c.name as categ_name,mo.state as state,
p.cy_opening_value as year_opening_balance,
p.cy_opening_value + sum((case when mo.type like 'receipt' and mo.date < date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * po.price_unit else 0 end) - (case when mo.type like 'internal' and mo.date < date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * po.price_unit else 0 end)) as month_opening_balance,
sum(case when mo.type like 'receipt' and mo.date <= date_trunc('day', CURRENT_DATE) and mo.date >= date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * po.price_unit else 0.0 end )as receipt,
sum(case when mo.type like 'internal' and mo.date <= date_trunc('day', CURRENT_DATE) and mo.date >= date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * t.standard_price else 0.0 end ) as consumption,
p.cy_opening_value + sum( (case when mo.type like 'receipt' and mo.date < date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * po.price_unit else 0 end) - (case when mo.type like 'internal' and mo.date < date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * po.price_unit else 0 end) + (case when mo.type like 'receipt' and mo.date <= date_trunc('day', CURRENT_DATE) and mo.date >= date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * po.price_unit else 0.0 end ) - (case when mo.type like 'internal' and mo.date <= date_trunc('day', CURRENT_DATE) and mo.date >= date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * t.standard_price else 0.0 end )) as closing_balance,
p.cy_opening_value + sum((case when mo.type like 'receipt' and mo.date < date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * po.price_unit else 0 end) - (case when mo.type like 'internal' and mo.date < date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * po.price_unit else 0 end) + (case when mo.type like 'receipt' and mo.date <= date_trunc('day', CURRENT_DATE) and mo.date >= date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * po.price_unit else 0.0 end ) - (case when mo.type like 'internal' and mo.date <= date_trunc('day', CURRENT_DATE) and mo.date >= date_trunc('month', CURRENT_DATE) and mo.product_id = p.id then mo.product_qty * t.standard_price else 0.0 end )) - p.cy_opening_value as variance
from  product_major_group pm 
 LEFT JOIN product_product p on (p.major_group_id = pm.id )
 LEFT JOIN product_template t ON (p.product_tmpl_id=t.id)
 LEFT JOIN product_category c ON (t.categ_id = c.id)
 LEFT JOIN stock_move mo ON (p.id= mo.product_id)
 LEFT JOIN purchase_order_line po ON (mo.purchase_line_id = po.id)
 where mo.product_id in (SELECT
        min(pt.id) as id
    FROM
        product_major_group m
        LEFT JOIN product_product pp ON (m.id=pp.major_group_id)
        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
        LEFT JOIN product_category pc ON (pt.categ_id = pc.id)
    WHERE m.name is not NULL and pc.name is not NULL
    GROUP BY
        pt.id) and mo.state = 'done' and mo.type  in ('receipt','internal') group by pm.name, c.name, mo.state, p.cy_opening_value
) );
        """)
report_product_major_inventory()