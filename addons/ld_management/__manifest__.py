# -*- coding: utf-8 -*-
{
    'name': "L&D Management",
    'summary': """
        Learning & Development Management System.
        Handles Training Requests, Course Catalog, Sessions, and Certifications.
    """,
    'description': """
        L&D Management System for Odoo 18
        =================================

        Key Features:
        -------------
        * **Role-Based Access:**
            - Learners (All employees)
            - L&D Officers (Operation)
            - L&D Managers (Strategic)
        * **Dynamic Approval:**
            - Line Managers automatically have approval rights via Record Rules without needing a specific group.
        * **Process Management:**
            - Training Requests -> Approval -> Enrollment -> Evaluation -> Certification.

        Technical Notes:
        ----------------
        - Dependencies: 'hr' for Org Chart, 'mail' for Chatter.
    """,
    'author': "Truong Phan",
    'website': "https://linkedin.com/in/truong-phan/",
    'category': 'Human Resources/Learning',
    'version': '18.0.1.0.0',

    # Any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'mail', 'hr_skills', 'survey'],

    # Always loaded
    'data': [
        # Security (Order is crucial: Groups first, then CSV, then Rules)
        'security/ld_security.xml',
        'security/ir.model.access.csv',
        'security/ld_record_rules.xml',
        'data/ld_training_request_sequence_data.xml',
        'data/ld_session_sequence_data.xml',
        'views/ld_course_category_views.xml',
        'views/ld_course_views.xml',
        'views/ld_room_views.xml',
        'views/ld_session_views.xml',
        'views/ld_enrollment_views.xml',
        'views/ld_training_request_views.xml',
        'views/ld_menus.xml',
        'wizards/ld_training_request_reject_wizard_views.xml',
        

        # Data
        # 'data/ld_sequence_data.xml',

        # Views
        # 'views/ld_request_views.xml',
        # 'views/ld_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
