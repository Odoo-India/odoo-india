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
import netsvc
import time

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from datetime import datetime
from operator import itemgetter
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp import tools

STATE_SELECTION = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('consumed', 'Consumed'),
        ('finished', 'Finished'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected')
    ]

def rounding(f, r):
    import math
    if not r:
        return f
    return math.ceil(f / r) * r

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _order = "id desc"
    _columns = {
        'workcenter_lines': fields.one2many('mrp.production.workcenter.line', 'production_id', 'Work Centers Utilisation',
            readonly=False, states={'done':[('readonly', True)]}),
        'moves_to_workorder': fields.boolean('Materials Moves To Work-Center?'),
    }

    def open_procurements(self, cr, uid, ids, context=None):
        """
        -Process
            -Open Procurments, which is waiting for what .. ??
            -User easily handles procurments from manufacturing order.
        """
        context = context or {}
        procurment_obj = self.pool.get('procurement.order')
        models_data = self.pool.get('ir.model.data')
        data= self.browse(cr, uid, ids[0])
        procurments_ids = procurment_obj.search(cr, uid, [('origin','ilike',':'+data.name)], context=context)
        # Get opportunity views
        dummy, form_view = models_data.get_object_reference(cr, uid, 'procurement', 'procurement_form_view')
        dummy, tree_view = models_data.get_object_reference(cr, uid, 'procurement', 'procurement_tree_view')
        return {
                'domain': "[('id','in',["+','.join(map(str, procurments_ids))+"])]",
                'name': 'Procurements Order',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'procurement.order',
                'type': 'ir.actions.act_window',
                'view_id': False,
                'views': [(tree_view or False, 'tree'),
                          (form_view or False, 'form'),
                        ],
                }

    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels the production order and related stock moves.
        @return: True
        -Process
            -Cancel all process lines in workorder
        """
        for data in self.browse(cr, uid, ids, context=context):
            for wrkorder in data.workcenter_lines:
                for process_mv in wrkorder.moves_workorder:
                    if process_mv.state == 'in_progress':
                        raise osv.except_osv(_('Can"t cancel Production order!'), _('Process line has been started in workorder(%s)'%(wrkorder.name)))
        return super(mrp_production, self).action_cancel(cr, uid, ids, context=context)

    def product_moves_to_workcenter(self, cr, uid, ids , context=None):
        """
        -Process
            -getting all moves to consume
            -pass that moves to _update_workorder_lines() for create workorder process lines
            -Update moves_to_workorder=True
        """

        def _none_qty(production_rec):
            """
            -Process
                getting total moves to consume
            """
            total_moves_to_consume = []
            for raw_m in production_rec.move_lines:
                total_moves_to_consume.append(raw_m.id)
            if not total_moves_to_consume:
                raise osv.except_osv(_('Raw material not found!'), _('Raw material not found for consume'))
            return total_moves_to_consume

        move_obj = self.pool.get('stock.move')
        production_rec = self.browse(cr, uid, ids[0], context=context)
        if production_rec.state <> 'ready':
            raise osv.except_osv(_('Production order not ready for start!'), _('You only put raw material into production department if production order must be into "ready to produce" state.'))
        if production_rec.moves_to_workorder:
            raise osv.except_osv(_('Warning!'), _('Raw materials already moved to workorder.'))

        total_moves_to_consume = _none_qty(production_rec)
        self._update_workorder_lines(cr, uid, total_moves_to_consume, ids[0], context=context)
        production_rec.write({'moves_to_workorder':True})
        move_obj.write(cr, uid, total_moves_to_consume, {'moves_to_workorder':True}, context=context)
        return True

    def action_produce(self, cr, uid, production_id, production_qty, production_mode, context=None):
        """ To produce final product based on production mode (consume/consume&produce).
        If Production mode is consume, all stock move lines of raw materials will be done/consumed.
        If Production mode is consume & produce, all stock move lines of raw materials will be done/consumed
        and stock move lines of final product will be also done/produced.
        @param production_id: the ID of mrp.production object
        @param production_qty: specify qty to produce
        @param production_mode: specify production mode (consume/consume&produce).
        @return: True

        * Our Goal
        - Process
            -We are here totally depended on workorder thatwhy just commented raise warning for cosuming raw materials
        """
        stock_mov_obj = self.pool.get('stock.move')
        production = self.browse(cr, uid, production_id, context=context)

        wf_service = netsvc.LocalService("workflow")
        if not production.move_lines and production.state == 'ready':
            # trigger workflow if not products to consume (eg: services)
            wf_service.trg_validate(uid, 'mrp.production', production_id, 'button_produce', cr)

        produced_qty = 0
        for produced_product in production.move_created_ids2:
            if (produced_product.scrapped) or (produced_product.product_id.id != production.product_id.id):
                continue
            produced_qty += produced_product.product_qty
        if production_mode in ['consume','consume_produce']:
            consumed_data = {}

            # Calculate already consumed qtys
            for consumed in production.move_lines2:
                if consumed.scrapped:
                    continue
                if not consumed_data.get(consumed.product_id.id, False):
                    consumed_data[consumed.product_id.id] = 0
                consumed_data[consumed.product_id.id] += consumed.product_qty

            # Find product qty to be consumed and consume it
            for scheduled in production.product_lines:

                # total qty of consumed product we need after this consumption
                total_consume = ((production_qty + produced_qty) * scheduled.product_qty / production.product_qty)

                # qty available for consume and produce
                qty_avail = scheduled.product_qty - consumed_data.get(scheduled.product_id.id, 0.0)

                if qty_avail <= 0.0:
                    # there will be nothing to consume for this raw material
                    continue

                raw_product = [move for move in production.move_lines if move.product_id.id==scheduled.product_id.id]
                if raw_product:
                    # qtys we have to consume
                    qty = total_consume - consumed_data.get(scheduled.product_id.id, 0.0)
                    if float_compare(qty, qty_avail, precision_rounding=scheduled.product_id.uom_id.rounding) == 1:
                        # if qtys we have to consume is more than qtys available to consume
                        prod_name = scheduled.product_id.name_get()[0][1]
                        #HIDE THIS PROCESS ONLY , BECAUSE WE ARE TOTTALY DEPENDS ON WORKORDER NOT PRODUCED BUTTON.
                        #raise osv.except_osv(_('Warning!'), _('You are going to consume total %s quantities of "%s".\nBut you can only consume up to total %s quantities.') % (qty, prod_name, qty_avail))
                    if qty <= 0.0:
                        # we already have more qtys consumed than we need
                        continue

                    raw_product[0].action_consume(qty, raw_product[0].location_id.id, context=context)

        if production_mode == 'consume_produce':
            # To produce remaining qty of final product
            #vals = {'state':'confirmed'}
            #final_product_todo = [x.id for x in production.move_created_ids]
            #stock_mov_obj.write(cr, uid, final_product_todo, vals)
            #stock_mov_obj.action_confirm(cr, uid, final_product_todo, context)
            produced_products = {}
            for produced_product in production.move_created_ids2:
                if produced_product.scrapped:
                    continue
                if not produced_products.get(produced_product.product_id.id, False):
                    produced_products[produced_product.product_id.id] = 0
                produced_products[produced_product.product_id.id] += produced_product.product_qty

            for produce_product in production.move_created_ids:
                produced_qty = produced_products.get(produce_product.product_id.id, 0)
                subproduct_factor = self._get_subproduct_factor(cr, uid, production.id, produce_product.id, context=context)
                rest_qty = (subproduct_factor * production.product_qty) - produced_qty

                if rest_qty < (subproduct_factor * production_qty):
                    prod_name = produce_product.product_id.name_get()[0][1]
                    #HIDE THIS PROCESS ONLY , BECAUSE WE ARE TOTTALY DEPENDS ON WORKORDER NOT PRODUCED BUTTON.
                    #raise osv.except_osv(_('Warning!'), _('You are going to produce total %s quantities of "%s".\nBut you can only produce up to total %s quantities.') % ((subproduct_factor * production_qty), prod_name, rest_qty))
                if rest_qty > 0 :
                    stock_mov_obj.action_consume(cr, uid, [produce_product.id], (subproduct_factor * production_qty), context=context)

        for raw_product in production.move_lines2:
            new_parent_ids = []
            parent_move_ids = [x.id for x in raw_product.move_history_ids]
            for final_product in production.move_created_ids2:
                if final_product.id not in parent_move_ids:
                    new_parent_ids.append(final_product.id)
            for new_parent_id in new_parent_ids:
                stock_mov_obj.write(cr, uid, [raw_product.id], {'move_history_ids': [(4,new_parent_id)]})

        wf_service.trg_validate(uid, 'mrp.production', production_id, 'button_produce_done', cr)
        return True

    def _to_find_shortestworkorder(self, cr, uid, production_id):
        """
        - Process
            -get production_id,
            -find shortest sequence in workorder,
        - return
            -shortest workorder
        """
        short_key = {}
        production = self.browse(cr, uid, production_id)
        for wrkorder in production.workcenter_lines:
            # need to check for not included done or cancel work-order
            if wrkorder.state != 'cancel':
                short_key.update({wrkorder.id: wrkorder.sequence})

        # find shorted by values
        shorted_wrkordr = sorted(short_key.items(), key=lambda x: x[1])
        return shorted_wrkordr and shorted_wrkordr[0][0] or False

    def _create_process_dict(self, cr, uid, move, shortest_wrkorder):
        """
        - Process
            - pass moves data and shortest workorderid
        - Returns
            - Final dictionary of process move
        """
        # check for routing not found for production order
        # if not shortest_wrkorder:
        #    raise osv.except_osv(_('WorkCenter not found!'), _('WorkOrder not found to attach process flow,\nKindly attach atleast one route for production order'))
        if not shortest_wrkorder:
            return {}
        return {
                'name': move.name,
                'move_id': move.id,
                'workorder_id': shortest_wrkorder,
                'product_id': move.product_id.id,
                'prodlot_id': move.prodlot_id and move.prodlot_id.id or False,
                'start_date':False,
                'end_date':False,
                'total_qty': move.product_qty or 0.0,
                'accepted_qty': 0.0,
                'rejected_qty': 0.0,
                'reason': '',
                'state': 'draft',
               }

    def _update_workorder_lines(self, cr, uid, all_moves, production_id, context=None):
        """
        - Process:
            - find shorted workorder,
            - browse all consume moves and attached it workorder processing,
            - find shortest workorder to attached all lines to it,
        @return: dictionaries for moves to generate workorders(moves)
        """
        context = context or {}
        stock_move = self.pool.get('stock.move')
        process_move = self.pool.get('stock.moves.workorder')

        # process moves dictionaries, find shorted work-order by sequence.
        process_lines = []
        shortest_wrkorder = self._to_find_shortestworkorder(cr, uid, production_id)
        for c_moves in stock_move.browse(cr, uid, all_moves, context=context):
            process_lines.append(self._create_process_dict(cr, uid, c_moves, shortest_wrkorder))
        # filter to any None dictionary.
        process_lines = filter(None, process_lines)
        # create process moves for shorted work-order.
        for dicts in process_lines:
            process_move.create(cr, uid, dicts, context=context)
        return True

    def _check_for_routing(self, cr, uid, production, context=None):
        """
        Process
            -Find BoM from finish product,
                -First check from production order Routing
                -If not available then check from production BoM to Routing
        Return
            - Warning raise if routing not found at production order
        """
        routing_id = production.bom_id.routing_id.id or False
        if (not production.routing_id) and (not routing_id):
            raise osv.except_osv(_('Routing not found!'), _('Atleast define one route for starting of production order'))
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """ 
        - Process
            - To check routing available to start production order,
            - To call _update_workorder_lines() at end of confirmation. 
        - Return
            - shipment_id(As it is)
        """
        # check for context
        context = context or {}
        shipment_id = False
        all_consume_moves = []
        wf_service = netsvc.LocalService("workflow")
        uncompute_ids = filter(lambda x:x, [not x.product_lines and x.id or False for x in self.browse(cr, uid, ids, context=context)])
        self.action_compute(cr, uid, uncompute_ids, context=context)
        for production in self.browse(cr, uid, ids, context=context):
            # check routing available or not
            self._check_for_routing(cr, uid, production, context=context)
            shipment_id = self._make_production_internal_shipment(cr, uid, production, context=context)
            produce_move_id = self._make_production_produce_line(cr, uid, production, context=context)

            source_location_id = production.location_src_id.id
            if production.bom_id.routing_id and production.bom_id.routing_id.location_id:
                source_location_id = production.bom_id.routing_id.location_id.id

            for line in production.product_lines:
                consume_move_id = self._make_production_consume_line(cr, uid, line, produce_move_id, source_location_id=source_location_id, context=context)
                # update all consume moves because its need to create process lines in work-order
                all_consume_moves.append(consume_move_id)
                if shipment_id:
                    shipment_move_id = self._make_production_internal_shipment_line(cr, uid, line, shipment_id, consume_move_id, \
                                 destination_location_id=source_location_id, context=context)
                    self._make_production_line_procurement(cr, uid, line, shipment_move_id, context=context)

            if shipment_id:
                wf_service.trg_validate(uid, 'stock.picking', shipment_id, 'button_confirm', cr)
            production.write({'state':'confirmed'}, context=context)
            # Call method to update moves attached on work-order process
            #self._update_workorder_lines(cr, uid, all_consume_moves, production.id, context=context)
        return shipment_id

    def copy(self, cr, uid, id, default=None, context=None):
        """
        -Process
            - blank workorder lines
        """
        if default is None: default = {}
        default.update({'workcenter_lines' : []})
        return super(mrp_production, self).copy(cr, uid, id, default, context)

    def _find_production_id(self, cr, uid, workorder):
        """
        -Process
            -loop on workorder to find production_id
        -Return
            -Production Id
        """
        return workorder.production_id.id

    def to_find_next_wrkorder(self, cr, uid, production_id, last_workorder_id, last_workorder_seq, context=None):
        """
        -Process
            - find next stage of work-order by,
                - Production_id
                - sequence greater then equal from current work-order
                - next order id not current work-order id ;)
        -Return
            -[Next work-order Id, production_id]
        """
        context = context or {}
        workorder_line_obj = self.pool.get('mrp.production.workcenter.line')
        next_workorder_ids = workorder_line_obj.search(cr, uid, [('production_id', '=', production_id), ('sequence', '>=', last_workorder_seq), ('id', '!=', last_workorder_id),('state','!=','cancel')], order='sequence')
        return [next_workorder_ids and next_workorder_ids[0] or False, production_id]

    def next_stage_workorder(self, cr, uid, workorder_processmove_id, context=None):
        """
        -Process
            -get current workorder move process Id,
            -First find Workorder of that process move,
            -call function to find production id then,
            -call function to find next workorder
        - Return
            - next work-order
        """
        process_moves_obj = self.pool.get('stock.moves.workorder')
        # to find current work-order
        wrkorder_id = process_moves_obj.browse(cr, uid, workorder_processmove_id, context=context).workorder_id
        # to find production from that current work-order
        production_id = self._find_production_id(cr, uid, wrkorder_id)
        # to find next work-order
        return self.to_find_next_wrkorder(cr, uid, production_id, wrkorder_id.id, wrkorder_id.sequence, context=context)

mrp_production()

class stock_moves_workorder(osv.osv):
    _name = 'stock.moves.workorder'
    _columns = {
        'name': fields.char('Name'),
        'workorder_id': fields.many2one('mrp.production.workcenter.line', 'WorkOrder'),
        'move_id': fields.many2one('stock.move', 'Move', readonly=True),
        #Problem when reallocated move to process
        #'prodlot_id': fields.related('move_id', 'prodlot_id', type='many2one', relation='stock.production.lot', string='Serial Number', readonly=True),
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial Number', readonly=True), 
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'start_date':fields.datetime('Start Date', help="Time when Product goes to start for workorder", readonly=True),
        'end_date':fields.datetime('End Date', help="Time when Product goes to finish or cancel for workorder", readonly=True),
        'total_qty': fields.float('Total Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'process_qty': fields.float('In Process Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'accepted_qty': fields.float('Accept Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'rejected_qty': fields.float('Reject Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        #'reason': fields.text('Reason'),
        'state': fields.selection(STATE_SELECTION, 'Status', readonly=True),

        #For outsourcing process
        'order_type': fields.related('workorder_id', 'order_type', type='selection', selection=[('in', 'Inside'), ('out', 'Outside')], string='Order Type', store=True), 
        'service_supplier_id': fields.many2one('res.partner', 'Supplier',domain=[('supplier','=',True)]),
        'po_order_id': fields.many2one('purchase.order', 'Service Order'),
        'delivery_order_id': fields.many2one('stock.picking', 'Delivery Order'),
    }

    _defaults = {
        'state': 'draft'
        }

    def button_to_draft(self, cr, uid, ids , context=None):
        return True

    def button_to_start(self, cr, uid, ids , context=None):
        """
        -Process
            -Raw material Process
                -Update State, Start Date, Process Qty
            -Start WorkOrder Also
        """
        #All process moves have its own PO, DO, INWORD
        currnt_data = self.browse(cr, uid, ids[0], context=context)
        if currnt_data.order_type == 'out':
            currnt_data.workorder_id.dummy_button()
            if not currnt_data.service_supplier_id: raise osv.except_osv(_('Warning!!!'),_('1)Define supplier on line or \n2)Click "⟳ (Update)" button to save the record!'))
            return self._call_service_order(cr, uid, ids, context=context)

        wf_service = netsvc.LocalService("workflow")
        self.write(cr, uid, ids, {
                                  'state':'in_progress',
                                  'start_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                  'process_qty':currnt_data.total_qty
                                  })
        #Start Work-Order Also.
        wf_service.trg_validate(uid, 'mrp.production.workcenter.line', currnt_data.workorder_id.id, 'button_start_working', cr)
        #currnt_data.workorder_id.action_start_working(context=context)
        return True

    def _call_service_order(self, cr, uid, ids, context=None):
        """
        Process
            -call wizard to ask for service order
        """
        # Get service order wizard
        models_data = self.pool.get('ir.model.data')
        dummy, form_view = models_data.get_object_reference(cr, uid, 'l10n_in_mrp_subcontract', 'view_generate_service_order')

        return {
            'name': _('Service Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'context':context,
            'res_model': 'generate.service.order',
            'views': [(form_view or False, 'form')],
            'type': 'ir.actions.act_window',
            'target':'new'
        }


    def button_to_reject(self, cr, uid, ids , context=None):
        """
        -Process
            -Call wizard for quantity for rejection process
        -Return
            -Open Rejection Wizard
        """
        context = context or {}
        models_data = self.pool.get('ir.model.data')
        # Get Rejected wizard
        dummy, form_view = models_data.get_object_reference(cr, uid, 'l10n_in_mrp_subcontract', 'view_process_qty_to_update_reject')
        currnt_data = self.browse(cr, uid, ids[0], context=context)
        context.update({
                        'total_qty':currnt_data.total_qty,
                        'product_id':currnt_data.product_id.id,
                        'already_rejected_qty': currnt_data.rejected_qty,
                        'process_qty': currnt_data.process_qty,
                        })

        return {
            'name': _('Rejected Quantity'),
            'view_type': 'form',
            'view_mode': 'form',
            'context':context,
            'res_model': 'process.qty.to.update.reject',
            'views': [(form_view or False, 'form')],
            'type': 'ir.actions.act_window',
            'target':'new'
        }

    def button_to_finish(self, cr, uid, ids , context=None):
        """
        -Process
            -Call wizard for quantity for finished process
        -Return
            -Open finished Wizard
        """
        context = context or {}
        models_data = self.pool.get('ir.model.data')
        # Get Accepted wizard
        dummy, form_view = models_data.get_object_reference(cr, uid, 'l10n_in_mrp_subcontract', 'view_process_qty_to_finished')
        currnt_data = self.browse(cr, uid, ids[0], context=context)
        context.update({
                        'already_accepted_qty':currnt_data.accepted_qty,
                        'total_qty':currnt_data.total_qty,
                        'product_id':currnt_data.product_id.id,
                        'process_qty': currnt_data.process_qty,
                        })

        return {
            'name': _('Accept Quantity'),
            'view_type': 'form',
            'view_mode': 'form',
            'context':context,
            'res_model': 'process.qty.to.finished',
            'views': [(form_view or False, 'form')],
            'type': 'ir.actions.act_window',
            'target':'new'
        }

    def button_to_consume(self, cr, uid, ids , context=None):
        """
        -Process
            -Call wizard for quantity for consuming process
        -Return
            -Open consume Wizard
        """
        context = context or {}
        models_data = self.pool.get('ir.model.data')
        # Get Accepted wizard
        dummy, form_view = models_data.get_object_reference(cr, uid, 'l10n_in_mrp_subcontract', 'view_process_qty_to_consume')
        currnt_data = self.browse(cr, uid, ids[0], context=context)
        context.update({
                        'already_accepted_qty':currnt_data.accepted_qty,
                        'total_qty':currnt_data.total_qty,
                        'product_id':currnt_data.product_id.id,
                        'process_qty': currnt_data.process_qty,
                        })

        return {
            'name': _('Consume Quantity'),
            'view_type': 'form',
            'view_mode': 'form',
            'context':context,
            'res_model': 'qty.to.consume',
            'views': [(form_view or False, 'form')],
            'type': 'ir.actions.act_window',
            'target':'new'
        }

stock_moves_workorder()

class stock_moves_rejection(osv.osv):
    _name = 'stock.moves.rejection'
    _columns = {
        'name': fields.char('Name'),
        'rejected_workorder_id': fields.many2one('mrp.production.workcenter.line', 'WorkOrder'),
        'move_id': fields.many2one('stock.move', 'Move', readonly=True),
        'prodlot_id': fields.related('move_id', 'prodlot_id', type='many2one', relation='stock.production.lot', string='Serial Number', readonly=True),
        'rejected_location_id': fields.many2one('stock.location', 'Rejection Location', readonly=True),
        'rejected_from_process_move_id': fields.many2one('stock.moves.workorder', 'Rejection From', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'rejected_date':fields.datetime('Rejected Date', readonly=True),
        'reallocate_date':fields.datetime('Reallocate Date', readonly=True),
        'rejected_qty': fields.float('Rejected Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'reason': fields.text('Reason'),
        'state': fields.selection([('rejected', 'Rejected')], 'Status', readonly=True),
        'is_reallocate':  fields.boolean('Re-Allocated?')
    }

    def button_to_reallocate(self, cr, uid, ids, context=None):
        """
        -Process
            -Call wizard for product,
                -Real stock availability,
                -you can select work-order to move,
                -create directly moves to work-order
        -Return
            -Open Reallocate Wizard
        """
        context = context or {}
        models_data = self.pool.get('ir.model.data')
        # Get Accepted wizard
        dummy, form_view = models_data.get_object_reference(cr, uid, 'l10n_in_mrp_subcontract', 'view_reallocate_rejected_move')
        currnt_data = self.browse(cr, uid, ids[0], context=context)
        context.update({
                        'total_qty':currnt_data.rejected_qty,
                        'product_id':currnt_data.product_id.id,
                        'process_move_id': currnt_data.rejected_from_process_move_id.id,
                        'rejected_workorder_id':currnt_data.rejected_workorder_id and currnt_data.rejected_workorder_id.id or False
                        })

        return {
            'name': _('Re-Allocate Product Quantity To Work-Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'context':context,
            'res_model': 'reallocate.rejected.move',
            'views': [(form_view or False, 'form')],
            'type': 'ir.actions.act_window',
            'target':'new'
        }

stock_moves_rejection()

class mrp_production_workcenter_line(osv.osv):
    _inherit = 'mrp.production.workcenter.line'
    _columns = {
        'moves_workorder': fields.one2many('stock.moves.workorder', 'workorder_id', 'Raw Material To Process'),
        'moves_rejection': fields.one2many('stock.moves.rejection', 'rejected_workorder_id', 'Rejected Raw Material'),
        #'service_product_id': fields.many2one('product.product', 'Service Product'),
        #'service_supplier_id': fields.many2one('res.partner', 'Partner',domain=[('supplier','=',True)]),
        #'service_description': fields.text('Description'),
        #'po_order_id': fields.many2one('purchase.order', 'Service Order'),
        'order_type': fields.selection([('in', 'Inside'), ('out', 'Outside')], 'WorkOrder Process', readonly=True, states={'draft':[('readonly', False)]}),
        'workcenter_id': fields.many2one('mrp.workcenter', 'Work Center', required=True , readonly=True, states={'draft':[('readonly', False)]}),
        'temp_date_finished':fields.related('date_finished', type="datetime",store=True),
    }
    _sql_constraints = [('sequence_uniq', 'unique(sequence, production_id)', "You cannot assign same sequence on current production order")] 

    _defaults = {
        'order_type': 'in'
        }

    def modify_production_order_state(self, cr, uid, ids, action):
        """
        -Process
            -overwrite this function to only ignore cancel workorder ;)
        -Return
            -As it is
        """
        wf_service = netsvc.LocalService("workflow")
        prod_obj_pool = self.pool.get('mrp.production')
        oper_obj = self.browse(cr, uid, ids)[0]
        prod_obj = oper_obj.production_id
        if action == 'start':
            if prod_obj.state =='confirmed':
                prod_obj_pool.force_production(cr, uid, [prod_obj.id])
                wf_service.trg_validate(uid, 'mrp.production', prod_obj.id, 'button_produce', cr)
            elif prod_obj.state =='ready':
                wf_service.trg_validate(uid, 'mrp.production', prod_obj.id, 'button_produce', cr)
            elif prod_obj.state =='in_production':
                return
            else:
                raise osv.except_osv(_('Error!'),_('Manufacturing order cannot be started in state "%s"!') % (prod_obj.state,))
        else:
            oper_ids = self.search(cr,uid,[('production_id','=',prod_obj.id)])
            obj = self.browse(cr,uid,oper_ids)
            flag = True
            for line in obj:
                #Update code for ignore cancel workorder
                if line.state != 'done' and line.state != 'cancel':
                    flag = False
            if flag:
                for production in prod_obj_pool.browse(cr, uid, [prod_obj.id], context= None):
                    if production.move_lines or production.move_created_ids:
                        prod_obj_pool.action_produce(cr,uid, production.id, production.product_qty, 'consume_produce', context = None)
                wf_service.trg_validate(uid, 'mrp.production', oper_obj.production_id.id, 'button_produce_done', cr)
        return

    def unlink(self, cr, uid, ids, context=None):
        """
        -Process
            - Raise Warning, if they have raw material in-process or rejected quantity assigned to it
        """
        for wrkorder in self.browse(cr, uid, ids, context=context):
            if wrkorder.moves_workorder or wrkorder.moves_rejection:
                raise osv.except_osv(_('Invalid Action!'), _('Cannot delete a work-order if they have raw material in-process or rejected quantity assigned to it.'))
        return super(mrp_production_workcenter_line, self).unlink(cr, uid, ids, context=context)

    def _check_for_process_none_qty(self, cr, uid, ids, process='start', context=None):
        """
        -Process
            - check process moves available then and then only start any workorder
        -Return
            - Raise Warning, if None in process moves
        """
        process_moves = self.pool.get('stock.moves.workorder')
        if not process_moves.search(cr, uid, [('workorder_id', '=', ids[0])], context=context):
            raise osv.except_osv(_('Raw Material not found!'), _('You cannot %s work-order without any raw material') % (process))
        return True

#    def _call_service_order(self, cr, uid, ids, context=None):
#        """
#        Process
#            -call wizard to ask for service order
#        """
#        # Get service order wizard
#        models_data = self.pool.get('ir.model.data')
#        dummy, form_view = models_data.get_object_reference(cr, uid, 'l10n_in_mrp_subcontract', 'view_generate_service_order')
#
#        return {
#            'name': _('Service Order'),
#            'view_type': 'form',
#            'view_mode': 'form',
#            'context':context,
#            'res_model': 'generate.service.order',
#            'views': [(form_view or False, 'form')],
#            'type': 'ir.actions.act_window',
#            'target':'new'
#        }

    def action_draft(self, cr, uid, ids, context=None):
        """ 
        -Return
            -same super call
        """
        return super(mrp_production_workcenter_line, self).action_draft(cr, uid, ids, context=context)

    def action_to_start_working(self, cr, uid, ids, context=None):
        """ 
        -Process
            -if order type == 'service':
                - Open wizard to ask to generate service order
                - Generate Service Order for Service type product
            -call funtion to check process moves available then and then only start any workorder
        -Return
            -same super call
        """
        context = context or {}

