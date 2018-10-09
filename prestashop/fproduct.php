<?php
/**
*  @author    Martin Tomasek
*  @copyright DiffSolutions, s.r.o.
*  @license   https://creativecommons.org/licenses/by-sa/4.0/ CC BY-SA 4.0
*/

include_once('fcommon.php');
include_once('fcategory.php');

function price_with_tax($id_product, $id_product_attribute, $use_reduction)
{
    $specific_price = 0;
    return Product::getPriceStatic(
        (int) $id_product,
        true,
        (int) $id_product_attribute,
        2,
        null,
        false,
        $use_reduction,
        1,
        false,
        null,
        null,
        null,
        $specific_price,
        true,
        true,
        null,
        false
    );
}



class FProduct
{
    public function __construct($w, $common)
    {
        $this->w = $w;
        $this->common = $common;
        $LANG_ID = $common->getConfig('LANG_ID');
        $SHOP_ID = $common->getConfig('SHOP_ID');
        $this->q = "select p.*, min(i.id_image) as image, pl.*, ".
            "cl.link_rewrite as cat_link_rewrite, s.quantity as stock ".
            'from '.$common->tname('product').' as p '.
            $common->tjoin('product_lang', 'pl').' on pl.id_product = p.id_product '.
            $common->tjoin('image', 'i').' on p.id_product = i.id_product '.
            $common->tjoin('stock_available', 's').' on s.id_product = p.id_product '.
            $common->tjoin('category_lang', 'cl').' on cl.id_category = p.id_category_default '.
            'where pl.id_lang = '.$LANG_ID.' & '.
                'pl.id_shop = '.$SHOP_ID.' & '.
                's.id_shop = '.$SHOP_ID.' & '.
                's.id_product_attribute = 0 & '.
                'cl.id_lang = '.$LANG_ID.' '.
            'group by p.id_product';
    }


    public function genFeed()
    {
        $w = $this->w;
        $common = $this->common;
        $LANG_ID = $this->common->getConfig('LANG_ID');
        $SHOP_ID = $this->common->getConfig('SHOP_ID');
        $EMPLOYEE_ID = $this->common->getConfig('EMPLOYEE_ID');

        $categories = new FCategory($w, $common, false);
        $cats = $categories->genFeed(); # returns indexed categories

        $db = Db::getInstance();
        $products = $db->ExecuteS($this->q);
        $context = Context::getContext();
        $employee = new Employee($EMPLOYEE_ID, $LANG_ID, $SHOP_ID);
        $context->employee = $employee;
        foreach ($products as $p) {
            $xw = $w->startLn();
            $product_id = $p['id_product'];
            #$core_product = new Product($product_id);
            $xw->writeElement('PRODUCT_ID', $product_id.'-0');
            $xw->writeElement('TITLE', $p['name']);
            $xw->writeElement('DESCRIPTION', $p['description']);
            $xw->writeElement('URL', $common->genUrl(
                array(
                'id' => $product_id,
                'rewrite' => $p['link_rewrite'],
                'id_product_attribute' => null,
                ),
                'product'
            ));
            $xw->writeElement('IMAGE', $common->imgUrl($p['image'], $p['link_rewrite']));
            if (array_key_exists('cattext', $cats[$p['id_category_default']])) {
                $cattext = ($cats[$p['id_category_default']])['cattext'];
                $xw->writeElement('CATEGORYTEXT', $cattext);
            }
            $stock = $p['stock'];
            if (!$p['active']) {
                $stock = 0;
            }
            if ($p['visibility'] == 'none') {
                $stock = 0;
            }
            if ($p['show_price'] <= 0) {
                $stock = 0;
            }
            $xw->writeElement('STOCK', $stock);
            //$xw->writeElement('PRICE', $price);
            $xw->writeElement('PRICE', price_with_tax((int)$product_id, null, true));
            $xw->writeElement('PRICE_BEFORE_DISCOUNT', price_with_tax((int)$product_id, null, false));

            $wsp = $p['wholesale_price'];
            if ($wsp && $wsp>0) {
                $xw->writeElement('PRICE_BUY', (int)((float)$wsp *100)/100);
            } #buy price rouded to 2 decimal places

            $common->parameter($xw, 'width', $p['width']);
            $common->parameter($xw, 'depth', $p['depth']);
            $common->parameter($xw, 'height', $p['height']);
            $common->parameter($xw, 'weight', $p['weight']);
            #$xw->writeElement('VARIANT', null);
            $this->variants($db, $product_id, $p['link_rewrite'], $p['image']);
            $w->endLn();
        }
        $w->end();
        return $products;
    }

    public function variants($db, $product_id, $link_rewrite, $image)
    {
        if (empty($product_id)) {
            return;
        }
        $common = $this->common;
        $q='select pa.*, pac.* from '.$common->tname('product_attribute', 'pa').' '.
            $common->tjoin('product_attribute_combination', 'pac').
            ' on pa.id_product_attribute = pac.id_product_attribute '.
            'where pa.id_product = '.$product_id.' '.
            'order by pac.id_product_attribute';
        $vs = $db->ExecuteS($q);
        $default_ixs = array();
        foreach ($vs as $ix => $v) {
            if ($v['default_on'] == '1') {
                $default_ixs[] = $ix;
            }
        }
        if ($default_ixs) {
            $default_ix = $default_ixs[0];
            if ($default_ix > 0) {
                $tmp = $vs[$default_ix];
                $vs[$default_ix] = $vs[0];
                $vs[0] = $tmp;
            }
        }

        foreach ($common->groupby($vs, 'id_product_attribute') as $id => $vg) {
            if (empty($vg)) {
                continue;
            }
            /*
            $aids = array();
            foreach ($vg as $item) {
                $aids[] = (int)($item['id_attribute']);
            }
            sort($aids);*/
            #$variant_id = $product_id.'-'.implode(':', $aids);
            $id_product_attribute = $vg[0]['id_product_attribute'];
            $variant_id = $product_id.'-'.$id_product_attribute;
            $xw = $this->w->getWriter();
            $xw->startElement('VARIANT');
            $xw->writeElement('PRODUCT_ID', $variant_id);
            $xw->writeElement(
                'PRICE',
                price_with_tax((int)$product_id, (int)$id_product_attribute, true)
            );
            $xw->writeElement(
                'PRICE_BEFORE_DISCOUNT',
                price_with_tax(
                    (int)$product_id,
                    (int)$id_product_attribute,
                    false
                )
            );
            $xw->writeElement('IMAGE', $common->imgUrl($image, $link_rewrite));
            $xw->writeElement('URL', $common->genUrl(
                array(
                'id' => $product_id,
                'rewrite' => $link_rewrite,
                'id_product_attribute' => $id_product_attribute,
                ),
                'product'
            ));

            #TODO: parameters
            #$parameters = array();
            $xw->endElement();
        }
    }
}
