# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
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
from lxml import etree
from openerp.osv import fields, osv
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class stock_partial_picking(osv.osv_memory):
    _name = "stock.partial.picking"
    _inherit = "stock.partial.picking"
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = {}
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not picking_ids or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('stock.picking', 'stock.picking.in', 'stock.picking.out','stock.picking.receipt'), 'Bad context propagation'
        picking_id, = picking_ids
        if 'picking_id' in fields:
            res.update(picking_id=picking_id)
        if 'move_ids' in fields:
            picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
            moves = [self._partial_move_for(cr, uid, m) for m in picking.move_lines if m.state not in ('done','cancel')]
            res.update(move_ids=moves)
        if 'date' in fields:
            res.update(date=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
        return res
    
    def _partial_move_for(self, cr, uid, move):
        partial_move = {
            'product_id' : move.product_id.id,
            'quantity' : move.product_qty if move.state == 'assigned' and move.type == 'out' else move.challan_qty,
            'product_uom' : move.product_uom.id,
            'prodlot_id' : move.prodlot_id.id,
            'move_id' : move.id,
            'location_id' : move.location_id.id,
            'location_dest_id' : move.location_dest_id.id,
        }
        if move.picking_id.type == 'in' and move.product_id.cost_method == 'average':
            partial_move.update(update_cost=True, **self._product_cost_for_average_update(cr, uid, move))
        return partial_move

class split_in_production_lot(osv.osv_memory):
    _name = "stock.move.split"
    _inherit = "stock.move.split"

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(split_in_production_lot, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            move = self.pool.get('stock.move').browse(cr, uid, context['active_id'], context=context)
            if 'challan_qty' in fields and context.get('picking_type') not in ['out']:
                res.update({'challan_qty': move.challan_qty})
            else:
                res.update({'challan_qty': move.product_qty})
        return res

    _columns = {
        'challan_qty': fields.float('Challan Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
    }

    def split_lot(self, cr, uid, ids, context=None):
        """ To split a lot"""
        if context is None:
            context = {}
        res = self.split(cr, uid, ids, context.get('active_ids'), context=context)
        return {'type': 'ir.actions.act_window_close'}

    def split(self, cr, uid, ids, move_ids, context=None):
        """ To split stock moves into serial numbers

        :param move_ids: the ID or list of IDs of stock move we want to split
        """
        if context is None:
            context = {}
        assert context.get('active_model') == 'stock.move',\
             'Incorrect use of the stock move split wizard'
        inventory_id = context.get('inventory_id', False)
        prodlot_obj = self.pool.get('stock.production.lot')
        inventory_obj = self.pool.get('stock.inventory')
        move_obj = self.pool.get('stock.move')
        new_move = []
        for data in self.browse(cr, uid, ids, context=context):
            for move in move_obj.browse(cr, uid, move_ids, context=context):
                move_qty = move.product_qty
                quantity_rest = move.product_qty
                challan_qty = move.challan_qty
                uos_qty_rest = move.product_uos_qty
                new_move = []
                if data.use_exist:
                    lines = [l for l in data.line_exist_ids if l]
                else:
                    lines = [l for l in data.line_ids if l]
                total_move_qty = 0.0
                for line in lines:
                    total_move_qty += line.quantity
                for line in lines:
                    quantity = line.quantity
                    if total_move_qty > challan_qty or total_move_qty < challan_qty:
                        raise osv.except_osv(_('Processing Error!'), _('Serial number quantity %d of %s is not exact challan quantity (%d)!') \
                                % (total_move_qty, move.product_id.name, challan_qty))
                    if quantity <= 0 or move_qty == 0:
                        continue
                    quantity_rest -= quantity
                    uos_qty = quantity / move_qty * move.product_uos_qty
                    uos_qty_rest = quantity_rest / move_qty * move.product_uos_qty
                    if quantity_rest < 0:
                        quantity_rest = quantity
                        self.pool.get('stock.move').log(cr, uid, move.id, _('Unable to assign all lots to this move!'))
                        return False
                    default_val = {
                        'product_qty': quantity,
                        'product_uos_qty': uos_qty,
                        'state': move.state,
                        'challan_qty': quantity
                    }
                    if quantity_rest > 0:
                        current_move = move_obj.copy(cr, uid, move.id, default_val, context=context)
                        if inventory_id and current_move:
                            inventory_obj.write(cr, uid, inventory_id, {'move_ids': [(4, current_move)]}, context=context)
                        new_move.append(current_move)

                    if quantity_rest == 0:
                        current_move = move.id
                    prodlot_id = False
                    if data.use_exist:
                        prodlot_id = line.prodlot_id.id
                    if not prodlot_id:
                        prodlot_id = prodlot_obj.create(cr, uid, {
                            'name': line.name,
                            'product_id': move.product_id.id},
                        context=context)

                    move_obj.write(cr, uid, [current_move], {'prodlot_id': prodlot_id, 'state':move.state})

                    update_val = {}
                    if quantity_rest > 0:
                        update_val['product_qty'] = quantity_rest
                        update_val['product_uos_qty'] = uos_qty_rest
                        update_val['state'] = move.state
                        update_val['challan_qty'] = quantity_rest
                        move_obj.write(cr, uid, [move.id], update_val)

        return new_move

split_in_production_lot()
