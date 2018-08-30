<!-- Samba.ai scripts -->
<script async src="https://yottlyscript.com/script.js?tp=XXXXXX"></script>
<script type="text/javascript">
function _yt_product_id(prod, attr){
return String(prod) + "-" + String(attr);
}

function _yt_send_order(){
sps = new Array();
function to_sp(o) { return {productID: _yt_product_id(o.id_product, o.id_product_attribute), amount: o.quantity, price: o.quantity * o.price_with_reduction}; };
prestashop.cart.products.forEach(function(el) { sps.push(to_sp(el)) });
diffAnalytics.order({ content: sps });
};

function yt_run() {
if (prestashop.customer.email) {
diffAnalytics.customerLoggedIn(prestashop.customer.email);
};

doc = document.querySelector("#payment-confirmation button");
if (doc != null) {
onOrderPage = true;
//doc.addEventListener("click", _yt_send_order); 
_yt_send_order();
} else {
onOrderPage = false;
};

sps = new Array();
function to_sp(o) { return {productID: _yt_product_id(o.id_product, o.id_product_attribute), amount: parseInt(o.cart_quantity)}; };
prestashop.cart.products.forEach(function(el) { sps.push(to_sp(el)) });
diffAnalytics.cartInteraction({ content: sps, onOrderPage: onOrderPage });
};

var _yottlyOnload = _yottlyOnload || []
_yottlyOnload.push(function () { 
yt_run();
});

</script>
<!-- End Samba.ai scripts -->
