# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EprApprovalRule(models.Model):
    _name = 'epr.approval.rule'
    _description = 'Approval Rule Header'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

    name = fields.Char(
        string='Rule Name',
        required=True,
        tracking=True
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    # Thứ tự ưu tiên của Rule (nếu có nhiều rule khớp điều kiện)
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )

    # Điều kiện áp dụng Rule (VD: Áp dụng cho phòng ban nào?)
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Apply for Department'
    )

    # Chi tiết các bước duyệt
    line_ids = fields.One2many(
        comodel_name='epr.approval.rule.line',
        inverse_name='rule_id',
        string='Approval Steps'
    )


class EprApprovalRuleLine(models.Model):
    _name = 'epr.approval.rule.line'
    _description = 'Approval Rule Steps'
    _order = 'sequence, id'

    rule_id = fields.Many2one(
        comodel_name='epr.approval.rule',
        ondelete='cascade'
    )

    sequence = fields.Integer(
        string='Step',
        default=1
    )

    # Tên bước (VD: Quản lý duyệt, Giám đốc duyệt)
    name = fields.Char(
        string='Step Name',
        required=True
    )

    # Điều kiện kích hoạt bước này
    min_amount = fields.Monetary(
        string='Minimum Amount',
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        related='rule_id.company_id.currency_id'
    )

    # Ai được duyệt bước này?
    user_ids = fields.Many2many(
        'res.users',
        string='Approvers',
        required=True
    )

    # Loại duyệt: 1 người bất kỳ trong list hay bắt buộc tất cả?
    approval_type = fields.Selection([
        ('any', 'Any User'),
        ('all', 'All Users')
    ], string='Approval Type', default='any', required=True)
