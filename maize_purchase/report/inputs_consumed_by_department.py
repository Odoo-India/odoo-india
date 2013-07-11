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

class inputs_consumed_by_department_report(osv.osv):
    _name = 'inputs.consumed.by.department.report'
    _auto = False
    
    
    def calc_excise(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is not None:
            active_id = context.get('active_id', False)
            obj = self.pool.get(context.get('active_model', False))
            if obj:
                for id in ids:
                    res[id] = {
                       'excisable_value': 0.0,
                       'non_excisable_value': 0.0,
                      }
                    excise_percent = obj.browse(cr, uid, active_id, context=context).excise_percentage
                    product_uos_qty = self.browse(cr, uid, id, context=context).product_uos_qty
                    excise = product_uos_qty * (excise_percent/100)
                    res[id]['excisable_value'] = excise
                    res[id]['non_excisable_value'] = product_uos_qty - excise
            return res
    
    _columns = {
        'date': fields.date('Inward Date'),
        'product_id': fields.many2one('product.product', 'Description of Goods'),
        'department_id': fields.many2one('stock.location', 'Department'),
        'product_uos_qty': fields.float('Total Quantity Consumed'),
        'excisable_value': fields.function(calc_excise, string='For Excisable Goods', type='float', multi='sums'),
        'non_excisable_value': fields.function(calc_excise, string='For Non Excisable Goods', type='float', multi='sums'),
    }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'inputs_consumed_by_department_report')
        cr.execute("""
            create or replace view inputs_consumed_by_department_report as (
                select sm.date as date, 
                       sm.id, 
                       i.department_id as department_id, 
                       sm.product_id as product_id, 
                       sm.product_uos_qty as product_uos_qty,
                       sm.product_uos_qty as excisable_value,
                       sm.product_uos_qty as non_excisable_value
                from stock_move sm 
                left join indent_indent i on (sm.indent_id = i.id)
                where sm.type = 'receipt' and sm.state = 'done'
            )
        """)
        
inputs_consumed_by_department_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: