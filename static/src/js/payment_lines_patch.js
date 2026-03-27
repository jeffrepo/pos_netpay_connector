odoo.define('pos_netpay_connector.payment_lines_patch', function(require) {
    'use strict';

    const PaymentScreenPaymentLines = require('point_of_sale.PaymentScreenPaymentLines');
    const Registries = require('point_of_sale.Registries');
    const { Gui } = require('point_of_sale.Gui');

    const PatchedPaymentLines = PaymentScreenPaymentLines => 
        class extends PaymentScreenPaymentLines {
            selectedLineClass(line) {
                const paymentMethod = line.payment_method;
                const order = line.order;
                const userIsAdmin = order.pos.user.role === 'manager';
                if (paymentMethod && paymentMethod.administrators_only && !userIsAdmin) {
                    Gui.showPopup('ErrorPopup', {
                        title: 'Acceso restringido',
                        body: `El método de pago "${paymentMethod.name}" solo está disponible para administradores.`,
                    }).then(() => {
                        order.remove_paymentline(line);
                        this.render();
                    });
                    return {};
                }
                return super.selectedLineClass(line);
            }
        };

    Registries.Component.extend(PaymentScreenPaymentLines, PatchedPaymentLines);
});