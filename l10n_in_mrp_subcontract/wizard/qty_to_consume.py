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

class qty_to_consume(osv.osv_memory):
    _name = "qty.to.consume"
    _description = "Quantity Consume Wizard"

    def default_get(self, cr, uid, fields, context):
        """
        -Process
            -Set default values of 
                -Active_id
                -Product
                -Total Qty
        """
        process_move_id = context and context.get('active_id', False) or False
        total_qty = context and context.get('total_qty', 0.0) or 0.0
        product_id = context and context.get('product_id', False) or False
        process_qty = context and context.get('process_qty', 0.0) or 0.0
        res = super(qty_to_consume, self).default_get(cr, uid, fields, context=context)

        if 'process_move_id' in fields:
            res.update({'process_move_id': process_move_id})
        if 'product_id' in fields:
            res.update({'product_id': product_id})
        if 'total_qty' in fields:
            res.update({'total_qty': total_qty})
        if 'process_qty' in fields:
            res.update({'process_qty': process_qty})
        if 'consume_qty' in fields:
            res.update({'consume_qty': 0.0})
        return res

    _columns = {
        'process_move_id':fields.many2one('stock.moves.workorder', 'WorkOrder Move'),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'total_qty': fields.float('Total Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'process_qty': fields.float('Process Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'consume_qty': fields.float('Consume Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
    }

    def _check_validation_consume_qty(self, cr, uid, total_qty, consume_qty):
        """
        - Process
            - Warning raise, if consume_qty > total qty or consume_qty  < 0
        """
        if consume_qty <= 0.0:
            raise osv.except_osv(_('Warning!'), _('Provide proper value of consume qty(%s)'%(consume_qty)))
        if consume_qty > total_qty:
            raise osv.except_osv(_('Consume Qty over the limit!'), _('Consume Qty(%s) greater then In Process Qty(%s)'%(consume_qty, total_qty)))
        return True

    def _create_move_of_rejection(self,cr, uid, wizard_rec, context=None):
        """
        -Process
            -call rejection move dictonary function
            -process on dictonary which comes from rejction function
        -Return
            -Result : created rejected move and attached to work-order
            -True
        """
        context = context or {}
        rejection_obj = self.pool.get('stock.moves.rejection')
        rejection_obj.create(cr, uid, self._create_rejection_mv_dict(cr, uid, wizard_rec, context), context=context)
        return True

    def to_consume_qty(self, cr, uid, ids, context=None):
        """
        - Process
            - Warning raise, Validation check for rejected qty
            - update according workorder process move
        """
        context = context or {}
        production_obj = self.pool.get('mrp.production')
        process_move = self.pool.get('stock.moves.workorder')
        move_obj =  self.pool.get('stock.move')

        wizard_rec = self.browse(cr, uid, ids[0])
        total_qty = wizard_rec.total_qty
        consume_qty = wizard_rec.consume_qty
        process_qty = wizard_rec.process_qty
        current_workorder_id = wizard_rec.process_move_id and wizard_rec.process_move_id.workorder_id and wizard_rec.process_move_id.workorder_id.id or False
        move_id = wizard_rec.process_move_id and wizard_rec.process_move_id.move_id and wizard_rec.process_move_id.move_id.id or False

        self._check_validation_consume_qty(cr, uid, process_qty, consume_qty)
        updt_prcs_mve = {}
        if process_qty == consume_qty:
            updt_prcs_mve.update({
                                  'state':'consumed',
                                  'process_qty': process_qty - consume_qty,
                                  'end_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                  'accepted_qty': consume_qty,
                                  })
        else:
            updt_prcs_mve.update({
                                  'state':'in_progress',
                                  'process_qty': process_qty - consume_qty,
                                  'total_qty': total_qty - consume_qty
                                  })
            if current_workorder_id:
                res = production_obj._create_process_dict(cr, uid, wizard_rec.process_move_id.move_id, current_workorder_id)
                res.update({
                            'total_qty':consume_qty,
                            'state':'consumed',
                            'accepted_qty': consume_qty,
                            'start_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            'end_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                            })
                process_move.create(cr, uid, res, context=context)

        #consumed qty
        move_id and move_obj.action_consume(cr, uid, [move_id], consume_qty, context=context)
        #update current record
        wizard_rec.process_move_id.write(updt_prcs_mve)
        return True

qty_to_consume()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: