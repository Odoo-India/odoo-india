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

class fault_analysis_report(osv.osv):
    _name = "fault.analysis.report"
    _description = "Fault Analysis Statistics"
    _auto = False
    

    _columns = {
        'fault_id': fields.many2one('fleet.service.type', 'Fault', required=True),
        'trade_id': fields.many2one('fleet.service.type', 'Trade Code', required=True),
        'job_id': fields.many2one('fleet.vehicle.log.services', 'Job', required=True),
        'job_no': fields.char('Job No'),
        'vehicle_id': fields.many2one('fleet.vehicle.log.services', 'Vehicle', required=True),
        'defect_repair_time': fields.float('Defect Repair Time'),
        'job_repair_time': fields.float('Job Repair Time'),
        'trademen': fields.integer('No of Trademen'),
        'repair_date': fields.date('Repair Date'),
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
        tools.drop_view_if_exists(cr, 'fault_analysis_report')
        cr.execute("""
            create or replace view fault_analysis_report as (
                 select
                     f.id as id,
                     f.fault_id as fault_id,
                     f.trade_id as trade_id,
                     f.job_id as job_id,
                     l.job_no as job_no,
                     f.repair_time as defect_repair_time,
                     l.repair_time as job_repair_time,
                     f.trademen as trademen,
                     f.repair_date as repair_date,
                     f.work_done as work_done,
                     f.entry_clerk as entry_clerk,
                     l.in_inspector_id as in_inspector,
                     l.out_inspector_id as out_inspector,
                     l.technician_id as technician,
                     l.location_id as workshop_id,
                     l.state as state
                 from
                     fleet_vehicle_fault f, fleet_vehicle_log_services l
                     where l.id = f.job_id
                group by
                     f.id, f.fault_id, f.trade_id, f.job_id, f.repair_time,
                     l.repair_time,
                     f.entry_clerk, l.in_inspector_id, l.out_inspector_id,
                     l.technician_id, l.location_id, l.state, 
                     f.trademen, f.repair_date, f.work_done, l.job_no
            )
        """)
fault_analysis_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
