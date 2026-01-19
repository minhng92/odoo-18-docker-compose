# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EprApprovalEntry(models.Model):
    _name = 'epr.approval.entry'
    _description = 'Approval Request Entry'
    _order = 'sequence, id'

    # Link về RFQ
    rfq_id = fields.Many2one(
        comodel_name='epr.rfq',
        string='RFQ Reference',
        ondelete='cascade',
        required=True
    )

    currency_id = fields.Many2one(
        related='rfq_id.currency_id',
        string='Currency',
        readonly=True
    )
    amount_total = fields.Monetary(
        related='rfq_id.amount_total',
        string='Total Amount',
        currency_field='currency_id',
        readonly=True
    )
    # Thông tin snapshot từ Rule (để truy vết nếu rule gốc bị sửa)
    rule_line_id = fields.Many2one(
        comodel_name='epr.approval.rule.line',
        string='Original Rule Line'
    )

    name = fields.Char(
        string='Step Name',
        required=True
    )

    sequence = fields.Integer(
        string='Step Sequence',
        required=True
    )

    # Trạng thái của bước này
    status = fields.Selection(
        selection=[
            ('new', 'To Approve'),
            ('pending', 'Pending Previous Step'),  # Chờ bước trước
            ('approved', 'Approved'),
            ('refused', 'Refused')
        ],
        string='Status',
        default='new',
        required=True,
        readonly=True
    )

    # Ai cần duyệt (Copy từ Rule sang)
    required_user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Required Approvers',
        readonly=True
    )

    # Ai đã duyệt thực tế (Audit Log)
    actual_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Approved By',
        readonly=True
    )

    approval_date = fields.Datetime(
        string='Date',
        readonly=True
    )

    rejection_reason = fields.Text(
        string='Reason'
    )

    # Logic UI: Cho phép nút Duyệt hiện hay ẩn
    can_approve = fields.Boolean(
        compute='_compute_can_approve'
    )

    @api.depends('status', 'required_user_ids')
    @api.depends_context('uid')
    def _compute_can_approve(self):
        current_user = self.env.user
        for entry in self:
            # 1. Phải ở trạng thái 'new'
            # 2. User hiện tại phải nằm trong danh sách được phép
            if entry.status == 'new' and current_user in entry.required_user_ids:
                entry.can_approve = True
            else:
                entry.can_approve = False

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_approve_line(self):
        """User bấm nút Approve trên dòng"""
        self.ensure_one()
        if not self.can_approve:
            raise UserError(_("You are not authorized to approve this step or it is not ready."))

        self.write({
            'status': 'approved',
            'actual_user_id': self.env.user.id,
            'approval_date': fields.Datetime.now()
        })

        # Trigger kiểm tra xem RFQ đã được duyệt hoàn toàn chưa
        self.rfq_id._check_approval_completion()

    def action_reject_line(self):
        """User bấm nút Refuse - Mở wizard để nhập lý do"""
        self.ensure_one()
        return {
            'name': _('Reject RFQ'),
            'type': 'ir.actions.act_window',
            'res_model': 'epr.reject.rfq.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.rfq_id.id,
                'active_model': 'epr.rfq'
            }
        }
