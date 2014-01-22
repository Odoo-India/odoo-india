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

from openerp.osv import osv,fields
import openerp.addons.decimal_precision as dp

class stock_move(osv.osv):
    """
    This field used only for hide Serial split wizard after all moves goes into the work-order
    """
    _inherit = 'stock.move'

    def _return_history(self, cr, uid, ids, field_name, arg, context=None):
        """ Gets returns qty of picking
        """
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]
        return_history = {}.fromkeys(ids, 0.0)
        for m in self.browse(cr, uid, ids):
            if m.state == 'done':
                return_history[m.id] = 0
                for rec in m.move_history_ids2:
                    # only take into account 'product return' moves, ignoring any other
                    # kind of upstream moves, such as internal procurements, etc.
                    # a valid return move will be the exact opposite of ours:
                    #     (src location, dest location) <=> (dest location, src location))
                    if rec.location_dest_id.id == m.location_id.id \
                        and rec.location_id.id == m.location_dest_id.id:
                        return_history[m.id] += (rec.product_qty * rec.product_uom.factor)
                #TODO:bettter to move in funct_inv
                if return_history[m.id] + m.qc_ok_qty == m.product_qty:
                    m.write({'qc_completed': True})
        return return_history

    def get_return_history(self, cr, uid, pick_id, context=None):
        """
            get return history
        """
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, pick_id, context=context)
        return_history = {}
        for m  in pick.move_lines:
            if m.state == 'done':
                return_history[m.id] = 0
                for rec in m.move_history_ids2:
                    # only take into account 'product return' moves, ignoring any other
                    # kind of upstream moves, such as internal procurements, etc.
                    # a valid return move will be the exact opposite of ours:
                    #     (src location, dest location) <=> (dest location, src location))
                    if rec.location_dest_id.id == m.location_id.id \
                        and rec.location_id.id == m.location_dest_id.id:
                        return_history[m.id] += (rec.product_qty * rec.product_uom.factor)
        return return_history

    #TODO : Better idea to called funct_inv and write to move
#    def _set_qc_completed(self, cr, uid, id, name, value, args, context=None):
#        """ 
#        -process
#            Calculates returned_qty + qc_qty == total qty
#                then
#                    qc_completed field Mark as true
#        """
#        if not value:
#            return False
#        return True

    _columns = {
        'moves_to_workorder': fields.boolean('Raw Material Move To Work-Center?'),
        #This field used for add raw materials dynamicaly on production order
        'extra_consumed': fields.boolean('Extra Consumed ?',help="Extra consumed raw material on production order"),
        'picking_qc_id': fields.many2one('stock.picking','QC Picking'),
        'qc_approved': fields.boolean('QC Approved?'),
        'qc_completed': fields.boolean('QC Completed?'),
        'qc_ok_qty': fields.float('QC Qty ', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'is_qc': fields.boolean('Can be QC?'),
        'returned_qty': fields.function(_return_history, string="Return Qty",digits_compute=dp.get_precision('Product Unit of Measure')),
    }

    def _prepare_chained_picking(self, cr, uid, picking_name, picking, picking_type, moves_todo, context=None):
        """Prepare the definition (values) to create a new chained picking.

           :param str picking_name: desired new picking name
           :param browse_record picking: source picking (being chained to)
           :param str picking_type: desired new picking type
           :param list moves_todo: specification of the stock moves to be later included in this
               picking, in the form::

                   [[move, (dest_location, auto_packing, chained_delay, chained_journal,
                                  chained_company_id, chained_picking_type)],
                    ...
                   ]

               See also :meth:`stock_location.chained_location_get`.
        -Our Process
            - To attach purchase order with in type chain location
        """
        res = super(stock_move, self)._prepare_chained_picking(cr, uid, picking_name, picking, picking_type, moves_todo, context=context)
        if picking_type == 'internal':
            if picking.purchase_id:
                res.update({'purchase_id': picking.purchase_id.id})
        return res

    def action_process_qc2x(self, cr, uid, ids, context=None):
        """
        -Process
            Call wizard for quality control to next "x"(purchase order destination location) location
        """
        context = context or {}
        data = self.browse(cr,uid,ids[0])
        if not (data.picking_id and data.picking_id.purchase_id):
            raise osv.except_osv(_('Warning!'), _('You cannot process this move to transfer another location')) 
        context.update({'product_id':data.product_id.id,'to_qc_qty': data.product_qty - data.qc_ok_qty,'qc_ok_qty':data.qc_ok_qty,'returned_qty': data.returned_qty})
        return {
                'name': 'Transfer Quantity from QC to X location',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'qc2xlocation',
                'type': 'ir.actions.act_window',
                'target':'new',
                'context':context
                }

stock_move()


class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
        'move_lines': fields.one2many('stock.move', 'picking_id', 'Internal Moves', readonly=True, states={'draft': [('readonly', False)]}),
        'service_order': fields.boolean('Service Order'),
        'pass_to_qc': fields.boolean('QC Test?'),
        'workorder_id':  fields.many2one('mrp.production.workcenter.line','Work-Order'),
        'move_lines_qc2store': fields.one2many('stock.move', 'picking_qc_id', 'Store Moves', readonly=True),
        'qc_loc_id': fields.many2one('stock.location', 'QC Location',readonly=True),
        'move_loc_id': fields.many2one('stock.location', 'Destination Location',readonly=True),
    }
stock_picking()

class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    _columns = {
        'service_order': fields.boolean('Service Order'),
        'move_lines': fields.one2many('stock.move', 'picking_id', 'Internal Moves', readonly=True, states={'draft': [('readonly', False)]}),
        'workorder_id':  fields.many2one('mrp.production.workcenter.line','Work-Order')
    }
stock_picking_out()

class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'
    _columns = {
        'pass_to_qc': fields.boolean('QC Test?'),
        'move_lines': fields.one2many('stock.move', 'picking_id', 'Internal Moves', readonly=True, states={'draft': [('readonly', False)]}),
        'move_lines_qc2store': fields.one2many('stock.move', 'picking_qc_id', 'Store Moves', readonly=True),
        'qc_loc_id': fields.many2one('stock.location', 'QC Location',readonly=True),
        'move_loc_id': fields.many2one('stock.location', 'Destination Location',readonly=True),
    }
stock_picking_in()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
