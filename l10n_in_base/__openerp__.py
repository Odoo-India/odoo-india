# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP SA (<http://openerp.com).
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
    'name' : 'Indian Localization (Unsupported)',
    'version' : '1.0',
    'author' : 'OpenERP SA',
    'sequence': 110,
    'category': 'Indian Localization',
    'website' : 'http://www.openerp.com',
    'summary' : 'Indian Localization settings',
    'description' : """
Provides the configuration for whole business suite according to indian localization.
==========================================================================================
Here, you can configure the whole business suite based on your requirements. You'll be provided different configuration options in the Settings where by only selecting some booleans you will be able to install several modules and apply access rights in just one go.

Features
+++++++++++++++
Product Features
--------------------
Manage and track containers in which products are delivered to the customers and to be taken back from customers. You can also configure a container to carry more than one quantity of product by selecting the container product in packaging.


Warehouse Features
------------------------
Track the current location of the product with serial numbers,also can track the current location of the product where it is lying.

Useful to manage and track containers in which products are received or delivered. Easily manage stock and current location of containers and products of different serial numbers.

Send products in repairing via creating an indent and gate pass with approvals of authority,and also keeps track of the incoming shipment of repaired products coming back from the supplier who has sent repaired product.

Sales Features
--------------------
The sales manager can prepare quotation templates for products and services, define discount etc. and a sales person can just select template while creating quotations.

* Create quotations quickly
* Provide Discounts on Templates
* Use different Pricelists and Currencies

Purchase Features
-------------------------
Allows you to manage different charges on Purchase orders & Supplier invoices used for Indian Localization.

* Freight
* Packaging & Forwarding
* Insurance
* Mill Delivery

Finance Features
------------------
Added tax category on tax which will be useful to get exact amount of tax levied on different types of services, goods, etc. (e.g. Excise, Service Tax, Cess, etc.) It also fixes the base amount calculation when children taxes are applied.

Transfer dealer discount to customer invoice when preparing invoice from warehouse.

Helps you to adjust Customer and Suppliers Invoices from the same party. You can reconcile customer and suppliers account against each other.

This module was developed by TinyERP Private Limited (OpenERP India), not supported under any contracts by OpenERP SA or TinyERP.
""",
    'depends' : ['base'],
    'data' : [
    ],
    'update_xml' : [
        'res_config_view.xml',
        'l10n_in_base_groups.xml'
    ],

    'demo': [
    ],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
