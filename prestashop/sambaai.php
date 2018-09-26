<?php
/**
*  @author    Martin Tomasek
*  @copyright DiffSolutions, s.r.o.
*  @license   https://creativecommons.org/licenses/by-sa/4.0/ CC BY-SA 4.0
*/

if (!defined('_PS_VERSION_')) {
    exit;
}


function generateRandomString($length = 10)
{
    $x='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    return Tools::substr(str_shuffle(str_repeat($x, ceil($length/Tools::strlen($x)))), 1, $length);
}

class SambaAi extends Module
{
    public function __construct()
    {
        /*
            throw new Exception('Constructor start');
         */
        $this->name = 'sambaai';
        $this->tab = 'emailing';
        $this->version = '1.0.0';
        $this->author = 'Samba.ai';
        $this->need_instance = 0;
        $this->ps_versions_compliancy = array('min' => '1.7', 'max' => '1.7');
        $this->bootstrap = true;
        parent::__construct();
        $this->displayName = $this->l('Samba.ai connector');
        $this->description = $this->l('Samba.ai online marketing a.i. automation connector.');
 
        $this->confirmUninstall = $this->l('Are you sure you want to uninstall?');
 
        #Configuration::get('SAMBA_TP'))
    }

    public function install()
    {
        if (!parent::install()) {
            return false;
        }
        $this->registerHook('displayBeforeBodyClosingTag');
        $this->registerHook('displayHome');

        if (Shop::isFeatureActive()) {
            Shop::setContext(Shop::CONTEXT_ALL);
        }

        $key=generateRandomString(20);

        if (empty(Configuration::getValue('SAMBA_KEY', $key))) {
            Configuration::updateValue('SAMBA_KEY', $key);
        }
 
        return true;
    }

    public function uninstall()
    {
        if (!parent::uninstall()) {
            return false;
        }

        if (!Configuration::deleteByName('SAMBA_TP')) {
            #!Configuration::deleteByName('SAMBA_WIDGET')) {
            return false;
        }
   
        return true;
    }

    public function hookdisplayBeforeBodyClosingTag()
    {
        if (array_key_exists('HTTP_DNT', $_SERVER)) {
            $dnt = $_SERVER['HTTP_DNT'];
            if ($dnt == '1') {
                return '<!-- SAMBA.AI tracking code not active due to user request -->';
            } #GDPR
        }
        $tp = Configuration::get('SAMBA_TP');
        if (!$tp) {
            return '<!-- SAMBA.AI tracking code will go here - please set your trackpoint number -->';
        }
        $id = (int)$this->context->customer->id;
        $this->context->smarty->assign(
            array( 'trackpoint'  => $tp,
                   'customer_id' => $id)
        );
        return $this->display(__FILE__, 'views/templates/front/tracker.tpl');
    }

    public function hookHome()
    {
        $widget = Configuration::get('SAMBA_WIDGET');
        if (!$widget) {
            return '<!-- SAMBA.AI recommeder code will go here if enabled.-->';
        }
        return $this->display(__FILE__, 'views/templates/front/recommender.tpl');
    }


    public function getContent()
    {
        $output = null;
 
        if (Tools::isSubmit('submit'.$this->name)) {
            $tp = Tools::getValue('SAMBA_TP');
            if (!$tp) {
                $output .= $this->displayError($this->l('Invalid Configuration value'));
            } else {
                Configuration::updateValue('SAMBA_TP', $tp);
                #$widget = (int) (Tools::getValue('SAMBA_WIDGET'));
                #Configuration::updateValue('SAMBA_WIDGET', $widget);
                $shop = (int) (Tools::getValue('SAMBA_SHOP'));
                Configuration::updateValue('SAMBA_SHOP', $shop);
                $lang = (int) (Tools::getValue('SAMBA_LANG'));
                Configuration::updateValue('SAMBA_LANG', $lang);
                #$key = (Tools::getValue('SAMBA_KEY'));
                #Configuration::updateValue('SAMBA_KEY', $key);


                $output .= $this->displayConfirmation($this->l('Configuration updated'));
            }
        }
        return $output.$this->displayForm();
    }

    protected static function genFeedUri($shopuri, $key, $feedname)
    {
        return $shopuri."modules/sambaai/feed2.php?key=".
        $key."&feed=".$feedname;
    }

