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

class indent_purchase_report(osv.osv):
    _name = "indent.purchase.report"
    _description = "Indent Purchase Statistics"
    _auto = False

    _columns = {
        'purchase_maize_id': fields.char('Maize Purchase', size=256, readonly=True),
        'name': fields.char('Indent #', size=256, readonly=True),
        'date': fields.date('Indent Date', readonly=True),
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
        'purchase_id': fields.many2one('purchase.order', 'Purchase Order', readonly=True),
        'indent_id': fields.many2one('indent.indent', 'Indent', readonly=True),
        'indentor_id': fields.many2one('res.users', 'Indentor', readonly=True),
        'price_total': fields.float('Total Price', readonly=True),
        'nbr': fields.integer('# of Lines', readonly=True),
        'state':fields.selection([
            ('draft','Draft'),
            ('confirm','Confirm'),
            ('waiting_approval','Waiting For Approval'),
            ('inprogress','Inprogress'),
            ('received','Received'),
            ('reject','Rejected')
            ], 'State', readonly=True),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Project', readonly=True),
    }
    _order = 'date desc'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'indent_purchase_report')
        cr.execute("""
            create or replace view indent_purchase_report as (
                select
                    min(po.id) as id,
                    i.id as indent_id,
                    i.maize as name,
                    i.contract as contract,
                    i.department_id as department_id,
                    po.id as purchase_id,
                    po.maize as purchase_maize_id,
                    i.requirement as requirement,
                    i.type as type,
                    i.item_for as item_for,
                    1 as nbr,
                    i.indent_date as date,
                    to_char(i.indent_date, 'YYYY') as year,
                    to_char(i.indent_date, 'MM') as month,
                    to_char(i.indent_date, 'YYYY-MM-DD') as day,
                    i.indentor_id as indentor_id,
                    i.state,
                    i.analytic_account_id as analytic_account_id
                from
                    indent_indent i
                    left join purchase_order po on (i.id=po.indent_id)
                    left join stock_location sl on (sl.id=i.department_id)
                where po.indent_id is not null
                group by
                    po.id,
                    i.id,
                    i.name,
                    i.contract,
                    po.name,
                    i.department_id,
                    i.requirement,
                    i.type,
                    i.item_for,
                    i.indent_date,
                    i.indentor_id,
                    i.state,
                    i.analytic_account_id,
                    po.maize
            )
        """)
indent_purchase_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
