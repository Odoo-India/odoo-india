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

from openerp.osv import fields, osv, orm
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class process_qty_to_update_reject(osv.osv_memory):
    _name = "process.qty.to.update.reject"
    _description = "Process Quantity To Accept or Rejection Wizard"

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
        already_rejected_qty = context and context.get('already_rejected_qty', 0.0) or 0.0
        res = super(process_qty_to_update_reject, self).default_get(cr, uid, fields, context=context)

        if 'process_move_id' in fields:
            res.update({'process_move_id': process_move_id})
        if 'product_id' in fields:
            res.update({'product_id': product_id})
        if 'total_qty' in fields:
            res.update({'total_qty': total_qty})
        if 'process_qty' in fields:
            res.update({'process_qty': process_qty})
        if 'already_rejected_qty' in fields:
            res.update({'already_rejected_qty': already_rejected_qty})
        if 'rejected_qty' in fields:
            res.update({'rejected_qty': 0.0})
        return res

    _columns = {
        'process_move_id':fields.many2one('stock.moves.workorder', 'WorkOrder Move'),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'total_qty': fields.float('Total Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'process_qty': fields.float('Process Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'already_rejected_qty': fields.float('Already Reject Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'rejected_qty': fields.float('Reject Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'rejected_location_id': fields.many2one('stock.location', 'Rejected Location', required=True),
        'reason': fields.text('Reason'),
    }

    def _check_validation_reject_qty(self, cr, uid, total_qty, rejected_qty):
        """
        - Process
            - Warning raise, if rejected qty > total qty or rejected qty < 0
        """
        if rejected_qty <= 0.0:
            raise osv.except_osv(_('Warning!'), _('Provide proper value of rejected qty(%s)'%(rejected_qty)))
        if rejected_qty > total_qty:
            raise osv.except_osv(_('Rejected Qty over the limit!'), _('Rejected Qty(%s) greater then In Process Qty(%s)'%(rejected_qty, total_qty)))
        return True

    def _create_rejection_mv_dict(self, cr, uid, wizard_rec, context=None):
        """
        -Process
            -all related parameteres needs to generate rejected moves
            -call action scrap to generate auto rejected move also from work-order to actual production order
        -Return
            - rejection move dictonary
        """

        move_obj = self.pool.get('stock.move')
        rejected_location_id = wizard_rec.rejected_location_id.id
        rejected_qty = wizard_rec.rejected_qty
        rejected_from_process_move_id = wizard_rec.process_move_id.id
        workorder_id = wizard_rec.process_move_id.workorder_id.id
        name = wizard_rec.process_move_id.move_id.name
        real_move_from_reject = wizard_rec.process_move_id.move_id.id
        reason= wizard_rec.reason
        product_id = wizard_rec.process_move_id.move_id.product_id and wizard_rec.process_move_id.move_id.product_id.id or False

        #call here action scrap to generate auto rejected move also from work-order to actual production order
        res = move_obj.action_scrap(cr, uid, [real_move_from_reject], rejected_qty, rejected_location_id, context=context)
        rj_move_dict = {
                        'name': name + ':Rejected:'+ str(rejected_qty),
                        'rejected_workorder_id': workorder_id,
                        'move_id': res and res[0] or False,#Todo Create New scrap moves
                        'rejected_location_id': rejected_location_id,
                        'rejected_from_process_move_id': rejected_from_process_move_id,
                        'product_id': product_id,
                        'rejected_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'rejected_qty': rejected_qty,
                        'reason': reason,
                        'state': 'rejected',
                        }
        return rj_move_dict

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

    def to_reject_qty(self, cr, uid, ids, context=None):
        """
        - Process
            - Warning raise, Validation check for rejected qty
            - update according workorder process move
        """
        context = context or {}
        wizard_rec = self.browse(cr, uid, ids[0])
        total_qty = wizard_rec.total_qty
        already_rejected_qty = wizard_rec.already_rejected_qty
        rejected_qty = wizard_rec.rejected_qty
        process_qty = wizard_rec.process_qty

        self._check_validation_reject_qty(cr, uid, process_qty, rejected_qty)
        updt_prcs_mve = {}
        if process_qty == rejected_qty:
            updt_prcs_mve.update({
                                  'state':'finished',
                                  'rejected_qty': already_rejected_qty + rejected_qty,
                                  'process_qty': process_qty - rejected_qty,
                                  'end_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                  })
        else:
            updt_prcs_mve.update({
                                  'state':'in_progress',
                                  'rejected_qty': already_rejected_qty + rejected_qty,
                                  'process_qty': process_qty - rejected_qty
                                  })
        #create rejection move and attach to work-order
        self._create_move_of_rejection(cr, uid, wizard_rec, context=context)
        #update current record
        wizard_rec.process_move_id.write(updt_prcs_mve)
        return True

process_qty_to_update_reject()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: