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

from osv import fields, osv

class project_launchpad_wizard(osv.osv_memory):
    _name = "project.launchpad.wizard"
    _description = "project launchpad wizard"
    _columns = {
        'project_id':fields.many2one('project.project', string='Projects',required=True),
        'date_start': fields.date('Date Start', required=True),
        'date_end': fields.date('Date End', required=True),
        'Development': fields.boolean('Development'),
        'Experimental': fields.boolean('Experimental'),
        'Mature': fields.boolean('Mature'),
        'Abandoned': fields.boolean('Abandoned'),
        'Merged': fields.boolean('Merged'),
    }

    _defaults = {
        'Development': 1,
        'Experimental': 1,
        'Mature': 1,
        'date_start': time.strftime('%Y-01-01'),
        'date_end': time.strftime('%Y-%m-%d'),
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'project.branch',
             'form': data
                 }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'project.branch',
            'datas': datas,
        }

project_launchpad_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
