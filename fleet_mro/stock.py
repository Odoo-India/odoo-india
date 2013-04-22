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

from openerp.osv import fields, osv

class stock_location(osv.Model):
    _inherit = 'stock.location'

    _columns = {
        'workshop': fields.boolean('Workshop'),
    }

stock_location()

class stock_warehouse(osv.Model):
    _inherit = "stock.warehouse"
    _columns = {
        'lot_workshop_id': fields.many2one('stock.location', 'Location Workshop', required=True),
    }

stock_warehouse()

class stock_picking(osv.Model):
    _inherit = "stock.picking"

    _columns = {
        'workshop_id': fields.many2one('stock.warehouse', 'Workshop'),
    }

    def _default_workshop_id(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.warehouse_id and user.warehouse_id.id or False

    _defaults = {
        'workshop_id': _default_workshop_id,
    }

stock_picking()

class stock_picking_in(osv.Model):
    _name = "stock.picking.in"
    _inherit = "stock.picking.in"

    _columns = {
        'workshop_id': fields.many2one('stock.warehouse', 'Workshop'),
    }

    def _default_workshop_id(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.warehouse_id and user.warehouse_id.id or False

    _defaults = {
        'workshop_id': _default_workshop_id,
    }

stock_picking_in()

class stock_picking_out(osv.Model):
    _name = "stock.picking.out"
    _inherit = "stock.picking.out"

    _columns = {
        'workshop_id': fields.many2one('stock.warehouse', 'Workshop'),
    }

    def _default_workshop_id(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.warehouse_id and user.warehouse_id.id or False

    _defaults = {
        'workshop_id': _default_workshop_id,
    }

stock_picking_out()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
