# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010,2011 NaN Projectes de Programari Lliure, S.L. All Rights Reserved.
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
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

{
    "name": "Quality Control",
    "version": "0.1",
    "author": "NaN·tic",
    "category": "Others",
    "description": """

Quality Control module for OpenERP, updated to version 6 where
have added some interesting functionality.

This module is generic, is the basis for integration automatically
with different models of the application, however allows us to
any quality control at the different models of the system so
manual. Over the following weeks introduce other modules
automate quality control in the production lots or in
invoices.

Definition:

* Method: The various procedures available to perform qual
proof.
* Test: The test to check. We have two types of tests:
    * Qualitative: The result is a description, color, yes, No..
    * Quantitative: The result must be within a range.
* Possible values: The values  choose in qualitative tests.
* Synonyms: Different names for the same test.
* References in test: different models of the application to which you can
pass a quality test.
* Template: The set of tests to be used in tests!

* Once these values we define the test.

  We have a * generic * test that can be applied to any model as
  Any company example, shipments, invoices or product, or a * test
  related *, making it specific to a particular product and that
  eg apply whenever food is sold or quan creating a
  batch.

* The * formula *, has been added in version 6.0 to be scored
the test.

So to define the formula simply use the name of the
lines as operands. For example: Taking the 3 lines of the template
named A, B, C respectively can create a formula such that: (A * 100 + B / C) * B ²


To give a practical example, this field has been used in some of our
customers engaged in artificial insemination to calculate the dose
according to the values resulting quality test passes extraction.

Once these parameters we just pass the test. We create a
new test, we create a relationship with the model, company sales .. , And pressed
the "Select Template", choose the test and fills us ĺínieas
depending on the template chosen.

Now we just fill línieas test. In cases has
different test methods need only one of the
combinations test method is correct.


We continue the workflow:

    Borarrador -> Confirmed -> Pending approval -> Success
                                        |
                                        | -> Failure

Developed for Trod y Avia, S.L.""",
    "depends": [
        'product'
    ],
    "images": ["images/test.png","images/menu.png","images/metodos.png",
            "images/plantilla.png","images/pantilla_relacionado.png",
            "images/prueba_cual.png","images/prueba_cuan.png",
            "images/pruebas.png","images/reference_model.png",
            "images/test_conf.png","images/test_ok.png",
            "images/valores_posibles.png"],
    "demo_xml": [],
    "update_xml": [
        'security/security.xml',
        'test_workflow.xml',
        'qc_sequence.xml',
        'security/ir.model.access.csv',
        'quality_control_view.xml',
        'qc_precision.xml',
        'quality_control_data.xml',
    ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
