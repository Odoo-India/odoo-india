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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from openerp.osv.orm import browse_record

SERIES = [
    ('repair', 'Repair'),
    ('purchase', 'Purchase'),
    ('store', 'Store')
]

GATE_PASS_TYPE = [
    ('foc', 'Free Of Cost'),
    ('chargeable', 'Chargeable'),
    ('sample', 'Sample'),
    ('contract', 'Contract'),
    ('cash', 'Cash'),
    ('Loan', 'Loan')
]

class stock_picking(osv.Model):
    _inherit = 'stock.picking'

    _columns = {
        'series':fields.selection(SERIES, 'Series'),
        'gate_pass_type':fields.selection(GATE_PASS_TYPE, 'Type'),
        'gate_pass_id': fields.many2one('gate.pass', 'Gate Pass'),
    }

    def create_gate_pass(self, cr, uid, ids, context=None):
        gate_pass_obj = self.pool.get('gate.pass')
        gate_pass_line_obj = self.pool.get('gate.pass.lines')
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.type == 'out':
                gate_pass_id = gate_pass_obj.create(cr, uid, {'partner_id': picking.partner_id.id, 'picking_id': picking.id}, context=context)
                self.write(cr, uid, [picking.id], {'gate_pass_id': gate_pass_id}, context=context)
                for move in picking.move_lines:
                    vals = dict(product_id = move.product_id.id, product_uom_qty = move.product_qty, pen_qty = move.product_id.qty_available, gps_qty=move.product_qty, app_rate = move.product_id.standard_price, product_uom = move.product_uom.id, name = move.product_id.name, gate_pass_id = gate_pass_id)
                    gate_pass_line_obj.create(cr, uid, vals, context=context)
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms picking.
        @return: True
        """
        self.create_gate_pass(cr, uid, ids, context=context)
        picking = False
        pickings = self.browse(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'confirmed'})
        todo = []
        for picking in pickings:
            for r in picking.move_lines:
                if r.state == 'draft':
                    todo.append(r.id)
        todo = self.action_explode(cr, uid, todo, context)
        if len(todo):
            picking = self.pool.get('stock.move').action_confirm(cr, uid, todo, context=context)
        if isinstance(picking, browse_record):
            picking = picking.id
        gate_pass_id = self.browse(cr, uid, ids[0], context=context).gate_pass_id.id
        if gate_pass_id:
            self.pool.get('gate.pass').write(cr, uid, [gate_pass_id], {'in_picking_id': picking}, context=context)
        return picking

stock_picking()

class stock_picking_in(osv.Model):
    _inherit = "stock.picking.in"
    _table = "stock_picking"

    _columns = {
        'series':fields.selection(SERIES, 'Series'),
        'gate_pass_type':fields.selection(GATE_PASS_TYPE, 'Type'),
    }

stock_picking_in()

class stock_picking_out(osv.Model):
    _inherit = "stock.picking.out"
    _table = "stock_picking"

    _columns = {
        'series':fields.selection(SERIES, 'Series'),
        'gate_pass_type':fields.selection(GATE_PASS_TYPE, 'Type'),
        'gate_pass_id': fields.many2one('gate.pass', 'Gate Pass'),
        'indent_id': fields.many2one('indent.indent', 'Indent'),
    }

    def open_gate_pass(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display gate pass of given picking ids.
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        gate_pass_id = self.browse(cr, uid, ids[0], context=context).gate_pass_id.id
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'gate_pass', 'view_gate_pass_form')
        result = {
            'name': _('Gate Passes'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': res and res[1] or False,
            'res_model': 'gate.pass',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': gate_pass_id,
        }
        return result

stock_picking_out()

class gate_pass(osv.Model):
    _name = 'gate.pass'
    _description = 'Gate Pass'

    def _get_total_amount(self, cr, uid, ids, name, args, context=None):
        result = {}
        for gatepass in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in gatepass.gate_pass_lines:
                total += line.app_value
            result[gatepass.id] = total
        return result

    _columns = {
        'name': fields.char('Name', size=256),
        'gate_pass_no': fields.char('Gate Pass No', size=256, required=True),
        'picking_id': fields.many2one('stock.picking', 'Picking'),
        'in_picking_id': fields.many2one('stock.picking', 'Incoming Shipment'),
        'series':fields.related('picking_id', 'series', type='selection', selection=SERIES, string='Series', store=True),
        'gate_pass_type':fields.related('picking_id', 'gate_pass_type', type='selection', selection=GATE_PASS_TYPE, string='Type', store=True),
        'date': fields.datetime('Gate Pass Date', required=True),
        'partner_id':fields.many2one('res.partner', 'Supplier'),
        'department_id': fields.many2one('stock.location', 'Department', required=True),
        'indent_id': fields.many2one('indent.indent', 'Indent'),
        'gate_pass_lines': fields.one2many('gate.pass.lines', 'gate_pass_id', 'Products'),
        'description': fields.text('Remarks'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'return_type': fields.selection([('Return', 'Return'), ('Non Return', 'Non Return')], 'Return Type', required=True),
        'amount_total': fields.function(_get_total_amount, type="float", string='Total', store=True),
        'state':fields.selection([('confirm','Confirm'), ('pending','Pending'), ('done','Done')], 'State', readonly=True),
    }

    def _default_stock_location(self, cr, uid, context=None):
        stock_location = self.pool.get('ir.model.data').get_object(cr, uid, 'stock', 'stock_location_stock')
        return stock_location.id

    _defaults = {
        'state': 'confirm',
        'gate_pass_no': lambda obj, cr, uid, context:obj.pool.get('ir.sequence').get(cr, uid, 'gate.pass'),
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'series': 'repair',
        'gate_pass_type': 'foc',
        'department_id': _default_stock_location,
        'return_type': 'Return',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'gate.pass', context=c)
    }

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res
        # name_get may receive int id instead of an id list
        if isinstance(ids, (int, long)):
            ids = [ids]

        return [(gatepass.id, gatepass.gate_pass_no) for gatepass in self.browse(cr, uid , ids, context=context)]

    def process_incoming_shipment(self, cr, uid, ids, context=None):
        in_picking_id = self.browse(cr, uid, ids[0], context=context).in_picking_id.id
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_picking_in_form')
        result = {
            'name': _('Incoming Shipment'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': res and res[1] or False,
            'res_model': 'stock.picking.in',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': in_picking_id,
        }
        return result

    def action_picking_create(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        picking = self.browse(cr, uid, ids[0], context=context).in_picking_id.id
        self.pool.get('stock.picking.in').write(cr, uid, [picking], {'gate_pass_id': ids[0]}, context=context)
        self.write(cr, uid, ids, {'state': 'pending'}, context=context)
        return picking

gate_pass()

class gate_pass_lines(osv.Model):
    _name = 'gate.pass.lines'
    _description = 'Gate Pass Lines'

    def _get_subtotal_amount(self, cr, uid, ids, name, args, context=None):
        result = {}
        for gatepass in self.browse(cr, uid, ids, context=context):
            result[gatepass.id] = (gatepass.product_uom_qty * gatepass.app_rate)
        return result
  
    _columns = {
         'gate_pass_id': fields.many2one('gate.pass', 'Gate Pass', required=True, ondelete='cascade'),
         'name': fields.text('Name', required=True),
         'product_id': fields.many2one('product.product', 'Product', required=True),
         'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True),
         'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True),
         'pen_qty': fields.float('Pen Qty'),
         'gps_qty': fields.float('Gps Qty'),
         'app_rate': fields.float('App Rate'),
         'app_value': fields.function(_get_subtotal_amount, type="float", string='App Value', store=True),
     }

    def _get_uom_id(self, cr, uid, *args):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')
        return result and result[1] or False

    _defaults = {
        'product_uom_qty': 1,
        'product_uom' : _get_uom_id,
    }

    def onchange_product_id(self, cr, uid, ids, product_id=False):
        result = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            result = dict(value = dict(name = product.name, product_uom = product.uom_id and product.uom_id.id or False, app_rate = product.list_price))
        return result

gate_pass_lines()

class stock_move(osv.Model):
    _inherit = 'stock.move'

    def _create_chained_picking(self, cr, uid, picking_name, picking, picking_type, moves_todo, context=None):
        picking_obj = self.pool.get('stock.picking')
        return picking_obj.create(cr, uid, self._prepare_chained_picking(cr, uid, picking_name, picking, picking_type, moves_todo, context=context))

    def create_chained_picking(self, cr, uid, moves, context=None):
        res_obj = self.pool.get('res.company')
        location_obj = self.pool.get('stock.location')
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        pickid = False
        new_moves = []
        if context is None:
            context = {}
        seq_obj = self.pool.get('ir.sequence')
        for picking, todo in self._chain_compute(cr, uid, moves, context=context).items():
            ptype = todo[0][1][5] and todo[0][1][5] or location_obj.picking_type_get(cr, uid, todo[0][0].location_dest_id, todo[0][1][0])
            if picking:
                # name of new picking according to its type
                new_pick_name = seq_obj.get(cr, uid, 'stock.picking.' + ptype)
                pickid = self._create_chained_picking(cr, uid, new_pick_name, picking, ptype, todo, context=context)
                # Need to check name of old picking because it always considers picking as "OUT" when created from Sales Order
                old_ptype = location_obj.picking_type_get(cr, uid, picking.move_lines[0].location_id, picking.move_lines[0].location_dest_id)
                if old_ptype != picking.type:
                    old_pick_name = seq_obj.get(cr, uid, 'stock.picking.' + old_ptype)
                    self.pool.get('stock.picking').write(cr, uid, [picking.id], {'name': old_pick_name, 'type': old_ptype}, context=context)
            else:
                pickid = False
            for move, (loc, dummy, delay, dummy, company_id, ptype, invoice_state) in todo:
                new_id = move_obj.copy(cr, uid, move.id, {
                    'location_id': move.location_dest_id.id,
                    'location_dest_id': loc.id,
                    'date': time.strftime('%Y-%m-%d'),
                    'picking_id': pickid,
                    'state': 'waiting',
                    'company_id': company_id or res_obj._company_default_get(cr, uid, 'stock.company', context=context)  ,
                    'move_history_ids': [],
                    'date_expected': (datetime.strptime(move.date, '%Y-%m-%d %H:%M:%S') + relativedelta(days=delay or 0)).strftime('%Y-%m-%d'),
                    'move_history_ids2': []}
                )
                move_obj.write(cr, uid, [move.id], {
                    'move_dest_id': new_id,
                    'move_history_ids': [(4, new_id)]
                })
                new_moves.append(self.browse(cr, uid, [new_id])[0])
            if pickid:
                wf_service.trg_validate(uid, 'stock.picking', pickid, 'button_confirm', cr)
        if new_moves:
            new_moves += self.create_chained_picking(cr, uid, new_moves, context)
        return new_moves, pickid


    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms stock move.
        @return: List of ids.
        """
        moves = self.browse(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'confirmed'})
        moves, picking = self.create_chained_picking(cr, uid, moves, context)
        return picking

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
