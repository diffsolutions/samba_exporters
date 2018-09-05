#!/usr/bin/python3

"""
    Prestashop exporter for samba.ai
    (C) 2018 Martin Tomasek
    (C) 2018 DiffSolutions s.r.o.
    Licensed under CC BY-SA 4.0

    * exporter exports prestashop data into configured directory.
    * configuration is loaded from config.py
    * first version, loads whole table into memory (sorry)
"""

from model import Customer, Order, Product, ProductLang, GenderLang
from model import Category, CategoryLang, OrderDetail, SpecificPrice
from model import Tax, TaxRule, Image, SpecificPriceCondition
from model import SpecificPriceConditionGroup, Address, SpecificPriceRule
from model import Stock, ProductAttribute, ProductAttributeCombination
from model import ProductCategory, Attribute, AttributeGroupLang, AttributeLang
from config import SHOP_ID, LANG_ID, ORDER_CANCELLED, ORDER_FINISHED, PRICE_BUY
from config import CATEGORY_URL_TEMPLATE, PRODUCT_URL_TEMPLATE, SHOP_GROUP_ID
from config import COUNTRY_ID, IMAGE_URL_BASE, PS_SPECIFIC_PRICE_PRIORITY
from config import OUTPUT_DIRECTORY, IMAGE_URL_TYPE
from xml_writer import Feed
from lxml.etree import Element, SubElement
import collections
import functools
import itertools
import operator
import datetime
import peewee
import os.path
from base64 import b64encode

def dt_iso(dt):
    if dt:
        d = dt.isoformat()
        if len(d)>10:
            return d + 'Z'
        else:
            return d

def order_state(state):
    if state in ORDER_CANCELLED:
        return 'canceled'
    if state in ORDER_FINISHED:
        return 'finished'
    return 'created'

def parameter(p, name, val):
    if not val: #filter out zero and empty values
        return
    sp = SubElement(p, "PARAMETER")
    i = SubElement(sp, "NAME")
    i.text = str(name)
    i = SubElement(sp, "VALUE")
    i.text = str(val)


def iseq_with_mask(a,b,mask):
    """
        masked compare of two vectors
        mask selects ignored components
    """
    return all((ai == bi) or not mi for ai,bi,mi in zip(a,b,mask))

def load_specific_prices(dt):
    def add_fltr(dct, pair):
        (k,v) = pair
        if v and v!='0' and not (type(v)==float and v == -1.0):
            dct[k] = v
        return dct

    prices = []
    for sp in SpecificPrice.select()\
              .order_by(SpecificPrice.id_specific_price_rule):
        #print(sp.id_customer, sp.id_group, sp.id_country, sp.id_shop,
        #      sp.id_shop_group, sp.id_cart)
        if sp.id_customer != 0:
            continue
        if sp.id_group != 0:
            continue
        if sp.id_country != 0:
            continue
        if sp.id_shop not in {0, SHOP_ID}:
            continue
        if sp.id_shop_group not in {0, SHOP_GROUP_ID}:
            continue
        if sp.id_cart != 0:
            continue
        if sp.from_quantity > 1:
            continue
        if (sp.date_from and not (sp.date_from < dt)) or \
            (sp.date_to and not (dt < sp.date_to)):
            continue
        p = {}
        [add_fltr(p, v) for v in [
            ('id_shop', sp.id_shop),
            ('id_currency', sp.id_currency),
            ('id_country', sp.id_country),
            ('id_group', sp.id_group),
            ('id_customer', sp.id_customer),
            ('id_product', sp.id_product),
            ('id_product_attribute', sp.id_product_attribute),
            ('price', sp.price),
            ('reduction', sp.reduction),
            ('reduction_tax', sp.reduction_tax),
            ('reduction_type', sp.reduction_type),
            ]]

        prices.append(p)
    return prices

def load_taxes():
    taxes = {} #indexed by id_tax_group
    for tax in Tax.select(Tax.rate, TaxRule.id_tax_rules_group)\
               .join(TaxRule, on = (Tax.id_tax == TaxRule.id_tax)) \
               .where(TaxRule.id_country == COUNTRY_ID).dicts():
        taxes[tax['id_tax_rules_group']] = tax['rate'] /100 #rate is in percents * 100
    return taxes

