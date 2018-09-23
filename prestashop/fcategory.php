<?php
/**
*  @author    Martin Tomasek
*  @copyright DiffSolutions, s.r.o.
*  @license   https://creativecommons.org/licenses/by-sa/4.0/ CC BY-SA 4.0
*/

include_once('fcommon.php');



class FCategory
{
    public function __construct($w, $common, $write = true)
    {
        $this->w = $w;
        $this->common = $common;
        $this->write = $write;
        $LANG_ID = $common->getConfig('LANG_ID');
        $SHOP_ID = $common->getConfig('SHOP_ID');

        $custom_order='CASE id_lang when '.$LANG_ID.' then 100 when 0 then 99 else -1000 end';
        $this->q = 'select c.*, cl.name, max('.$custom_order.') '.
            ' from '.$common->tname('category', 'c').' '.
            $common->tjoin('category_lang', 'cl').' on cl.id_category = c.id_category '.
            ' where cl.id_lang = '.$LANG_ID.' and cl.id_shop = '.$SHOP_ID.' '.
            ' group by c.id_category';
    }

    public function genFeed()
    {
        $w = $this->w;
        $common = $this->common;
        $children = array();
        $roots = array();
        $nodes = array();

        #echo "query: ".$this->q.'\n';
        $cats = Db::getInstance()->ExecuteS($this->q);
        foreach ($cats as $c) {
            $parent_id = $c['id_parent'];
            $node = array('id' => $c['id_category'],
                'name' => $c['name'],
                'url' => $common->genUrl(
                    array(
                    'id' => $c['id_category'],
                    'rewrite' => $c['name'],
                    ),
                    'category'
                ));
            $nodes[$c['id_category']] = $node;
            if ($c['is_root_category']) {
                $roots[]= $node;
            }

            if (!array_key_exists($parent_id, $children)) {
                $children[$parent_id] = array();
            }
            $children[$parent_id][]= $node;
        }

        foreach ($roots as $root) {
            $common->subtree($w->getWriter(), $root['id'], $cattext = array(), $nodes, $children, $this->write);
        }

        if ($this->write) {
            $w->end();
        }
        return $nodes;
    }
}
