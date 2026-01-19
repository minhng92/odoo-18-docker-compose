# -*- coding: utf-8 -*-
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError, ValidationError


class EprRfq(models.Model):
    _name = 'epr.rfq'
    _description = 'EPR Request for Quotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # === 1. IDENTIFICATION ===
    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    active = fields.Boolean(default=True)

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('sent', 'Sent'),
            ('received', 'Received'),      # Nhà cung cấp đã báo giá
            ('to_approve', 'To Approve'),  # Trình sếp duyệt giá
            ('approved', 'Approved'),      # Đã duyệt xong, chờ PO
            ('confirmed', 'Confirmed'),    # Đã chốt -> Đang tạo/Có PO
            ('rejected', 'Rejected'),      # Đã từ chối
            ('cancel', 'Cancelled')
        ],
        string='Status',
        readonly=True,
        index=True,
        copy=False,
        default='draft',
        tracking=True
    )

    # Tích hợp với Approval Entry
    approval_state = fields.Selection(
        selection=[
            ('draft', 'Not Required'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('refused', 'Refused')
        ],
        string='Approval Matrix Status',
        compute='_compute_approval_state',
        store=True
    )

    approval_entry_ids = fields.One2many(
        comodel_name='epr.approval.entry',
        inverse_name='rfq_id',
        string='Approvals'
    )

    # Tính tổng tiền trên RFQ để so sánh trong approval process
    amount_total = fields.Monetary(
        compute='_compute_amount_total',
        string='Total',
        currency_field='currency_id'
    )

    # Stores the reason directly on the RFQ for easy visibility
    rejection_reason = fields.Text(
        string='Rejection Reason',
        readonly=True,
        tracking=True,
        help="The reason why this RFQ was rejected."
    )

    department_id = fields.Many2one(
        comodel_name='hr.department',
        compute='_compute_department_id',
        string='Department',
        store=True,
        help="Phòng ban của người yêu cầu (lấy từ PR đầu tiên)."
    )

    @api.depends('request_ids.department_id')
    def _compute_department_id(self):
        for rfq in self:
            # Lấy phòng ban từ PR đầu tiên gắn với RFQ này
            rfq.department_id = rfq.request_ids[:1].department_id or False

    # === 2. RELATIONS ===
    # Link ngược lại PR gốc (01 RFQ có thể gom nhiều PR)
    request_ids = fields.Many2many(
        comodel_name='epr.purchase.request',
        relation='epr_rfq_purchase_request_rel',  # Tên bảng trung gian
        column1='rfq_id',
        column2='request_id',
        string='Source Requests',
        # Chỉ lấy các PR đã duyệt để tạo RFQ
        domain="[('state', '=', 'approved')]"
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        required=True,
        tracking=True
        # domain="[('supplier_rank', '>', 0)]",  # Chỉ chọn đã từng được chọn qua ít nhất 01 lần
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )

    # === 3. DATES ===
    date_order = fields.Datetime(
        string='Order Date', 
        default=fields.Datetime.now,
        readonly=True
    )

    date_deadline = fields.Date(
        string='Bid Deadline',
        help="Ngày hạn chót Vendor phải gửi báo giá",
        readonly=True
    )

    # === 4. LINES & PURCHASES ===
    line_ids = fields.One2many(
        comodel_name='epr.rfq.line',
        inverse_name='rfq_id',
        string='Products',
        copy=True
    )

    # Link sang Purchase Order gốc của Odoo (Many2many)
    purchase_ids = fields.Many2many(
        comodel_name='purchase.order',
        relation='epr_rfq_purchase_order_rel',
        column1='epr_rfq_id',
        column2='purchase_id',
        string='Purchase Orders'
    )

    purchase_count = fields.Integer(
        compute='_compute_purchase_count',
        string='PO Count'
    )

    request_count = fields.Integer(
        compute='_compute_request_count',
        string='PR Count'
    )

    # -------------------------------------------------------------------------
    # 5. COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('purchase_ids')
    def _compute_purchase_count(self):
        for rfq in self:
            rfq.purchase_count = len(rfq.purchase_ids)

    # Link ngược về PR gốc
    @api.depends('request_ids')
    def _compute_request_count(self):
        for rfq in self:
            rfq.request_count = len(rfq.request_ids)

    # Compute Approval State
    @api.depends('approval_entry_ids.status')
    def _compute_approval_state(self):
        for rfq in self:
            if not rfq.approval_entry_ids:
                rfq.approval_state = 'draft'
                continue

            # Nếu có bất kỳ dòng nào bị từ chối -> Toàn bộ bị từ chối
            if any(e.status == 'refused' for e in rfq.approval_entry_ids):
                rfq.approval_state = 'refused'
            # Nếu tất cả đã duyệt -> Approved
            elif all(e.status == 'approved' for e in rfq.approval_entry_ids):
                rfq.approval_state = 'approved'
            # Còn lại là đang chờ
            else:
                rfq.approval_state = 'pending'

    # === 6. CRUD OVERRIDES ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('epr.rfq') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.subtotal')
    def _compute_amount_total(self):
        for rfq in self:
            rfq.amount_total = sum(rfq.line_ids.mapped('subtotal'))

    # -------------------------------------------------------------------------
    # 7. ACTIONS
    # -------------------------------------------------------------------------
    def action_send_email(self):
        """Gửi email RFQ cho Vendor"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Chỉ có thể gửi RFQ khi ở trạng thái Draft."))
        self.write({'state': 'sent'})
        return True

    def action_mark_received(self):
        """Chuyển trạng thái sang Received khi nhận được phản hồi từ NCC"""
        for rfq in self:
            if rfq.state != 'sent':
                # Tư vấn: Nên chặn nếu nhảy cóc trạng thái để đảm bảo quy trình
                raise UserError(_("Chỉ có thể đánh dấu 'Đã nhận' khi RFQ đang ở trạng thái 'Đã gửi'."))
            rfq.write({'state': 'received'})

    def action_confirm(self):
        """Chốt RFQ, chuyển sang Confirmed"""
        for rfq in self:
            if rfq.state != 'approved':
                raise UserError(_("Chỉ có thể xác nhận khi RFQ đã được duyệt (Trạng thái 'Approved')."))
            rfq.write({
                'state': 'confirmed',
            })

    def action_cancel_rfq(self):
        """Hủy RFQ ở bất kỳ trạng thái nào (trừ khi đã hủy rồi)"""
        for rfq in self:
            if rfq.state == 'cancel':
                continue

            # Nếu đã có PO liên kết, nên cảnh báo hoặc hủy luôn PO con
            if rfq.purchase_ids and any(po.state not in ['cancel'] for po in rfq.purchase_ids):
                raise UserError(_("Không thể hủy RFQ này vì đã có Đơn mua hàng (PO) được tạo. Vui lòng hủy PO trước."))

            rfq.write({'state': 'cancel'})

    def action_create_po(self):
        """Chuyển đổi RFQ này thành Purchase Order"""
        self.ensure_one()
        if not self.line_ids:
            raise ValidationError(_("Vui lòng thêm sản phẩm trước khi tạo PO."))

        # Logic tạo PO
        po_vals = {
            'partner_id': self.partner_id.id,
            'date_order': fields.Datetime.now(),
            'epr_source_rfq_ids': [Command.link(self.id)],  # Link ngược lại RFQ này (Many2many)
            'origin': self.name,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'order_line': []
        }

        for line in self.line_ids:
            po_vals['order_line'].append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.description or line.product_id.name,
                'product_qty': line.quantity,
                'price_unit': line.price_unit,
                'product_uom': line.uom_id.id,
                'date_planned': fields.Datetime.now(),
            }))

        new_po = self.env['purchase.order'].create(po_vals)

        self.write({'state': 'confirmed'})

        # Mở view PO vừa tạo
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': new_po.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_reject(self):
        """
        Opens the specific RFQ Rejection Wizard.
        """
        self.ensure_one()
        return {
            'name': _('Reject RFQ'),
            'type': 'ir.actions.act_window',
            'res_model': 'epr.reject.rfq.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reason': self.rejection_reason or '', # Optional: Pre-fill if needed
                'active_id': self.id,
                'active_model': 'epr.rfq'
            }
        }

    # === CALLBACK: HANDLE REJECTION ===
    def action_handle_rejection(self, reason):
        """
        Callback method called by the Wizard after confirmation.
        1. Updates the state to 'cancel' (or keeps it in a specific rejected state).
        2. Stores the reason.
        """
        for rfq in self:
            rfq.write({
                'state': 'rejected',            # Move RFQ to Cancelled state
                'approval_state': 'refused',    # Update Approval Matrix status
                'rejection_reason': reason      # Persist the reason on the main record
            })

            # Log a chatter message for visibility
            # rfq.message_post(
            #     body=_("RFQ has been rejected. Reason: %s") % reason,
            #     message_type='comment',
            #     subtype_xmlid='mail.mt_note'
            # )

    def action_reset_draft(self):
        """Cho phép quay lại Draft nếu cần sửa"""
        for rfq in self:
            if rfq.state not in ['sent', 'to_approve', 'cancel', 'rejected']:
                raise UserError(_("Chỉ có thể reset khi ở trạng thái Sent, To Approve, Cancel hoặc Rejected."))
            rfq.write({'state': 'draft'})

    # Mở danh sách các PO được tạo từ RFQ này
    def action_view_purchase_orders(self):
        """Mở danh sách các Purchase Orders (PO) được tạo từ RFQ này"""
        self.ensure_one()
        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            # Filter các PO có field epr_source_rfq_ids chứa ID hiện tại
            'domain': [('epr_source_rfq_ids', 'in', self.ids)],
            'context': {'default_epr_source_rfq_ids': [Command.link(self.id)]},
            'target': 'current',
        }

    # Mở danh sách các PR gốc của RFQ này
    def action_view_source_requests(self):
        """Mở danh sách các PR gốc của RFQ này"""
        self.ensure_one()
        return {
            'name': _('Source Purchase Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'epr.purchase.request',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.request_ids.ids)],
            'target': 'current',
        }
    # -------------------------------------------------------------------------
    # RFQ APPROVAL PROCESS
    # -------------------------------------------------------------------------

    def action_submit_approval(self):
        """Nút bấm Submit for Approval - Odoo 18 Optimized"""
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_("Vui lòng nhập chi tiết sản phẩm trước khi trình duyệt."))

        # 1. Quy đổi tiền tệ
        currency_company = self.company_id.currency_id
        amount_company = self.amount_total
        if self.currency_id and self.currency_id != currency_company:
            amount_company = self.currency_id._convert(
                self.amount_total, currency_company, self.company_id, 
                self.date_order or fields.Date.context_today(self)
            )

        # 2. Tìm Rule phù hợp
        rule = self.env['epr.approval.rule'].search([
            ('active', '=', True),
            ('company_id', '=', self.company_id.id),
            '|', ('department_id', '=', False), ('department_id', '=', self.department_id.id)
        ], order='department_id desc, sequence asc, id desc', limit=1)

        if not rule:
            self.write({'state': 'approved', 'approval_state': 'approved'})
            return 
        # 3. Lọc các bước duyệt dựa trên giá trị đơn hàng
        applicable_lines = rule.line_ids.filtered(
            lambda l: (not l.min_amount or l.min_amount <= amount_company)
        ).sorted('sequence')

        if not applicable_lines:
            self.write({'state': 'approved', 'approval_state': 'approved'})
            return

        # 3. Lọc và Sắp xếp các bước duyệt
        applicable_lines = rule.line_ids.filtered(
            lambda l: (not l.min_amount or l.min_amount <= amount_company)
        ).sorted('sequence')
        if not applicable_lines:
            self.write({'state': 'approved', 'approval_state': 'approved'})
            return

        # 4. Hỗ trợ Duyệt song song cùng tầng (Sequence)
        self.sudo().approval_entry_ids.unlink()
        vals_list = []
        min_seq = applicable_lines[0].sequence
        for line in applicable_lines:
            # Nếu cùng tầng Sequence nhỏ nhất -> 'new' luôn
            status = 'new' if line.sequence == min_seq else 'pending'
            vals_list.append({
                'rfq_id': self.id,
                'name': line.name,
                'sequence': line.sequence,
                'status': status,
                'required_user_ids': [Command.set(line.user_ids.ids)],
                'rule_line_id': line.id,
            })
        self.env['epr.approval.entry'].create(vals_list)

        self.write({
            'state': 'to_approve', 
            'approval_state': 'pending'
        })

        # Optional: Gửi email thông báo cho người duyệt bước đầu tiên
        # self._notify_next_approvers()

    # -------------------------------------------------------------------------
    # APPROVAL LOGIC: LINEARIZATION
    # -------------------------------------------------------------------------
    def _check_approval_completion(self):
        """
        Hàm này được gọi mỗi khi 1 dòng entry được Approve/Refuse.
        Nhiệm vụ: Kích hoạt bước tiếp theo hoặc Confirm RFQ.
        """
        self.ensure_one()

        # A. Nếu có bất kỳ dòng nào bị từ chối -> Hủy toàn bộ quy trình
        if any(e.status == 'refused' for e in self.approval_entry_ids):
            self.write({
                'state': 'rejected',
                'approval_state': 'refused'
            })

            return

        remaining = self.approval_entry_ids.filtered(lambda e: e.status in ['new', 'pending']).sorted('sequence')
        if not remaining:
            self.write({'state': 'approved', 'approval_state': 'approved'})
            return

        # Nếu tầng hiện tại đã duyệt xong hết (không còn ai status='new')
        if not remaining.filtered(lambda e: e.status == 'new'):
            # Kích hoạt tầng tiếp theo (tất cả các dòng có Sequence nhỏ nhất còn lại)
            next_min_seq = remaining[0].sequence
            remaining.filtered(lambda e: e.sequence == next_min_seq).write({'status': 'new'})

# ==============================================================================
# CLASS CON: epr.rfq.line (Chi tiết hàng hóa trong RFQ)
# ==============================================================================


class EprRfqLine(models.Model):
    _name = 'epr.rfq.line'
    _description = 'EPR RFQ Line'

    rfq_id = fields.Many2one(
        comodel_name='epr.rfq',
        string='RFQ Reference',
        required=True,
        ondelete='cascade',
        index=True
    )

    # === LIÊN KẾT VỚI PR (QUAN TRỌNG) ===
    # Link về dòng chi tiết của PR gốc
    pr_line_id = fields.Many2one(
        'epr.purchase.request.line',
        string='Source PR Line',
        ondelete='set null',
        index=True,
        help="Dòng yêu cầu mua hàng gốc sinh ra dòng báo giá này."
    )

    # Link về PR Header (Tiện ích để group/filter)
    purchase_request_id = fields.Many2one(
        related='pr_line_id.request_id',
        string='Purchase Request',
        store=True,
        readonly=True
    )

    # === SẢN PHẨM & CHI TIẾT ===
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True
    )

    description = fields.Text(string='Description')

    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
        digits='Product Unit of Measure'
    )

    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UoM',
        required=True
    )

    price_unit = fields.Float(
        string='Unit Price',
        digits='Product Price'
    )

    taxes_id = fields.Many2many(
        comodel_name='account.tax',
        relation='epr_rfq_line_taxes_rel',
        column1='line_id',
        column2='tax_id',
        string='Taxes',
        context={'active_test': False}
    )

    # === TÍNH TOÁN TIỀN TỆ ===
    currency_id = fields.Many2one(
        related='rfq_id.currency_id',
        store=True, 
        string='Currency',
        readonly=True
    )

    subtotal = fields.Monetary(
        compute='_compute_subtotal',
        string='Subtotal',
        store=True,
        currency_field='currency_id'
    )

    @api.depends('quantity', 'price_unit', 'taxes_id')
    def _compute_subtotal(self):
        """Tính tổng tiền (chưa bao gồm thuế)"""
        for line in self:
            taxes = line.taxes_id.compute_all(
                line.price_unit,
                line.currency_id,
                line.quantity,
                product=line.product_id,
                partner=line.rfq_id.partner_id
            )
            # Nếu bạn muốn duyệt dựa trên GIÁ SAU THUẾ, dùng 'total_included'
            # Nếu muốn duyệt trên GIÁ TRƯỚC THUẾ, dùng 'total_excluded'
            line.subtotal = taxes['total_included']

    # === ONCHANGE PRODUCT (GỢI Ý) ===
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Tự động điền UoM và tên khi chọn sản phẩm"""
        if self.product_id:
            self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
            self.description = self.product_id.display_name
            # Tự động lấy thuế mua hàng mặc định của sản phẩm
            self.taxes_id = self.product_id.supplier_taxes_id

    # ==============================================================================
    # LINE-LEVEL LINKING LOGIC (From RFQs to POs)
    # ==============================================================================

    # Link tới dòng của Purchase Order chuẩn Odoo
    purchase_line_id = fields.Many2one(
        'purchase.order.line',
        string='Purchase Order Line',
        readonly=True,
        copy=False
    )

    # Tiện ích để xem nhanh trạng thái
    po_id = fields.Many2one(
        related='purchase_line_id.order_id',
        string='Purchase Order',
        store=True,
        readonly=True
    )
