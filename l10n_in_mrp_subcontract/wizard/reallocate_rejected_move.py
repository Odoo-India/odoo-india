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

class reallocate_rejected_move(osv.osv_memory):
    _name = "reallocate.rejected.move"
    _description = "Reallocate Rejected Move"

    def default_get(self, cr, uid, fields, context=None):
        """
        -Process
            -Set default values of 
                -Active_id
                -Product
                -Total Qty
        """
        context = context or {}
        res = {}

        prod_obj = self.pool.get('product.product')
        mrp_obj = self.pool.get('mrp.production')

        process_move_id = context and context.get('process_move_id', False) or False
        total_qty = context and context.get('total_qty', 0.0) or 0.0
        product_id = context and context.get('product_id', False) or False
        rejected_workorder_id = context and context.get('rejected_workorder_id', False) or False
        next_stage_workorder_id, production_id = False, False

        if process_move_id:
            # return [next route, production_id]
            next_stage = mrp_obj.next_stage_workorder(cr, uid, process_move_id, context=context)
            next_stage_workorder_id = next_stage[0]  # next route
            production_id = next_stage[1]  # production id

        #first assign same work-order
        if rejected_workorder_id:
            next_stage_workorder_id = rejected_workorder_id

        if 'process_move_id' in fields:
            res.update({'process_move_id': process_move_id})
        if 'product_id' in fields:
            res.update({'product_id': product_id})
        if 'total_qty' in fields:
            res.update({'total_qty': total_qty})
        if 'next_stage_workorder_id' in fields:
            res.update({'next_stage_workorder_id': next_stage_workorder_id})
        if 'production_id' in fields:
            res.update({'production_id': production_id})

        return res

    _columns = {
        'process_move_id':fields.many2one('stock.moves.workorder', 'WorkOrder Move'),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'total_qty': fields.float('Total Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'next_stage_workorder_id':fields.many2one('mrp.production.workcenter.line', 'Next Stage of Work-Order'),
        'production_id':fields.many2one('mrp.production', 'Production'),

        #'qty_available': fields.float(string='Quantity On Hand'),
        #'virtual_available': fields.float(string='Quantity Available'),
        #'incoming_qty': fields.float(string='Incoming'),
        #'outgoing_qty': fields.float(string='Outgoing'),

    }

    def onchange_workorder_id(self, cr, uid, ids, workorder_id, production_id, context=None):
        """
        -Process
            -to set domain of current production order
        """
        context = context or {}
        workorder_line_obj = self.pool.get('mrp.production.workcenter.line')
        current_wrkorder_id = context and context.get('active_id', False) or False
        where_clause = [('production_id', '=', production_id)]
        if current_wrkorder_id:
            where_clause.append(('id','!=',current_wrkorder_id))
        workorder_ids = workorder_line_obj.search(cr, uid, where_clause, context=context)
        return {'domain': {'next_stage_workorder_id': [('id', 'in', workorder_ids)]}}

    def _check_validation_process(self, cr, uid, reallocate_qty, real_product_qty):
        if real_product_qty < 0.0:
            raise osv.except_osv(_('Product Quantity not found!'), _('Product Quantity is not available. \n You should run scheduler to generate purchase order from Warehouse>Schedulers>Run Schedulers'))
        return True

    def to_reallocate_qty(self, cr, uid, ids, context=None):
        """
        - Process
            - Warning raise, Validation check for Re-Allocate qty,
            - update according work-order process move,
            - create new work-order move and attached to next stage if process goes to finished.
        """
        context = context or {}
        production_obj = self.pool.get('mrp.production')
        rejected_mv_obj = self.pool.get('stock.moves.rejection')
        process_move = self.pool.get('stock.moves.workorder')

        wizard_rec = self.browse(cr, uid, ids[0])
        current_rjctd_wrkorder_id = context and context.get('active_id', False) or False
        next_workorder_id = wizard_rec.next_stage_workorder_id.id
        reallocate_qty = wizard_rec.total_qty
        real_product_qty = wizard_rec.product_id.qty_available

        #check validation process to check for stock avaibility.
        self._check_validation_process(cr, uid, reallocate_qty, real_product_qty)

        # to write old rejected process moves to re-allocated
        if current_rjctd_wrkorder_id:
            rejected_mv_obj.write(cr, uid, current_rjctd_wrkorder_id, {'is_reallocate':True,'reallocate_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})

        # create new process move of next stage if work-order available.
        if next_workorder_id:
            res = production_obj._create_process_dict(cr, uid, wizard_rec.process_move_id.move_id, next_workorder_id)
            res.update({'total_qty':reallocate_qty, 'prodlot_id':False})
            process_move.create(cr, uid, res, context=context)

        return True

reallocate_rejected_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
