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

                if (paymentMethod.administrators_only && !userIsAdmin) {
                    // Mostrar el popup de error
                    Gui.showPopup('ErrorPopup', {
                        title: 'Acceso restringido',
                        body: `El método de pago "${paymentMethod.name}" solo está disponible para administradores.`,
                    }).then(() => {
                        // Eliminar la línea de pago no autorizada
                        order.remove_paymentline(line);
                        // Forzar la actualización de la vista
                        this.render();
                    });
                    
                    return {}; // No aplicar estilos de selección
                }

                return super.selectedLineClass(line);
            }
        };

    Registries.Component.extend(PaymentScreenPaymentLines, PatchedPaymentLines);
    return PaymentScreenPaymentLines;
});