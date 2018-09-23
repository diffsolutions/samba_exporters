<?php
/**
*  @author    Martin Tomasek
*  @copyright DiffSolutions, s.r.o.
*  @license   https://creativecommons.org/licenses/by-sa/4.0/ CC BY-SA 4.0
*/

include_once('fcommon.php');
include_once('fcustomer.php');

function group_order_details($orders)
{
    $os = array();
    $oid = null;
    $acc = array();
    foreach ($orders as $order) {
        $order_id = $order['id_order'];
        if ($oid != $order_id) {
            if (isset($oid)) {
                $os[$oid] = $acc;
            }
            $acc = array();
            $oid = $order_id;
        }
        $acc[] = $order;
    }
    return $os;
}

class FOrder
{
    public function __construct($w, $common)
    {
        $this->w = $w;
        $this->common = $common;
        #$LANG_ID = $common->getConfig('LANG_ID');
        #$SHOP_ID = $common->getConfig('SHOP_ID');
        $this->q = "select o.*, a.*, od.* from ".$common->tname('orders', 'o')." ".
                $common->tjoin('address', 'a').' on o.id_address_delivery = a.id_address '.
                $common->tjoin('order_detail', 'od').' on o.id_order = od.id_order '.
                'order by o.id_order';
    }

    public function genFeed()
    {
        $w = $this->w;
        $common = $this->common;

        $customer = new FCustomer($w, $common, false);
        $customer_info = $customer->genFeed();
        $cust_email = $customer_info['email'];
        $cust_valid = $customer_info['valid'];

        $orders = Db::getInstance()->ExecuteS($this->q);
        $orders = group_order_details($orders);
        foreach ($orders as $order_id => $ods) {
            $o = $ods[0];
            $order_id = $o['id_order'];
            $customer_id = (int)$o['id_customer'];

            if (!array_key_exists($customer_id, $cust_valid)) {
                continue; #GDPR
            }
            $xw = $w->startLn();
            #$customer_id = base64_encode($o['id_customer']);
            $status = $common->orderStatus((int)($o['current_state']));
            $xw->writeElement('ORDER_ID', $order_id);
            $xw->writeElement('CUSTOMER_ID', $customer_id);
            $xw->writeElement('CREATED_ON', $common->dtIso($o['date_add']));
            if (array_key_exists($customer_id, $cust_email)) {
                $xw->writeElement('EMAIL', $cust_email[$customer_id]);
            }
            if ($status == 'finished') {
                $xw->writeElement('FINISHED_ON', $common->dtIso($o['delivery_date']));
            }
            $xw->writeElement('STATUS', $status);
            if (!empty($o['postcode'])) {
                $xw->writeElement('ZIP_CODE', $o['postcode']);
            }
            if (!empty($o['phone_mobile'])) {
                $xw->writeElement('PHONE', $o['phone_mobile']);
            }
            $xw->startElement('ITEMS');
            foreach ($ods as $od) {
                $xw->startElement('ITEM');
                $xw->writeElement('PRODUCT_ID', $od['product_id'].'-'.$od['product_attribute_id']);
                $xw->writeElement('PRICE', $od['total_price_tax_incl']);
                $xw->writeElement('AMOUNT', $od['product_quantity']);
                $xw->endElement();
            }
            $xw->endElement();
            $w->endLn();
        }
        $w->end();
        return $orders;
    }
}
