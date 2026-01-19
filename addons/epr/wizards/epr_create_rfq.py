# -*- coding: utf-8 -*-
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError


class EprCreateRfqWizard(models.TransientModel):
    _name = 'epr.create.rfq.wizard'
    _description = 'Wizard: Merge PRs to RFQ'

    # Danh sách các dòng PR đang được xử lý trong Wizard
    line_ids = fields.One2many(
        comodel_name='epr.create.rfq.line',
        inverse_name='wizard_id',
        string='PR Lines to Process'
    )

    # -------------------------------------------------------------------------
    # 1. LOAD DATA (BẮT BUỘC CÓ)
    # -------------------------------------------------------------------------
    @api.model
    def default_get(self, fields_list):
        """
        Lấy dữ liệu từ các PR được chọn (active_ids) và điền vào dòng Wizard.
        """
        res = super().default_get(fields_list)

        # Lấy ID của các PR đang được chọn ở màn hình danh sách
        active_ids = self.env.context.get('active_ids', [])

        if not active_ids:
            return res

        # Đọc dữ liệu PR
        requests = self.env['epr.purchase.request'].browse(active_ids)

        # Kiểm tra trạng thái (Optional: chỉ cho phép gộp PR đã duyệt)
        if any(pr.state != 'approved' for pr in requests):
            raise UserError(_("Bạn chỉ có thể tạo RFQ từ các PR đã được phê duyệt."))

        lines_vals = []
        for pr in requests:
            # Loop qua từng dòng sản phẩm của PR để đưa vào Wizard
            # Giả sử PR Line có model là 'epr.purchase.request.line'
            for pr_line in pr.line_ids:
                lines_vals.append(Command.create({
                    # Link dữ liệu để truy vết sau này
                    'request_id': pr.id,
                    'pr_line_id': pr_line.id,

                    # Dữ liệu hiển thị/chỉnh sửa trên wizard
                    'suggested_vendor_name': pr_line.suggested_vendor_name,
                    'final_vendor_id': pr_line.final_vendor_id.id,

                    'final_product_id': pr_line.product_id.id,
                    'product_description': pr_line.name or pr_line.product_id.name,
                    'quantity': pr_line.quantity,
                    'price_unit': pr_line.estimated_price,
                    'uom_id': (
                        pr_line.product_id.uom_po_id.id or
                        pr_line.product_id.uom_id.id
                    ),
                }))

        # Gán danh sách lệnh tạo dòng vào field line_ids
        res['line_ids'] = lines_vals
        return res

    def action_create_rfqs(self):
        """
        Gộp PR thành RFQ:
        1. Validate: Chọn đầy đủ Vendor & Product.
        2. Gom nhóm theo Vendor.
        3. Tạo RFQ Header & Lines (Dùng sudo để bypass quyền truy cập PR).
        """
        self.ensure_one()

        # 1. Validate & Sync Vendor
        for line in self.line_ids:
            if not line.final_vendor_id:
                raise UserError(_("Vui lòng chọn Vendor cho sản phẩm: %s", line.product_description))

            if line.pr_line_id.final_vendor_id != line.final_vendor_id:
                line.pr_line_id.sudo().write({
                    'final_vendor_id': line.final_vendor_id.id
                })

        # 2. Grouping
        grouped_lines = {}
        for wiz_line in self.line_ids:
            vendor = wiz_line.final_vendor_id
            if vendor not in grouped_lines:
                grouped_lines[vendor] = self.env['epr.create.rfq.line']
            grouped_lines[vendor] |= wiz_line

        created_rfqs = self.env['epr.rfq'].sudo()

        # 3. RFQ Creation
        for vendor, wiz_lines in grouped_lines.items():
            # A. Lấy danh sách PR unique cho field Many2many
            source_requests = wiz_lines.mapped('request_id')

            # B. Chuẩn bị dữ liệu lines (One2many)
            rfq_line_commands = []
            for wiz_line in wiz_lines:
                rfq_line_commands.append(Command.create({
                    'product_id': wiz_line.final_product_id.id,
                    'description': wiz_line.product_description,
                    'quantity': wiz_line.quantity,
                    'price_unit': wiz_line.price_unit,
                    'uom_id': wiz_line.uom_id.id,
                    # Link ngược lại dòng PR gốc để truy vết
                    'pr_line_id': wiz_line.pr_line_id.id
                }))

            # Tạo RFQ Header
            rfq_vals = {
                'partner_id': vendor.id,
                'state': 'draft',
                'date_order': fields.Datetime.now(),
                'request_ids': [Command.set(source_requests.ids)],
                'line_ids': rfq_line_commands,
            }

            rfq = self.env['epr.rfq'].create(rfq_vals)
            created_rfqs |= rfq

        # 4. Redirect
        if not created_rfqs:
            return {'type': 'ir.actions.act_window_close'}

        action = {
            'name': _('Generated RFQs'),
            'type': 'ir.actions.act_window',
            'res_model': 'epr.rfq',
            'context': {'create': False},
        }

        if len(created_rfqs) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = created_rfqs.id
        else:
            action['view_mode'] = 'list,form' # Odoo 18 dùng 'list'
            action['domain'] = [('id', 'in', created_rfqs.ids)]

        return action


class EprCreateRfqLine(models.TransientModel):
    _name = 'epr.create.rfq.line'
    _description = 'Wizard Line: PR Details'

    wizard_id = fields.Many2one('epr.create.rfq.wizard', string='Wizard')

    # Dữ liệu PR gốc
    request_id = fields.Many2one(
        'epr.purchase.request',
        string='PR',
        readonly=True
    )

    pr_line_id = fields.Many2one(
        'epr.purchase.request.line',
        string='PR Line',
        readonly=True
    )

    suggested_vendor_name = fields.Char(string='Suggested Vendor', readonly=True)

    # Cho phép User chọn/sửa trong Wizard
    final_vendor_id = fields.Many2one(
        'res.partner',
        string='Final Vendor',
        required=True
    )

    final_product_id = fields.Many2one(
        'product.product',
        string='Final Product',
        required=True
    )

    product_description = fields.Char(string='Description')
    quantity = fields.Float(
        string='Qty',
        digits='Product Unit of Measure'
    )

    price_unit = fields.Float(
        string='Price',
        digits='Product Price'
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='UoM'
    )

    uom_name = fields.Char(
        string='PR UoM',
        readonly=True
    )

    @api.onchange('final_product_id')
    def _onchange_final_product_id(self):
        if self.final_product_id:
            product = self.final_product_id
            self.uom_id = product.uom_po_id or product.uom_id
