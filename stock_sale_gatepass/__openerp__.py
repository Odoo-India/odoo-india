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
    'name' : 'Sales Delivery Gatepass',
    'version' : '1.0',
    'author' : 'OpenERP SA',
    'sequence': 110,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Delivery Order link on Delivery Gatepass',
    'description' : """
Process delivery of goods via Gatepass
==========================================
This module lets you choose the delivery order on the gatepass to deliver the goods of company's sales via gatepass. This way you can automate the pickings of returnable products such as containers etc.

Gatepass with Sales Delivery
-------------------------------
When the goods are delivered to customers through gatepass, you can create gatepass of type sales delivery. While selecting the delivery order on gatepass, OpenERP will automatically fill the partner and product information based on the selected delivery order.

Gatepass with Returnable Sales Delivery
----------------------------------------------
When the goods are delivered in containers and if the containers are to be taken back from customers, you can create gatepass of type returnable delivery. While processing the products out for the delivery, you should put them in one pack to track the container. Once this gatepass is confirmed, OpenERP will automatically create incoming shipment for the containers that are coming back on the same gatepass.
""",
    'depends' : ['l10n_in_base', 'stock', 'stock_gatepass', 'product_container_tracking'],
    'data' : [
        'stock_sale_gatepass_view.xml',
    ],

    'demo': [],

    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
