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
    }

    def onchange_name(self, cr, uid, ids, product_name, context=None):
        """ 
            @ Check similar products on onchange event
         """
        res = {'value':{'product_ids':[]}}
        if isinstance(product_name, bool): return res
        if not product_name.strip(): return res
        if product_name:
            product_name,merge_string, count = (product_name.strip()).split(), '', 0
            for str_list in product_name:
                if count == 0: merge_string += '%'+str_list+'%'
                else: merge_string += '|%'+str_list+'%'
                count += 1
            if merge_string.strip():
                cr.execute(""" 
                            SELECT id FROM product_product 
                            WHERE lower(desc2) SIMILAR TO %s
                            OR lower(desc3) SIMILAR TO %s
                            OR lower(desc4) SIMILAR TO %s
                        """,(merge_string,merge_string,merge_string))
                res['value'].update({'product_ids': [x[0] for x in cr.fetchall()]})
        return res

#    def action_check_availability(self, cr, uid, ids, context=None):
#        """ 
#            @ Check similar products on button click
#         """
#        product_name = self.browse(cr, uid, ids[0]).name
#        avail_ids = []
#        if product_name:
#            product_name,merge_string, count = (product_name.strip()).split(), '', 0
#            for str_list in product_name:
#                if count == 0: merge_string += '%'+str_list+'%'
#                else: merge_string += '|%'+str_list+'%'
#                count += 1
#            if merge_string.strip():
#                cr.execute(""" 
#                            SELECT id FROM product_product 
#                            WHERE lower(desc2) SIMILAR TO %s
#                            OR lower(desc3) SIMILAR TO %s
#                            OR lower(desc4) SIMILAR TO %s
#                        """,(merge_string,merge_string,merge_string))
#                avail_ids = [x[0] for x in cr.fetchall()]
#        if avail_ids: self.write(cr ,uid, ids[0],{'product_ids': avail_ids}, context)
#        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
