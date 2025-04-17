# -*- coding: utf-8 -*-


{
    'name': 'Pos netpay connector',
    'version': '1.1',
    'category': 'Hidden',
    'sequence': 6,
    'summary': 'Pos netpay connector',
    'description': """

""",
    'depends': ['base','point_of_sale'],
    'data': [
        'views/pos_config_view.xml',
        'views/pos_order_views.xml',
        # 'security/ir.model.access.csv',
    ],
    'assets':{
        'point_of_sale.assets': [
            'pos_netpay_connector/static/src/js/pos_netpay_connector.js',
            'pos_netpay_connector/static/src/js/payment_netpay.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}
