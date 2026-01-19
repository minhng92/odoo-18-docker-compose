# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # === HEADER-LEVEL LINKING ===
    epr_source_rfq_ids = fields.Many2many(
        comodel_name='epr.rfq',
        relation='epr_rfq_purchase_order_rel',  # Tên bảng trung gian rõ ràng
        column1='purchase_id',
        column2='epr_rfq_id',
        string='Source ePR RFQs',
        copy=False,
        readonly=True,
        help="Danh sách các phiếu yêu cầu báo giá (EPR RFQ) nguồn tạo nên PO này."
    )

    epr_source_pr_ids = fields.Many2many(
        comodel_name='epr.purchase.request',
        relation='epr_pr_purchase_order_rel',
        column1='purchase_id',
        column2='epr_pr_id',
        string='Source ePR Requests',
        copy=False,
        readonly=True,
    )

    # === COMPUTED FIELDS CHO SMART BUTTON (Line-Level Linking) ===
    epr_rfq_count = fields.Integer(
        string='RFQ Count',
        compute='_compute_epr_counts'
    )

    epr_pr_count = fields.Integer(
        string='PR Count',
        compute='_compute_epr_counts'
    )

    @api.depends('epr_source_rfq_ids', 'epr_source_pr_ids')
    def _compute_epr_counts(self):
        for po in self:
            po.epr_rfq_count = len(po.epr_source_rfq_ids)
            po.epr_pr_count = len(po.epr_source_pr_ids)

    # === ACTION SMART BUTTON ===
    def action_view_epr_rfqs(self):
        """Mở danh sách các EPR RFQ nguồn"""
        self.ensure_one()
        rfq_ids = self.epr_source_rfq_ids.ids

        # Nếu chỉ có 1 RFQ nguồn, mở form view trực tiếp cho tiện
        if len(rfq_ids) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'epr.rfq',
                'view_mode': 'form',
                'res_id': rfq_ids[0],
                'target': 'current',
            }

        # Nếu có nhiều RFQs nguồn, mở list view
        return {
            'name': _('Source RFQs'),
            'type': 'ir.actions.act_window',
            'res_model': 'epr.rfq',
            'view_mode': 'list,form',
            'domain': [('id', 'in', rfq_ids)],
            'context': {'create': False}, 
        }

    def action_view_epr_prs(self):
        """Mở danh sách các PR nguồn"""
        self.ensure_one()
        pr_ids = self.epr_source_pr_ids.ids
        return {
            'name': _('Source PRs'),
            'type': 'ir.actions.act_window',
            'res_model': 'epr.purchase.request',
            'view_mode': 'list,form',
            'domain': [('id', 'in', pr_ids)],
            'context': {'create': False},
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # === FIELD LIÊN KẾT QUAN TRỌNG NHẤT ===
    epr_rfq_line_id = fields.Many2one(
        comodel_name='epr.rfq.line',
        string='EPR RFQ Line Ref',
        readonly=True,
        copy=False,
        ondelete='set null',
        help="Dòng chi tiết tương ứng trên phiếu yêu cầu báo giá."
    )
