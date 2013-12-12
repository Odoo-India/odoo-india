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

from osv import osv, fields
from tools.translate import _


class qc_trigger(osv.osv):
    _name = 'qc.trigger'
    _description = 'Quality Control Trigger Tag'

    _columns = {
        'name': fields.char('Name', size=128, required=True),
    }

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "The Name of the Quality Control "
                "Trigger Tags must be unique!"),
    ]
qc_trigger()


class qc_test(osv.osv):
    _inherit = 'qc.test'

    # qc.test
    def action_workflow_draft(self, cr, uid, ids, context=None):
        """
        Check if the Test is in any Lot Trigger Test. In these case, raise an
        exception if the Test is not the current test of Lot or it is not in
        'Draft', 'Waiting QC Test' or 'QC Test Failed' states.
        """
        lot_test_proxy = self.pool.get('stock.production.lot.qc.trigger.test')

        lot_test_ids = lot_test_proxy.search(cr, uid, [
                    ('test_id', 'in', ids),
                ], context=context)
        for lot_test in lot_test_proxy.browse(cr, uid, lot_test_ids, context):
            if lot_test.prodlot_id.state == 'draft':
                continue
            curr_trigger_id = lot_test.prodlot_id.current_qc_test_trigger_id.id
            if (lot_test.id == curr_trigger_id and
                    lot_test.prodlot_id.state in
                            ('pending_test', 'test_failed', 'draft')):
                continue

            state_labels = self.pool.get('stock.production.lot').fields_get(cr,
                    uid, ['state'], context)['state']['selection']
            state_labels = dict(state_labels)
            raise osv.except_osv(
                    _("Error canceling Test!"),
                    _("You are trying to cancel the Quality Control Test "
                      "'%(test_name)s' (id:%(test_id)d) but it is in a Test "
                      "Trigger of the Production Lot '%(lot_name)s' "
                      "(id:%(lot_id)d) which is in '%(lot_state)s' state.\n"
                      "You can only cancel this test if it is the current "
                      "test of the Lot and the Lot's state is "
                      "'Waiting QC Test' or 'QC Test Failed") % {
                        'test_name': lot_test.test_id.name,
                        'test_id': lot_test.test_id.id,
                        'lot_name': lot_test.prodlot_id.name,
                        'lot_id': lot_test.prodlot_id.id,
                        'lot_state': state_labels[lot_test.prodlot_id.state],
                    })
        return super(qc_test, self).action_workflow_draft(cr, uid, ids,
                context)
qc_test()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
