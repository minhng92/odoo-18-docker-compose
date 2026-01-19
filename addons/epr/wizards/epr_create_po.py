from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError


class EprCreatePoWizard(models.TransientModel):
    _name = 'epr.create.po.wizard'
    _description = 'Merge RFQs to Purchase Order'

    # Hiển thị Vendor chung để user confirm
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        required=True
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True
    )

    # Danh sách các dòng sẽ được đẩy vào PO (Cho phép user bỏ tick để xé nhỏ RFQ)
    line_ids = fields.One2many(
        comodel_name='epr.create.po.line.wizard',
        inverse_name='wizard_id',
        string='Products to Order'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            return res

        # 1. Lấy danh sách RFQ được chọn
        rfqs = self.env['epr.rfq'].browse(active_ids)

        # 2. Validate: Cùng Vendor và Currency
        first_partner = rfqs[0].partner_id
        first_currency = rfqs[0].currency_id

        if any(r.partner_id != first_partner for r in rfqs):
            raise UserError(_("Tất cả các RFQ được chọn phải cùng một Nhà cung cấp."))

        if any(r.currency_id != first_currency for r in rfqs):
            raise UserError(_("Tất cả các RFQ được chọn phải cùng loại Tiền tệ."))

        if any(r.state != 'confirmed' for r in rfqs):  # Giả sử trạng thái 'confirmed' là đã chốt
            raise UserError(_("Chỉ có thể tạo PO từ các RFQ đã xác nhận (Confirmed)."))

        # 3. Loop qua từng dòng RFQ để prepare dữ liệu cho Wizard
        lines_list = []
        for rfq in rfqs:
            for line in rfq.line_ids:
                # Chỉ load những dòng chưa tạo PO
                if not line.purchase_line_id:
                    lines_list.append(Command.create({
                        'rfq_line_id': line.id,
                        'product_id': line.product_id.id,
                        'description': line.description,
                        'quantity': line.quantity,  # User có thể sửa số lượng tại wizard nếu muốn partial
                        'price_unit': line.price_unit,
                        'uom_id': line.uom_id.id,
                        'taxes_id': [Command.set(line.taxes_id.ids)],
                    }))

        if not lines_list:
            raise UserError(_("Không tìm thấy dòng sản phẩm nào khả dụng để tạo PO (có thể đã được tạo trước đó)."))

        res.update({
            'partner_id': first_partner.id,
            'currency_id': first_currency.id,
            'line_ids': lines_list
        })
        return res

    def action_create_po(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("Vui lòng chọn ít nhất một dòng sản phẩm."))

        rfq_ids = self.line_ids.mapped('rfq_line_id.rfq_id').ids
        pr_ids = self.line_ids.mapped('rfq_line_id.pr_line_id.request_id').ids

        # 1. Prepare Header PO (Chuẩn Odoo)
        po_vals = {
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'date_order': fields.Datetime.now(),
            'origin': ', '.join(self.line_ids.mapped('rfq_line_id.rfq_id.name')),
            'epr_source_rfq_ids': [Command.set(rfq_ids)],  # Gán Link RFQ
            'epr_source_pr_ids': [Command.set(pr_ids)],    # Gán Link PR
            'order_line': [],
        }

        # 2. Prepare PO Lines
        for w_line in self.line_ids:
            po_line_vals = {
                'product_id': w_line.product_id.id,
                'name': w_line.description or w_line.product_id.name,
                'product_qty': w_line.quantity,
                'price_unit': w_line.price_unit,
                'product_uom': w_line.uom_id.id,
                'taxes_id': [Command.set(w_line.taxes_id.ids)],
                # inherit purchase.order.line để link 2 chiều chặt chẽ
                'epr_rfq_line_id': w_line.rfq_line_id.id
            }
            po_vals['order_line'].append(Command.create(po_line_vals))

        # 3. Tạo PO
        purchase_order = self.env['purchase.order'].create(po_vals)

        # 4. Update ngược lại RFQ Line (Line-Level Linking)
        # Vì PO Line được tạo qua Command.create, ta cần map lại ID
        # Cách đơn giản nhất: Loop lại PO Lines vừa tạo

        # Lưu ý: Logic này giả định thứ tự tạo không đổi, để chính xác tuyệt đối
        # nên thêm field 'epr_rfq_line_id' vào 'purchase.order.line'
        for i, po_line in enumerate(purchase_order.order_line):
            # Lấy dòng wizard tương ứng theo index (nếu thứ tự được bảo toàn)
            # Hoặc tốt hơn: Thêm field epr_rfq_line_id vào purchase.order.line (Xem mục 3)
            wizard_line = self.line_ids[i]
            wizard_line.rfq_line_id.write({'purchase_line_id': po_line.id})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_mode': 'form',
            'target': 'current',
        }


class EprCreatePoLineWizard(models.TransientModel):
    _name = 'epr.create.po.line.wizard'
    _description = 'Line details for PO creation'

    wizard_id = fields.Many2one(
        comodel_name='epr.create.po.wizard',
        string='Wizard',
        required=True,
        readonly=True
    )

    rfq_line_id = fields.Many2one(
        comodel_name='epr.rfq.line',
        string='RFQ Line',
        required=True
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product'
    )

    description = fields.Text(
        string='Description'
    )

    quantity = fields.Float(
        string='Quantity',
        required=True
    )

    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UoM'
    )

    price_unit = fields.Float(
        string='Price'
    )

    taxes_id = fields.Many2many(
        comodel_name='account.tax',
        string='Taxes',
        readonly=True
    )
