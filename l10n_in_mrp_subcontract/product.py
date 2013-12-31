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

class product_product(osv.osv):
    _inherit = 'product.product'

    def _get_p_uom_id(self, cr, uid, *args):
        cr.execute('select id from product_uom order by id limit 1')
        res = cr.fetchone()
        return res and res[0] or False

    _columns = {
        'p_coefficient': fields.float('Purchase Coefficient'),
        'p_uom_id': fields.many2one('product.uom','Purchase UoM',required=True),
    }
    _defaults = {
        'type':'product',
        'p_coefficient':1.0,
        'p_uom_id':_get_p_uom_id
    }

    #Thats depends on industry
#    def _manufacture_mto_produce(self, cr, uid, ids, context=None):
#        """
#        -Process
#            -Configuration
#                Manufacture product, always configure as "Make to Order".
#        """
#        for product in self.browse(cr, uid, ids, context=context):
#            if product.supply_method == 'produce' and product.procure_method == "make_to_stock":
#                return False
#        return True
#
#    _constraints = [
#        (_manufacture_mto_produce, '\nWrong Configuration !!!.\n Manufacture product, always configure as "Make to Order"', ['procure_method']),
#    ]

product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
