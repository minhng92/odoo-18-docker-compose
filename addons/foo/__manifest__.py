# -*- coding: utf-8 -*-
# https://www.odoo.com/documentation/18.0/developer/reference/backend/module.html
{
    'name': 'Foo',
    'summary': """Foo custom addon""",
    'description': """Foo module description""",
    'author': 'minhng.info',
    'maintainer': 'minhng.info',
    'website': 'https://minhng.info',
    'category': 'Uncategorized', # https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    'version': '0.1',
    'depends': [
        'sale',
        'hr',
    ],
    'data': [],
    'demo': [],
    'css': [],
    # 'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
}