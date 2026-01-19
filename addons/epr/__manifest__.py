{
    'name': 'Electronic Purchase Request (ePR) Enterprise',
    'version': '18.0.1.0.0',
    'category': 'Procurement/Inventory',
    'summary': 'Hệ thống quản lý yêu cầu mua sắm nội bộ với quy trình phê duyệt đa cấp động',
    'description': """
        Module ePR được thiết kế chuyên biệt cho Odoo 18.
        Các tính năng cốt lõi:
        - Tách biệt quy trình Yêu cầu (Internal) và Mua hàng (External).
        - Cho phép gom nhiều PRs vào một RFQs và có thể truy xuất theo từng dòng trên PO.
        - Ma trận phê duyệt động (Approval Matrix) dựa trên ngưỡng tiền tệ và phòng ban.
    """,
    'author': 'Trường Phan',
    'depends': [
        'base',
        'purchase',       # Để kết nối với purchase.order [8]
        'hr',             # Để lấy thông tin phòng ban và quản lý
        'product',        # Quản lý danh mục sản phẩm
        # 'stock',          # Quản lý kho và địa điểm nhận hàng
        'mail',           # Tích hợp Chatter và Activity
        'uom',            # Đơn vị tính
        # 'analytic',       # Kế toán quản trị (nếu cần phân bổ chi phí)
    ],

    'data': [
        'security/epr_security.xml',
        'security/ir.model.access.csv',
        'security/epr_record_rules.xml',
        'data/epr_pr_sequence_data.xml',
        'data/epr_rfq_sequence_data.xml',
        'views/epr_purchase_request_views.xml',
        'views/epr_rfq_views.xml',
        'views/epr_approval_views.xml',
        'views/epr_po_views.xml',
        'views/epr_menus.xml',
        'wizards/epr_reject_wizard_views.xml',
        'wizards/epr_reject_rfq_wizard_views.xml',
        'wizards/epr_create_rfq_views.xml',
        'wizards/epr_create_po_views.xml',
    ],
    'assets': {
        # 'web.assets_backend': [
        #     'epr_management/static/src/scss/epr_status_widget.scss',
        # ],
    },
    'installable': True,
    'application': True,
    'license': 'OEEL-1',
}
