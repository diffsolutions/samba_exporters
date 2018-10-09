{*
*  @author    Martin Tomasek
*  @copyright DiffSolutions, s.r.o.
*  licensed under CC BY-SA 4.0
*}
{literal}
<!-- Samba.ai scripts -->
<script async src="https://yottlyscript.com/script.js?tp={/literal}{$trackpoint|escape:'htmlall':'UTF-8'}{literal}"></script>
<script type="text/javascript">
function _yt_product_id(prod, attr){
return String(prod) + "-" + String(attr);
}

function _yt_send_order(){
sps = new Array();
function to_sp(o) { return {productId: _yt_product_id(o.id_product, o.id_product_attribute), price: o.quantity * o.price_with_reduction}; };
prestashop.order.forEach(function(el) { sps.push(to_sp(el)) });
diffAnalytics.order({ content: sps });
};

function yt_run() {
id_customization = "0"
el=document.getElementById('add-to-cart-or-refresh')
if (el != null){
 for(node of el.childNodes) { if (node.name == 'id_product') {id_product = node.value;};
  if (node.name == 'id_customization') {id_customization = node.value;} }
diffAnalytics.productId(id_product + "-" + id_customization)
};
if (prestashop.customer.email) {
diffAnalytics.customerLoggedIn("{/literal}{$customer_id|escape:'htmlall':'UTF-8'}{literal}");
};
diffAnalytics.setTrackingPermissions({ "doNotTrack": false });

doc = document.querySelector("#payment-confirmation button");
if (doc != null) {
onOrderPage = true;
} else {
onOrderPage = false;
};

if (prestashop.order != null) {
_yt_send_order();
};

sps = new Array();
function to_sp(o) { return {productId: _yt_product_id(o.id_product, o.id_product_attribute), amount: parseInt(o.cart_quantity)}; };
prestashop.cart.products.forEach(function(el) { sps.push(to_sp(el)) });
diffAnalytics.cartInteraction({ content: sps, onOrderPage: onOrderPage });
};

var _yottlyOnload = _yottlyOnload || []
_yottlyOnload.push(function () { 
yt_run();
});

</script>
<!-- End Samba.ai scripts -->
{/literal}
