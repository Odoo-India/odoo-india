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
from openerp import netsvc

class stock_picking(osv.Model):
    _inherit = 'stock.picking'

    _columns = {
        'gate_pass_id': fields.many2one('stock.gatepass', 'Gate Pass'),
    }

stock_picking()

class stock_picking_in(osv.Model):
    _inherit = "stock.picking.in"

    _columns = {
        'gate_pass_id': fields.many2one('stock.gatepass', 'Gate Pass'),
    }

stock_picking_in()

class stock_picking_out(osv.Model):
    _inherit = "stock.picking.out"

    _columns = {
        'gate_pass_id': fields.many2one('stock.gatepass', 'Gate Pass'),
    }

stock_picking_out()

class gate_pass_type(osv.Model):
    _name = 'gatepass.type'
    _description = 'Gate Pass Type'

    _columns = {
        'name': fields.char('Name', size=256, select=1),
        'code': fields.char('Code', size=16, select=1),
        'approval_required': fields.boolean('Approval State'),
        'return_type': fields.selection([('return', 'Returnable'), ('non_return', 'Non-Returnable')], 'Return Type', required=True),
        'active': fields.boolean('Active')
    }

    _defaults = {
        'active': True,
        'return_type': 'return'
    }

gate_pass_type()

class stock_gatepass(osv.Model):
    _name = 'stock.gatepass'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Gate Pass'
    _order = "name desc"

    def _get_total_amount(self, cr, uid, ids, name, args, context=None):
        result = {}
        for gatepass in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in gatepass.line_ids:
                total += (line.product_qty * line.price_unit)
            result[gatepass.id] = total
        return result

    def onchange_type(self, cr, uid, ids, type_id=False):
        result = {}
        if type_id:
            type = self.pool.get('gatepass.type').browse(cr, uid, type_id)
            result['return_type'] = type.return_type
            result['approval_required'] = type.approval_required
        return {'value': result}

    _columns = {
        'name': fields.char('Name', size=256, readonly=True, states={'draft': [('readonly', False)]}),
        'driver_id': fields.many2one('res.partner', 'Driver', readonly=True, states={'draft': [('readonly', False)]}),
        'person_id': fields.many2one('res.partner', 'Delivery Person', readonly=True, states={'draft': [('readonly', False)]}),
        'user_id': fields.many2one('res.users', 'User', required=True, readonly=True),
        'date': fields.datetime('Create Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'approve_date': fields.datetime('Approve Date', readonly=True, states={'draft': [('readonly', False)]}),
        'type_id': fields.many2one('gatepass.type', 'Type', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'partner_id':fields.many2one('res.partner', 'Supplier', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'line_ids': fields.one2many('stock.gatepass.line', 'gatepass_id', 'Products', readonly=True, states={'draft': [('readonly', False)]}),
        'description': fields.text('Remarks', readonly=True, states={'draft': [('readonly', False)]}),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'amount_total': fields.function(_get_total_amount, type="float", string='Total', store=True, readonly=True),
        'location_id': fields.many2one('stock.location', 'Source Location', readonly=True, states={'draft': [('readonly', False)]}),
        'state':fields.selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('pending', 'Pending'), ('done', 'Done')], 'State', readonly=True),
        'return_type': fields.selection([('return', 'Returnable'), ('non_return', 'Non Returnable')], 'Return Type'),
        'out_picking_id': fields.many2one('stock.picking.out', 'Delivery Order', readonly=True, states={'draft': [('readonly', False)]}),
        'in_picking_id': fields.many2one('stock.picking.in', 'Incoming Shipment', readonly=True, states={'draft': [('readonly', False)]}),
        'approval_required': fields.boolean('Approval State', readonly=True, states={'draft': [('readonly', False)]}),
    }

    _defaults = {
        'state': 'draft',
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'gate.pass', context=c),
        'user_id': lambda self, cr, uid, context: uid,
    }

    def create_delivery_order(self, cr, uid, ids, context=None):
        picking_out_obj = self.pool.get('stock.picking.out')
        move_obj = self.pool.get('stock.move')
        picking_ids = []
        for gatepass in self.browse(cr, uid, ids, context=context):
            vals = {
                'partner_id': gatepass.partner_id.id,
                'gate_pass_id': gatepass.id,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'origin': gatepass.name,
                'type': 'out',
            }
            out_picking_id = picking_out_obj.create(cr, uid, vals, context=context)
            picking_ids.append(out_picking_id)
            self.write(cr, uid, [gatepass.id], {'out_picking_id': out_picking_id}, context=context)
            for line in gatepass.line_ids:
                result = dict(name=line.product_id.name, 
                    product_id=line.product_id.id, 
                    product_qty=line.product_qty, 
                    product_uom=line.uom_id.id, 
                    location_id=line.location_id.id, 
                    location_dest_id=line.location_dest_id.id, 
                    picking_id=out_picking_id,
                    prodlot_id = line.prodlot_id.id
                )
                move_obj.create(cr, uid, result, context=context)
        return picking_ids

    def create_incoming_shipment(self, cr, uid, ids, context=None):
        picking_in_obj = self.pool.get('stock.picking.in')
        move_obj = self.pool.get('stock.move')
        picking_ids = []
        for gatepass in self.browse(cr, uid, ids, context=context):
            vals = {
                'partner_id': gatepass.partner_id.id,
                'gate_pass_id': gatepass.id,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'origin': gatepass.name,
                'type': 'in',
            }
            in_picking_id = picking_in_obj.create(cr, uid, vals, context=context)
            picking_ids.append(in_picking_id)
            self.write(cr, uid, [gatepass.id], {'in_picking_id': in_picking_id}, context=context)
            for line in gatepass.line_ids:
                result = dict(name=line.product_id.name, 
                    product_id=line.product_id.id, 
                    product_qty=line.product_qty, 
                    product_uom=line.uom_id.id, 
                    location_id=line.location_dest_id.id, 
                    location_dest_id=line.location_id.id,
                    picking_id=in_picking_id,
                    prodlot_id = line.prodlot_id.id
                )
                move_obj.create(cr, uid, result, context=context)
        return picking_ids

    def open_delivery_order(self, cr, uid, ids, context=None):
        out_picking_id = self.browse(cr, uid, ids[0], context=context).out_picking_id.id
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_picking_out_form')
        result = {
            'name': _('Delivery Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': res and res[1] or False,
            'res_model': 'stock.picking.out',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': out_picking_id,
        }
        return result

    def open_incoming_shipment(self, cr, uid, ids, context=None):
        in_picking_id = self.browse(cr, uid, ids[0], context=context).in_picking_id.id
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_picking_in_form')
        result = {
            'name': _('Incoming Shipment'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': res and res[1] or False,
            'res_model': 'stock.picking.in',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': in_picking_id,
        }
        return result

    def check_returnable(self, cr, uid, ids, context=None):
        for gp in self.browse(cr, uid, ids, context=context):
            if gp.type_id.return_type == 'return':
                return True
        return False

    def action_confirm(self, cr, uid, ids, context=None):
        picking_ids = self.create_delivery_order(cr, uid, ids, context=context)
        picking_obj = self.pool.get('stock.picking')
        wf_service = netsvc.LocalService("workflow")
        seq_obj = self.pool.get('ir.sequence')
        for gatepass in self.browse(cr, uid, ids, context=context):
            if not gatepass.line_ids:
                raise osv.except_osv(_('Warning!'),_('You cannot confirm a gate pass which has no line.'))
            if gatepass.type_id and gatepass.type_id.return_type == 'return':
                self.create_incoming_shipment(cr, uid, [gatepass.id], context=context)
            name = seq_obj.get(cr, uid, 'stock.gatepass')
            self.write(cr, uid, [gatepass.id], {'state': 'confirm', 'name': name, 'approve_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        for picking in picking_ids:
            wf_service.trg_validate(uid, 'stock.picking', picking, 'button_confirm', cr)
            picking_obj.action_move(cr, uid, [picking], context=context)
            wf_service.trg_validate(uid, 'stock.picking', picking, 'button_done', cr)

        return True

    def action_picking_create(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        picking = self.browse(cr, uid, ids[0], context=context).in_picking_id.id
        self.pool.get('stock.picking.in').write(cr, uid, [picking], {'gate_pass_id': ids[0]}, context=context)
        self.write(cr, uid, ids, {'state': 'pending'}, context=context)
        return picking

stock_gatepass()

class stock_gatepass_line(osv.Model):
    _name = 'stock.gatepass.line'
    _description = 'Gate Pass Lines'

    def _get_subtotal_amount(self, cr, uid, ids, name, args, context=None):
        result = {}
        for gp in self.browse(cr, uid, ids, context=context):
            result[gp.id] = (gp.product_qty * gp.price_unit)
        return result

    _columns = {
        'name': fields.text('Name', required=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True),
        'gatepass_id': fields.many2one('stock.gatepass', 'Gate Pass', required=True, ondelete='cascade'),
        'product_qty': fields.float('Quantity', required=True),
        'location_id': fields.many2one('stock.location', 'Source Location', required=True),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', required=True),
        'price_unit': fields.float('Approx. Value'),
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial #', domain="[('product_id','=',product_id)]"),
     }

    def _get_uom_id(self, cr, uid, *args):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')
        return result and result[1] or False

    def _default_stock_location(self, cr, uid, context=None):
        stock_location = self.pool.get('ir.model.data').get_object(cr, uid, 'stock', 'stock_location_stock')
        return stock_location.id

    _defaults = {
        'product_qty': 1,
        'uom_id': _get_uom_id,
        'location_id': _default_stock_location,
        'location_dest_id': _default_stock_location,
    }

    def onchange_product_id(self, cr, uid, ids, product_id=False):
        result = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            result = dict(value=dict(name=product.name, uom_id=product.uom_id and product.uom_id.id or False, price_unit=product.list_price))
        return result

stock_gatepass_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
