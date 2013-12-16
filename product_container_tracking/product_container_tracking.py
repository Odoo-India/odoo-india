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
from openerp.tools.translate import _

class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'
    
    _columns = {
        'container_serial_id':fields.many2one('stock.production.lot', 'Container Serial', readonly=True)
    }
stock_production_lot()

class stock_picking(osv.Model):
    _inherit = "stock.picking"
    _table = "stock_picking"
    _order = "name desc"
    
    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        move_pool = self.pool.get('stock.move')
        warehouse_pool = self.pool.get('stock.warehouse')
        serial_pool = self.pool.get('stock.production.lot')
        
        res = super(stock_picking, self).do_partial(cr, uid, ids, partial_datas, context=context)
        
        package_serial_entry = {}
        
        for picking_id in res:
            picking = self.browse(cr, uid, picking_id)
            for move in picking.move_lines:
                
                if move.product_id.container_id and move.product_id.container_id.track_outgoing and not move.prodlot_id:
                    raise osv.except_osv(_('Warning!'),_('You cannot confirm shipping for %s with container %s, without serial number' % (move.name, move.product_id.container_id.name)))
                
                if move.product_packaging and not move.product_packaging.ul.container_id:
                    raise osv.except_osv(_('Warning!'),_('Please define container product on package %s' % (move.product_packaging.ul.name)))
                
                if move.product_packaging and (not move.prodlot_id or not move.tracking_id):
                    raise osv.except_osv(_('Warning!'),_('You cannot confirm an shipping %s with container %s, without serial number' % (move.name, move.product_packaging.ul.container_id.id)))
                
                if move.product_id.container_id and move.prodlot_id:
                    serial_id = False
                    if not move.prodlot_id.container_serial_id:
                        serial_ids = serial_pool.search(cr, uid, [('product_id','=',move.product_id.container_id.id), ('name','=',move.prodlot_id.name)])
                        if serial_ids:
                            serial_id = serial_ids[0]
                        else:
                            res = {
                                'name':move.prodlot_id.name,
                                'product_id':move.product_id.container_id.id,
                                'date':time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                            serial_id = serial_pool.create(cr, uid, res)
                        serial_pool.write(cr, uid, [move.prodlot_id.id], {'container_serial_id':serial_id})
                    else:
                        serial_id = move.prodlot_id.container_serial_id.id
                    
                    res = {
                        'product_id':move.product_id.container_id.id,
                        'product_qty':1,
                        'product_uom':move.product_id.container_id.uom_id.id,
                        'name':move.name,
                        'origin':picking.name,
                        'type':'internal',
                        'location_id':move.location_id.id,
                        'location_dest_id':move.location_dest_id.id,
                        'partner_id':move.partner_id.id,
                        'date':move.date,
                        'prodlot_id':serial_id,
                        'state':'done'
                    }
                    move_pool.create(cr, uid, res)
                elif not move.product_id.container_id and move.prodlot_id and move.tracking_id and move.product_packaging:
                    serial_id = False
                    if not move.prodlot_id.container_serial_id:
                        serial_ids = serial_pool.search(cr, uid, [('product_id','=',move.product_packaging.ul.container_id.id), ('name','=',move.tracking_id.name)])
                        if serial_ids:
                            serial_id = serial_ids[0]
                        else:
                            res = {
                                'name':move.tracking_id.name,
                                'product_id':move.product_packaging.ul.container_id.id,
                                'date':time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                            serial_id = serial_pool.create(cr, uid, res)
                        serial_pool.write(cr, uid, [move.prodlot_id.id], {'container_serial_id':serial_id})
                    else:
                        serial_id = move.prodlot_id.container_serial_id.id
                    
                    if not package_serial_entry.get(serial_id):
                        res = {
                            'product_id':move.product_packaging.ul.container_id.id,
                            'product_qty':1,
                            'product_uom':move.product_packaging.ul.container_id.uom_id.id,
                            'name':move.name,
                            'origin':picking.name,
                            'type':'internal',
                            'location_id':move.location_id.id,
                            'location_dest_id':move.location_dest_id.id,
                            'partner_id':move.partner_id.id,
                            'date':move.date,
                            'prodlot_id':serial_id,
                            'state':'done'
                        }
                        package_serial_entry[serial_id] = move_pool.create(cr, uid, res)
        return res
    
stock_picking()