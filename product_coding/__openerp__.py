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
    'name' : 'Product Coding',
    'version' : '1.0',
    'author' : 'OpenERP SA',
    'sequence': 120,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Product Coding',
    'description' : """
Autogeneration of internal reference of a product.
===================================================
An automatic Internal Reference of the product is generated depending on the coding method you select on a product. Allows two ways of coding:

* Based on product categories
* Based on major and sub groups

You can also create major and sub groups of products and based on the code provided on those groups it creates an internal reference of a product by combining both.
""",
    'depends' : ['l10n_in_base', 'product'],
    'data' : [
    ],
    'update_xml' : [
        'product_coding_view.xml'
    ],

    'demo': [
    ],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

