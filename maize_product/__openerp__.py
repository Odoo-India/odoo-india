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

{
    'name' : 'Maize Product',
    'version' : '0.1',
    'author' : 'OpenERP S.A.',
    'sequence': 110,
    'category': 'Product Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Managing Maize Product',
    'description' : """
This module inherits the base product module which maintains some product history data like last purchase order number, last supplier rate etc.
================================================================================================================================================================ 
""",
    'depends' : ['indent'],
    'data' : [
        'security/ir.model.access.csv',
        'product_sequence.xml',
        'product_series_data.xml',
        'product_view.xml',
        'wizard/import_product_data.xml',
        'wizard/import_product_supp_data.xml',
        'wizard/product_search_view.xml'
    ],
    'update_xml' : [],

    'demo': [],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
