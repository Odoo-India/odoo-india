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
from openerp import netsvc

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

STATE_SELECTION = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
    ]

class all_process_moves_in(osv.osv_memory):
    _name = "all.process.moves.in"
    _description = "All In Once"
    _columns = {
        'select':fields.boolean('Select'),
        'wizard_id': fields.many2one('all.in.once.qty.to.finished', 'WorkOrder Move'),
        'process_move_id':fields.many2one('stock.moves.workorder', 'WorkOrder Move'),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'accepted_qty': fields.float('Total Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'total_qty': fields.float('Total Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'state': fields.selection(STATE_SELECTION, 'Status', readonly=True),
    }
all_process_moves_in()

class all_in_once_qty_to_finished(osv.osv_memory):
    _name = "all.in.once.qty.to.finished"
    _description = "All In Once Accept Wizard"

    def default_get(self, cr, uid, fields, context=None):
        """
        -Process
            -Set one2many for all draft or in_progress moves 
        """
        context = context or {}
        res = {}
        all_process_moves_ids = context and context.get('all_process_moves_ids', False) or False
        next_stage_workorder_id = context and context.get('next_stage_workorder_id', False) or False

        if 'all_process_moves_ids' in fields:
            res.update({'all_process_moves_ids': all_process_moves_ids})
        if 'next_stage_workorder_id' in fields:
            res.update({'next_stage_workorder_id': next_stage_workorder_id[0]})
        if 'production_id' in fields:
            res.update({'production_id': next_stage_workorder_id[1]})
        return res

    _columns = {
        'all_process_moves_ids': fields.one2many('all.process.moves.in', 'wizard_id', 'All Process Moves'),
        'production_id':fields.many2one('mrp.production', 'Production'),
        'next_stage_workorder_id':fields.many2one('mrp.production.workcenter.line', 'Next Stage of Work-Order'),
    }

    def onchange_workorder_id(self, cr, uid, ids, workorder_id, production_id, context=None):
        """
        -Process
            -to set domain for  workorder_id which is coming from only current production order
        """
        context = context or {}
        workorder_line_obj = self.pool.get('mrp.production.workcenter.line')
        current_wrkorder_id = context and context.get('active_id', False) or False
        where_clause = [('production_id', '=', production_id),('state','!=','cancel')]
        if current_wrkorder_id:
            where_clause.append(('id','!=',current_wrkorder_id))
        workorder_ids = workorder_line_obj.search(cr, uid, where_clause, context=context)
        return {'domain': {'next_stage_workorder_id': [('id', 'in', workorder_ids)]}}

    def to_all_finish_qty(self, cr, uid, ids, context=None):
        """
        - Process
            - ask to apply all quantity at once, or cancel wizard flow also,
            - Updated old process moves in current order, which has been proceed,
            - create new process moves into next work-order
            - Work-Order done process,
            - create new work-order move and attached to next stage if process goes to finished.
        - Return
            - True
        """
        process_move = self.pool.get('stock.moves.workorder')
        prod_obj =  self.pool.get('mrp.production')
        current_wrkorder_line_id = context and context.get('active_id', False) or False
        wizard_rec = self.browse(cr, uid, ids[0])
        go_to_finished = []
        updt_prcs_mve = {}
        for data in wizard_rec.all_process_moves_ids:
            go_to_finished.append(data.process_move_id.id)
            #all line first in draft stage to in_progress state
            if data.state == 'draft':
                data.process_move_id.button_to_start(context=context)
            #update that current moves
            updt_prcs_mve.update({
                                  data.process_move_id.id:{
                                                           'state':'finished', 
                                                           'end_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                                           'accepted_qty': data.total_qty + data.accepted_qty,
                                                           'process_qty':0.0
                                                           }})

        #all current moves finished at once
        for key,value in updt_prcs_mve.items():
            process_move.write(cr, uid ,key, value)

        #create new process moves into next work-order
        if wizard_rec.next_stage_workorder_id:
            for data in wizard_rec.all_process_moves_ids:
                res = prod_obj._create_process_dict(cr, uid, data.process_move_id.move_id, wizard_rec.next_stage_workorder_id.id)
                res.update({'total_qty':data.total_qty})
                process_move.create(cr, uid, res, context=context)

        #Work-Order done process
        wf_service = netsvc.LocalService("workflow")
        if current_wrkorder_line_id:
            self.pool.get('mrp.production.workcenter.line').action_done(cr,uid,[current_wrkorder_line_id])
            wf_service.trg_validate(uid, 'mrp.production.workcenter.line', current_wrkorder_line_id, 'button_done', cr)
        return True

all_in_once_qty_to_finished()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
