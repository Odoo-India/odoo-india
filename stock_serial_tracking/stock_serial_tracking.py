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
        for serial in self.browse(cr, uid, ids, context={}):
            cid = -1
            location_id = -1
            for move in serial.move_ids:
                if move.id > cid and move.state == 'done':
                    cid = move.id
                    location_id = move.location_dest_id.id
            if location_id == -1:
                res[serial.id] = False
            else:
                res[serial.id] = location_id
        return res
    
    _columns = {
        'current_location_id': fields.function(_get_current_location, type="many2one", relation="stock.location", string='Current Location',
             store={
                'stock.move':  (_get_transections, ['state'], 10)
            }
        ),
    }
stock_production_lot()