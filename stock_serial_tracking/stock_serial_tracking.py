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

import time

from openerp.osv import fields, osv

class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'
    
    def _get_transections(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            if line.prodlot_id:
                result[line.prodlot_id.id] = True
        return result.keys()
    
    def _get_current_location(self, cr, uid, ids, name, args, context=None):
        res = dict([(id, {'current_location_id':False}) for id in ids])
        move_pool= self.pool.get('stock.move')

        for serial_id in ids:
            date = time.strftime('%Y-%m-%d %H:%M:%S')
            
            move_ids = move_pool.search(cr, uid, [('prodlot_id','=',serial_id), ('date','<=',date), ('state','=','done')], order='date desc')
            
            if move_ids:
                location_dest_id = move_pool.browse(cr, uid, move_ids[0]).location_dest_id.id
                res[serial_id] = location_dest_id
            else:
                res[serial_id] = False 
                
        return res
    
    _columns = {
        'current_location_id': fields.function(_get_current_location, type="many2one", relation="stock.location", string='Current Location',
             store={
                'stock.move':  (_get_transections, ['state'], 10)
            }
        ),
    }
stock_production_lot()