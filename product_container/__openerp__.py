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
    'name' : 'Product Container',
    'version' : '0.1',
    'author' : 'OpenERP S.A.',
    'sequence': 110,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Managing the container products',
    'description' : """
Manage Product Container
==========================
Useful to manage and track containers in which products are delivered to the customers and to be taken back from customers.  
e.g. Oxygen Gas delivered in Bottle

* Define product as container (e.g. Bottle)
* Select container in products (e.g. Oxygen)
* Track containers on hand
* Track containers to be taken back from customers
""",
    'depends' : ['product'],
    'data' : [
        
    ],
    'update_xml' : [
        'product_container_view.xml'
    ],

    'demo': [],
    'images': ['images/container1.png', 'images/container2.png', 'images/container3.png'],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
