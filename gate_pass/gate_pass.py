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
from openerp.tools.translate import _

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

stock_picking()

class stock_picking_in(osv.Model):
    _inherit = "stock.picking.in"
    _table = "stock_picking"

    _columns = {
        'series':fields.selection(SERIES, 'Series'),
        'gate_pass_type':fields.selection(GATE_PASS_TYPE, 'Type'),
        'gate_pass_id': fields.many2one('gate.pass', 'Gate Pass'),
    }

    def create(self, cr, uid, vals, context=None):
        gate_pass_obj = self.pool.get('gate.pass')
        move_obj = self.pool.get('stock.move')
        value = dict(partner_id = vals.get('partner_id'))
        gate_pass_id = gate_pass_obj.create(cr, uid, value, context=context)
        vals['gate_pass_id'] = gate_pass_id
        res = super(stock_picking_in, self).create(cr, uid, vals, context=context)
        gate_pass_obj.write(cr, uid, gate_pass_id, {'picking_id': res}, context=context)
        move_lines = self.browse(cr, uid, res, context=context).move_lines
        for move in move_lines:
            move_obj.write(cr, uid, [move.id], {'gate_pass_id': gate_pass_id}, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(stock_picking_in, self).write(cr, uid, ids, vals, context=context)
        move_obj = self.pool.get('stock.move')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for picking in self.browse(cr, uid, ids, context=context):
            gate_pass_id = picking.gate_pass_id.id
            for move in picking.move_lines:
                move_obj.write(cr, uid, [move.id], {'gate_pass_id': gate_pass_id}, context=context)
        return res

stock_picking_in()

class stock_picking_out(osv.Model):
    _inherit = "stock.picking.out"
    _table = "stock_picking"

    _columns = {
        'series':fields.selection(SERIES, 'Series'),
        'gate_pass_type':fields.selection(GATE_PASS_TYPE, 'Type'),
        'gate_pass_id': fields.many2one('gate.pass', 'Gate Pass'),
    }

    def create(self, cr, uid, vals, context=None):
        gate_pass_obj = self.pool.get('gate.pass')
        move_obj = self.pool.get('stock.move')
        value = dict(partner_id = vals.get('partner_id'))
        gate_pass_id = gate_pass_obj.create(cr, uid, value, context=context)
        vals['gate_pass_id'] = gate_pass_id
        res = super(stock_picking_out, self).create(cr, uid, vals, context=context)
        gate_pass_obj.write(cr, uid, gate_pass_id, {'picking_id': res}, context=context)
        move_lines = self.browse(cr, uid, res, context=context).move_lines
        for move in move_lines:
            move_obj.write(cr, uid, [move.id], {'gate_pass_id': gate_pass_id}, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(stock_picking_out, self).write(cr, uid, ids, vals, context=context)
        move_obj = self.pool.get('stock.move')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for picking in self.browse(cr, uid, ids, context=context):
            gate_pass_id = picking.gate_pass_id.id
            for move in picking.move_lines:
                move_obj.write(cr, uid, [move.id], {'gate_pass_id': gate_pass_id}, context=context)
        return res


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

    _columns = {
        'name': fields.char('Name', size=256),
        'gate_pass_no': fields.char('Gate Pass No', size=256, required=True),
        'picking_id': fields.many2one('stock.picking', 'Picking'),
        'series':fields.related('picking_id', 'series', type='selection', selection=SERIES, string='Series', store=True),
        'gate_pass_type':fields.related('picking_id', 'gate_pass_type', type='selection', selection=GATE_PASS_TYPE, string='Type', store=True),
        'date': fields.datetime('Gate Pass Date', required=True),
        'partner_id':fields.many2one('res.partner', 'Supplier'),
        'department_id': fields.many2one('stock.location', 'Department', required=True),
        'indent_id': fields.many2one('indent.indent', 'Indent'),
        'move_lines': fields.one2many('stock.move', 'gate_pass_id', 'Products'),
        'description': fields.text('Remarks'),
    }

    def _default_stock_location(self, cr, uid, context=None):
        stock_location = self.pool.get('ir.model.data').get_object(cr, uid, 'stock', 'stock_location_stock')
        return stock_location.id

    _defaults = {
        'gate_pass_no': lambda obj, cr, uid, context:obj.pool.get('ir.sequence').get(cr, uid, 'gate.pass'),
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'series': 'repair',
        'gate_pass_type': 'foc',
        'department_id': _default_stock_location,
    }

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res
        # name_get may receive int id instead of an id list
        if isinstance(ids, (int, long)):
            ids = [ids]

        return [(gatepass.id, gatepass.gate_pass_no) for gatepass in self.browse(cr, uid , ids, context=context)]

gate_pass()

class stock_move(osv.Model):
    _inherit = 'stock.move'

    _columns = {
        'gate_pass_id':fields.many2one('gate.pass', 'Gate Pass'),
    }

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