#        This has been moved to process moves because all process moves have its own PO, DO, INWORD
#        wrk_rec = self.browse(cr, uid, ids[0], context=context)
#        if wrk_rec.order_type == 'out':
#            return self._call_service_order(cr, uid, ids, context=context)

        self._check_for_process_none_qty(cr, uid, ids, 'start', context=context)
        self.modify_production_order_state(cr, uid, ids, 'start')
        self.write(cr, uid, ids, {'state':'startworking', 'date_start': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        return True

    def _check_out_all_lines(self, cr, uid, current_data, context=None):
        """
        Process(OutSide)
            -Check to finished all process move lines
        """
        context = context or {}
        for lines in current_data.moves_workorder:
            if lines.state in ('draft','in_progress'):
                raise osv.except_osv(_('Couldn"t finish workorder!'), _('You must finish all work-order process lines first.'))
        return True

    def action_finish(self, cr, uid, ids, context=None):
        """ 
        -Process
            -find next workorder id which all moves goes to that workorder
            -create list of all process moves to finished
        -Return
            -Wizard to ask for all in once to process ?
        Note: Super method call on apply button on wizard ;)
        """
        context = context or {}
        models_data = self.pool.get('ir.model.data')
        mrp_obj = self.pool.get('mrp.production')
        # Get Accepted wizard
        dummy, form_view = models_data.get_object_reference(cr, uid, 'l10n_in_mrp_subcontract', 'view_all_in_once_qty_to_finished')
        currnt_data = self.browse(cr, uid, ids[0], context=context)
        if currnt_data.order_type == 'out':
            self._check_out_all_lines(cr, uid, currnt_data, context)
        next_stage_workorder_id = mrp_obj.to_find_next_wrkorder(cr, uid, currnt_data.production_id.id, ids[0], currnt_data.sequence, context=context)
        all_process_moves_ids = []
        for find_pm in currnt_data.moves_workorder:
            if find_pm.state not in ('finished', 'rejected','consumed'):
                all_process_moves_ids.append({
                                            'select':True,
                                            'process_move_id':find_pm.id,
                                            'product_id': find_pm.product_id and find_pm.product_id.id or False,
                                            'accepted_qty': find_pm.accepted_qty,
                                            'total_qty': find_pm.total_qty - (find_pm.accepted_qty + find_pm.rejected_qty),
                                            'state': find_pm.state
                                             })

        context.update({
                        'all_process_moves_ids':all_process_moves_ids,
                        'next_stage_workorder_id':next_stage_workorder_id
                        })

        return {
            'name': _('All In Once Quantity To Finish'),
            'view_type': 'form',
            'view_mode': 'form',
            'context':context,
            'res_model': 'all.in.once.qty.to.finished',
            'views': [(form_view or False, 'form')],
            'type': 'ir.actions.act_window',
            'target':'new'
        }

    def action_cancelled(self, cr, uid, ids, context=None):
        """ 
        -Process
            -find next workorder id which all moves goes to that workorder
            -create list of all process moves goes to cancel
        -Return
            -Wizard to ask for all in once to process ?
        Note: Super method call on apply button on wizard ;)
        """
        context = context or {}
        models_data = self.pool.get('ir.model.data')
        mrp_obj = self.pool.get('mrp.production')
        # Get Cancel wizard
        dummy, form_view = models_data.get_object_reference(cr, uid, 'l10n_in_mrp_subcontract', 'view_all_in_once_qty_to_cancelled')
        currnt_data = self.browse(cr, uid, ids[0], context=context)
        next_stage_workorder_id = mrp_obj.to_find_next_wrkorder(cr, uid, currnt_data.production_id.id, ids[0], currnt_data.sequence, context=context)
        all_process_moves_cancel_ids = []
        for find_pm in currnt_data.moves_workorder:
            if find_pm.state not in ('finished', 'rejected','consumed'):
                all_process_moves_cancel_ids.append({
                                            'select':True,
                                            'process_move_id':find_pm.id,
                                            'product_id': find_pm.product_id and find_pm.product_id.id or False,
                                            'accepted_qty': find_pm.accepted_qty,
                                            'total_qty': find_pm.total_qty - (find_pm.accepted_qty + find_pm.rejected_qty),
                                            'state': find_pm.state
                                             })

        context.update({
                        'all_process_moves_cancel_ids':all_process_moves_cancel_ids,
                        'next_stage_workorder_id':next_stage_workorder_id
                        })

        return {
            'name': _('All In Once Quantity To Cancel'),
            'view_type': 'form',
            'view_mode': 'form',
            'context':context,
            'res_model': 'all.in.once.qty.to.cancelled',
            'views': [(form_view or False, 'form')],
            'type': 'ir.actions.act_window',
            'target':'new'
        }

    def action_pause(self, cr, uid, ids, context=None):
        """ 
        -Process
            -call funtion to check process moves available then and then only start any workorder
        -Return
            -same super call
        """
        self._check_for_process_none_qty(cr, uid, ids, 'Pause', context=context)
        return super(mrp_production_workcenter_line, self).action_pause(cr, uid, ids, context=context)

    def action_resume(self, cr, uid, ids, context=None):
        """ 
        -Process
            -call funtion to check process moves available then and then only start any workorder
        -Return
            -same super call
        """
        self._check_for_process_none_qty(cr, uid, ids, 'Resume', context=context)
        return super(mrp_production_workcenter_line, self).action_resume(cr, uid, ids, context=context)

    def add_consume_product(self, cr, uid, ids, context=None):
        """
        -Process
            -add consume line to Product to consume
            -Done this consume line to consume
            -add line to workorder for consume 
        """
        context = context or {}
        models_data = self.pool.get('ir.model.data')
        # Get consume wizard
        dummy, form_view = models_data.get_object_reference(cr, uid, 'l10n_in_mrp_subcontract', 'view_add_rawmaterial_to_consume')
        current = self.browse(cr, uid, ids[0], context=context).production_id
        finish_move_id = False

        #To find produce move
        for move in current.move_created_ids:
            finish_move_id = move.id
            break
        if not finish_move_id:
            for move in current.move_created_ids2:
                finish_move_id = move.id
                break

        context.update({
                        'finish_move_id': finish_move_id,
                        })
        return {
            'name': _('Add consume Material to Work-Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'context':context,
            'res_model': 'add.rawmaterial.to.consume',
            'views': [(form_view or False, 'form')],
            'type': 'ir.actions.act_window',
            'target':'new'
        }

    def dummy_button(self, cr, uid, ids, context=None):
        """
        -Process
            -Update process moves to work-order
        """
        return True

    def create_service_order(self, cr, uid, ids , context=None):
        return True

mrp_production_workcenter_line()


class mrp_routing_workcenter(osv.osv):
    _inherit = 'mrp.routing.workcenter'
    _columns = {
#        'service_supplier_id': fields.many2one('res.partner', 'Partner',domain=[('supplier','=',True)]),
#        'service_description': fields.text('Description'),
#        'po_order_id': fields.many2one('purchase.order', 'Service Order'),
        'order_type': fields.selection([('in', 'Inside'), ('out', 'Outside')], 'WorkOrder Process'),
    }
    _defaults = {'order_type':'in'}

mrp_routing_workcenter()

class mrp_bom(osv.osv):
    _inherit = 'mrp.bom'

    def _bom_explode(self, cr, uid, bom, factor, properties=None, addthis=False, level=0, routing_id=False):
        """ Finds Products and Work Centers for related BoM for manufacturing order.
        @param bom: BoM of particular product.
        @param factor: Factor of product UoM.
        @param properties: A List of properties Ids.
        @param addthis: If BoM found then True else False.
        @param level: Depth level to find BoM lines starts from 10.
        @return: result: List of dictionaries containing product details.
                 result2: List of dictionaries containing Work Center details.
        """
        routing_obj = self.pool.get('mrp.routing')
        factor = factor / (bom.product_efficiency or 1.0)
        max_rounding = max(bom.product_rounding, bom.product_uom.rounding)
        factor = rounding(factor, max_rounding)
        if factor < max_rounding:
            factor = max_rounding
        result = []
        result2 = []
        phantom = False
        if bom.type == 'phantom' and not bom.bom_lines:
            newbom = self._bom_find(cr, uid, bom.product_id.id, bom.product_uom.id, properties)

            if newbom:
                res = self._bom_explode(cr, uid, self.browse(cr, uid, [newbom])[0], factor*bom.product_qty, properties, addthis=True, level=level+10)
                result = result + res[0]
                result2 = result2 + res[1]
                phantom = True
            else:
                phantom = False
        if not phantom:
            if addthis and not bom.bom_lines:
                result.append(
                {
                    'name': bom.product_id.name,
                    'product_id': bom.product_id.id,
                    'product_qty': bom.product_qty * factor,
                    'product_uom': bom.product_uom.id,
                    'product_uos_qty': bom.product_uos and bom.product_uos_qty * factor or False,
                    'product_uos': bom.product_uos and bom.product_uos.id or False,
                })
            routing = (routing_id and routing_obj.browse(cr, uid, routing_id)) or bom.routing_id or False
            if routing:
                for wc_use in routing.workcenter_lines:
                    wc = wc_use.workcenter_id
                    d, m = divmod(factor, wc_use.workcenter_id.capacity_per_cycle)
                    mult = (d + (m and 1.0 or 0.0))
                    cycle = mult * wc_use.cycle_nbr
                    result2.append({
                        'name': tools.ustr(wc_use.name) + ' - '  + tools.ustr(bom.product_id.name),
                        'workcenter_id': wc.id,
                        'order_type':wc_use.order_type,
                        'service_description':wc_use.note,
                        #'service_supplier_id':wc_use.service_supplier_id and wc_use.service_supplier_id.id or False,
                        'sequence': level+(wc_use.sequence or 0),
                        'cycle': cycle,
                        'hour': float(wc_use.hour_nbr*mult + ((wc.time_start or 0.0)+(wc.time_stop or 0.0)+cycle*(wc.time_cycle or 0.0)) * (wc.time_efficiency or 1.0)),
                    })
            for bom2 in bom.bom_lines:
                res = self._bom_explode(cr, uid, bom2, factor, properties, addthis=True, level=level+10)
                result = result + res[0]
                result2 = result2 + res[1]
        return result, result2

mrp_bom()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
