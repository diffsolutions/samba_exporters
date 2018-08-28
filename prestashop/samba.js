<!-- Samba.ai scripts -->
<script async src="https://yottlyscript.com/script.js?tp=720224"></script>
<script type="text/javascript">
function yt_run() {
diffAnalytics.customerLoggedIn(prestashop.customer.email);
sps = new Array();
function to_sp(o) { return {productID: o.id_product, amount: o.cart_quantity}; };
prestashop.cart.products.forEach(function(el) { sps.push(to_sp(el)) });
diffAnalytics.cartInteraction({ content: sps });

doc = document.querySelector("#payment-confirmation button");
if (doc != null) {addEventListener("click", function(){
sps = new Array();
function to_sp(o) { return {productID: o.id_product, amount: o.quantity, price: o.quantity * o.price_with_reduction}; };
prestashop.cart.products.forEach(function(el) { sps.push(to_sp(el)) });
diffAnalytics.order({ content: sps });
});
}};

var _yottlyOnload = _yottlyOnload || []
_yottlyOnload.push(function () {
yt_run();
});

</script>
<!-- End Samba.ai scripts -->


