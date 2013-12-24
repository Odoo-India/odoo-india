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

class stock_gatepass(osv.Model):
    _inherit = 'stock.gatepass'
    
    def onchange_delivery_order(self, cr, uid, ids, order_id=False, *args, **kw):
        result = {'line_ids': []}
        lines = []
 
        if not order_id:
            return {'value': result}
        
        order = self.pool.get('stock.picking.out').browse(cr, uid, order_id)
        products = order.move_lines
        
        for product in products:
            vals = dict(
                product_id = product.product_id.id, 
                product_qty = product.product_qty, 
                uom_id= product.product_uom.id, 
                name = product.product_id.name, 
                location_id = product.location_id.id,
                location_dest_id = product.location_dest_id.id,
                prodlot_id=product.prodlot_id.id
            )
            
            #TODO: need to check in other ways whether sale module is installed or not instead of try and except..
            try:
                if product.sale_line_id:
                    vals['price_unit'] = product.sale_line_id.price_unit
            except:
                vals['price_unit'] = product.product_id.list_price
            lines.append(vals)
        result['line_ids'] = lines
        result['partner_id'] = order.partner_id.id
        return {'value': result}
    
    def create_incoming_shipment(self, cr, uid, gatepass, context=None):
        picking_in_obj = self.pool.get('stock.picking.in')
        move_obj = self.pool.get('stock.move')

        vals = {
            'partner_id': gatepass.partner_id.id,
            'gate_pass_id': gatepass.id,
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'origin': gatepass.name,
            'type': 'in',
        }
        in_picking_id = picking_in_obj.create(cr, uid, vals, context=context)
        
        supplier_location = self.pool.get('ir.model.data').get_object(cr, uid, 'stock', 'stock_location_suppliers')
        
        package_serial_entry = {}
        
        for line in gatepass.line_ids:
            result = None
            if line.product_id.container_id:
                result = dict(name=line.product_id.container_id.name, 
                    product_id=line.product_id.container_id.id, 
                    product_qty=1, 
                    product_uom=line.product_id.container_id.uom_id.id, 
                    location_id=supplier_location.id, 
                    location_dest_id=line.location_id.id,
                    picking_id=in_picking_id,
                    prodlot_id = line.prodlot_id.container_serial_id.id,
                    origin=gatepass.name
                )
            elif line.prodlot_id.container_serial_id:
                if not package_serial_entry.get(line.prodlot_id.container_serial_id.name, False):
                    result = dict(name=line.prodlot_id.container_serial_id.product_id.name, 
                        product_id=line.prodlot_id.container_serial_id.product_id.id, 
                        product_qty=1,
                        product_uom=line.prodlot_id.container_serial_id.product_id.uom_id.id, 
                        location_id=supplier_location.id, 
                        location_dest_id=line.location_id.id,
                        picking_id=in_picking_id,
                        prodlot_id = line.prodlot_id.container_serial_id.id,
                        origin=gatepass.name
                    )
                    package_serial_entry[line.prodlot_id.container_serial_id.name] = True
                else:
                    continue
            elif gatepass.type_id.approval_required == True:
                result = dict(name=line.product_id.name, 
                    product_id=line.product_id.id, 
                    product_qty=line.product_qty, 
                    product_uom=line.uom_id.id, 
                    location_id=supplier_location.id, 
                    location_dest_id=line.location_id.id,
                    picking_id=in_picking_id,
                    prodlot_id = line.prodlot_id.id,
                    origin=gatepass.name
                )
            
            if result:
                move_obj.create(cr, uid, result, context=context)
        
        return in_picking_id

    _sql_constraints = [
        ('gatepass_delivery_uniq', 'unique(out_picking_id)', 'You can not create multiple Gatepass for same Delivery Order!'),
    ]

stock_gatepass()

class stock_picking(osv.Model):
    _inherit = "stock.picking"
    
    _columns = {
        'prodlot_id': fields.related('move_lines', 'prodlot_id', type='many2one', relation='stock.production.lot', string='Serial #')
    }
stock_picking()

class stock_picking_in(osv.Model):
    _inherit = "stock.picking.in"
    
    _columns = {
        'prodlot_id': fields.related('move_lines', 'prodlot_id', type='many2one', relation='stock.production.lot', string='Serial #')
    }
stock_picking_in()