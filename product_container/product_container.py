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

class product_ul(osv.osv):
    _inherit = "product.ul"

    _columns = {
        'container_id' : fields.many2one('product.product', 'Container Product', domain=[('container_ok','=',True)]),
    }
product_ul()

class product_product(osv.Model):
    _inherit = 'product.product'
 
    _columns = {
        'container_ok': fields.boolean('Container', help='Select this if the product will act as a container to carry other products.'),
        'container_id': fields.many2one('product.product', 'Packed In', domain=[('container_ok','=',True)])
    }
product_product()