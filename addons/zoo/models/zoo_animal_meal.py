# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext, format_date

class ZooAnimalMeal(models.Model):
    _name = "zoo.animal.meal"
    _description = "Batch Feeding Record"
    _inherit = ['mail.thread']

    # Định nghĩa các field
    record_name = fields.Char(
        string='Batch Name',
        compute='_compute_record_name',
        store=True,
        readonly=True
    )
    
    creature_id = fields.Many2one(
        comodel_name="zoo.creature",
        string="Species",
        required=True,
        help='Loài vật'
    )

    meal_date = fields.Datetime(
        string="Meal Date",
        required=True,
        default=fields.Datetime.now,
        help='Thời điểm cho ăn'
    )

    # domain logic: Chỉ chọn được Animal thuộc creature_id đã chọn
    animal_ids = fields.Many2many(
        comodel_name='zoo.animal',
        relation='zoo_animal_meal_animal_rel',
        column1='meal_id',
        column2='animal_id',
        string='Animals Fed',
        domain="[('creature_id', '=', creature_id), ('is_alive', '=', True)]"
    )

    allowed_product_ids = fields.Many2many(comodel_name='product.product',
        string='Allowed Products',
        related='creature_id.allowed_product_ids')

    # Chọn product để cho ăn
    product_id = fields.Many2one(comodel_name='product.product',
        string='Food Item',
        required=True,
        domain="[('id', 'in', allowed_product_ids)]")

    uom_id = fields.Many2one(comodel_name='uom.uom',
        related='product_id.uom_id',
        string='Unit',
        readonly=True,
        required=True)

    qty_per_animal = fields.Float(
        string='Qty per Animal',
        default=1.0,
        required=True,
        help='Số lượng thức ăn cho mỗi con vật'
    )

    total_qty = fields.Float(
        string='Total Qty',
        compute='_compute_total_qty',
        store=True,
        help='Tổng số lượng = Qty per animal × Số động vật'
    )

    staff_id = fields.Many2one(
        comodel_name="res.users",
        string="Staff",
        default=lambda self: self.env.user,
        required=True,
        help='Nhân viên phụ trách cho ăn'
    )

    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done')],
        string='State',
        default='draft',
        tracking=True
    )

    meal_note = fields.Html(
        string='Meal Note',
        required=False,
        help='Ghi chú về bữa ăn',
        sanitize=True,
        strip_style=False,
        translate=False
    )

    # --- Validation ---
    @api.constrains('meal_note')
    def _check_meal_note_content(self):
        for record in self:
            if record.meal_note:
                text_content = html2plaintext(record.meal_note).strip()
                if not text_content:
                    raise ValidationError(_("Vui lòng nhập nội dung chi tiết về bữa ăn."))

    # --- Computed Fields ---
    @api.depends('creature_id', 'meal_date', 'product_id')
    def _compute_record_name(self):
        for record in self:
            if record.creature_id and record.meal_date:
                date_str = format_date(self.env, record.meal_date)
                # Lấy tên món ăn
                food_name = record.product_id.name if record.product_id else "..."
                
                # Format: Lion - Beef - 22/11/2025
                record.record_name = f"{record.creature_id.name} - {food_name} - {date_str}"
            else:
                record.record_name = 'New Meal'

    @api.depends('qty_per_animal', 'animal_ids')
    def _compute_total_qty(self):
        for record in self:
            # Tổng = Định lượng * Số con
            record.total_qty = record.qty_per_animal * len(record.animal_ids)

    # --- Actions ---
    def action_load_all_animals(self):
        """Load all animals of selected creature"""
        for record in self:
            if not record.creature_id:
                raise UserError(_("Please select a creature first!"))
            
            # Tìm tất cả thú thuộc loài này
            animals = self.env['zoo.animal'].search([
                ('creature_id', '=', record.creature_id.id),
                ('is_alive', '=', True)
            ])
            
            if not animals:
                raise UserError(_("No alive animals found for this creature!"))
            
            # Gán vào field Many2many (cú pháp replace: [(6, 0, ids)])
            record.animal_ids = [(6, 0, animals.ids)]
            
        return True

    def action_mark_done(self):
        """Mark feeding as done"""
        for record in self:
            if not record.animal_ids:
                raise UserError(_("Please select at least one animal!"))
            if not record.product_id:
                raise UserError(_("Please select a product!"))
            
            record.state = 'done'
        
        return True

    def action_reset_to_draft(self):
        """Reset to draft"""
        self.write({'state': 'draft'})
        return True

    # Định nghĩa các hàm Action:
    def action_done(self):
        for record in self:
            # 1. Logic trừ kho (Inventory) sẽ viết ở đây
            # ...
            
            # 2. Chuyển trạng thái
            record.state = 'done'

    def action_draft(self):
        for record in self:
            record.state = 'draft'