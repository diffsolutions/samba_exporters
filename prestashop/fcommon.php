<?php
/**
*  @author    Martin Tomasek
*  @copyright DiffSolutions, s.r.o.
*  @license   https://creativecommons.org/licenses/by-sa/4.0/ CC BY-SA 4.0
 */

class Common
{
    public function __construct($config)
    {
        $this->config = $config;
        $this->dispatcher = Dispatcher::getInstance();
    }

    public function getConfig($name)
    {
        return $this->config[$name];
    }

    public function tname($name, $alias = null)
    {
        if (isset($alias)) {
            return $this->config['DB_PREFIX'].$name.' as '.$alias;
        } else {
            return $this->config['DB_PREFIX'].$name;
        }
    }

    public function tjoin($name, $alias = null)
    {
        $q= ' inner join '.$this->tname($name, null);
        if (isset($alias)) {
            $q.= ' as '.$alias;
        }
        return $q;
    }

    public function parameter($w, $name, $value)
    {
        if (!empty($value) and (!gettype($value) == 'string' or $value != '0.0000000')) {
            #strings are not converted to floats during processing

            $w->startElement('PARAMETER');
            $w->writeElement('NAME', $name);
            $w->writeElement('VALUE', $value);
            $w->endElement();
        }
    }

    public function subtree($w, $node_id, $cattext = array(), &$nodes = null, &$children = null, $write = true)
    {
        $node = $nodes[$node_id];
        $ct = $cattext; #explicit copy
        $name = $node['name'];
        $ct[] = $name;
        $full_name = implode(' | ', $ct);
        $node['cattext'] = $full_name;
        if ($write) {
            $w->startElement('ITEM');
            $w->writeElement('TITLE', $name);
            $w->writeElement('URL', $node['url']);
            #$w->writeElement('CATTEXT', $full_name);
        }
        if (array_key_exists($node_id, $children)) {
            foreach ($children[$node_id] as $child) {
                $this->subtree($w, $child['id'], $ct, $nodes, $children, $write);
            }
        }
        if ($write) {
            $w->endElement();
        }
        $nodes[$node_id] = $node;
    }

    public function dtIso($dt)
    {
        $p = explode(' ', $dt);
        if (count($p)>1) {
            return $p[0].'T'.$dt[1].'Z';
        } else {
            return $dt;
        }
    }


    public function genUrl($params, $what = 'category')
    {
        $url_path = $this->dispatcher->createUrl(
            $what.'_rule',
            $this->config['LANG_ID'],
            $params,
            false,
            '',
            $this->config['SHOP_ID']
        );
        return $this->config['SHOP_URL_BASE'].$url_path;
    }

    public function imgUrl($img_id, $link_rewrite)
    {
        return "http://".$this->config['link']->getImageLink($link_rewrite, $img_id);
    }

    public function reducedPrice($product_id, $price, $tax = 0)
    {
        $r=SpecificPrice::getSpecificPrice($product_id, 0, 0, 0, 0, 1);
        $price_before = $price;
        if ($r) {
            if ($r['reduction_type'] == 'percentage') {
                $price = $price * (1-$r['reduction']);
            } else {
                $price = ($price - $r['reduction']);
            }
        }
        return array($price * (1+$tax), $price_before * (1+$tax));
    }

    public function orderStatus($status_id)
    {
        $ORDER_CANCELLED = array(6 => true);
        $ORDER_FINISHED = array(5 => true);

        if (array_key_exists($status_id, $ORDER_FINISHED)) {
            return 'finished';
        }
        if (array_key_exists($status_id, $ORDER_CANCELLED)) {
            return 'canceled';
        }
        return 'created';
    }

    public function groupby($items, $key)
    {
        $is = array();
        $id = null;
        $acc = array();
        foreach ($items as $item) {
            $item_id = $item[$key];
            if ($id != $item_id) {
                if (isset($id)) {
                    $is[$id] = $acc;
                }
                $acc = array();
                $id = $item_id;
            }
            $acc[] = $item;
        }
        $is[$id] = $acc;
        return $is;
    }

    public function maybeFloat($val)
    {
        if (empty($val)) {
            return null;
        }
        $v = (float)($val);
        return $v;
    }
}
