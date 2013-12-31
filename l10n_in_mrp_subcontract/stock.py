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

from openerp.osv import osv,fields

class stock_move(osv.osv):
    """
    This field used only for hide Serial split wizard after all moves goes into the work-order
    """
    _inherit = 'stock.move'
    _columns = {
        'moves_to_workorder': fields.boolean('Raw Material Move To Work-Center?')
    }

    def _prepare_chained_picking(self, cr, uid, picking_name, picking, picking_type, moves_todo, context=None):
        """Prepare the definition (values) to create a new chained picking.

           :param str picking_name: desired new picking name
           :param browse_record picking: source picking (being chained to)
           :param str picking_type: desired new picking type
           :param list moves_todo: specification of the stock moves to be later included in this
               picking, in the form::

                   [[move, (dest_location, auto_packing, chained_delay, chained_journal,
                                  chained_company_id, chained_picking_type)],
                    ...
                   ]

               See also :meth:`stock_location.chained_location_get`.
        -Our Process
            - To attach purchase order with in type chain location
        """
        res = super(stock_move, self)._prepare_chained_picking(cr, uid, picking_name, picking, picking_type, moves_todo, context=context)
        if picking_type == 'internal':
            if picking.purchase_id:
                res.update({'purchase_id': picking.purchase_id.id})
        return res

stock_move()


class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
        'service_order': fields.boolean('Service Order'),
        'workorder_id':  fields.many2one('mrp.production.workcenter.line','Work-Order')
    }
stock_picking()

class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    _columns = {
        'service_order': fields.boolean('Service Order'),
        'workorder_id':  fields.many2one('mrp.production.workcenter.line','Work-Order')
    }
stock_picking_out()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
