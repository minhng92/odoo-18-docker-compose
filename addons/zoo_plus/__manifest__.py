{
    'name': 'Zoo Plus',
    'summary': """Zoo Plus""",
    'description': """Building a zoo plus - Inheritence from Zoo City""",
    'author': 'Truong Phan',
    'maintainer': 'Truong Phan',
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'zoo', # <-- depends on zoo (parent - Folder name) addon
        'point_of_sale',    # <-- depends on point_of_sale addon
    ],
    'data': [
        'security/ir.model.access.csv',
    ],

    'assets': {
        'point_of_sale._assets_pos': [            
            'zoo_plus/static/src/xml/product_card_name_template.xml',
            'zoo_plus/static/src/xml/product_price.xml',
        ],
    },
    'demo': [],
    'css': [],
    # 'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
}