def load_conditions():
    conds = collections.defaultdict(list)
    for cond in SpecificPriceCondition.select(SpecificPriceCondition, SpecificPriceConditionGroup).join(SpecificPriceConditionGroup,
        on=(SpecificPriceCondition.id_specific_price_rule_condition_group ==
            SpecificPriceConditionGroup.id_specific_price_rule_condition_group)).dicts():
        rule = cond['id_specific_price_rule']
        typ = cond['typ']
        val = cond['value']
        conds[rule].append((typ, val))
    return conds

def load_specific_price_rules(dt):
    def add_fltr(dct, pair):
        (k,v) = pair
        if v and v!='0' and not (type(v)==float and v == -1.0):
            dct[k] = v
        return dct
    rules = []
    for rule in SpecificPriceRule.select().join(SpecificPriceConditionGroup)\
                .where(SpecificPriceRule.from_quantity <= 1):

        if (rule.date_from and not (rule.date_from < dt)) or \
            (rule.date_to and not (dt < rule.date_to)):
            continue
        if rule.id_country != 0:
            continue
        if rule.id_shop not in {0, SHOP_ID}:
            continue
        r = {}
        [add_fltr(r, v) for v in [
            ('name', rule.name),
            ('id_shop', rule.id_shop),
            ('id_currency', rule.id_currency),
            ('id_country', rule.id_country),
            ('id_group', rule.id_group),
            ('price', rule.price),
            ('reduction', rule.reduction),
            ('reduction_tax', rule.reduction_tax),
            ('reduction_type', rule.reduction_type),
            ]]
        cgs = list(iter(rule.conditiongroups))
        cg_list = []
        for cg in cgs:
            cond_dict = {}
            for cond in cg.conditions:
                cond_dict[cond.typ] = cond.value
            if cond_dict: #empty conditions list means 'true'
                cg_list.append(cond_dict)
        add_fltr(r, ('condition_groups', cg_list))
        rules.append(r)
    return rules

def load_product_categories():
    prod_cat = collections.defaultdict(list)
    cat_prod = collections.defaultdict(list)
    for pc in ProductCategory.select():
        prod = pc.id_product
        cat = pc.id_category
        prod_cat[prod].append(cat)
        cat_prod[cat].append(prod)
    return (prod_cat, cat_prod)

def load_attributes():
    id_val = {}
    id_name = {}
    for attr in Attribute.select(Attribute, AttributeLang, AttributeGroupLang)\
            .join(AttributeLang, on=Attribute.id_attribute ==
                    AttributeLang.id_attribute)\
            .join(AttributeGroupLang, on=Attribute.id_attribute_group ==
                    AttributeGroupLang.id_attribute_group)\
            .where(AttributeLang.id_lang == LANG_ID &
                    AttributeGroupLang.id_lang == LANG_ID).dicts():
        attr_id = attr['id_attribute']
        grp = attr['public_name']
        val = attr['name']
        id_val[attr_id] = val
        id_name[attr_id] = grp
    return (id_name, id_val)


