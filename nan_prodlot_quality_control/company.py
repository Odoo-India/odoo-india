##############################################################################
#
# Copyright (c) 2012 NaN Projectes de Programari Lliure, S.L.
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

from osv import osv, fields


class res_company_qc_trigger_template(osv.osv):
    '''
    Model to configure the default Quality Control Templates/Tests triggers by
    Company. Define the template to use for a trigger, ordering it by sequence.
    '''
    _name = 'res.company.qc.trigger.template'
    _description = 'Quality Control Template Triggers by Company'
    _order = 'company_id, sequence'

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'sequence': fields.integer('Sequence', required=True),
        'trigger_id': fields.many2one('qc.trigger', 'Trigger', required=True,
                help="The Quality Control Trigger Tag which defines when must "
                "to be created a Test (using the specified template) for a "
                "Production Lot."),
        'template_id': fields.many2one('qc.test.template', 'Template',
                required=True, help="The Quality Control Template to use."),
    }

    _defaults = {
        'sequence': 0,
    }
res_company_qc_trigger_template()


class res_company(osv.osv):
    '''
    Adds to the company a one2many field to the model which configures Quality
    Control Templates/Tests triggers.
    It will be used as default values when a new Product is created.
    '''
    _inherit = 'res.company'

    _columns = {
        'qc_template_trigger_ids': fields.one2many(
                'res.company.qc.trigger.template', 'company_id', 'QC Triggers',
                help="Defines when a Production Lot must to pass a Quality "
                "Control Test (based on the defined Template).\n"
                "It defines the default Template Triggers which will be used "
                "when a Product is created. Only the Product's field define "
                "the final behavior of its lots: which template to use or "
                "don't require any test if there aren't any trigger defined."),
    }
res_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
