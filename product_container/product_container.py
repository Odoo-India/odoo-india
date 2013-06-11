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

class product_product(osv.Model):
    _inherit = 'product.product'

    _columns = {
        'return_container': fields.boolean('Return Container'),
        'product_container_id': fields.many2one('product.product', 'Container'),
    }

product_product()

class stock_picking_in(osv.Model):
    _inherit = 'stock.picking.in'

    def action_process(self, cr, uid, ids, context=None):
        prodlot_obj = self.pool.get('stock.production.lot')
        move_obj = self.pool.get('stock.move')
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.type == 'in':
                for move in picking.move_lines:
                    if not move.manage_container and move.prodlot_id and move.product_id and move.product_id.return_container and move.product_id.product_container_id:
                        move_obj.write(cr, uid, [move.id], {'manage_container': True}, context=context)
                        default = dict(product_id = move.product_id.product_container_id.id)
                        new_prodlot = prodlot_obj.copy(cr, uid, move.prodlot_id.id, default, context=context)
                        default = dict(product_id = move.product_id.product_container_id.id, product_uom = move.product_id.product_container_id.uom_id.id, product_qty = 1, prodlot_id = new_prodlot, state = 'assigned')
                        move_obj.copy(cr, uid, move.id, default, context=context)
        return super(stock_picking_in, self).action_process(cr, uid, ids, context=context)

stock_picking_in()

class stock_move(osv.Model):
    _inherit = 'stock.move'

    _columns = {
        'manage_container': fields.boolean('Manage Container'),
    }

    _defaults = {
        'manage_container': False,
    }

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