    public function displayForm()
    {
        $output = null;

        // Get default language
        $default_lang = (int)Configuration::get('PS_LANG_DEFAULT');

        $shops_options = array();
        foreach ($this->shops() as $s) {
            $shops_options[] = array('value'=> $s['id'], 'text' => $s['name']);
        }

        $lang_options = array();
        foreach (Language::getLanguages(true) as $l) { #get all active languages
            $lang_options[] = array('value'=> $l['id_lang'], 'text' => $l['name']);
        }


        // Init Fields form array
        $fields_form = array();
        $fields_form[0]['form'] = array(
        'legend' => array(
            'title' => $this->l('Settings'),
        ),
        'input' => array(
            array(
                'type' => 'text',
                'label' => $this->l('Trackpoint'),
                'name' => 'SAMBA_TP',
                'desc' => $this->l('Trackpoint from samba.ai.'),
                'size' => 20,
                'required' => true
            ),
        /*
        array(


        'type' => 'select',
        'name' => 'SAMBA_WIDGET',
        'label' => $this->l('Recommeder widget'),
        'options' => array(
            'query' => array(
                array(
                    'value' => 0,
                    'text' => $this->l('Disabled'),
                ),
                array(
                    'value' => '1',
                    'text' => $this->l('Enabled'),
                ),
            ),
            'id' => 'value',
            'name' => 'text'
        )
        ),*/
        array(

        'type' => 'select',
        'name' => 'SAMBA_SHOP',
        'label' => $this->l('Choose shop for exports: '),
        'desc' => $this->l('Which shop export to samba.ai.'),
        'options' => array(
            'query' => $shops_options,
            'id' => 'value',
            'name' => 'text'
        )
        ),
        array(


        'type' => 'select',
        'name' => 'SAMBA_LANG',
        'label' => $this->l('Choose language for exports: '),
        'desc' => $this->l('Language for emails and recommendations. All emails will be in this language.'),
        'options' => array(
            'query' => $lang_options,
            'id' => 'value',
            'name' => 'text'
        )
        ),
        /*
        array(
                'type' => 'text',
                'label' => $this->l('feed access key'),
                'name' => 'SAMBA_KEY',
                'size' => 20,
                'required' => true
        ),
        */
        array(
                'type' => 'textarea',
                'label' => $this->l('Samba feed URLs'),
                'name' => 'feeds',
                'lang' => false,
                'autoload_rte' => false,
                'hint' => 'Copy these to samba.',
                'cols' => 50,
                'rows' => 4
        ),
        ),
        'submit' => array(
            'title' => $this->l('Save'),
            'class' => 'btn btn-default pull-right'
        )
        );
        $helper = new HelperForm();
        // Module, token and currentIndex
        $helper->module = $this;
        $helper->name_controller = $this->name;
        $helper->token = Tools::getAdminTokenLite('AdminModules');
        $helper->currentIndex = AdminController::$currentIndex.'&configure='.$this->name;
        // Language
        $helper->default_form_language = $default_lang;
        $helper->allow_employee_form_lang = $default_lang;
        // Title and toolbar
        $helper->title = $this->displayName;
        $helper->show_toolbar = true;        // false -> remove toolbar
        $helper->toolbar_scroll = true;      // yes - > Toolbar is always visible on the top of the screen.
        $helper->submit_action = 'submit'.$this->name;
        $helper->toolbar_btn = array(
        'save' =>
        array(
            'desc' => $this->l('Save'),
            'href' => AdminController::$currentIndex.'&configure='.$this->name.'&save'.$this->name.
            '&token='.Tools::getAdminTokenLite('AdminModules'),
        ),
        'back' => array(
            'href' => AdminController::$currentIndex.'&token='.Tools::getAdminTokenLite('AdminModules'),
            'desc' => $this->l('Back to list')
        )
        );
        // Load current value
        $helper->fields_value['SAMBA_TP'] = Configuration::get('SAMBA_TP');
        #$helper->fields_value['SAMBA_WIDGET'] = Configuration::get('SAMBA_WIDGET');
        $helper->fields_value['SAMBA_SHOP'] = Configuration::get('SAMBA_SHOP');
        $helper->fields_value['SAMBA_LANG'] = Configuration::get('SAMBA_LANG') or $default_lang;
        #$helper->fields_value['SAMBA_KEY'] = Configuration::get('SAMBA_KEY');
        $SAMBA_KEY=Configuration::get('SAMBA_KEY');
        $SHOP_URL = 'https://'.Configuration::get('PS_SHOP_DOMAIN_SSL').'/';
        $helper->fields_value['feeds'] = $this->genFeedUri($SHOP_URL, $SAMBA_KEY, 'products')."\n".
        $this->genFeedUri($SHOP_URL, $SAMBA_KEY, 'categories')."\n".
        $this->genFeedUri($SHOP_URL, $SAMBA_KEY, 'orders')."\n".
        $this->genFeedUri($SHOP_URL, $SAMBA_KEY, 'customers')."\n";

        $this->context->smarty->assign(array(
            'dir' => $this->_path,
        ));
        $output = $output.$this->context->smarty->fetch($this->local_path.'views/templates/admin/config.tpl');

        return $output.$helper->generateForm($fields_form);
    }

    public function shops()
    {
        $l = array();
        foreach (Shop::getShops() as $s) {
            $l[] = array( 'id' => $s['id_shop'], 'name' => $s['name'] );
        }
        return $l;
    }
}