def specific_price(product, dt, prices, taxes, rules, prod_cat, cat_prod,
        add_price = 0):
    def match_attr(a, b, attr):
        a1 = a.get(attr)
        b1 = b.get(attr)
        #print("match_attr {}: {}, {}".format(attr,a1, b1))
        return b1==0 or b1==None or a1==b1

    def calc_tax(price, tax):
        price = price * (1 + tax)
        return price

    def sale(p, sp, tax, add_price):
        price = p['price'] + add_price
        if sp['reduction_type'] == 'percentage':
            price2 = price * (1 - sp['reduction'])
            #print("reducing price {} to {}, price reduction {} product id {}"\
            #      .format(price, price2, sp['reduction'], p['id_product']))
            if price2 > price:
                raise ValueError("bad percentage for SpecificPrice "
                                 "{}".format(sp))
            return calc_tax(price2, tax)
        elif sp['reduction_type'] == 'amount':
            if sp.get('reduction_tax'):
                return calc_tax(price, tax) - sp['reduction'] #reduction with tax
            else:
                return calc_tax(price - sp['reduction'], tax) #reduction without tax
        raise NotImplemented("reduction type {} is not "
                             "implemented/supported".format(sp['reduction_type']))

    def match_rule(a,b):
        all_attrs = {'id_cart', 'id_product', 'id_currency', 'id_country',
                    'id_group', 'id_customer', 'id_product_attribute'}
        matches = all(match_attr(a,b,attr) for attr in all_attrs)
        cgroup = b.get('condition_group')
        if matches and cgroup:
            #TODO:matching cgroup
            matches = False
        #if matches:
        #    print("MATCH: rule {} matched for product {}" \
        #          .format(b,a.get('id_product')))
        return matches

    id_specific_price_rule = 0
    reduction_tax = 1
    price = product['price'] + add_price
    price_before = price
    tax = taxes.get(product['id_tax_rules_group'])
    if tax is None:
        raise ValueError("missing tax info for product id "
                         "{}".format(product['id_product']))
    matches = [price for price in prices #+rules
                if match_rule(product, price)]
    #attrs = PS_SPECIFIC_PRICE_PRIORITY.split(";")
    #attr_getter = lambda x:[x.get(a) for a in attrs]
    #attrs = sorted(attrs, key = attr_getter)
    if matches:
        price = sale(product, matches[0], tax, add_price) #calculate sale + tax
    else:
        price = calc_tax(price, tax) #calculate tax by default
    price2 = calc_tax(price_before, tax)
    #print("tax: {} resulting price: {}".format(tax, price))
    return (price, price2)

def img_url(img_id, link_rewrite):
    if IMAGE_URL_TYPE == 'dirs':
        dirs = list(str(img_id))
        return IMAGE_URL_BASE + "/".join(dirs) + '/{}.jpg'.format(img_id)
    else:
        return os.path.join(IMAGE_URL_BASE, "{}-large_default".format(img_id), link_rewrite + '.jpg')

customer_email = {}
b64 = lambda s: b64encode(s.encode('UTF-8'))
with Feed('customer', os.path.join(OUTPUT_DIRECTORY, 'customers.xml'), 'CUSTOMERS') as f:
    for customer in Customer.select(Customer, GenderLang.name,
                                    Address.postcode, Address.phone,
                                    Address.phone_mobile,
                                    peewee.fn.min(Address.id_address).alias('min_id')).join(GenderLang) \
            .join(Address, on=(Customer.id_customer ==
                Address.id_customer)) \
            .where(GenderLang.id_lang == LANG_ID) \
            .group_by(Address.id_customer) \
            .dicts():
        el = Element("CUSTOMER")
        i = SubElement(el, "FIRST_NAME")
        i.text = customer['firstname']
        i = SubElement(el, "LAST_NAME")
        i.text = customer['lastname']
        i = SubElement(el, "CUSTOMER_ID")
        #i.text = str(customer['id_customer'])
        i.text = b64(str(customer['email']))
        i = SubElement(el, "EMAIL")
        i.text = customer['email']
        phone = customer.get('phone_mobile') or customer.get('phone')
        if phone:
            i = SubElement(el, "PHONE")
            i.text = phone
        zip_code = customer.get('postcode')
        if zip_code:
            i = SubElement(el, "ZIP_CODE")
            i.text = zip_code
        i = SubElement(el, "NEWSLETTER_FREQUENCY")
        i.text = "every day" if customer['newsletter'] else "never"
        i = SubElement(el, "REGISTRATION")
        i.text  = dt_iso(customer['date_add'])
        par = SubElement(el, "PARAMETERS")
        parameter(par, "Birthday", dt_iso(customer['birthday']))
        parameter(par, "Optin", customer['optin'])
        parameter(par, "Deleted", customer['deleted'])
        parameter(par, "Gender", customer['name'])
        f.write(el)
        customer_email[customer['id_customer']] = customer['email']


