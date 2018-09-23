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

print($common->getConfig('LANG_ID'));

$w = new XMLW('customers.xml', 'CUSTOMERS', 'CUSTOMER');
$cust = new FCustomer($w, $common);
$cust->genFeed();

$w = new XMLW('categories.xml', 'CATEGORIES', '');
$cats = new FCategory($w, $common);
$cats->genFeed();

$w = new XMLW('products.xml', 'PRODUCTS', 'PRODUCT');
$prod = new FProduct($w, $common);
$prod->genFeed();

$w = new XMLW('orders.xml', 'ORDERS', 'ORDER');
$ord = new FOrder($w, $common);
$ord->genFeed();
