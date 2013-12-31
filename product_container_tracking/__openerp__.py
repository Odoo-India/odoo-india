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
    'author' : 'OpenERP SA',
    'sequence': 110,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Tracking the containers in warehouse',
    'description' : """
Track the product containers in warehouse
====================================================== 
Useful to manage and track containers in which products are received or delivered. Easily manage stock and current location of containers and products of different serial numbers.

Key Features
+++++++++++++++++
When a product is configured with a container, the product is received or delivered through the container. With use of this module, you can create incoming or outgoing movements of the container along with the product, so you can easily track the container in the warehouse.

* Track containers with serial number once issued
* Get exact location of containers using serial numbers
* Get exact containers on hand by locations
* Return containers back to the suppliers or take back containers from customers

How it works?
++++++++++++++
Container for single product
------------------------------
* Define product as container (e.g. Cylinder)
* Select container in products (e.g. Oxygen Gas)
* Receive incoming shipment of Oxygen Gas and Assign serial numbers (e.g. 001) for Oxygen Gas while processing it
* OpenERP will automatically create an Incoming move for Cylinder with serial number (i.e. 001)

Container for multiple product
----------------------------------
* Define product as container (e.g. Box 30x40x60)
* Select container in packaging for product Mouse
* Select 15 quantity of products and packaging in product sales tab
* Receive incoming shipment of 15 Mouse and Assign serial numbers a0001 for Mouse and select pack 00000017 to indicate that the products are received in the same pack.
* OpenERP will automatically create a serial number 00000017 for 1 qty of Box 30x40x60 and will assign 00000017 as a container serial number for a0001
""",
    'depends' : ['l10n_in_base', 'product_container', 'stock_serial_tracking'],
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
