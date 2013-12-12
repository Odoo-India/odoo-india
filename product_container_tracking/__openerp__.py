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
    'name' : 'Product Container Tracking',
    'version' : '1.0',
    'author' : 'OpenERP S.A.',
    'sequence': 110,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Tracking the containers in warehouse',
    'description' : """
Tracking the containers in warehouse
==========================
Useful to track container which comes with product delivery as we have to return container back to the suppliers
e.g. Oxygen Gas delivered in Bottle, we have to return that bottle once the gas consumed

* Define product as container (e.g. Bottle)
* Select container in products (e.g. Oxygen)
* Track containers with serial once issued with in company 
* return container back to the suppliers with gatepass
""",
    'depends' : ['product_container', 'stock_serial_tracking'],
    'data' : [
        
    ],
    'update_xml' : [
        'product_container_tracking_view.xml'
    ],

    'demo': [],
    'images': [],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
