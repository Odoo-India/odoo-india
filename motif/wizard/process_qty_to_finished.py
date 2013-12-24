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
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class process_qty_to_finished(osv.osv_memory):
    _name = "process.qty.to.finished"
    _description = "Process Quantity To Accept Wizard"

    def default_get(self, cr, uid, fields, context=None):
        """
        -Process
            -Set default values of 
                -Active_id
                -Product
                -Total Qty
        """
        context = context or {}
        mrp_obj = self.pool.get('mrp.production')
        process_move_id = context and context.get('active_id', False) or False
        total_qty = context and context.get('total_qty', 0.0) or 0.0
        product_id = context and context.get('product_id', False) or False
        process_qty = context and context.get('process_qty', 0.0) or 0.0
        already_accepted_qty = context and context.get('already_accepted_qty', 0.0) or 0.0

        res = super(process_qty_to_finished, self).default_get(cr, uid, fields, context=context)
        next_stage_workorder_id, production_id = False, False
        if process_move_id:
            # return [next route, production_id]
            next_stage = mrp_obj.next_stage_workorder(cr, uid, process_move_id, context=context)
            next_stage_workorder_id = next_stage[0]  # next route
            production_id = next_stage[1]  # production id

        if 'process_move_id' in fields:
            res.update({'process_move_id': process_move_id})
        if 'product_id' in fields:
            res.update({'product_id': product_id})
        if 'total_qty' in fields:
            res.update({'total_qty': total_qty})
        if 'process_qty' in fields:
            res.update({'process_qty': process_qty})
        if 'already_accepted_qty' in fields:
            res.update({'already_accepted_qty': already_accepted_qty})
        if 'accepted_qty' in fields:
            res.update({'accepted_qty': 0.0})
        if 'next_stage_workorder_id' in fields:
            res.update({'next_stage_workorder_id': next_stage_workorder_id})
        if 'production_id' in fields:
            res.update({'production_id': production_id})
        return res

    _columns = {
        'process_move_id':fields.many2one('stock.moves.workorder', 'WorkOrder Move'),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'total_qty': fields.float('Total Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'process_qty': fields.float('Process Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'already_accepted_qty': fields.float('Already Accepted Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'accepted_qty': fields.float('Accept Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'next_stage_workorder_id':fields.many2one('mrp.production.workcenter.line', 'Next Stage of Work-Order'),
        'production_id':fields.many2one('mrp.production', 'Production'),
    }

    def onchange_workorder_id(self, cr, uid, ids, workorder_id, production_id, context=None):
        """
        -Process
            -to set domain of current production order
        """
        context = context or {}
        workorder_line_obj = self.pool.get('mrp.production.workcenter.line')
        current_wrkorder_id = context and context.get('active_id', False) or False
        where_clause = [('production_id', '=', production_id),('state','!=','cancel')]
        if current_wrkorder_id:
            where_clause.append(('id','!=',current_wrkorder_id))
        workorder_ids = workorder_line_obj.search(cr, uid, where_clause, context=context)
        return {'domain': {'next_stage_workorder_id': [('id', 'in', workorder_ids)]}}

    def _check_validation_finished_qty(self, cr, uid, total_qty, accepted_qty):
        """
        - Process
            - Warning raise, if accepted qty > In process qty or accepted qty < 0
        """
        if accepted_qty <= 0.0:
            raise osv.except_osv(_('Warning!'), _('Provide proper value of Accepted qty(%s)' % (accepted_qty)))
        if accepted_qty > total_qty:
            raise osv.except_osv(_('Accepted Qty over the limit!'), _('Accepted Qty(%s) greater then In Process Qty(%s)' % (accepted_qty, total_qty)))
        return True

    def to_finish_qty(self, cr, uid, ids, context=None):
        """
        - Process
            - Warning raise, Validation check for Accepted qty
            - update according workorder process move
            - create new work-order move and attached to next stage if process goes to finished.
        """
        production_obj = self.pool.get('mrp.production')
        process_move = self.pool.get('stock.moves.workorder')
        wizard_rec = self.browse(cr, uid, ids[0])
        already_accepted_qty = wizard_rec.already_accepted_qty
        accepted_qty = wizard_rec.accepted_qty
        process_qty = wizard_rec.process_qty
        next_workorder_id = wizard_rec.next_stage_workorder_id.id

        self._check_validation_finished_qty(cr, uid, process_qty, accepted_qty)
        updt_prcs_mve = {}
        if process_qty == accepted_qty:
            updt_prcs_mve.update({
                                  'state':'finished',
                                  'accepted_qty': already_accepted_qty + accepted_qty,
                                  'process_qty': process_qty - accepted_qty,
                                  'end_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                  })
        else:
            updt_prcs_mve.update({
                                  'accepted_qty': already_accepted_qty + accepted_qty,
                                  'process_qty': process_qty - accepted_qty
                                  })

        # to write old process moves
        wizard_rec.process_move_id.write(updt_prcs_mve)

        # create new process move of next stage if work-order available.
        if next_workorder_id:
            res = production_obj._create_process_dict(cr, uid, wizard_rec.process_move_id.move_id, next_workorder_id)
            res.update({'total_qty':accepted_qty})
            process_move.create(cr, uid, res, context=context)
        else:
            # TODO:Close order if all products have done stage...
            print "process flow goes to done"

        return True

process_qty_to_finished()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
