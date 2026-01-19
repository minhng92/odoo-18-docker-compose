I. Phạm vi Triển khai
	1. Hệ thống ePR sẽ bao phủ toàn bộ vòng đời của một yêu cầu mua sắm:

	2. Khởi tạo (Drafting): Nhân viên tạo yêu cầu với chi tiết sản phẩm, số lượng, và ngày cần hàng.

	3. Định tuyến Phê duyệt (Routing): Hệ thống tự động xác định danh sách người phê duyệt dựa trên ma trận phân quyền (Phòng ban, Ngân sách, Loại sản phẩm).

	4. Phê duyệt Đa cấp (Multi-level Approval): Hỗ trợ phê duyệt tuần tự hoặc song song.

	5. Chuyển đổi (Conversion): Tự động gom nhóm các yêu cầu đã duyệt để tạo ra các RFQ tương ứng, phân loại theo nhà cung cấp định trước.

	6. Kiểm soát và Báo cáo: Theo dõi trạng thái của từng dòng yêu cầu (đã đặt hàng, đã nhận hàng, đã hủy).
	
II. Định nghĩa Manifest (__manifest__.py)
{
    'name': 'Electronic Purchase Request (ePR) Enterprise',
    'version': '18.0.1.0.0',
    'category': 'Procurement/Inventory',
    'summary': 'Hệ thống quản lý yêu cầu mua sắm nội bộ với quy trình phê duyệt động',
    'description': """
        Module ePR được thiết kế chuyên biệt cho Odoo 18.
        Các tính năng cốt lõi:
        - Tách biệt quy trình Yêu cầu (Internal) và Mua hàng (External).
        - Sử dụng cú pháp View <list> mới nhất của Odoo 18.
        - Tích hợp ORM Command Interface.
        - Ma trận phê duyệt động (Approval Matrix) dựa trên ngưỡng tiền tệ và phòng ban.
    """,
    'author': 'Google Antigravity Implementation Team',
    'website': 'https://google-antigravity.dev',
    'depends': [
        'base',
        'purchase',       # Để kết nối với purchase.order [8]
        'hr',             # Để lấy thông tin phòng ban và quản lý 
        'product',        # Quản lý danh mục sản phẩm
        'stock',          # Quản lý kho và địa điểm nhận hàng
        'mail',           # Tích hợp Chatter và Activity 
        'uom',            # Đơn vị tính
        'analytic',       # Kế toán quản trị (nếu cần phân bổ chi phí)
    ],
    'data': [
        'security/epr_security.xml',
        'security/ir.model.access.csv',
        'data/epr_sequence_data.xml',
        'data/epr_approval_default_data.xml',
        'data/mail_template_data.xml',
        'views/epr_request_views.xml',
        'views/epr_request_line_views.xml',
        'views/epr_approval_matrix_views.xml',
        'views/res_config_settings_views.xml',
        'views/epr_menus.xml',
        'wizards/epr_reject_reason_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'epr_management/static/src/scss/epr_status_widget.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'OEEL-1',
}

Phân tích sâu: Việc phụ thuộc vào hr là bắt buộc vì Odoo 18 quản lý phân cấp nhân sự rất chặt chẽ thông qua trường parent_id (Người quản lý) trong model hr.employee. Hệ thống ePR sẽ sử dụng cấu trúc này để tự động định tuyến phê duyệt cấp 1 (Direct Manager) trước khi chuyển đến các cấp phê duyệt chuyên môn (như Giám đốc Tài chính hay Giám đốc Mua hàng).   

III. Cấu trúc Thư mục Chuẩn Odoo 18

epr_management/
├── __init__.py
├── manifest.py
├── models/
│   ├── __init__.py
│   ├── epr_request.py               # Model chính (Header)
│   ├── epr_request_line.py          # Chi tiết yêu cầu (Lines)
│   ├── epr_approval_matrix.py       # Logic ma trận phê duyệt
│   ├── purchase_order.py            # Kế thừa để liên kết ngược
│   └── hr_employee.py               # Mở rộng logic tìm quản lý đặc thù
├── views/
│   ├── epr_request_views.xml        # Form, List, Kanban, Search
│   ├── epr_request_line_views.xml
│   ├── epr_approval_matrix_views.xml
│   ├── epr_menus.xml                # Cấu trúc Menu
│   └── res_config_settings_views.xml
├── security/
│   ├── epr_security.xml             # Groups và Record Rules
│   └── ir.model.access.csv          # Phân quyền CRUD (ACL)
├── data/
│   ├── epr_sequence_data.xml        # Sequence PR (PR/2024/0001)
│   └── epr_approval_data.xml
├── wizards/
│   ├── __init__.py
│   ├── epr_reject_reason.py         # Xử lý logic từ chối
│   └── epr_reject_reason_views.xml
├── report/
│   ├── epr_report.xml
│   └── epr_report_template.xml
└── static/
    ├── description/
    │   ├── icon.png
    │   └── index.html
    └── src/
        └── js/                      # Tùy biến OWL Components (nếu có)

IV. Thiết kế Mô hình Dữ liệu (Data Modeling)

	4.1 Model Yêu cầu Mua sắm (epr.request)
Đây là đối tượng chứa thông tin chung của phiếu yêu cầu.

Tên Trường (Field Name)		Loại Dữ liệu (Type)		Thuộc tính (Attributes)														Mô tả Chi tiết & Logic Nghiệp vụ
name						Char					required=True, readonly=True, copy=False, default='New'						Mã định danh duy nhất, được sinh tự động từ ir.sequence khi bản ghi được tạo.
employee_id					Many2one				comodel='hr.employee', required=True, tracking=True							Người yêu cầu. Mặc định lấy env.user.employee_id.
department_id				Many2one				comodel='hr.department', related='employee_id.department_id', store=True	Phòng ban của người yêu cầu. Quan trọng để định tuyến phê duyệt theo ngân sách phòng ban. store=True để hỗ trợ tìm kiếm và nhóm.
date_required				Date					required=True, tracking=True												Ngày cần hàng. Dữ liệu này sẽ được đẩy sang trường date_planned của RFQ.
priority					Selection				[('0', 'Normal'), ('1', 'Urgent')]											Mức độ ưu tiên. Ảnh hưởng đến màu sắc trên giao diện List/Kanban.
state						Selection				tracking=True, index=True													Các trạng thái: draft (Nháp), to_approve (Chờ duyệt), approved (Đã duyệt), in progress (đang xử lý), done (Đã xử lý), rejected (Từ chối), cancel (Hủy).
line_ids					One2many				comodel='epr.request.line', inverse='request_id'							Danh sách các sản phẩm cần mua.
company_id					Many2one				comodel='res.company', default=lambda self: self.env.company				Hỗ trợ môi trường đa công ty (Multi-company).
approver_ids				Many2many				comodel='res.users', compute='_compute_approvers', store=True				Trường tính toán lưu danh sách những người cần phê duyệt tại thời điểm hiện tại.
rejection_reason			Text					readonly=True																Lý do từ chối (nếu có), được điền từ Wizard.

Chi tiết Kỹ thuật Python (Odoo 18): Trong Odoo 18, việc sử dụng tracking=True (thay thế cho track_visibility='onchange' cũ) giúp tích hợp tự động với Chatter, ghi lại mọi thay đổi quan trọng.   

from odoo import models, fields, api, _

class EprRequest(models.Model):
    _name = 'epr.request'
    _description = 'Yêu cầu Mua sắm'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # Định nghĩa các trường như bảng trên...
    
    @api.model_create_multi
    def create(self, vals_list):
        """ Override hàm create để sinh mã Sequence """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('epr.request') or _('New')
        return super().create(vals_list)
		
	4.2 Model Chi tiết Yêu cầu (epr.request.line)
Model này chứa thông tin chi tiết từng dòng sản phẩm. Việc thiết kế model này cần tính đến khả năng liên kết N-N với Purchase Order Line, vì một dòng yêu cầu có thể được tách ra mua từ nhiều nhà cung cấp khác nhau hoặc mua làm nhiều lần.

Tên Trường			Loại Dữ liệu		Thuộc tính													Mô tả & Logic
product_id			Many2one			comodel='product.product', domain=							Sản phẩm cần mua. Chỉ lọc các sản phẩm được phép mua.
name				Char				required=True												Mô tả sản phẩm (mặc định lấy tên sản phẩm, cho phép sửa đổi).
quantity			Float				digits='Product Unit of Measure', required=True				Số lượng yêu cầu.
uom_id				Many2one			comodel='uom.uom'											Đơn vị tính. Tự động điền từ sản phẩm nhưng cho phép đổi nếu cùng nhóm ĐVT.
estimated_cost		Monetary			currency_field='currency_id'								Đơn giá dự kiến. Có thể lấy từ giá vốn (standard_price) hoặc bảng giá nhà cung cấp.
total_cost			Monetary			compute='_compute_total', store=True						Thành tiền dự kiến (Số lượng * Đơn giá). Dùng để so sánh với hạn mức phê duyệt.
supplier_id			Many2one			comodel='res.partner', domain=[('supplier_rank', '>', 0)]	Nhà cung cấp đề xuất (tùy chọn).
purchase_line_ids	Many2many			comodel='purchase.order.line'								Liên kết với các dòng PO đã tạo. Giúp truy vết trạng thái mua hàng.
request_state		Selection			related='request_id.state', store=True						Trạng thái dòng, dùng để lọc trong các báo cáo chi tiết.
is_rfq_created		Boolean				compute														Cờ đánh dấu dòng này đã được xử lý tạo RFQ hay chưa.

Logic Tính toán Giá (Compute Method):

@api.depends('quantity', 'estimated_cost')
    def _compute_total(self):
        for line in self:
            line.total_cost = line.quantity * line.estimated_cost
			
	4.3 Model Ma trận Phê duyệt (epr.approval.matrix)
Để đáp ứng yêu cầu về "sự tinh tế" và "chi tiết", chúng ta không thể sử dụng logic phê duyệt cứng nhắc. Model này cho phép định nghĩa các quy tắc linh hoạt.   

Tên Trường			Mô tả
name				Tên quy tắc (VD: Phòng IT - Trên 50 triệu).
department_ids		Áp dụng cho danh sách phòng ban nào (Many2many). Để trống = Áp dụng tất cả.
min_amount			Giá trị tối thiểu của tổng PR để kích hoạt quy tắc này.
max_amount			Giá trị tối đa.
approver_type		Loại người duyệt: manager (Quản lý trực tiếp), specific_user (Người cụ thể), role (Nhóm người dùng).
user_ids			Danh sách người duyệt cụ thể (nếu loại là specific_user).
group_ids			Nhóm người dùng (nếu loại là role).
sequence			Thứ tự ưu tiên kiểm tra.

V. Logic Nghiệp vụ và Luồng Quy trình (Business Logic & Workflows)

	5.1 Thuật toán Phê duyệt (Approval Engine)
	
Khi người dùng nhấn nút "Gửi duyệt" (action_submit), hệ thống sẽ thực hiện các bước sau:

		1. Kiểm tra tính hợp lệ: Đảm bảo PR không rỗng (line_ids > 0).

		2. Tính tổng giá trị: Cộng dồn total_cost của tất cả các dòng.

		3. Quét Ma trận: Tìm kiếm các bản ghi trong epr.approval.matrix thỏa mãn điều kiện:

			. department_id của PR nằm trong department_ids của quy tắc (hoặc quy tắc áp dụng toàn cục).

			. min_amount <= Tổng giá trị PR <= max_amount.

		4. Xác định Người duyệt:

			. Nếu quy tắc yêu cầu manager: Truy xuất employee_id.parent_id.user_id. Nếu không có quản lý, truy xuất department_id.manager_id.   

			. Nếu quy tắc yêu cầu specific_user: Lấy danh sách user_ids.

		5. Tạo Hoạt động (Activity): Sử dụng mail.activity.schedule để tạo task "To Do" cho người duyệt xác định được.

		6. Cập nhật Trạng thái: Chuyển state sang to_approve.

Snippet Logic Python (Sử dụng ORM Command):

def action_submit(self):
        self.ensure_one()
        # Tìm quy tắc phù hợp
        matrix_rules = self.env['epr.approval.matrix'].search([
            ('min_amount', '<=', self.total_amount),
            ('max_amount', '>=', self.total_amount),
            '|', ('department_ids', '=', False), ('department_ids', 'in', self.department_id.id)
        ], order='sequence asc')
        
        if not matrix_rules:
            # Nếu không có quy tắc nào khớp -> Tự động duyệt (hoặc báo lỗi tùy cấu hình)
            self.state = 'approved'
            return

        # Giả sử quy trình duyệt tuần tự theo sequence
        next_approvers = self._get_approvers_from_rule(matrix_rules)
        self.approver_ids = [Command.set(next_approvers.ids)]
        self.state = 'to_approve'
        
        # Gửi thông báo
        for user in next_approvers:
            self.activity_schedule(
                'epr_management.mail_activity_data_epr_approval',
                user_id=user.id,
                note=_("Yêu cầu mua sắm %s cần bạn phê duyệt.") % self.name
            )
			
	5.2 Wizard tạo RFQ Tự động (RFQ Generation)
	
Sau khi PR được duyệt (state = approved), nhân viên mua hàng sẽ nhấn nút "Tạo RFQ". Hệ thống cần thông minh để gom nhóm các dòng sản phẩm.

Thuật toán:

		1. Gom nhóm (Grouping): Duyệt qua các dòng line_ids và nhóm chúng theo supplier_id.

			. Các dòng có cùng supplier_id sẽ vào cùng một RFQ.

			. Các dòng không có supplier_id sẽ được gom vào một RFQ nháp không có nhà cung cấp (hoặc tách riêng để xử lý thủ công).

		2. Khởi tạo RFQ:

			. Tạo header purchase.order.

			. Tạo lines purchase.order.line sử dụng Command.create.

		3. Liên kết ngược: Cập nhật trường purchase_line_ids trên epr.request.line để biết dòng này đã thuộc về PR nào.

Sử dụng Command.create (Chuẩn Odoo 18): Odoo 18 loại bỏ dần cách viết cũ (0, 0, values).
	
def action_create_rfqs(self):
        self.ensure_one()
        grouped_lines = {}
        # Gom nhóm logic...
        
        for supplier, lines in grouped_lines.items():
            po_vals = {
                'partner_id': supplier.id,
                'origin': self.name,
                'date_order': fields.Datetime.now(),
                'order_line': [
                    Command.create({
                        'product_id': line.product_id.id,
                        'product_qty': line.quantity,
                        'name': line.name,
                        'price_unit': 0.0, # Để trống để lấy giá mặc định từ bảng giá
                        'date_planned': self.date_required,
                    }) for line in lines
                ]
            }
            po = self.env['purchase.order'].create(po_vals)
            
            # Link back
            for line in lines:
                # Tìm line tương ứng trong PO mới tạo để link
                matching_po_line = po.order_line.filtered(lambda l: l.product_id == line.product_id)
                line.purchase_line_ids = [Command.link(matching_po_line.id)]
        
        self.state = 'done'


	5.3 Quy trình Từ chối (Rejection Workflow)
	
Khi từ chối, hệ thống bắt buộc người dùng nhập lý do. Điều này được thực hiện thông qua một TransientModel (Wizard).

		1. Nút "Reject" trên PR gọi action mở Wizard epr.reject.reason.

		2. Wizard có trường reason (Text, required).

		3. Khi confirm Wizard:

			. Ghi lý do vào Chatter của PR (sử dụng message_post).

			. Chuyển trạng thái PR sang draft.

			. Gửi email thông báo lại cho người yêu cầu (employee_id).
			
VI. Thiết kế Giao diện Người dùng (Views)

	6.1 View Danh sách (List View)
	
<record id="view_epr_request_list" model="ir.ui.view">
    <field name="name">epr.request.list</field>
    <field name="model">epr.request</field>
    <field name="arch" type="xml">
        <list string="Danh sách Yêu cầu" decoration-info="state == 'draft'" decoration-warning="state == 'to_approve'" decoration-success="state == 'approved'" sample="1">
            <field name="name"/>
            <field name="employee_id" widget="many2one_avatar_user"/>
            <field name="department_id" optional="show"/>
            <field name="date_required"/>
            <field name="amount_total" sum="Tổng giá trị" decoration-bf="1"/>
            <field name="state" widget="badge" decoration-success="state == 'approved'" decoration-danger="state == 'rejected'"/>
            <field name="company_id" groups="base.group_multi_company" optional="hide"/>
        </list>
    </field>
</record>

Phân tích: widget="many2one_avatar_user" hiển thị avatar người dùng, tăng tính thẩm mỹ ("vibe") cho giao diện. Thuộc tính sample="1" cho phép hiển thị dữ liệu mẫu khi view rỗng, giúp người dùng mới dễ hình dung.   

	6.2 View Biểu mẫu (Form View) và Chatter
	
<form string="Yêu cầu Mua sắm">
    <header>
        <button name="action_submit" string="Gửi duyệt" type="object" class="oe_highlight" invisible="state!= 'draft'"/>
        <button name="action_approve" string="Phê duyệt" type="object" class="oe_highlight" invisible="state!= 'to_approve'" groups="epr_management.group_epr_approver"/>
        <button name="%(action_epr_reject_wizard)d" string="Từ chối" type="action" invisible="state!= 'to_approve'" groups="epr_management.group_epr_approver"/>
        <button name="action_create_rfqs" string="Tạo Báo giá" type="object" class="btn-primary" invisible="state!= 'approved'" groups="purchase.group_purchase_user"/>
        <field name="state" widget="statusbar" statusbar_visible="draft,to_approve,approved,done"/>
    </header>
    <sheet>
        <div class="oe_title">
            <label for="name" class="oe_edit_only"/>
            <h1><field name="name"/></h1>
        </div>
        <group>
            <group>
                <field name="employee_id"/>
                <field name="department_id"/>
            </group>
            <group>
                <field name="date_required"/>
                <field name="company_id" groups="base.group_multi_company"/>
            </group>
        </group>
        <notebook>
            <page string="Sản phẩm">
                <field name="line_ids" widget="section_and_note_one2many">
                    <list editable="bottom">
                        <field name="product_id"/>
                        <field name="name"/>
                        <field name="quantity"/>
                        <field name="uom_id"/>
                        <field name="estimated_cost"/>
                        <field name="total_cost"/>
                        <field name="supplier_id"/>
                    </list>
                </field>
            </page>
        </notebook>
    </sheet>
    <chatter/>
</form>

	6.3 View Tìm kiếm và Search Panel (Mobile Optimized)
	
<record id="view_epr_request_search" model="ir.ui.view">
    <field name="name">epr.request.search</field>
    <field name="model">epr.request</field>
    <field name="arch" type="xml">
        <search>
            <field name="name"/>
            <field name="employee_id"/>
            <field name="product_id" filter_domain="[('line_ids.product_id', 'ilike', self)]"/>
            
            <filter string="Yêu cầu của tôi" name="my_requests" domain="[('employee_id.user_id', '=', uid)]"/>
            <filter string="Chờ duyệt" name="to_approve" domain="[('state', '=', 'to_approve')]"/>
            
            <searchpanel>
                <field name="state" icon="fa-tasks" enable_counters="1"/>
                <field name="department_id" icon="fa-building" enable_counters="1"/>
            </searchpanel>
        </search>
    </field>
</record>

VII. Bảo mật và Phân quyền (Security & Access Control)

	7.1 Định nghĩa Nhóm (Groups)
Chúng ta sẽ tạo 3 nhóm quyền chính trong security/epr_security.xml:

		1. ePR / User (Người dùng): Chỉ có quyền tạo và xem PR của chính mình.

		2. ePR / Approver (Người duyệt): Có quyền xem và duyệt PR của các phòng ban mà mình quản lý.

		3. ePR / Administrator (Quản trị): Có quyền cấu hình ma trận phê duyệt và can thiệp mọi PR.
		
	7.2 Record Rules
Để đảm bảo tính riêng tư dữ liệu (Row-level security):

	- Rule User: [('employee_id.user_id', '=', user.id)] -> Chỉ thấy PR do mình tạo.

	- Rule Approver:
	
['|',
    ('employee_id.user_id', '=', user.id),
    '|',
        ('department_id.manager_id.user_id', '=', user.id),
        ('approver_ids', 'in', [user.id])
]

-> Thấy PR của mình HOẶC PR của phòng mình quản lý HOẶC PR mà mình được chỉ định duyệt.

	7.3 Danh sách Quyền Truy cập (ACL - CSV)
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_epr_request_user,epr.request.user,model_epr_request,group_epr_user,1,1,1,0
access_epr_request_approver,epr.request.approver,model_epr_request,group_epr_approver,1,1,0,0
access_epr_request_manager,epr.request.manager,model_epr_request,group_epr_manager,1,1,1,1
access_epr_matrix_user,epr.matrix.user,model_epr_approval_matrix,group_epr_user,1,0,0,0
access_epr_matrix_manager,epr.matrix.manager,model_epr_approval_matrix,group_epr_manager,1,1,1

VIII. Tích hợp với Module Kho (Inventory)

Khi tạo RFQ từ PR, cần xác định chính xác picking_type_id (Loại giao nhận) trên PO.

	- Logic: PR sẽ có trường destination_warehouse_id.

	- Khi tạo PO, hệ thống sẽ tìm picking_type_id ứng với kho đó (thường là "Receipts" - Nhận hàng).

	- Điều này đảm bảo hàng về đúng kho yêu cầu, tránh việc hàng về kho tổng rồi phải điều chuyển nội bộ thủ công.