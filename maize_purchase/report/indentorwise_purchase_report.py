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

class indentor_purchase_report(osv.osv):
    _name = "indentor.purchase.report"
    _description = "Indentor Purchase Statistics"
    _auto = False

    def series_purchase(self, cr, uid, ids, field_name, arg, context=None):
        ids =  list(set(ids)) 
        res = {}
        line_obj = self.pool.get('purchase.order.line')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'store': 0.0,
                'repair': 0.0,
                'misc': 0.0,
                'min_max': 0.0,
                'fil_cloth':0.0,
                'oil_gre':0.0,
                'lab':0.0,
                'total_amount':0.0
            }

        for order in self.browse(cr, uid, ids, context=context):
            search_id = line_obj.search(cr, uid,[('indentor_id','=',order.indentor_id.id)],context=context)
            st_amount = 0.0
            mm_amount = 0.0
            og_amount = 0.0
            lb_amount = 0.0
            rp_amount = 0.0
            ms_amount = 0.0
            fc_amount = 0.0
            total_amount = 0.0
            for line in line_obj.browse(cr, uid, search_id, context=context):
                if line.po_series_id.id:
                    if line.po_series_id.code == 'ST':
                        st_amount += line.amount_total
                    if line.po_series_id.code == 'MM':
                        mm_amount += line.amount_total
                    if line.po_series_id.code == 'OG':
                        og_amount += line.amount_total
                    if line.po_series_id.code == 'LB':
                        lb_amount += line.amount_total
                    if line.po_series_id.code == 'FC':
                        fc_amount += line.amount_total
                    if line.po_series_id.code == 'MS':
                        ms_amount += line.amount_total
                    if line.po_series_id.code == 'RP':
                        rp_amount += line.amount_total
            total_amount = st_amount + mm_amount + og_amount + lb_amount + ms_amount + rp_amount + fc_amount        
            res[order.id]['store'] = st_amount
            res[order.id]['min_max'] = mm_amount
            res[order.id]['oil_gre'] = og_amount
            res[order.id]['lab'] = lb_amount
            res[order.id]['misc'] = ms_amount
            res[order.id]['repair'] = rp_amount
            res[order.id]['fil_cloth'] = fc_amount
            res[order.id]['total_amount'] = total_amount
        return res

    _columns = {
        'date': fields.date('Date of Indent', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'name': fields.char('NAME', size=64, readonly=True),
        'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
        'purchase_id': fields.many2one('purchase.order', 'PO Number', readonly=True),
        'indentor_id': fields.many2one('res.users', 'Indentor', readonly=True),
        'nbr': fields.integer('# of Lines', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'po_series' : fields.many2one('product.order.series', 'Series'),
        'line_id' : fields.many2one('purchase.order.line', 'Lines'),
        'po_series_id': fields.char('PO Series',size=64,readonly=True),
        'state':fields.selection([
            ('draft','Draft'),
            ('confirm','Confirm'),
            ('waiting_approval','Waiting For Approval'),
            ('inprogress','Inprogress'),
            ('received','Received'),
            ('reject','Rejected')
            ], 'State', readonly=True),
        'purchase_total': fields.float('Total', readonly=True),
        'store': fields.function(series_purchase, digits_compute= dp.get_precision('Account'), string='STORE', type="float", multi="series",help="STORE"),
        'repair': fields.function(series_purchase, digits_compute= dp.get_precision('Account'), string='REPAIR', type="float", multi="series",help="REPAIR"),
        'misc': fields.function(series_purchase, digits_compute= dp.get_precision('Account'), string='MISC', type="float", multi="series",help="MISC"),
        'min_max': fields.function(series_purchase, digits_compute= dp.get_precision('Account'), string='MIN/MAX', type="float", multi="series",help="MIN/MAX"),
        'fil_cloth': fields.function(series_purchase, digits_compute= dp.get_precision('Account'), string='FIL_CLOTH', type="float", multi="series",help="FIL_CLOTH"),
        'lab': fields.function(series_purchase, digits_compute= dp.get_precision('Account'), string='LAB', type="float", multi="series",help="LAB"),
        'oil_gre': fields.function(series_purchase, digits_compute= dp.get_precision('Account'), string='OIL/GREASE', type="float", multi="series",help="OIL/GREASE"),
        'total_amount': fields.function(series_purchase, digits_compute= dp.get_precision('Account'), string='Total', type="float", multi="series",help="TOTAL AMOUNT"),
        'purchase_limit': fields.float('PURCHASE LIMIT', readonly=True),
        'group_desc': fields.char('GROUP DISC',size=64,readonly=True),

    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'indentor_purchase_report')
        cr.execute("""
            create or replace view indentor_purchase_report as(
 select
                    min(emp.resource_id) as id,
                    r.name as name, 
                    ps.id as po_series_id,
        		    emp.purchase_limit as purchase_limit,
		            emp.group_desc as group_desc,
		            l.date_planned as date_planned,
                    l.product_id as product_id,
                    l.id as line_id,
                    po.id as purchase_id,
                    l.amount_total as purchase_total,
                    l.indentor_id as indentor_id,
                    i.indent_date as date,
                    to_char(i.indent_date, 'YYYY') as year,
                    to_char(i.indent_date, 'MM') as month,
                    to_char(i.indent_date, 'YYYY-MM-DD') as day,
                    1 as nbr,
                    i.state as state,
                    po.po_series_id as po_series
                from
		            hr_employee as emp
                    left join resource_resource r on (r.id = emp.resource_id)
                    left join res_users u on (u.id = r.user_id)
                    left join purchase_order_line l on (u.id=l.indentor_id)
                    left join product_product p on (l.product_id=p.id)
                    left join purchase_order po on (l.order_id=po.id)
                    left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_order_series ps on (po.po_series_id = ps.id)
                    left join indent_indent i on (i.indentor_id = u.id)
                where l.indentor_id is not null
            group by
                emp.id,
		        l.date_planned,
		        l.indentor_id,
		        l.product_id,
		        l.amount_total,
		        emp.purchase_limit,
		        emp.group_desc,
		        ps.id,
		        po.id,
		        i.state,
		        l.id,
		        r.name,
		        i.indent_date,
                po.payment_term_id


            )

        """)
indentor_purchase_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
