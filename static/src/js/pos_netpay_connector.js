odoo.define('pos_netpay_connector.models', function(require) {
    "use strict";
    const models = require('point_of_sale.models');

    // Cargar campos en la cache del POS para poder acceder desde JS
    models.load_fields('pos.payment.method', ['terminal_api_key', 'terminal_api_pwd', 'terminal_id', 'administrators_only', 'netpay_test_mode', 'netpay_api_base', 'netpay_terminal_identifier']);
});