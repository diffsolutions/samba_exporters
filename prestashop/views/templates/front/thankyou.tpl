{*
*  @author    Martin Tomasek
*  @copyright DiffSolutions, s.r.o.
*  licensed under CC BY-SA 4.0
*}

<!-- samba.ai thankyou code -->
<!-- order products: -->
<script>
prestashop.order = [
{foreach $products as $p}
{literal}{{/literal}
id_product: "{$p['id_product']|escape:'javascript'}",
id_product_attribute: "{$p['id_product_attribute']|escape:'javascript'}",
name: "{$p['product_name']|escape:'javascript'}",
quantity: {$p['product_quantity']|escape:'javascript'},
price_with_reduction: {$p['product_price_wt']|escape:'javascript'}
{literal}}{/literal},
{/foreach}
];
</script>
