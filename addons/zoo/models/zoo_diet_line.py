from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class ZooDietLine(models.Model):
    _name = "zoo.diet.line"
    _description = '''
    Chi tiết cấu thành nên Khẩu phần
    '''

    diet_plan_id = fields.Many2one(comodel_name='zoo.diet.plan',
        string='Khẩu phần gốc',
        required=True)

    product_id = fields.Many2one(comodel_name='product.product',
        string='Nguyên liệu',
        required=True)

    quantity_per_day = fields.Float(string='Quantity Per Day',
        required=True)

    uom_id = fields.Many2one(comodel_name='uom.uom',
        string='UOM',
        required=True)

    cost_per_unit = fields.Float(
        string='Cost Per Unit',
        compute='_compute_cost_per_unit',
        store=True,     # Lưu vào DB để dễ tìm kiếm và báo cáo
        readonly=True,  # Không cho phép người dùng sửa tay
        required=False, 
        digits='Product Price', # Sử dụng định dạng giá tiền chuẩn của Odoo
        help='Chi phí tiêu chuẩn của sản phẩm, được lấy tự động từ thẻ sản phẩm.'
    )

    is_supplement = fields.Boolean(string='Bổ sung (Vitamin, Khoáng chất)',
        required=False,
        default=False)

    # Hàm tính toán (Computation Function)
    @api.depends('product_id')
    def _compute_cost_per_unit(self):
        for record in self:
            # Kiểm tra xem có sản phẩm nào được chọn không
            if record.product_id:
                # Lấy giá trị standard_price (Chi phí tiêu chuẩn) từ product.product
                record.cost_per_unit = record.product_id.standard_price
            else:
                record.cost_per_unit = 0.0