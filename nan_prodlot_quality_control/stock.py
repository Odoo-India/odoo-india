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
from tools.translate import _
import netsvc


class stock_production_lot_qc_trigger_test(osv.osv):
    '''
    Model that defines the Quality Control Tests which a Production Lot must
    to pass in certain situations defined by the Trigger Tag.
    '''
    _name = 'stock.production.lot.qc.trigger.test'
    _description = 'Quality Control Test Triggers by Lot'
    _rec_name = 'trigger_id'
    _order = 'prodlot_id, sequence'

    # stock.production.lot.qc.trigger.test
    def name_get(self, cr, uid, ids, context=None):
        res = []
        for trigger in self.read(cr, uid, ids, ['trigger_id'], context):
            res.append((trigger['id'], trigger['trigger_id'][1]))
        return res

    # stock.production.lot.qc.trigger.test
    def _calc_test_state_data(self, cr, uid, ids, fieldnames, args,
            context=None):
        """
        Calcs the value of fields 'test_approved' and 'test_success'.
        The 'test_approved' field will be true if its test is in 'success' or
        'failed' final states, and the fields 'test_success' will be True only
        if its test is in 'success' state.
        """
        res = {}
        for lot_trigger in self.browse(cr, uid, ids, context):
            res[lot_trigger.id] = {}.fromkeys(fieldnames, False)

            if (not lot_trigger.test_id or
                    lot_trigger.test_id.state not in ('success', 'failed')):
                continue

            if 'test_approved' in fieldnames:
                res[lot_trigger.id]['test_approved'] = True
            if ('test_success' in fieldnames and
                    lot_trigger.test_id.state == 'success'):
                res[lot_trigger.id]['test_success'] = True
        return res

    _columns = {
        'prodlot_id': fields.many2one('stock.production.lot', 'Lot',
                required=True, ondelete="cascade"),
        'sequence': fields.integer('Sequence', required=True),
        'trigger_id': fields.many2one('qc.trigger', 'Trigger', required=True,
                help="The Quality Control Trigger Tag which defines when must "
                "to be created a Test (using the specified template) for a "
                "Production Lot of this Product."),
        'test_id': fields.many2one('qc.test', 'Test', required=True),
        'test_approved': fields.function(_calc_test_state_data, method=True,
                type='boolean', string="Test approved?", multi='test_state'),
        'test_success': fields.function(_calc_test_state_data, method=True,
                type='boolean', string="Test success?", multi='test_state'),
    }

    _defaults = {
        'sequence': 0,
    }
stock_production_lot_qc_trigger_test()


