# -*- coding: utf-8 -*-
# https://www.odoo.com/documentation/18.0/developer/reference/backend/module.html
{
    'name': 'Zoo City',
    'summary': """Zoo City Tutorials""",
    'description': """Building my own zoo city""",
    'author': 'minhng.info',
    'maintainer': 'minhng.info',
    'website': 'https://minhng.info',
    'category': 'Uncategorized', # https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    'version': '0.1',

    # Dependencies
    'depends': [
        'product',
        'mail',
        'hr',
    ],

    # Data files declaration
    'data': [
        'security/zoo_security.xml',
        'security/ir.model.access.csv',
        'views/zoo_animal_views.xml',
        'views/zoo_creature_views.xml',
        'views/zoo_cage_views.xml',
        'views/zoo_health_records.xml',
        'views/zoo_animal_meal_views.xml',
        'views/zoo_diet_plans.xml',
        'views/zoo_husbandry_task_views.xml',
        'views/zoo_keeper_views.xml',
        'views/zoo_keeper_certificate_views.xml',
        'views/zoo_keeper_speciality_views.xml',
        'wizard/toy_add_views.xml',
        'wizard/cage_update_views.xml',
        'wizard/animal_feeding_views.xml',
        'report/zoo_report_action.xml',
        'report/zoo_report_template.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