with Feed('category', os.path.join(OUTPUT_DIRECTORY, 'categories.xml'), 'CATEGORIES') as f:
    root_id = None
    nodes = {}
    subcats = collections.defaultdict(list)
    global cat_names
    cat_names = {}

    def subtree(node_id, cattext = ""):
        global cat_names
        node = nodes[node_id]
        subnodes = subcats[node_id]
        title = node.findtext('TITLE', default = 'None')
        if cattext:
            name = cattext + ' | ' + title
        else:
            name = title
        cat_names[node_id] = name
        for subnode in subnodes:
            node.append(nodes[subnode])
            subtree(subnode, name)

    custom_order = peewee.Case(CategoryLang.id_lang, [
            (LANG_ID, 100),
            (0, 99),
            ], -1000)
    for category in Category.select(Category, CategoryLang.name,
            peewee.fn.max(custom_order)).join(CategoryLang, on = (Category.id_category ==
                                            CategoryLang.id_category)) \
            .where(CategoryLang.id_lang == LANG_ID and \
            CategoryLang.id_shop == SHOP_ID).group_by(Category.id_category).dicts():
        #print(category)
        node = Element("ITEM")
        node_id = category['id_category']
        i = SubElement(node, "URL")
        i.text = CATEGORY_URL_TEMPLATE.format(id_category =
                                              category['id_category'])
        i = SubElement(node, "TITLE")
        i.text = category['name']
        subcats[category['id_parent']].append(node_id)
        nodes[node_id] = node
        if category['is_root_category']:
            if root_id is None:
                root_id = category['id_category']
            else:
                #print("More than one root for category tree, ignoring other.")
                raise ValueError("More than one root for category tree")
    if not root_id:
        raise ValueError("Missing category tree root")
    for node in subcats[root_id]:
        subtree(node)
        f.write(nodes[node])
    #print(cat_names)