class stock_production_lot(osv.osv):
    '''
    Adds to the Lot an 'state' field and a workflow to manage its status
    related to the Quality test that has passed.
    It also adds one2many field to the model which defines the Quality Control
    Tests that it must to pass.
    '''
    _inherit = 'stock.production.lot'

    # stock.production.lot
    def get_available_states(self, cr, uid, context=None):
        """
        Returns the list of available states for Lot objects. It is defined as
        a function to make easier to extend the list of states.
        """
        return [
            ('draft', 'Draft'),
            ('pending_test', 'Waiting QC Test'),
            ('valid', 'Valid'),
            ('test_failed', 'QC Test Failed'),
            ('cancel', 'Cancelled'),
        ]

    # stock.production.lot
    def __get_available_states(self, cr, uid, context=None):
        """
        Returns the list of available states for Lot objects.
        It call's the function '_get_available_states' which could be
        reimplemented to extend or modify the list of available states.
        @see: _get_available_states
        """
        return self.get_available_states(cr, uid, context)

    # stock.production.lot
    def _calc_test_trigger_data(self, cr, uid, ids, fieldnames, args,
            context=None):
        trigger_proxy = self.pool.get('stock.production.lot.qc.trigger.test')

        res = {}
        for lot_id in ids:
            res[lot_id] = {}.fromkeys(fieldnames, [])

        lot_trigger_ids = trigger_proxy.search(cr, uid, [
                    ('prodlot_id', 'in', ids),
                ], context=context)

        for lot_trigger in trigger_proxy.browse(cr, uid, lot_trigger_ids,
                context):
            lot_id = lot_trigger.prodlot_id.id
            if 'qc_test_trigger_ro_ids' in fieldnames:
                res[lot_id]['qc_test_trigger_ro_ids'].append(lot_trigger.id)
            if 'qc_trigger_ids' in fieldnames:
                res[lot_id]['qc_trigger_ids'].append(lot_trigger.trigger_id.id)
        return res

    _columns = {
        # adds the 'readonly' and 'states' attributes
        'product_id': fields.many2one('product.product', 'Product',
                required=True, readonly=True, states={
                    'draft': [('readonly', False), ],
                }),
        'state': fields.selection(__get_available_states, 'State',
                required=True, readonly=True),
        'active': fields.boolean('Active'),

        'qc_test_trigger_ids': fields.one2many(
                'stock.production.lot.qc.trigger.test', 'prodlot_id',
                'QC Tests', help="Defines the Quality Control Tests that this "
                "Production Lot must to pass in certain situations defined by "
                "the Trigger Tag."),
        # Read Only version of previous field. Better solutions are wellcome
        'qc_test_trigger_ro_ids': fields.function(_calc_test_trigger_data,
                method=True, type='one2many', string='QC Tests',
                relation='stock.production.lot.qc.trigger.test',
                multi='trigges'),
        'qc_trigger_ids': fields.function(_calc_test_trigger_data, method=True,
                type='many2many', string='QC Triggers', relation='qc.trigger',
                multi='trigges'),

        'current_qc_test_trigger_id': fields.many2one(
                'stock.production.lot.qc.trigger.test',
                'Current QC Test Trigger',
                domain="[('id','in',[x.id for x in qc_test_trigger_ids])]",
                readonly=True, states = {
                    'draft': [('readonly', False), ],
                    'valid': [('readonly', False), ],
                }),
        'current_qc_test_id': fields.related('current_qc_test_trigger_id',
                'test_id', type='many2one', relation='qc.test',
                string="Current QC Test", readonly=True),
    }

    _defaults = {
        'state': 'draft',
        'active': True,
    }

    # stock.production.lot
    def onchange_product_id(self, cr, uid, ids, product_id, context):
        """
        Void function. Defined to could be extended in dependan modules
        """
        return {}

    # stock.production.lot
    def _calc_qc_test_vals(self, cr, uid, prodlot, context):
        """
        Prepare data to create a qc.test instance related to a Production Lot
        @param prodlot: Browse object of stock.production.lot
        @return: Dictionary of stock.production.lot values
        """
        reference = 'stock.production.lot,%d' % prodlot.id
        return {
            'object_id': reference,
        }

    # stock.production.lot
    def _calc_qc_test_trigger_ids_vals(self, cr, uid, prodlot, trigger_id,
            context):
        """
        Prepare data to create and write in the field 'qc_test_trigger_ids' of
        Production Lot the QC Test Triggers corresponding to the supplied
        trigger.
        @param prodlot: Browse object of stock.production.lot instance
        @param trigger_id: ID of qc.trigger instance
        @return: Dictionary of stock.production.lot values
        """
        qc_test_proxy = self.pool.get('qc.test')

        if trigger_id in [x.id for x in prodlot.qc_trigger_ids]:
            netsvc.Logger().notifyChannel(self._name, netsvc.LOG_DEBUG,
                    "Lot id:%d already has QC Test Trigger for Trigger %d" % (
                            prodlot.id, trigger_id))
            return False

        if trigger_id not in [x.id for x in prodlot.product_id.qc_trigger_ids]:
            netsvc.Logger().notifyChannel(self._name, netsvc.LOG_DEBUG,
                    "Product id:%d of Lot id:%d doesn't have QC Template "
                    "Trigger for Trigger %d" % (prodlot.product_id.id,
                            prodlot.id, trigger_id))
            return False

        test_trigger_vals = []
        for template_trigger in prodlot.product_id.qc_template_trigger_ids:
            if template_trigger.trigger_id.id != trigger_id:
                continue

            test_vals = self._calc_qc_test_vals(cr, uid, prodlot, context)
            test_id = qc_test_proxy.create(cr, uid, test_vals, context)

            qc_test_proxy.set_test_template(cr, uid, [test_id],
                    template_trigger.template_id.id, context=context)

            test_trigger_vals.append((0, 0, {
                        'sequence': template_trigger.sequence,
                        'trigger_id': template_trigger.trigger_id.id,
                        'test_id': test_id,
                    }))
        if not test_trigger_vals:
            return False

        return {
            'qc_test_trigger_ids': test_trigger_vals,
        }

    # stock.production.lot
    def create_qc_test_triggers(self, cr, uid, prodlot, trigger_id,
            set_next_test, context):
        """
        Create and write into Production Lot the Trigger Test corresponding to
        supplied Trigger, getting templates configuration and QC templates from
        the Product of Lot.
        @param prodlot: Browse object of stock.production.lot instance
        @param trigger_id: ID of qc.trigger instance
        @param set_next_test: Sets the first Test of Trigger as
                current_qc_test_id and move Lot workflow to Pending Test
        @return: Boolean value depending of triggers has been created
        @raise except_osv: If set_next_test is True and Lot is not in 'Draft'
                or 'Valid' state
        """
        trigger_proxy = self.pool.get('stock.production.lot.qc.trigger.test')
        wf_service = netsvc.LocalService("workflow")

        if set_next_test and prodlot.state not in ('draft', 'valid'):
            raise osv.except_osv(
                    _("Error setting next test!"),
                    _("It is trying to set a new next test for Production Lot "
                      "'%(lot_name)s' (id: %(lot_id)s) but it is in state "
                      "'%(lot_state)s' when it is expected 'Draft' or 'Valid' "
                      "states to change the current test.") % {
                        'lot_name': prodlot.name,
                        'lot_id': prodlot.id,
                        'lot_state': prodlot.state,
                    })

        test_trigger_vals = self._calc_qc_test_trigger_ids_vals(cr, uid,
            prodlot, trigger_id, context)
        if test_trigger_vals:
            self.write(cr, uid, [prodlot.id], test_trigger_vals, context)
            res = True
        else:
            res = False

        if not set_next_test:
            return res

        trigger_test_ids = trigger_proxy.search(cr, uid, [
                    ('prodlot_id', '=', prodlot.id),
                    ('trigger_id', '=', trigger_id),
                ], order='sequence asc', limit=1, context=context)
        if trigger_test_ids:
            self.write(cr, uid, [prodlot.id], {
                        'current_qc_test_trigger_id': trigger_test_ids[0],
                    }, context)

        # If 'set_next_test' is true it move the workflow independly if the Lot
        # has any test (in this case it will be moved to 'Valid' state
        if prodlot.state == 'draft':
            wf_service.trg_validate(uid, 'stock.production.lot', prodlot.id,
                    'confirm', cr)
        else:
            wf_service.trg_validate(uid, 'stock.production.lot', prodlot.id,
                    'next_test', cr)
        return res

    # stock.production.lot
    def action_workflow_draft(self, cr, uid, ids, context=None):
        """
        Sets the State of Lot to 'Draft' and deactivate it
        """
        self.write(cr, uid, ids, {
                    'state': 'draft',
                    'active': False,
                }, context)
        return True

    # stock.production.lot
    def _get_next_test_trigger_id(self, cr, uid, prodlot, context):
        """
        Calculates the Lot Trigger Test Id for the next Test to pass.
        If there isn't a current trigger test specified, it returns False.
        If the current Trigger Test is not 'Success', it returns this.
        In other case, search the next trigger test (by Sequence) with the same
        Trigger and return its Id.
        @param prodlot: Browse object of stock.production.lot
        @return: ID of stock.production.lot.qc.trigger.test instance or False
        """
        trigger_proxy = self.pool.get('stock.production.lot.qc.trigger.test')

        if not prodlot.current_qc_test_trigger_id:
            return False

        # if current test is not 'Success' => it remains as Current test
        if not prodlot.current_qc_test_trigger_id.test_success:
            return prodlot.current_qc_test_trigger_id.id

        # if current test is 'Success' => search next test for the same trigger
        current_trigger = prodlot.current_qc_test_trigger_id
        next_trigger_ids = trigger_proxy.search(cr, uid, [
                    ('prodlot_id', '=', prodlot.id),
                    ('id', '!=', current_trigger.id),
                    ('sequence', '>=', current_trigger.sequence),
                    ('trigger_id', '=', current_trigger.trigger_id.id),
                ], limit=1, context=context)

        return next_trigger_ids and next_trigger_ids[0] or False

    # stock.production.lot
    def action_workflow_next_test(self, cr, uid, ids, context=None):
        """
        Find the Next Test to pass and write it to 'current_qc_test_trigger_id'
        field.
        It will be empty if there isn't any current test or there aren't any
        next test for current Trigger.
        It will maintain the current test trigger if its test is not 'Success'
        @see: _get_next_test_trigger_id
        @param ids: List of IDs of stock.production.lot
        """
        for prodlot in self.browse(cr, uid, ids, context):
            next_trigger_id = self._get_next_test_trigger_id(cr, uid, prodlot,
                    context)
            self.write(cr, uid, [prodlot.id], {
                        'current_qc_test_trigger_id': next_trigger_id,
                    }, context)
        return True

    # stock.production.lot
    def test_valid(self, cr, uid, ids, context=None):
        """
        Checks that Production Lot doesn't has Current Test or it is in
        'Success' state.
        """
        for prodlot in self.browse(cr, uid, ids, context):
            if (prodlot.current_qc_test_id and
                    prodlot.current_qc_test_id.state != 'success'):
                return False
        return True

    # stock.production.lot
    def action_workflow_valid(self, cr, uid, ids, context=None):
        """
        Sets the State of Lot to 'Valid' and activate the Lot.
        """
        self.write(cr, uid, ids, {
                    'current_qc_test_trigger_id': False,
                    'state': 'valid',
                    'active': True,
                }, context)
        return True

    # stock.production.lot
    def test_pending_test(self, cr, uid, ids, context=None):
        """
        Checks that Production Lot has a Current Test and it is not Success
        """
        for prodlot in self.browse(cr, uid, ids, context):
            if (not prodlot.current_qc_test_id or
                    prodlot.current_qc_test_trigger_id.test_success):
                return False
        return True

    # stock.production.lot
    def action_workflow_pending_test(self, cr, uid, ids, context=None):
        """
        Sets the State of Lot to 'Pending Test' and deactivate it, and returns
        the ID of current QC Test.
        """
        assert len(ids) == 1, "Unexpected number of Lot IDs in function of " \
                "'Pending Test' workflow step."

        lot = self.browse(cr, uid, ids[0], context)
        assert lot.current_qc_test_id, "The 'Current Test' field is " \
                "required for the Lots which reaches the 'Pending Test' " \
                "workflow step, but the Lot %d doesn't have." % lot.id

        self.write(cr, uid, ids, {
                    'state': 'pending_test',
                    'active': False,
                }, context)
        return lot.current_qc_test_id.id

    # stock.production.lot
    def action_workflow_test_failed(self, cr, uid, ids, context=None):
        """
        Sets the State of Lot to 'Test Failed', deactivate it and returns the
        ID of current Test
        """
        assert len(ids) == 1, "Unexpected number of Lot IDs in function of " \
                "'Pending Test' workflow step."

        lot = self.browse(cr, uid, ids[0], context)
        assert lot.current_qc_test_id, "The 'Current Test' field is " \
                "required for the Lots which reaches the 'Test Failed' " \
                "workflow step, but the Lot %d doesn't have." % lot.id

        self.write(cr, uid, ids, {
                    'state': 'test_failed',
                    'active': False,
                }, context)
        return lot.current_qc_test_id.id

    def test_not_qc_test_subflow(self, cr, uid, ids, context=None):
        """
        To be able to go out of 'subflow' activity without subflow signal,
        the workitem must to be disassociated of any subflow.
        It could be done with 'force_cancel' function which after raise
        'cancel' signal
        """
        workitem_proxy = self.pool.get('workflow.workitem')

        workflow_ids = self.pool.get('workflow').search(cr, uid, [
                    ('osv', '=', 'stock.production.lot'),
                    ('name', '=', 'stock.production.lot.basic'),
                ], context=context)
        assert len(workflow_ids) == 1, "Unexpected number of workflows for " \
                "'stock.production.lot' with name " \
                "'stock.production.lot.basic'. Expected 1 and found %d" \
                        % len(workflow_ids)

        instance_ids = self.pool.get('workflow.instance').search(cr, uid, [
                    ('wkf_id', '=', workflow_ids[0]),
                    ('res_type', '=', 'stock.production.lot'),
                    ('res_id', 'in', ids),
                    ('state', '=', 'active'),
                ], context)
        if not instance_ids:
            netsvc.Logger().notifyChannel(self._name, netsvc.LOG_WARNING,
                    "Unexpected not found any active Workflow Instance for "
                    "Production Lots with ids '%s' in "
                    "test_not_qc_test_subflow function." % str(ids))
            return True

        workitem_ids = workitem_proxy.search(cr, uid, [
                    ('inst_id', 'in', instance_ids),
                    ('state', '=', 'running'),
                    ('subflow_id', '!=', False),
                ], context=context)
        if not workitem_ids:
            return True

        lot_w_subflow = [str(w.inst_id.res_id)
                for w in workitem_proxy.browse(cr, uid, workitem_ids, context)]
        raise osv.except_osv(
                _("Error Cancelling Lot with subflow!"),
                _("You are trying to cancel the Production Lots with IDs "
                  "'%(lot_ids)s' which are associated to QC Test workflow, "
                  "and it is not allowed.\n"
                  "Please, use the 'Force Cancel' button or function to "
                  "cancel a Lot in 'Pending Test' or 'Test Failed' state.") % {
                    'lot_ids': ", ".join(lot_w_subflow),
                })
        return False

    # stock.production.lot
    def action_workflow_cancel(self, cr, uid, ids, context=None):
        """
        Sets the State of Lot to 'Cancel', deactivate it and leave empty the
        'Current QC Test Trigger' field.
        """
        self.write(cr, uid, ids, {
                    'current_qc_test_trigger_id': False,
                    'state': 'cancel',
                    'active': False,
                }, context)
        return True

    # stock.production.lot
    def action_force_cancel(self, cr, uid, ids, context=None):
        """
        Find Workitems (workflow) for these Lots with subflow and disassociate
        them and sets their state to 'complete', and raise a 'cancel' signal
        for all supplied Lot's ID's.
        """
        workitem_proxy = self.pool.get('workflow.workitem')
        wf_service = netsvc.LocalService("workflow")

        workflow_ids = self.pool.get('workflow').search(cr, uid, [
                    ('osv', '=', 'stock.production.lot'),
                    ('name', '=', 'stock.production.lot.basic'),
                ], context=context)
        assert len(workflow_ids) == 1, "Unexpected number of workflows for " \
                "'stock.production.lot' with name " \
                "'stock.production.lot.basic'. Expected 1 and found %d" \
                        % len(workflow_ids)

        instance_ids = self.pool.get('workflow.instance').search(cr, uid, [
                    ('wkf_id', '=', workflow_ids[0]),
                    ('res_type', '=', 'stock.production.lot'),
                    ('res_id', 'in', ids),
                    ('state', '=', 'active'),
                ], context=context)
        if instance_ids:
            workitem_ids = workitem_proxy.search(cr, uid, [
                        ('inst_id', 'in', instance_ids),
                        ('state', '=', 'running'),
                        ('subflow_id', '!=', False),
                    ], context=context)
            if workitem_ids:
                workitem_proxy.write(cr, uid, workitem_ids, {
                            'subflow_id': False,
                            'state': 'complete',
                        }, context)

        for lot_id in ids:
            wf_service.trg_validate(uid, 'stock.production.lot', lot_id,
                    'cancel', cr)
        return True

    # stock.production.lot
    def copy(self, cr, uid, orig_id, default=None, context=None):
        """
        It only duplicate the trigger tests if the context has a True value for
        'duplicate_trigger_test' key
        """
        if not context or not context.get('duplicate_trigger_test'):
            default['qc_test_trigger_ids'] = False

        return super(stock_production_lot, self).copy(cr, uid, orig_id,
                default, context)
stock_production_lot()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
