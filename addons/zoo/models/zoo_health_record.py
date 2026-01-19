# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext


class ZooHealthRecord(models.Model):
    _name = "zoo.health.record"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '''
    ghi nhận mọi sự kiện y tế, thủ tục phòng ngừa (preventive medicine), và kết quả chẩn đoán liên quan đến một cá thể Thú cụ thể.
    '''

    record_name = fields.Char(
        string='Health Records',
        compute='_compute_record_name',
        store=True,     # store=True để lưu vào DB, giúp tìm kiếm và filter nhanh hơn
        required=True,  # Bắt buộc (nhưng vì là compute nên hệ thống sẽ tự điền)
        readonly=True   # Thường field compute sẽ không cho sửa tay
    )

    animal_id = fields.Many2one(comodel_name='zoo.animal',
        string='Animal',
        required=True)

    veterinarian_id = fields.Many2one(comodel_name='res.partner',
        string='Veterinarian',
        required=True)

    date_occurrence = fields.Date(string='Date Occurrence',
        default=fields.Date.context_today,
        required=True,
        copy=False)

    record_type = fields.Selection([
        ('exam', 'Exam'),
        ('vaccination', 'Vaccination'),
        ('treatment', 'Treatment'),
        ('surgery', 'Surgery'),
        ('quarantine_check', 'Quarantine Check'),
    ], string='Record Type',
    default='exam',
    required=True)

    record_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        string='Status',                  # Nhãn hiển thị
        default='draft',                  # Giá trị mặc định khi tạo mới
        required=True,                    # Bắt buộc phải có giá trị
        copy=False,                       # Không sao chép trạng thái khi Duplicate record
        tracking=True,                    # Ghi log vào chatter khi trạng thái đổi (Cần mail.thread)
        index=True                        # Đánh index để tìm kiếm/lọc nhanh hơn
    )
    diagnosis = fields.Text(string='Diagnosis',
        required=True)

    treatment_details = fields.Html(
        string='Treatment Details',
        required=True,
        # Help text hiển thị khi hover chuột vào tiêu đề trường
        help='Cực kỳ quan trọng. Thiếu tài liệu chi tiết về các thủ tục và liều lượng thuốc là một "recordkeeping deficiencies" phổ biến.',
        sanitize=True,       # Bảo mật: Lọc bỏ các mã độc JS/XSS (Mặc định True)
        strip_style=False,   # False: Cho phép giữ lại màu sắc/font chữ khi copy-paste từ Word/Excel
        translate=False,     # True nếu bạn muốn hỗ trợ đa ngôn ngữ cho trường này
    )

    is_preventive = fields.Boolean(string='Is Preventive',
        default=False,
        required=False)

    next_follow_up_date = fields.Date(string='Next Follow Up Date',
        required=False,
        copy=False,
        tracking=True,
        help="Ngày dự kiến để theo dõi và đánh giá lại tình trạng sức khỏe."
    )

    related_cage_id = fields.Many2one(comodel_name='zoo.cage',
        string='Related Cage',
        required=False)
   
    # --- Các hàm tính toán ---
    @api.depends('animal_id.name', 'date_occurrence')
    def _compute_record_name(self):
        for record in self:
            # Kiểm tra xem đã có dữ liệu chưa để tránh lỗi
            if record.animal_id and record.date_occurrence:
                # Format: [Tên Con Vật] - [Ngày]
                # Ví dụ: Lion King - 2024-11-21
                record.record_name = f"{record.animal_id.name} - {record.date_occurrence}"
            else:
                # Giá trị tạm thời khi chưa nhập đủ thông tin
                record.record_name = "New Health Record"

    # Validate kỹ hơn vì required=True của HTML đôi khi vẫn lọt lưới nếu chỉ nhập dấu cách
    @api.constrains('treatment_details')
    def _check_treatment_details_content(self):
        for record in self:
            if record.treatment_details:
                # Chuyển HTML sang text thuần để kiểm tra độ dài thực
                text_content = html2plaintext(record.treatment_details).strip()
                if not text_content:
                    raise ValidationError("Vui lòng nhập nội dung chi tiết điều trị (không được để trống hoặc chỉ nhập khoảng trắng).")

    # --- Các hàm chuyển trạng thái (State Transition Actions) ---
    def action_in_progress(self):
        """Chuyển trạng thái sang 'In Progress'"""
        for record in self:
            if record.record_state == 'draft':
                record.record_state = 'in_progress'

    def action_completed(self):
        """Chuyển trạng thái sang 'Completed'"""
        for record in self:
            if record.record_state == 'in_progress':
                record.record_state = 'completed'

    def action_cancel(self):
        """Chuyển trạng thái sang 'Cancelled'"""
        for record in self:
            if record.record_state not in ('completed', 'cancelled'):
                record.record_state = 'cancelled'

    def action_draft(self):
        """Reset trạng thái về 'Draft'"""
        for record in self:
            if record.record_state == 'cancelled':
                record.record_state = 'draft'
