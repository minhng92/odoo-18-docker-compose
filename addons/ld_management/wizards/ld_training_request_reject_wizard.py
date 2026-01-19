# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LdTrainingRequestRejectWizard(models.TransientModel):
    """
    Transient model to handle the rejection reason input.
    """
    _name = 'ld.training.request.reject.wizard'
    _description = 'L&D Training Request Reject Wizard'

    reason = fields.Text(
        string='Rejection Reason',
        required=True,
        help="Please explain why the training request is being rejected."
    )

    def action_confirm_reject(self):
        """
        Confirm the rejection:
        1. Validate permissions (Double-check).
        2. Write reason and update state on the main record.
        3. Log message in chatter.
        """
        self.ensure_one()

        # 1. Retrieve Context
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')

        if not active_id or active_model != 'ld.training.request':
            raise UserError(_("System error: Wizard called from incorrect context."))

        request_id = self.env['ld.training.request'].browse(active_id)

        if not request_id.exists():
            raise UserError(_("Request record not found."))

        # 2. Security Check (Layer 2)
        # Even though we checked in action_reject, it's safer to re-check here
        is_line_manager = self.env.user == request_id.line_manager_id
        is_admin = self.env.user.has_group('ld_management.group_ld_manager')

        if not is_line_manager and not is_admin:
            raise UserError(_("Access Denied: You do not have permission to reject this request."))

        # 3. Process Rejection
        request_id.write({
            'rejection_reason': self.reason,
            'state': 'rejected'
        })

        # 4. Log in Chatter
        # Using subtype_xmlid='mail.mt_comment' ensures it sends notifications to followers (like the employee)
        request_id.message_post(
            body=_("Request rejected by %s.<br/><strong>Reason:</strong> %s") % (self.env.user.name, self.reason),
            message_type='comment',
            subtype_xmlid='mail.mt_comment' 
        )

        # 5. UI Feedback
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Request Rejected'),
                'message': _('The request has been rejected successfully.'),
                'type': 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
