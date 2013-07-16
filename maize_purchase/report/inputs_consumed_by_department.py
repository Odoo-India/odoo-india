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
                    
                    excise_calc = self.browse(cr, uid, id, context=context).excise
                    claimed_excise = excise_calc * (excise_percent/100)
                    res[id]['claimed_excise'] = claimed_excise
                    res[id]['un_claimed_excise'] = excise_calc - claimed_excise
                    
                    cess_calc = self.browse(cr, uid, id, context=context).cess
                    claimed_cess = cess_calc * (excise_percent/100)
                    res[id]['claimed_cess'] = claimed_cess
                    res[id]['un_claimed_cess'] = cess_calc - claimed_cess
                    
                    higher_education_cess_calc = self.browse(cr, uid, id, context=context).higher_education_cess
                    claimed_higher_education_cess = higher_education_cess_calc * (excise_percent/100)
                    res[id]['claimed_higher_education_cess'] = claimed_higher_education_cess
                    res[id]['un_claimed_higher_education_cess'] = higher_education_cess_calc - claimed_higher_education_cess
                    
                    import_duty_calc = self.browse(cr, uid, id, context=context).import_duty
                    claimed_import_duty = import_duty_calc * (excise_percent/100)
                    res[id]['claimed_import_duty'] = claimed_import_duty
                    res[id]['un_claimed_import_duty'] = import_duty_calc - claimed_import_duty
                    
            return res
    
    _columns = {
        'date': fields.date('Inward Date'),
        'product_id': fields.many2one('product.product', 'Description of Goods'),
        'department_id': fields.many2one('stock.location', 'Department'),
        'product_uos_qty': fields.float('Total Quantity Consumed'),
        'excisable_value': fields.function(calc_excise, string='For Excisable Goods', type='float', multi='sums'),
        'non_excisable_value': fields.function(calc_excise, string='For Non Excisable Goods', type='float', multi='sums'),
        'excise': fields.float('Total Excise'),
        'cess': fields.float('Cess'),
        'higher_education_cess': fields.float('Higher Education Cess'),
        'import_duty': fields.float('Import Duty'),
        'claimed_excise': fields.function(calc_excise, string='Claimed Excise', type='float', multi='sums'),
        'claimed_cess': fields.function(calc_excise, string='Claimed Cess', type='float', multi='sums'),
        'claimed_higher_education_cess': fields.function(calc_excise, string='Claimed Higher Education Cess', type='float', multi='sums'),
        'claimed_import_duty': fields.function(calc_excise, string='Claimed Import Duty', type='float', multi='sums'),
        'un_claimed_excise': fields.function(calc_excise, string='Unclaimed Excise', type='float', multi='sums'),
        'un_claimed_cess': fields.function(calc_excise, string='Unclaimed Cess', type='float', multi='sums'),
        'un_claimed_higher_education_cess': fields.function(calc_excise, string='Unclaimed Higher Education Cess', type='float', multi='sums'),
        'un_claimed_import_duty': fields.function(calc_excise, string='Unclaimed Import Duty', type='float', multi='sums'),
    }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'inputs_consumed_by_department_report')
        cr.execute("""
            create or replace view inputs_consumed_by_department_report as (
                select sm.date as date, 
                       sm.id, 
                       sm.department_id as department_id, 
                       sm.product_id as product_id, 
                       sm.product_uos_qty as product_uos_qty,
                       sm.product_uos_qty as excisable_value,
                       sm.product_uos_qty as non_excisable_value,
                       sm.excies as excise,
                       sm.c_cess as cess,
                       sm.c_high_cess as higher_education_cess,
                       sm.import_duty1 as import_duty,
                       sm.excies as claimed_excise,
                       sm.excies as un_claimed_excise,
                       sm.c_cess as claimed_cess,
                       sm.c_high_cess as claimed_higher_education_cess,
                       sm.import_duty1 as claimed_import_duty
                from stock_move sm 
                where sm.type = 'receipt' and sm.state = 'done'
            )
        """)
        
inputs_consumed_by_department_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: