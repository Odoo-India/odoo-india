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
    'name' : 'Store & Purchase Management',
    'version' : '1.1',
    'author' : 'OpenERP S.A.',
    'sequence': 120,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Manage warehouse and purchase, Indian localization',
    'description' : """
Store & Purchase Management, Indian localization
====================================================
A vertical to install different modules used to manage different features to control and automates various operations of Store and Warehouse.

* Indent Management
* Gate Pass Management
* Serial Number Tracking
* Product Containers
* Excise Receipts
* Freight, Insurance, Packing & Forwarding changes on Purchase Order

Indent Management
++++++++++++++++++++
Using Indent Management you can control the purchase and internal requisition to be raised by Engineer, Plant Managers or Authorised Employees within company warehouse.

When integrated with gate pass, it allows you to send products using gate pass and also keeps track of the incoming shipment from the supplier.

Gate Pass Management
+++++++++++++++++++++
Manage documents that allows gate keeper to pass the outgoing materials, products, etc. and keeps track of returning items.

You can manage returnable or non-returnable products. Its shipments associated for the gate pass are reflected based on the gate pass you choose.

Serial Number Tracking
+++++++++++++++++++++++
Allows you to track location of products with serial numbers. If the product is assigned with serial number, you can easily find current location of the product.


Product Containers
+++++++++++++++++++
When a product is configured with a container, the product is received or delivered through the container. With use of this module you can manage and track containers in which products are received or delivered. It also helps to easily manage stock and current location of containers and products of different serial number.

Excise Receipts
++++++++++++++++
Helps you to manage excise duties on the Goods Receipt. When receiving products for a purchase order, the system will automatically create goods receipt based on the duties and other charges applicable. Inventory update is done after goods receipt.


Freight, Insurance, Packing & Forwarding changes on Purchase Order
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
This module allows you to manage different charges on Purchase orders & Supplier invoices.

* Freight
* Packaging & Forwarding
* Insurance
* Mill Delivery

You can manage calculation of various charges by different options like Fix Amount, Percentage, Per Unit, At actual, Include in Price.
""",
    'depends' : [
        'stock_indent', 
        'stock_gatepass', 
        'product_container', 
        'stock_indent_gatepass', 
        'stock_sale_gatepass', 
        'stock_serial_tracking', 
        'l10n_in_purchase',
        'l10n_in_excise_receipt'
    ],
    'data' : [
        
    ],
    'update_xml' : [
        
    ],

    'demo': [],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
