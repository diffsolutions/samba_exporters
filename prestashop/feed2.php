<?php
/**
*  @author    Martin Tomasek
*  @copyright DiffSolutions, s.r.o.
*  @license   https://creativecommons.org/licenses/by-sa/4.0/ CC BY-SA 4.0
*/

ini_set('max_execution_time', '0');

include_once(dirname(__FILE__).'/../../config/config.inc.php');
#include_once(dirname(__FILE__).'/../../config/setting.inc.php');
include_once('fcommon.php');
include_once('xmlWriter.php');
include_once('fcustomer.php');
include_once('fcategory.php');
include_once('fproduct.php');
include_once('forder.php');

$config = array(
    'DB_PREFIX' => 'ps_',
    'LANG_ID' => (int)(Configuration::get('SAMBA_LANG')),
    'SHOP_ID' => (int)(Configuration::get('SAMBA_SHOP')),
    'EMPLOYEE_ID' => 1, #TODO: we are using this employee id to get correct prices. find a better solution.
    'SHOP_URL_BASE' => 'http://'.Configuration::get('PS_SHOP_DOMAIN_SSL').'/',
    'link' =>new Link()
    );

$common = new Common($config);

$feed_name = Tools::getValue('feed');
$key = Tools::getValue("key");
$SAMBA_KEY= Configuration::get('SAMBA_KEY');
if ($key!=$SAMBA_KEY) {
    echo "<html><body>Wrong key, access denied.</body></html>";
    http_response_code(403);
    return;
}

header('Content-Type: text/xml');

switch ($feed_name) {
    case 'customers':
        //customers
        $w = new XMLW('php://output', 'CUSTOMERS', 'CUSTOMER');
        $cust = new FCustomer($w, $common);
        $cust->genFeed();
        break;

    case 'categories':
        //categories
        $w = new XMLW('php://output', 'CATEGORIES', '');
        $cats = new FCategory($w, $common);
        $cats->genFeed();
        break;

    case 'products':
        //products
        $w = new XMLW('php://output', 'PRODUCTS', 'PRODUCT');
        $prod = new FProduct($w, $common);
        $prod->genFeed();
        break;

    case 'orders':
        //orders
        $w = new XMLW('php://output', 'ORDERS', 'ORDER');
        $ord = new FOrder($w, $common);
        $ord->genFeed();
        break;
}
