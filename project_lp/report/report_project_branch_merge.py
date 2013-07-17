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


import tools
from osv import fields, osv

class branch_merge_report(osv.osv):
    _name = "branch.merge.report"
    _description = "Sales Orders Statistics"
    _auto = False
    _rec_name = 'date_created'
    _columns = {
        'name': fields.char('Branch', size=512, readonly=True),
        'date_created': fields.datetime('Created', readonly=True),
        'user_id': fields.many2one('res.users', 'Owner', readonly=True),
        'project_id': fields.many2one('project.project', 'Project', readonly=True),
        'target_branch_id':fields.many2one('project.branch', 'Target Branch', readonly=True),
        'added_lines_count': fields.integer('Lines Added', readonly=True),
        'removed_lines_count': fields.integer('Lines Removed', readonly=True),
        'diff_lines_count': fields.integer('Lines Diff', readonly=True),
        'diff_file_count': fields.integer('Files Modified', readonly=True),
        'delay_in_development': fields.float('Delay In Development(Days)', readonly=True),
        'delay_in_merge': fields.float('Delay In Merge(Days)', readonly=True ),
        'branch_type': fields.selection([
            ('fix','Bug Fix'),
            ('feature','Feature'),
            ('improvement','Improvements'),
            ('junk','Need Review'),
            ('not_clean','Junk'),
            ('removed','Deleted')], 'Type', readonly=True),
        'state': fields.selection([
            ('Experimental','Experimental'),
            ('Development','Development'),
            ('Mature','Mature'),
            ('Merged','Merged'),
            ('Abandoned','Abandoned')], 'State', readonly=True),
        'stage': fields.selection([
            ('Work in progress','Work in progress'),
            ('Needs review','Needs review'),
            ('Approved','Approved'),
            ('Rejected','Rejected'),
            ('Merged','Merged'),
            ('Code failed to merge','Code failed to merge'),
            ('Queued','Queued'),
            ('Superseded','Superseded')], 'Stage', readonly=True),
        'year': fields.char('Year',size=64,required=False, readonly=True),
        'day': fields.char('Day', size=128, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
        'reviewer_user_id':fields.many2one('res.users', 'Reviewer'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'branch_merge_report')
        cr.execute("""
            CREATE OR REPLACE VIEW branch_merge_report AS (
                SELECT
                    MIN(pbr.id) AS id,
                    pbr.name AS name,
                    pbr.project_id AS project_id,
                    pbr.user_id AS user_id,
                    pbr.date_created AS date_created,
                    pmer.branch_type AS branch_type,
                    pmer.target_branch_id AS target_branch_id,
                    pmer.reviewer_user_id AS reviewer_user_id,
                    CASE WHEN pmer.state IN ('Work in progress','Needs review', 'Queued') THEN 'Development'
                         WHEN pmer.state IN ('Rejected','Superseded', 'Code failed to merge') THEN 'Abandoned'
                         WHEN pmer.state IN ('Approved','Merged') THEN 'Merged'
                    ELSE pbr.state END AS state,
                    pmer.state AS stage,
                    to_char(pbr.date_created, 'YYYY-MM-DD') AS day,
                    to_char(pbr.date_created,'YYYY') AS year,
                    to_char(pbr.date_created,'MM') AS month,
                    COALESCE(pmer.added_lines_count, 0) AS added_lines_count,
                    COALESCE(pmer.removed_lines_count, 0) AS removed_lines_count,
                    COALESCE(pmer.diff_lines_count, 0) AS diff_lines_count,
                    COALESCE(pmer.diff_file_count, 0) AS diff_file_count,
                    CASE
                        WHEN pmer.date_created IS NOT NULL THEN extract('epoch' FROM (pmer.date_created-pbr.date_created))/(3600*24)
                    ELSE
                        extract('epoch' FROM (current_date-pbr.date_created))/(3600*24) END AS delay_in_development,
                    CASE
                        WHEN pmer.date_reviewed IS NOT NULL THEN extract('epoch' FROM (pmer.date_reviewed-pmer.date_created))/(3600*24)
                    ELSE
                        extract('epoch' FROM (current_date-pmer.date_created))/(3600*24) END AS delay_in_merge
                    FROM project_branch_merge pmer
                    LEFT JOIN project_project prj ON(prj.id = pmer.project_id)
                    LEFT JOIN project_branch pbr ON(pbr.id = pmer.branch_id)
                    LEFT JOIN account_analytic_account anly ON (anly.id = prj.analytic_account_id)
                    WHERE pmer.date_created = (SELECT MAX(pmer.date_created) FROM project_branch_merge pmer WHERE pmer.branch_id=pbr.id) AND anly.state='open'
                    AND pmer.active='t'
                    GROUP BY
                    pbr.name,
                    pbr.project_id,
                    pbr.user_id,
                    pmer.branch_type,
                    pbr.date_created,
                    pbr.state,
                    pmer.state,
                    pmer.added_lines_count,
                    pmer.removed_lines_count,
                    pmer.diff_lines_count,
                    pmer.diff_file_count,
                    pmer.date_reviewed,
                    pmer.date_created,
                    pmer.target_branch_id,
                    pmer.reviewer_user_id
            )
        """)

branch_merge_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
