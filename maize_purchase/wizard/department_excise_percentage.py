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

from openerp.osv import fields, osv

class department_excise_percentage(osv.osv_memory):
    
    _name = 'department.excise.percentage'
    
    _columns = {
            'department_id': fields.many2one('stock.location', 'Department', required=True),
            'excise_percentage': fields.float('Excise Percentage', help="% for Excisable Goods", required=True)
        }
    
    def get_data(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        browse_rec = self.browse(cr, uid, ids[0], context=context)
        department_id = browse_rec.department_id.id
        excise_percentage = browse_rec.excise_percentage
        action_model, action_id = tuple(mod_obj.get_object_reference(cr, uid, 'maize_purchase', 'action_inputs_consumed_by_department_report'))
        action = self.pool.get(action_model).read(cr, uid, action_id, context=context)
        domain = [
                  ('department_id', '=', department_id),
                 ]
        action['domain'] = domain
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
