##############################################################################
#
# Copyright (c) 2010-2012 NaN Projectes de Programari Lliure, S.L.
#                         All Rights Reserved.
#                         http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

{
    "name": "Production Lot Quality Control",
    "version": "0.2",
    "author": "NaN·tic",
    "category": "Quality Control",
    "website": "http://www.nan-tic.com",
    "description": """
    Module developed for Trod y Avia, S.L.

    This module supply an infrastructure to define Quality Test that the
    Production Lots must pass in some situations. It adds a workflow to
    Production Lot.
    Adds a new simple model for Quality Test to define Triggers (a mark to
    specify when a test must be passed) a model related to product with
    one2many field which define which tests must to pass the lots of the
    product specifying the Test Template and the Trigger. In the Company there
    are a similar field and one2many to define the general tests (when a
    product is created take the default values from these values).
    In the Production Lot there are a similar model and one2many field but
    relates the Lot with a trigger and Test.

    IMPORTANT: This module without anything else do not define any Test to pass
    It will be defined in other dependant modules.
    """,
    "depends": [
        'stock',
        'nan_quality_control',
    ],
    "init_xml": [],
    "update_xml": [
        'security/security.xml',
        'quality_control_view.xml',
        'company_view.xml',
        'product_view.xml',
        'stock_view.xml',
        'prodlot_workflow.xml',
        'security/ir.model.access.csv',
    ],
    "images": [
        'images/company.png',
        'images/prodlot_form.png',
        'images/prodlot_form2.png',
        'images/prodlot_list.png',
        'images/product.png',
    ],
    "demo_xml": [
        'prodlot_quality_control_demo.xml',
    ],
    "test": [
        'test/prodlot_without_quality_control.yml',
        'test/prodlot_with_one_qc_test.yml',
        'test/prodlot_with_two_qc_test.yml',
        'test/prodlot_with_two_qc_test_diff_trigger.yml',
    ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