with Feed('product', os.path.join(OUTPUT_DIRECTORY, 'products.xml'), 'PRODUCTS') as f:
    dt_now = datetime.datetime.now()
    specific_prices = load_specific_prices(dt_now)
    taxes = load_taxes()
    rules = load_specific_price_rules(dt_now)
    prod_cat, cat_prod = load_product_categories()
    attr_name, attr_val = load_attributes()
    #print("loaded specific {} price rules + {} catalog price "
    #      "rules ".format(len(specific_prices), len(rules)))
    for product in Product.select(Product,
                                  peewee.fn.min(Image.id_image).alias('image'),
                                  ProductLang,
                                  Stock.quantity.alias('stock'))\
                   .join(ProductLang).join(Image, on=(Product.id_product ==
                                                      Image.id_product),
                                           attr='image')\
                   .join(Stock, on=(Stock.id_product ==
                                    Product.id_product))\
                   .where((ProductLang.id_lang == LANG_ID) &
                          (ProductLang.id_shop ==
                           SHOP_ID) & (Stock.id_shop == SHOP_ID) &
                           (Stock.id_product_attribute == 0))\
                   .group_by(Product.id_product).dicts():
        el = Element("PRODUCT")
        product_id = product['id_product']
        i = SubElement(el, "PRODUCT_ID")
        i.text = str("{}-0".format(product_id))
        i = SubElement(el, "TITLE")
        i.text = product['name']
        i = SubElement(el, "DESCRIPTION")
        i.text = product['description']
        i = SubElement(el, "URL")
        i.text = PRODUCT_URL_TEMPLATE.format(id_product = product_id)
        i = SubElement(el, "IMAGE")
        i.text = img_url(product['image'], product['link_rewrite'])
        i = SubElement(el, "CATEGORYTEXT")
        i.text = cat_names.get(product.get('id_category_default', 'None'), 'None')
        stock = product['stock']
        #stock = 1 #HACK, FIXME
        active = product['active']
        if not active:
            stock = 0
        if product['visibility'] == 'none':
            stock = 0
        if product['show_price'] <=0:
            stock = 0
        price, price_before = specific_price(product, dt_now, specific_prices,
                                             taxes, rules, prod_cat, cat_prod)
        wsp = product['wholesale_price']
        i = SubElement(el, "STOCK")
        i.text = str(stock)
        i = SubElement(el, "PRICE")
        i.text = str(price)
        if price != price_before:
            i = SubElement(el, "PRICE_BEFORE_DISCOUNT")
            i.text = str(price_before)
        if PRICE_BUY and wsp:
            i = SubElement(el, "PRICE_BUY")
            i.text = str(wsp)

        par = SubElement(el, "PARAMETERS")
        parameter(par, "width", product['width'])
        parameter(par, "height", product['height'])
        parameter(par, "depth", product['depth'])
        parameter(par, "weight", product['weight'])

        variants = ProductAttribute.select(ProductAttribute,
                    ProductAttributeCombination).join(
                            ProductAttributeCombination, on = (
                            ProductAttribute.id_product_attribute ==
                            ProductAttributeCombination.id_product_attribute))\
                            .where(ProductAttribute.id_product
                            == product_id)\
                            .order_by(ProductAttributeCombination.id_product_attribute)
        #print(variants.sql())
        variants = variants.dicts()
        variants = list(variants)
        default_ixs = [ix for ix, v in enumerate(variants) if v.get('default_on')]
        if default_ixs:
            #move default variant to the first place
            default_ix = default_ixs[0]
            (variants[0], variants[default_ix]) = (variants[default_ix],
                    variants[0])
        else:
            default_ix = 0
        #variants = list(variants)
        #print(variants)
        for id_product_attr, g in itertools.groupby(variants, key =
                operator.itemgetter('id_product_attribute')):
            group = list(g)
            variant_id = "{}-{}".format(product_id,
#                    ":".join(sorted([str(it['id_attribute']) for it in group])))
                     id_product_attr)
            v = SubElement(el, "VARIANT")
            i = SubElement(v, "PRODUCT_ID")
            i.text = variant_id
            add_price = group[0].get('price')
            if add_price:
                i = SubElement(v, "PRICE")
                price, price_before = specific_price(product, dt_now, specific_prices,
                                             taxes, rules, prod_cat, cat_prod,
                                             add_price = add_price)
                i.text = str(price)
                i = SubElement(v, "PRICE_BEFORE_DISCOUNT")
                i.text = str(price_before)
            parameters = [(attr_name[it['id_attribute']],
                    attr_val[it['id_attribute']]) for it in group]
            if parameters:
                par = SubElement(v, "PARAMETERS")
                parameters = [(attr_name[it['id_attribute']],
                        attr_val[it['id_attribute']]) for it in group]
                for pn, pv in parameters:
                    parameter(par, pn, pv)

        f.write(el)


with Feed('order', os.path.join(OUTPUT_DIRECTORY, 'orders.xml'), 'ORDERS') as f:
    for order in Order.select() \
                 .join(Address, on=(Order.id_address_delivery ==
                                    Address.id_address)):
        el = Element("ORDER")
        i = SubElement(el, "ORDER_ID")
        i.text = str(order.id_order)
        i = SubElement(el, "CUSTOMER_ID")
        #i.text = str(order.id_customer)
        i.text = b64(str(customer_email.get(order.id_customer, "")))
        i = SubElement(el, "CREATED_ON")
        i.text = dt_iso(order.date_add)
        i = SubElement(el, "FINISHED_ON")
        i.text = dt_iso(order.delivery_date)
        i = SubElement(el, "STATUS")
        i.text = order_state(order.current_state)
        i = SubElement(el, "ZIP_CODE")
        i.text = order.id_address_delivery.postcode
        it = SubElement(el, "ITEMS")
        for item in order.items:
            i2 = SubElement(it, "ITEM")
            i = SubElement(i2, "PRODUCT_ID")
            i.text = "{}-{}".format(item.product_id,
                item.product_attribute_id)
            i = SubElement(i2, "PRICE")
            i.text = str(item.total_price_tax_incl)
            i = SubElement(i2, "AMOUNT")
            i.text = str(int(item.product_quantity))

        f.write(el)


