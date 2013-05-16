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
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp import tools

class product_search(osv.osv_memory):
    _name = "product.search"
    _description = "Product Search"
    _columns = {
        'name' : fields.char('Product Name', size=256),
        'product_ids': fields.many2many('product.product', string='Products'),
        'type_product': fields.boolean('Stockable Product'),
        'type_consu': fields.boolean('Consumable'),
        'type_service': fields.boolean('Service'),
    }

    _defaults = {
        'type_product': True,
        'type_consu': True,
        'type_service': True,
                 }

    def onchange_name(self, cr, uid, ids, product_name, type_product, type_consu, type_service, context=None):
        """ 
            @ Check similar products on onchange event
         """
        def concat_string(type_product, type_consu, type_service):
            type_string = ''
            if type_product: type_string += "'product'"
            if type_consu: type_string += ' '+"'consu'"
            if type_service: type_string += ' '+"'service'"
            return (type_string.strip()).replace(' ',',')

        res = {'value':{'product_ids':[]}}
        if isinstance(product_name, bool) or (not product_name.strip()): return {}
        if product_name:
            product_name,merge_string, type_query, count = (product_name.strip()).split(), '', '',0
            for str_list in product_name:
                if count == 0: merge_string += "'%"+str_list.lower()+"%'"
                else: merge_string += ",'%"+str_list.lower()+"%'"
                count += 1
            if merge_string.strip():
                type_cnct_string = concat_string(type_product, type_consu, type_service)
                if not type_cnct_string: return res
                type_query = ' AND pt.type in ('+type_cnct_string+') '
                cr.execute(''' 
                            SELECT pp.id,pt.name FROM product_product pp, product_template pt
                            WHERE pt.id = pp.product_tmpl_id 
                            AND lower(complete_name) ilike ALL(array['''+merge_string+'''])''' +type_query
                            )
                res['value'].update({'product_ids': [x[0] for x in cr.fetchall()]})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
