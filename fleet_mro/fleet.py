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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
from openerp import netsvc
from openerp import tools
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class res_users(osv.Model):
    _inherit = "res.users"

    _columns = {
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse'),
    }
#
#    def unlink(self, cr, uid, ids, context=None):
#        service_ids = self.pool.get('fleet.vehicle.log.services').search(cr, uid, ['|', ('in_inspector_id', 'in', ids), ('out_inspector_id', 'in', ids)], context=context)
#        if service_ids:
#            raise osv.except_osv(_('Invalid Action!'),
#                                 _('You cannot delete a user associated with job cards. You can either delete all the job cards related to user and then delete the user.'))
#        return super(res_users, self).unlink(cr, uid, ids, context=context)

res_users()

class fleet_vehicle_fault(osv.Model):
    _name = 'fleet.vehicle.fault'
    _description = 'Vehicle Fault'

    _columns = {
        'fault_id': fields.many2one('fleet.service.type', 'Fault', required=True, domain="[('category', 'in', ('contract', 'service', 'both'))]"),
        'trade_id': fields.many2one('fleet.service.type', 'Trade Code', required=True, domain="[('category', '=', 't_code')]"),
        'job_id': fields.many2one('fleet.vehicle.log.services', 'Job', required=True, ondelete='cascade'),
        'repair_time': fields.float('Repair Time'),
        'trademen': fields.integer('No of Trademen'),
        'repair_date': fields.date('Repair Date'),
        'work_done': fields.text('Work Done'),
        'entry_clerk': fields.many2one('res.users', 'Entry Clerk', readonly=True),
    }
    _defaults = {
        'repair_date': fields.date.context_today,
        'entry_clerk': lambda self, cr, uid, context: uid,
    }

fleet_vehicle_fault()

class fleet_equipment_status(osv.Model):
    _name = 'fleet.equipment.status'
    _description = 'Equipment Status'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=32, required=True),
    }

fleet_equipment_status()

