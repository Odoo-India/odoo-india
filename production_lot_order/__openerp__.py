# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today Tiny SPRL (<http://tiny.be>).
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
    "name" : "Production Lot Order (Unsupported)",
    "version" : "1.0",
    "author" : "OpenERP SA",
    "website" : "http://www.openerp.com",
    "category": "Warehouse Management",
    "complexity": "easy",
    "description": """
Module to make ordering on Production Lot / Batch
=====================================================
- Apply FIFO on Production Lot / Batch.
- Add actions on dashboards.

This module was developed by TinyERP Private Limited (OpenERP India), not supported under any contracts by OpenERP SA or TinyERP.
""",        
    "depends" : ["sale_stock"],
    "update_xml" : [
        "production_lot_order_view.xml",
        ],
    "installable": True,
    "auto_install": False,
    "application": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
