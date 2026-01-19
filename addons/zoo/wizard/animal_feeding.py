from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError

class AnimalFeedingWizard(models.TransientModel):
    _name = 'zoo.animal.feeding.wizard'
    _description = 'Bulk Feeding Wizard'

    def _default_animals(self):
        """Lấy danh sách thú được chọn từ màn hình List View"""
        return self.env.context.get('active_ids', [])

    # 1. Context Fields
    animal_ids = fields.Many2many(
        comodel_name='zoo.animal',
        string='Animals to Feed',
        required=True,
        default=_default_animals
    )
    
    # Tự động tính loài (dùng để validate và lọc thức ăn)
    creature_id = fields.Many2one(
        comodel_name='zoo.creature',
        string='Species',
        compute='_compute_creature_info',
        store=True,
        readonly=True
    )

    meal_date = fields.Datetime(
        string="Feeding Time",
        required=True,
        default=fields.Datetime.now
    )
    
    staff_id = fields.Many2one(
        comodel_name="res.users",
        string="Staff",
        default=lambda self: self.env.user,
        required=True
    )

    allowed_product_ids = fields.Many2many(
        related='creature_id.allowed_product_ids', 
        readonly=True
    )

    # 2. Feeding Lines (Bảng tạm để chọn nhiều món)
    line_ids = fields.One2many(
        comodel_name='zoo.animal.feeding.wizard.line',
        inverse_name='wizard_id',
        string='Food Lines'
    )

    # --- Compute & Validation ---
    @api.depends('animal_ids')
    def _compute_creature_info(self):
        for record in self:
            if not record.animal_ids:
                record.creature_id = False
                continue
            
            # Lấy loài của con đầu tiên
            first_creature = record.animal_ids[0].creature_id
            
            # Validate: Tất cả thú được chọn phải cùng 1 loài
            # Nếu có con nào khác loài với con đầu tiên -> Báo lỗi hoặc False
            if any(animal.creature_id != first_creature for animal in record.animal_ids):
                raise UserError(_("You can only feed animals of the SAME species in a single batch!"))
            
            record.creature_id = first_creature

    # --- Main Action ---
    def action_confirm(self):
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError(_("Please select at least one food item to feed."))

        MealObj = self.env['zoo.animal.meal']
        created_meals = []

        # LOOP: Với mỗi dòng thức ăn trong Wizard -> Tạo 1 phiếu Batch Meal thật
        for line in self.line_ids:
            vals = {
                'creature_id': self.creature_id.id,
                'meal_date': self.meal_date,
                'staff_id': self.staff_id.id,
                'product_id': line.product_id.id,
                'qty_per_animal': line.qty_per_animal,
                'state': 'draft', # Mặc định là Draft để Staff check lại lần cuối
                # Link toàn bộ thú đang chọn vào phiếu
                'animal_ids': [Command.set(self.animal_ids.ids)],
            }
            new_meal = MealObj.create(vals)
            created_meals.append(new_meal.id)

        # Return Action: Mở danh sách các phiếu vừa tạo
        return {
            'name': _('Created Feeding Batches'),
            'type': 'ir.actions.act_window',
            'res_model': 'zoo.animal.meal',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_meals)],
            'context': {'create': False}, # Tùy chọn: Không cho tạo thêm ở màn hình kết quả
        }

class AnimalFeedingWizardLine(models.TransientModel):
    _name = 'zoo.animal.feeding.wizard.line'
    _description = 'Feeding Line Detail'

    wizard_id = fields.Many2one('zoo.animal.feeding.wizard',
        required=True)
    
    # Fields kỹ thuật để lấy domain từ cha
    creature_id = fields.Many2one(related='wizard_id.creature_id')
    allowed_product_ids = fields.Many2many(related='creature_id.allowed_product_ids')

    product_id = fields.Many2one(
        'product.product', 
        string='Food Item', 
        required=True
    )
    
    uom_id = fields.Many2one(related='product_id.uom_id',
        readonly=True)

    qty_per_animal = fields.Float(
        string='Qty / Animal',
        default=1.0,
        required=True
    )