class fleet_vehicle(osv.Model):
    _name = 'fleet.vehicle'
    _inherit='fleet.vehicle'

    def open_equipment_job_cards(self, cr, uid, ids, context=None):
        """ This opens the xml view specified in xml_id for the current vehicle """
        if context is None:
            context = {}
        if context.get('xml_id'):
            res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'fleet_mro', context['xml_id'], context=context)
            res['context'] = context
            res['context'].update({'default_vehicle_id': ids[0]})
            res['domain'] = [('vehicle_id','=', ids[0])]
            return res
        return False

    def _vehicle_name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            name = record.model_id.brand_id.name + '/' + record.model_id.modelname
            if record.type == 'vehicle' and record.license_plate:
                res[record.id] = name + ' / ' + record.license_plate
            else:
                if record.erid:
                    res[record.id] = name + ' / ' + record.erid
        return res

    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.image)
        return result

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)

    _columns = {
        'name': fields.function(_vehicle_name_get_fnc, type="char", string='Name', store=True),
        'image': fields.binary("Image",
            help="This field holds the image used for the vehicle, limited to 1024x1024px."),
        'image_medium': fields.function(_get_image, fnct_inv=_set_image,
            string="Medium-sized image", type="binary", multi="_get_image",
            store = {
                'fleet.vehicle': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Medium-sized image of the vehicle. It is automatically "\
                 "resized as a 128x128px image, with aspect ratio preserved. "\
                 "Use this field in form views or some kanban views."),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary", multi="_get_image",
            store = {
                'fleet.vehicle': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Small-sized image of the vehicle. It is automatically "\
                 "resized as a 64x64px image, with aspect ratio preserved. "\
                 "Use this field anywhere a small image is required."),
        'license_plate': fields.char('License Plate', size=32, help='License plate number of the vehicle (ie: plate number for a car)'),
        'erid': fields.char('Eqpt Registration ID', size=64),
        'present_eqpt_status': fields.many2one('fleet.equipment.status', 'Present Eqpt Status'),
        'type': fields.selection([('vehicle', 'Vehicle'), ('equipment','Equipment')], 'Type', required=True),
        'unit_id': fields.many2one('stock.location', 'Unit', domain=[('usage','=','internal')], required=True),
        'issue_date': fields.date('Date of Issue'),
    }

    def _default_eqpt_status(self, cr, uid, ids, context=None):
        status_ids = self.pool.get('fleet.equipment.status').search(cr, uid, [('code', '=', 'ser')], context=context)
        return status_ids and status_ids[0] or False 

    def _default_unit_id(self, cr, uid, context=None):
        stock_location = self.pool.get('ir.model.data').get_object(cr, uid, 'stock', 'stock_location_stock')
        warehouse = self.pool.get('res.users').browse(cr, uid, uid, context=context).warehouse_id
        if warehouse:
            stock_location = warehouse.lot_stock_id
        return stock_location.id

    _defaults = {
        'present_eqpt_status': _default_eqpt_status,
        'type': 'vehicle',
        'unit_id': _default_unit_id,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'fleet.vehicle', context=c)
    }

fleet_vehicle()

class fleet_vehicle_log_services(osv.Model):
    _name = 'fleet.vehicle.log.services'
    _inherit = ['fleet.vehicle.log.services', 'mail.thread'] 

    def on_change_vehicle(self, cr, uid, ids, vehicle_id, context=None):
        vals = {}
        if not vehicle_id:
            return vals
        vehicle = self.pool.get('fleet.vehicle').browse(cr, uid, vehicle_id, context=context)
        vals = dict(odometer_unit = vehicle.odometer_unit, purchaser_id = vehicle.driver_id.id, image = vehicle.image)
        if vehicle.issue_date:
            current_date = datetime.strptime(fields.date.context_today(self,cr,uid,context=context), '%Y-%m-%d')
            vintage_date = datetime.strptime(vehicle.issue_date, '%Y-%m-%d')
            vals = dict(vals, eqpt_vintage = 'Years: %d, Months: %d, Days: %d' %(current_date.year-vintage_date.year,current_date.month-vintage_date.month,current_date.day-vintage_date.day))
        return {'value': vals}

    def onchange_maint_type(self, cr, uid, ids, maint_type, work_date, context=None):
        expected_date = (datetime.strptime(work_date, '%Y-%m-%d') + relativedelta(days=2)).strftime('%Y-%m-%d')
        if maint_type == 'scheduled':
            expected_date = work_date
        return {'value': {'expected_date': expected_date}}

    def _previous_jobs(self, cr, uid, ids, name, args, context=None):
        ''' This function will automatically computes the previous job related to particular vehicle.'''
        result = {}
        vehicle = self.browse(cr, uid, ids[0], context=context).vehicle_id
        for job in self.browse(cr, uid, ids, context=context):
            job_ids = self.search(cr, uid, [('vehicle_id', '=', vehicle.id), ('time_in', '<', job.time_in)], context=context)
            result[job.id] = job_ids
        return result

    def _get_total_insp_time(self, cr, uid, ids, name, args, context=None):
        result = {}
        for job in self.browse(cr, uid, ids, context=context):
            result[job.id] = job.in_inspection_time + job.out_inspection_time
        return result

    def _get_total_time(self, cr, uid, ids, name, args, context=None):
        result = {}
        for job in self.browse(cr, uid, ids, context=context):
            result[job.id] = job.total_inspection_time + job.repair_time
        return result

    def _get_repair_time(self, cr, uid, ids, name, args, context=None):
        result = {}
        for job in self.browse(cr, uid, ids, context=context):
            total_time = 0.00
            for defect in job.defect_ids:
                total_time = total_time + defect.repair_time
            result[job.id] = total_time
        return result

    def _cost_name_get_fnc(self, cr, uid, ids, name, unknow_none, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            name = record.vehicle_id.name
            if record.job_no:
                name += ' / '+ record.job_no
            res[record.id] = name
        return res

    _columns = {
        'name': fields.function(_cost_name_get_fnc, type="char", string='Name', store=True),
        'job_no': fields.char('Job No', size=64, required=True),
        'image': fields.binary('Image'),
        'time_in': fields.datetime('Time In'),
        'fuel_in_tank': fields.float('Fuel in Tank'),
        'eqpt_vintage': fields.char('Eqpt Vintage', size=64, help="Contact MIS cell to update correct Vintage date of eqpt/veh."),
        'type': fields.selection([('vehicle', 'Vehicle'), ('equipment','Equipment')], 'Type', required=True),
        'exploitation_type': fields.selection([('routine','Routine'), ('excercise','Excercise'), ('operational','Operational')],'Exploitation Type', required=True),
        'maint_type': fields.selection([('unscheduled','Unscheduled'), ('scheduled','Scheduled')],'Maint Type', required=True),
        'work_no': fields.char('Work No', size=64, required=True),
        'work_date': fields.date('Work Date'),
        'dues': fields.boolean('Dues'),
        'out_km': fields.float('Out KM'),
#        'in_inspector_id': fields.many2one('res.users','In Inspector', required=True),
#        'out_inspector_id': fields.many2one('res.users','Out Inspector', required=True),
        'in_inspector_id': fields.char('In Inspector', size=64),
        'out_inspector_id': fields.char('Out Inspector', size=64),
        'in_inspection_time': fields.float('In Insp Time'),
        'out_inspection_time': fields.float('Out Insp Time'),
        'job_remarks': fields.text('Job Remarks'),
        'present_eqpt_status': fields.related('vehicle_id', 'present_eqpt_status', type='many2one', relation='fleet.equipment.status', string="Present Eqpt Status"),
        'expected_date': fields.date('Tentative Date of Repair'),
        'pss_date': fields.date('PSS Date'),
        'technician_id': fields.char('Contact Technician', size=64),
        'repair_time': fields.function(_get_repair_time, type='float', string='Repair Time', store=True),
        'total_inspection_time': fields.function(_get_total_insp_time, type='float', string='Time for Inspection'),
        'total_time': fields.function(_get_total_time, type='float', string='Total Time'),
        'work_value': fields.float('Work Value'),
        'tech_delay': fields.integer('Tech Avl Delay Time'),
        'tools_delay': fields.integer('Tools/SMT Delay Time'),
        'defect_ids': fields.one2many('fleet.vehicle.fault', 'job_id', 'Defects'),
        'previous_job_ids': fields.function(_previous_jobs, relation='fleet.vehicle.log.services', type='one2many', string='Previous Jobs'),
        'product_lines': fields.one2many('job.product.lines', 'job_id', 'Products to Consume', readonly=True, states={'draft': [('readonly', False)], 'observation': [('readonly', False)]},),
        'picking_id': fields.many2one('stock.picking','Picking'),
        'unit_id': fields.related('vehicle_id', 'unit_id', type='many2one', relation='stock.location', string='Unit', readonly=True, store=True),
        'location_id': fields.many2one('stock.location', 'Workshop', required=True),
        'company_id': fields.related('vehicle_id', 'company_id', type='many2one', relation='res.company', string="Company"),
        'state':fields.selection([('draft','Draft'), ('observation','Observation'), ('inprogress','Waiting for Material'), ('repair','Repair In Progress'), ('done','Repairing Done'), ('inspection','Inspection'), ('cancel','Cancel'), ('delivered','Delivered')],'State',readonly=True)
    }

    def _default_stock_location(self, cr, uid, context=None):
        user_obj = self.pool.get('res.users')
        stock_location = self.pool.get('ir.model.data').get_object(cr, uid, 'stock', 'stock_location_stock')
        warehouse = user_obj.browse(cr, uid, uid, context=context).warehouse_id
        if warehouse:
            stock_location = warehouse.lot_stock_id
        return stock_location.id

    _defaults = {
        'state': 'draft',
        'time_in': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'type': 'vehicle',
        'exploitation_type': 'routine',
        'maint_type': 'unscheduled',
#        'in_inspector_id': lambda self, cr, uid, context: uid,
        'in_inspection_time':00.50,
#        'out_inspector_id': lambda self, cr, uid, context: uid,
        'expected_date': fields.date.context_today,
        'work_date': fields.date.context_today,
        'job_no': lambda obj, cr, uid, context:obj.pool.get('ir.sequence').get(cr, uid, 'job.number'),
        'work_no': lambda obj, cr, uid, context:obj.pool.get('ir.sequence').get(cr, uid, 'work.number'),
        'location_id': _default_stock_location
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('vehicle_id'):
            job_ids = self.search(cr, uid, [('vehicle_id', '=', vals.get('vehicle_id'))], context=context)
            for job in self.browse(cr, uid, job_ids, context=context):
                if job.state != 'delivered':
                    raise osv.except_osv(_('Error!'),_('You cannot create a job for a vehicle which is already in maintenance.'))
        return super(fleet_vehicle_log_services, self).create(cr, uid, vals, context=context)

    def action_picking_create(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        picking_obj = self.pool.get('stock.picking')
        picking_id = False
        job = self.browse(cr, uid, ids[0], context=context)
        if job.product_lines:
            picking_id = self._create_pickings_and_procurements(cr, uid, job, job.product_lines, None, context=context)
        self.write(cr, uid, ids, {'picking_id': picking_id, 'state' : 'inprogress'}, context=context)
        return picking_id

    def action_receive_products(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display internal move of given job ids.
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        picking_id = self.browse(cr, uid, ids[0], context=context).picking_id.id
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_picking_form')
        result = {
            'name': _('Internal Moves'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': res and res[1] or False,
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': picking_id,
        }
        return result

    def _prepare_job_line_move(self, cr, uid, job, line, picking_id, date_planned, context=None):
        warehouse_obj = self.pool.get('stock.warehouse')
        warehouse_id = warehouse_obj.search(cr, uid, [('lot_stock_id', '=', job.location_id.id)], context=context)[0]
        warehouse = warehouse_obj.browse(cr, uid, warehouse_id, context=context)
        res = {
            'name': line.name,
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'location_id': job.location_id.id,
            'location_dest_id': warehouse.lot_workshop_id.id,
            'state': 'draft',
            'price_unit': line.product_id.standard_price or 0.0
        }
        if job.company_id:
            res = dict(res, company_id = job.company_id.id)
        return res

    def _prepare_job_picking(self, cr, uid, job, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        workshop = user.warehouse_id and user.warehouse_id.id or False
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking')
        res = {
            'name': pick_name,
            'origin': job.job_no,
            'date': job.work_date,
            'type': 'internal',
            'workshop_id': workshop,
        }
        if job.company_id:
            res = dict(res, company_id = job.company_id.id)
        return res

#    def _get_date_planned(self, cr, uid, order, line, start_date, context=None):
#        date_planned = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=line.delay or 0.0)
#        date_planned = (date_planned - timedelta(days=order.company_id.security_lead)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
#        return date_planned

    def _create_pickings_and_procurements(self, cr, uid, job, product_lines, picking_id=False, context=None):
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        proc_ids = []

        for line in product_lines:
            date_planned = job.work_date
#            date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)

            if line.product_id:
                if line.product_id.type in ('product', 'consu'):
                    if not picking_id:
                        picking_id = picking_obj.create(cr, uid, self._prepare_job_picking(cr, uid, job, context=context))
                    move_id = move_obj.create(cr, uid, self._prepare_job_line_move(cr, uid, job, line, picking_id, date_planned, context=context), context=context)
                else:
                    # a service has no stock move
                    move_id = False
                proc_id = procurement_obj.create(cr, uid, self._prepare_job_line_procurement(cr, uid, job, line, move_id, date_planned, context=context))
                proc_ids.append(proc_id)

        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        for proc_id in proc_ids:
            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

        return picking_id

    def _prepare_job_line_procurement(self, cr, uid, job, line, move_id, date_planned, context=None):
        res = {
            'name': line.name,
            'origin': job.job_no,
            'date_planned': date_planned,
            'product_id': line.product_id.id,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty)\
                    or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'location_id': job.location_id.id,
            'procure_method': line.type,
            'move_id': move_id,
            'note': line.name,
        }
        if job.company_id:
            res = dict(res, company_id = job.company_id.id)
        return res

fleet_vehicle_log_services()

class fleet_service_type(osv.Model):
    _name = 'fleet.service.type'
    _inherit = 'fleet.service.type'
    _description = 'Type of services available on a vehicle'
    _columns = {
        'category': fields.selection([('contract', 'Contract'), ('service', 'Service'), ('both', 'Both'), ('t_code', 'T-Code')], 'Category', required=True, help='Choose wheter the service refer to contracts, vehicle services or both'),
    }

fleet_service_type()

class fleet_vehicle_tag(osv.Model):

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res
        # name_get may receive int id instead of an id list
        if isinstance(ids, (int, long)):
            ids = [ids]

        for tag in self.browse(cr, uid, ids, context=context):
            name = tag.name
            if tag.parent_id:
                name = tag.parent_id.name + ' / ' + name
            res += [(tag.id, name)]
        return res

    _inherit = 'fleet.vehicle.tag'
    _columns = {
        'parent_id':fields.many2one('fleet.vehicle.tag', 'Parent Category'),
    }

fleet_vehicle_tag()

class job_product_lines(osv.Model):

    _name = 'job.product.lines'
    _description = 'Job Product Lines'
    _columns = {
        'job_id': fields.many2one('fleet.vehicle.log.services', 'Job', required=True, ondelete='cascade'),
        'name': fields.text('Description', required=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'type': fields.selection([('make_to_stock', 'from stock'), ('make_to_order', 'on order')], 'Procurement Method', required=True,
         help="From stock: When needed, the product is taken from the stock or we wait for replenishment.\nOn order: When needed, the product is purchased or produced."),
        'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True),
        'product_uos_qty': fields.float('Quantity (UoS)' ,digits_compute= dp.get_precision('Product UoS')),
        'product_uos': fields.many2one('product.uom', 'Product UoS'),
    }

    def _get_uom_id(self, cr, uid, *args):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')
        return result and result[1] or False

    _defaults = {
        'product_uom' : _get_uom_id,
        'product_uom_qty': 1,
        'product_uos_qty': 1,
        'type': 'make_to_stock',
    }

    def product_id_change(self, cr, uid, ids, product, qty=0, uom=False, qty_uos=0, uos=False, name='', date_order=False):
        warning = {}
        product_uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')

        if not product:
            return {'value': {'product_uos_qty': qty}, 'domain': {'product_uom': [], 'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        warning_msgs = {}
        product_obj = product_obj.browse(cr, uid, product)

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False

        result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id])[0][1]
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty

        if not uom2:
            uom2 = product_obj.uom_id

        result['type'] = product_obj.procure_method
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'), 'message' : warning_msgs
                    }
        return {'value': result, 'domain': domain, 'warning': warning}

    def product_uom_change(self, cr, uid, ids, product, qty=0, uom=False, qty_uos=0, uos=False, name='', date_order=False):
        if not uom:
            return {'value': {'product_uom' : uom or False}}
        return self.product_id_change(cr, uid, ids, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name, date_order=date_order)

job_product_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
