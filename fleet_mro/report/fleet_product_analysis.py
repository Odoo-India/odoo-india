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

from openerp import tools
from openerp.osv import fields,osv

class fleet_material_defect_report(osv.osv):
    _name = "fleet.material.defect.report"
    _description = "Material Analysis"
    _auto = False
    

    _columns = {
        'name': fields.text('Description', required=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'type': fields.selection([('make_to_stock', 'From Stock'), ('make_to_order', 'On Order')], 'Procurement Method', required=True,
         help="From stock: When needed, the product is taken from the stock or we wait for replenishment.\nOn order: When needed, the product is purchased or produced."),
        'product_uom_qty': fields.float('Quantity', required=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True),

        'job_id': fields.many2one('fleet.vehicle.log.services', 'Job', required=True),
        'job_no': fields.char('Job No'),
        'vehicle_id': fields.many2one('fleet.vehicle.log.services', 'Vehicle', required=True),
        'defect_repair_time': fields.float('Defect Repair Time'),
        'job_repair_time': fields.float('Job Repair Time'),
        'work_date': fields.date('work Date'),
        'work_done': fields.text('Work Done'),
        'entry_clerk': fields.many2one('res.users', 'Entry Clerk', readonly=True),
        'vehicle_id': fields.many2one('fleet.vehicle', 'Vehicle', required=True),
        'unit_id': fields.many2one('stock.location', 'Workshop', required=True),
        'in_inspector': fields.char('In Inspector', size=64, readonly=True),
        'out_inspector': fields.char('Out Inspector', size=64, readonly=True),
        'technician': fields.char('Contact Technician', size=64, readonly=True),
        'workshop_id': fields.many2one('stock.location', 'Workshop', required=True),
        'state':fields.selection([('draft','Draft'), ('observation','Observation'), ('inprogress','Need Equipment'), 
            ('repair','Repair In Progress'), ('done','Done'), ('inspection','Inspection'), ('cancel','Cancel'), 
            ('delivered','Delivered')],'State',readonly=True)
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'fleet_material_defect_report')
        cr.execute("""
            create or replace view fleet_material_defect_report as (
                 select
                     p.id as id,
                     p.name as name,
                     p.product_id as product_id,
                     p.type as type,
                     p.job_id as job_id,
                     l.job_no as job_no,
                     p.product_uom_qty as product_uom_qty,
                     l.repair_time as job_repair_time,
                     l.work_date as work_date,
                     p.product_uom as product_uom,
                     l.in_inspector_id as in_inspector,
                     l.out_inspector_id as out_inspector,
                     l.technician_id as technician,
                     l.location_id as workshop_id,
                     l.state as state
                 from
                     job_product_lines p, fleet_vehicle_log_services l
                     where l.id = p.job_id
                group by
                     p.id, p.name, p. product_id, p.type, p.job_id,
                     p.product_uom_qty,
                     l.repair_time,
                     p.product_uom,
                     l.in_inspector_id, l.out_inspector_id,
                     l.technician_id, l.location_id, l.state, 
                     l.job_no,
                     l.work_date
            )
        """)
fleet_material_defect_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
