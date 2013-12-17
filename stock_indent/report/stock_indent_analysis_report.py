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

class stock_indent_analysis_report(osv.osv):
    _name = "stock.indent.analysis.report"
    _description = "Indent Analysis Report"
    _auto = False
    
    _columns = {
        'id':fields.integer('ID'),
        'indent_id':fields.many2one('indent.indent', 'Indent'),
        'product_id':fields.many2one('product.product', 'Product'),
        'uom_id':fields.many2one('product.uom', 'Uom'),
        
        'price_unit': fields.float('Unit Price'),
        'product_qty': fields.float('Qty'),
        'total': fields.float('Value'),
        
        'procure_type':fields.selection([('make_to_stock', 'Stock'), ('make_to_order', 'Purchase')], 'Procure'),
        'indentor_id':fields.many2one('res.users', 'Indentor'),
        
        'department_id':fields.many2one('stock.location', 'Department'),
        
        'indent_date':fields.date('Indent Date'),
        'approve_date':fields.date('Approve Date'),
        
        'type': fields.selection([('new', 'Purchase Indent'), ('existing', 'Repairing Indent')], 'Type'),
        'item_for': fields.selection([('store', 'Store'), ('capital', 'Capital')], 'Purchase for'),
        'project_id': fields.many2one('account.analytic.account', 'Project'),
        
        'equipment_id': fields.many2one('indent.equipment', 'Equipment'),
        'section_id': fields.many2one('indent.equipment.section', 'Section'),
        'state':fields.selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('waiting_approval', 'Waiting for Approval'), ('inprogress', 'In Progress'), ('received', 'Received'), ('reject', 'Rejected')], 'State'),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse')
    }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_indent_analysis_report')
        cr.execute("""CREATE OR REPLACE view stock_indent_analysis_report AS (
            select 
                il.id as id,
                il.indent_id as indent_id, 
                il.product_id as product_id, 
                il.product_uom_qty as product_qty,
                il.price_unit as price_unit,
                il.product_uom_qty * il.price_unit as total,
                il.product_uom as uom_id, 
                il.type as procure_type,
                l.indentor_id as indentor_id,
                l.department_id as department_id,
                l.indent_date as indent_date,
                l.approve_date as approve_date,
                l.type as type,
                l.item_for as item_for,
                l.analytic_account_id as project_id,
                l.equipment_id as equipment_id,
                l.equipment_section_id as section_id,
                l.state as state,
                l.warehouse_id as warehouse_id
            from 
                indent_product_lines il
                left join indent_indent l on (il.indent_id=l.id))""")
stock_indent_analysis_report()