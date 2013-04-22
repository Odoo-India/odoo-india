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
    'name' : 'WAO (Workshop Automation using OpenERP)',
    'version' : '0.1',
    'author' : 'OpenERP S.A.',
    'sequence': 110,
    'category': 'Managing vehicles and equipments',
    'website' : 'http://www.openerp.com',
    'summary' : 'Vehicles, Equipments, Jobcards, Faults',
    'description' : """
Vehicles, Equipments, Jobcards, Faults
======================================
With this module, OpenERP helps you managing all your vehicles and equipments the
contracts associated to those vehicle as well as services, fuel log
entries, costs and many other features necessary to the management 
of your fleet of vehicle(s)

Main Features
-------------
* Add vehicles and equipments
* Manage contracts for vehicles
* Add services, fuel log entry, odometer values for all vehicles
* Fault Analysis
""",
    'depends' : ['purchase', 'fleet'],
    'data' : [
        'fleet_view.xml',
        'stock_view.xml',
        'job_workflow.xml',
        'fleet_data.xml',
        'stock_data.xml',
        'job_sequence.xml',
        'work_sequence.xml',
        'fleet_mro_report.xml'
    ],
    'update_xml' : ['security/ir.model.access.csv', 'security/fleet_mro_security.xml'],

    'demo': ['fleet_demo.xml', 'stock_demo.xml'],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
