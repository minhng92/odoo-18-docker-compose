from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext

import datetime

class ZooDietPlan(models.Model):
    _name = "zoo.diet.plan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '''
    Là nơi lưu trữ công thức khẩu phần chính thức (Master Data/Recipe) cho các loài hoặc nhóm cá thể
    '''

    diet_plan_name = fields.Char(string='Diet Plan Name',
        help='Tên định danh cho công thức',
        required=True)

    creature_id = fields.Many2one(comodel_name='zoo.creature',
        string="Creature",
        required=True)

    diet_type = fields.Selection([
        ('standard', 'Standard'),
        ('clinical', 'Clinical'),
        ('breeding', 'Breeding'),
    ], string='Diet Type',
    default='standard',
    required=True)

    nutritionist_id = fields.Many2one(comodel_name='res.partner',
        string='Nutritionist',
        help='Đảm bảo người có chuyên môn và kinh nghiệm ',
        required=True)

    next_review_date = fields.Date(string='Next Review Date',
        help='Ngày đánh giá định kỳ tiếp theo',
        required=True)

    diet_status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('under_review', 'Under Review'),
        ('deprecated','Deprecated')
    ], string='Status',
    default='draft',
    required=True,
    tracking=True)

    is_active = fields.Boolean(string='Is Active',
        default=False,
        required=False)

    ingredient_ids = fields.One2many(comodel_name='zoo.diet.line',
        inverse_name='diet_plan_id',
        string='Ingredient',
        help='Danh sách thành phần',
        required=True)

    notes = fields.Html(
        string='Other Notes',
        required=False,
        help='Hướng dẫn pha chế và lưu trữ',
        sanitize=True,       # Bảo mật: Lọc bỏ các mã độc JS/XSS (Mặc định True)
        strip_style=False,   # False: Cho phép giữ lại màu sắc/font chữ khi copy-paste từ Word/Excel
        translate=False,     # True nếu bạn muốn hỗ trợ đa ngôn ngữ cho trường này
    )

    # Validate kỹ hơn vì required=True của HTML đôi khi vẫn lọt lưới nếu chỉ nhập dấu cách
    @api.constrains('notes')
    def _check_notes_content(self):
        for record in self:
            if record.notes:
                # Chuyển HTML sang text thuần để kiểm tra độ dài thực
                text_content = html2plaintext(record.notes).strip()
                if not text_content:
                    raise ValidationError("Vui lòng nhập nội dung chi tiết về điều chế và lưu trữ thức ăn cho động vật.")

    # --- Các hàm chuyển trạng thái (State Transition Actions) ---
    def action_activate(self):
        """Chuyển trạng thái từ Draft sang Active"""
        for record in self:
            if record.diet_status == 'draft':
                record.diet_status = 'active'
                record.is_active = True

    def action_under_review(self):
        """Chuyển trạng thái sang Under Review để đánh giá lại"""
        for record in self:
            if record.diet_status == 'active':
                record.diet_status = 'under_review'

    def action_approve(self):
        """Approve và chuyển về Active sau khi review"""
        for record in self:
            if record.diet_status == 'under_review':
                record.diet_status = 'active'
                record.is_active = True

    def action_deprecate(self):
        """Đánh dấu diet plan là deprecated (không còn sử dụng)"""
        for record in self:
            if record.diet_status != 'deprecated':
                record.diet_status = 'deprecated'
                record.is_active = False

    def action_reset_draft(self):
        """Reset về Draft (từ deprecated hoặc under_review)"""
        for record in self:
            if record.diet_status in ('deprecated', 'under_review'):
                record.diet_status = 'draft'
                record.is_active = False









