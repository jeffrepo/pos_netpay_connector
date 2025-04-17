odoo.define('pos_netpay_connector.models', function(require) {
    var models = require('point_of_sale.models');
    var PaymentTerminal = require('pos_netpay_connector.payment');

    models.register_payment_method('netpay', PaymentTerminal);
    models.load_fields('pos.payment.method', ['terminal_api_key', 'terminal_api_pwd', 'terminal_id']);

   var _payterminal = models.Paymentline.prototype;
   //var _payecoduit = models.Paymentline.prototype
   models.Paymentline = models.Paymentline.extend({
        init_from_JSON: function(json) {
           _payterminal.init_from_JSON.apply(this, arguments);
               //pass your credentials like
              //this.last_digits = json.last_digits;
            },
        export_as_JSON: function() {
             return _.extend(_payterminal.export_as_JSON.apply(this, arguments), {
              //pass your credentials like
              //this.last_digits = json.last_digits;
        });
        },
  });


var _super_order = models.Order.prototype;
models.Order = models.Order.extend({
    
    initialize: function() {
        _super_order.initialize.apply(this,arguments);
        this.set_netpay_orderId();
    },
    
    export_as_JSON: function() {
        var json = _super_order.export_as_JSON.apply(this,arguments);
        
        json.netpay_orderId = this.get_netpay_orderId();
        
        return json;
    },
    
    get_netpay_orderId: function(){
        return this.get('netpay_orderId');
    },
    
    set_netpay_orderId: function(netpay_orderId){
        this.set({
          netpay_orderId: netpay_orderId
        });
    },
    
});
});