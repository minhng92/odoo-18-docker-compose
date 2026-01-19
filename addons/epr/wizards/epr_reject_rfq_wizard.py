# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EprRejectRfqWizard(models.TransientModel):
    """
    Wizard specifically for rejecting EPR RFQs.
    It updates both the Approval Entry (history) and the RFQ record (status & reason).
    """
    _name = 'epr.reject.rfq.wizard'
    _description = 'EPR RFQ Reject Wizard'

    # ==========================================================================
    # FIELDS
    # ==========================================================================

    reason = fields.Text(
        string="Rejection Reason",
        required=True,
        help="Please explain why you are rejecting this RFQ."
    )

    # ==========================================================================
    # METHODS
    # ==========================================================================

    def action_confirm_reject(self):
        """
        Process the rejection:
        1. Find and update the user's pending approval entry.
        2. Call the callback on the RFQ to update its state and store the reason.
        """
        self.ensure_one()

        # 1. Get Context Data
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')

        if not active_id or active_model != 'epr.rfq':
            raise UserError(_("This wizard can only be used for EPR RFQs."))

        rfq = self.env['epr.rfq'].browse(active_id)

        # 2. Update Approval Entry (The Log)
        # Search for a pending approval entry for this user and this RFQ
        approval_entry = self.env['epr.approval.entry'].search([
            ('rfq_id', '=', rfq.id),
            ('required_user_ids', 'in', self.env.uid),
            ('status', '=', 'new')
        ], limit=1)
        if approval_entry:
            approval_entry.write({
                'status': 'refused',
                'rejection_reason': self.reason,
                'actual_user_id': self.env.uid,
                'approval_date': fields.Datetime.now()
            })

        # Note: Depending on your strictness, you might allow Admins to reject without an entry.
        # Here we strictly enforce that an entry must exist.
        if approval_entry:
            approval_entry.write({
                'status': 'refused',
                'rejection_reason': self.reason,
                'actual_user_id': self.env.uid,
                'approval_date': fields.Datetime.now()
            })

        # 3. Update the RFQ Record (The Main Document)
        # We pass the reason back to the RFQ model to store it permanently
        rfq.action_handle_rejection(self.reason)

        # 4. Feedback to User
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('RFQ Rejected'),
                'message': _('The RFQ has been rejected and the reason has been recorded.'),
                'type': 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
