# -*- coding: utf-8 -*-
{
    'name': 'Pos Netpay Connector',
    'version': '2.0.0',
    'category': 'Point Of Sale',
    'summary': 'Connector Netpay para POS (migrado a Odoo 19)',
    'description': """Integración de Netpay para pagos en el Point of Sale.""",
    'license': 'LGPL-3',
    'author': 'Tu Empresa',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/pos_config_view.xml',
        'views/pos_order_views.xml',
        'views/pos_payment_method_views.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_netpay_connector/static/src/app/payment_netpay.js',
            'pos_netpay_connector/static/src/app/pos_payment.js',
            'pos_netpay_connector/static/src/app/screens/payment_screen/payment_screen.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
