# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext


class ZooHusbandryTask(models.Model):
    _name = 'zoo.husbandry.task'
    _description = 'Daily Husbandry & Enrichment Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name_custom'

    name = fields.Char(
        string='Reference',
        required=True, 
        copy=False, 
        readonly=True, 
        default=lambda self: _('New'))

    # Ví dụ: "Lion Cage - 25/11/2025"
    display_name_custom = fields.Char(
        string='Subject', 
        compute='_compute_display_name_custom', 
        store=True
    )

    cage_id = fields.Many2one(
        comodel_name='zoo.cage',
        domain="[('active', '=', True)]",
        string='Cage/Enclosure',
        required=True,
        tracking=True)

    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        required=True)

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigned To',
        default=lambda self: self.env.user,
        required=True)

    task_type = fields.Selection([
        ('routine', 'Daily Routine'),
        ('enrichment', 'Enrichment'),
        ('maintenance', 'Minor Maintenance'),
        ('vet_check', 'Visual Vet Check'),
        ('observation', 'Observation'),
        ('other', 'Other'),
        ],
        string='Task Type',
        default='routine',
        required=True)

    task_line_ids = fields.One2many(
        comodel_name='zoo.husbandry.task.line',
        inverse_name='task_id',
        string='Checklist',
        required=True)

    keeper_note = fields.Html(
        string='Observations/Issues',
        help='Ghi chú của Keeper',
        sanitize=True,
        strip_style=False,
        translate=False)

    state = fields.Selection([
        ('draft', 'To Do'),
        ('in_progress', 'In Progress'),
        ('to_approve', 'Waiting Approval'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
        ],
        ondelete={'to_approve': 'set default'},
        string='Status',
        default='draft',
        tracking=True,
        group_expand='_expand_groups')

    # Xác định Approver
    approver_id = fields.Many2one(
        comodel_name='res.users',
        string='Approver',
        compute='_compute_approver',
        store=True)

    # --- Logic đặt tên: Mã phiếu tự động
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            # HUSB là mã sequence chúng ta sẽ định nghĩa trong XML data
            vals['name'] = self.env['ir.sequence'].next_by_code('zoo.husbandry.task') or _('New')
        return super(ZooHusbandryTask, self).create(vals)

    # --- Logic đặt tên cho Display name
    @api.depends('cage_id', 'date', 'task_type')
    def _compute_display_name_custom(self):
        for record in self:
            cage_name = record.cage_id.name or 'Unknown Cage'
            date_str = record.date.strftime('%d/%m') if record.date else ''
            # Kết quả: "Lion Cage - 25/11"
            record.display_name_custom = f"{cage_name} - {date_str}"

    # --- Kanban Grouping (Để Kanban hiển thị đủ cột Draft/Done dù không có data) ---
    @api.model
    def _expand_groups(self, states, domain, order=None):
        """Force display all state columns in Kanban, even if empty"""
        return ['draft', 'in_progress', 'to_approve', 'done', 'cancel']

    # --- ACTIONS ---
    def action_start(self):
        self.state = 'in_progress'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    # --- Validate kỹ hơn vì required=True của HTML đôi khi vẫn lọt lưới nếu chỉ nhập dấu cách
    @api.constrains('keeper_note')
    def _check_keeper_note_content(self):
        for record in self:
            if record.keeper_note:
                text_content = html2plaintext(record.keeper_note).strip()
                if not text_content:
                    raise ValidationError(_("Please enter meaningful content (not just spaces)."))

    # Load template task mỗi khi chọn Chuồng
    @api.onchange('cage_id')
    def _onchange_cage_id(self):
        """
        Khi chọn Chuồng:
        1. Xóa sạch checklist cũ (nếu có).
        2. Copy checklist mẫu từ cấu hình Chuồng sang Task này.
        """
        if not self.cage_id:
            return

        # Bước 1: Chuẩn bị danh sách lệnh
        # Command.clear(): Xóa hết dòng cũ (tránh bị double khi user chọn lại chuồng)
        lines_commands = [Command.clear()]

        # Bước 2: Lấy mẫu từ zoo.cage
        if self.cage_id.checklist_template_ids:
            for template in self.cage_id.checklist_template_ids:
                # Command.create(values): Tạo dòng mới trong RAM (chưa lưu DB)
                lines_commands.append(Command.create({
                    'name': template.name,
                    'required': template.required,
                    'is_done': False,  # Mặc định chưa làm
                }))

        # Bước 3: Gán vào field One2many của Task
        self.task_line_ids = lines_commands

    # --- Compute Approver ---
    @api.depends('user_id')
    def _compute_approver(self):
        for record in self:
            # Logic: Tìm Employee ứng với User -> Lấy Parent (Manager) -> Lấy User của Manager
            if record.user_id and record.user_id.employee_id and record.user_id.employee_id.parent_id:
                record.approver_id = record.user_id.employee_id.parent_id.user_id
            else:
                record.approver_id = False

    # --- Approval Workflow ---
    # --- 1. Keepers gửi yêu cầu phê duyệt ---
    def action_request_approval(self):
        """Keeper bấm nút này để xin duyệt"""
        for record in self:
            if not record.approver_id:
                raise UserError(_("You don't have a direct manager defined in HR Settings to approve this task."))

            # THÊM LOGIC KIỂM TRA CHECKLIST
            unfinished_lines = record.task_line_ids.filtered(lambda l: l.required and not l.is_done)
            if unfinished_lines:
                raise ValidationError(_("You must complete all required checklist items before finishing!"))

            # Chuyển trạng thái
            record.state = 'to_approve'

            # Tạo Activity cho Sếp
            # record.activity_schedule(
            #     user_id=record.approver_id.id,
            #     summary=f"Approval Request: {record.name}",
            #     note=f"Please approve husbandry task for {record.cage_id.name}"
            # )


    # --- 2. Sếp phê duyệt hoặc từ chối ---
    # --- 2.1. Sếp phê duyệt ---
    def action_approve(self):
        """Approver bấm nút này để phê duyệt"""
        for record in self:
            if self.env.user != record.approver_id:
                raise UserError(_("Only the assigned approver can approve this task."))

            record.state = 'done'

            # Tự động đánh dấu hoàn thành Activity đã giao cho sếp
            activities = record.activity_ids.filtered(
                lambda a: a.activity_type_id == self.env.ref('mail.mail_activity_data_todo')
            )

            if activities:
                activities.action_feedback(feedback="Approved")

    # --- 2.2. Sếp từ chối ---
    def action_reject(self):
        """Approver bấm nút này để từ chối"""
        for record in self:
            if self.env.user != record.approver_id:
                raise UserError(_("Only the assigned approver can reject this task."))

            record.state = 'draft'  # ← GIẢM INDENT (chuyển ra ngoài khối if)

            # Gửi tin nhắn lý do từ chối
            activities = record.activity_ids.filtered(
                lambda a: a.activity_type_id == self.env.ref('mail.mail_activity_data_todo')
            )

            if activities:
                activities.action_feedback(feedback="Rejected")

            # Gửi tin nhắn lý do từ chối
            record.message_post(body="Task was refused by Manager. Please check and submit again.")


# --- CHECKLIST ---
class ZooHusbandryTaskLine(models.Model):
    _name = 'zoo.husbandry.task.line'
    _description = 'Task Checklist'

    task_id = fields.Many2one(
        comodel_name='zoo.husbandry.task',
        string='Task',
        required=True,
        ondelete='cascade')

    name = fields.Char(
        string='Description',
        required=True)

    is_done = fields.Boolean(
        string='Done',
        default=False)

    required = fields.Boolean(
        string='Required',
        default=True,
        help="If checked, this item must be done to finish the task.")

    remark = fields.Char(
        string='Remark',
        help="Quick note issues here (e.g. Broken lock)")