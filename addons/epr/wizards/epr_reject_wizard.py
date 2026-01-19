# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EprRejectWizard(models.TransientModel):
    """
    Wizard này được sử dụng để nhập lý do từ chối cho một Purchase Request.
    Là một TransientModel, dữ liệu sẽ được tự động xóa định kỳ bởi Odoo.
    """
    _name = 'epr.reject.wizard'
    _description = 'Purchase Request Rejection Wizard'

    # ==========================================================================
    # FIELDS
    # ==========================================================================

    request_id = fields.Many2one(
        comodel_name='epr.purchase.request',
        string='Purchase Request',
        required=True,
        readonly=True,
        ondelete='cascade',
        help="The Purchase Request linked to this rejection action."
    )

    reason = fields.Text(
        string='Rejection Reason',
        required=True,
        help='Please provide a detailed reason for rejection so the requester understands why.'
    )

    # ==========================================================================
    # COMPUTE & ONCHANGE & DEFAULTS
    # ==========================================================================

    @api.model
    def default_get(self, fields_list):
        """
        Ghi đè phương thức default_get để tự động lấy ID của Purchase Request
        đang kích hoạt (active_id) từ context và điền vào field request_id.
        Điều này giúp User không phải chọn lại PR thủ công.
        """
        res = super(EprRejectWizard, self).default_get(fields_list)

        # Lấy ID của bản ghi đang đứng từ context ('active_id')
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')

        # Kiểm tra xem có phải đang mở từ đúng model không
        if active_id and active_model == 'epr.purchase.request':
            res['request_id'] = active_id

        return res

    # ==========================================================================
    # BUSINESS LOGIC (ACTIONS)
    # ==========================================================================

    def action_confirm_reject(self):
        """
        Hành động được gọi khi User nhấn nút 'Reject' trên Wizard.
        1. Kiểm tra dữ liệu.
        2. Gọi hàm xử lý logic trên model chính (epr.purchase.request).
        3. Đóng wizard.
        """
        self.ensure_one()

        # Mặc dù field required=True đã chặn ở UI, nhưng kiểm tra ở backend vẫn an toàn hơn
        if not self.reason:
            raise UserError(_('Please provide a reason for rejection to proceed.'))

        # Gọi phương thức nghiệp vụ trên model chính để xử lý logic chuyển trạng thái
        # Việc tách logic này giúp code gọn gàng và dễ bảo trì.
        self.request_id.action_reject(self.reason)

        # Đóng cửa sổ wizard và (tùy chọn) reload lại giao diện phía sau
        return {
            'type': 'ir.actions.act_window_close',
            # 'tag': 'reload',  # Uncomment nếu muốn reload lại trang phía sau ngay lập tức
        }
