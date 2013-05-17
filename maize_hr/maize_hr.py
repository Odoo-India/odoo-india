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


from openerp.osv import fields, osv

class hr_cost_code(osv.Model):
    _name = "hr.cost.code"
    _description = "Cost Code Description"
    _inherit = ['mail.thread']
    _columns = {
        'name': fields.char('Cost Name', size=64, required=False, readonly=False),
        'code': fields.char('Cost Code', size=64, required=False, readonly=False),
    }

hr_cost_code()

class hr_grade_code(osv.Model):
    _name = "hr.grade.code"
    _description = "Grade Code Description"
    _inherit = ['mail.thread']
    _columns = {
        'name': fields.char('Grade Name', size=64, required=False, readonly=False),
        'code': fields.char('Grade Code', size=64, required=False, readonly=False),
    }

hr_grade_code()

class hr_category_code(osv.Model):
    _name = "hr.category.code"
    _description = "Category Code Description"
    _inherit = ['mail.thread']
    _columns = {
        'name': fields.char('Category Name', size=64, required=False, readonly=False),
        'code': fields.char('Category Code', size=64, required=False, readonly=False),
    }

hr_category_code()

class hr_employee(osv.Model):
    _inherit = 'hr.employee'
    
    _columns = {
        'join_date': fields.date('Join Date'),
        'resign_date': fields.date('Resign Date'),
        'confirm_date': fields.date('Confirm Date'),
        'marriage_date': fields.date('Marriage Date'),
        'esi_no': fields.char('ESI No.', size=64, required=False, readonly=False),
        'pf_no': fields.char('PF No', size=64, required=False, readonly=False),
        'qualification': fields.char('Qualification', size=64, required=False, readonly=False),
        'blood_group': fields.char('Blood Group', size=64, required=False, readonly=False),
        'cost_id': fields.many2one('hr.cost.code', "Cost Code"),
        'grade_id': fields.many2one('hr.grade.code', "Grade Code"),
        'categ_id': fields.many2one('hr.category.code', "Category Code"),
        'emp_code': fields.char('Code', size=64, required=False, readonly=False),
        'emp_cost_code': fields.char('Cost Code', size=64, required=False, readonly=False),
    }
    
hr_employee()