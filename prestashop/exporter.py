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
from model import SpecificPriceConditionGroup, Address
from config import SHOP_ID, LANG_ID, ORDER_CANCELLED, ORDER_FINISHED, PRICE_BUY
from config import CATEGORY_URL_TEMPLATE, PRODUCT_URL_TEMPLATE, SHOP_GROUP_ID
from config import COUNTRY_ID, IMAGE_URL_BASE
from xml_writer import Feed
from lxml.etree import Element, SubElement
import collections
import datetime
import peewee

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

def load_specific_prices():
    prices = []
    for sp in SpecificPrice.select():
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
        prices.append(sp)
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


def specific_price(product, dt, prices, taxes, conds):
    def match_attr(a, b, attr):
        #a1 = getattr(a, attr)
        a1 = a.get(attr)
        b1 = getattr(b, attr)
        #print("match_attr {}, {} for product {}".format(a1, b1, product))
        return b1==0 or a1==b1
    def sale(p, sp):
        price = p['price']
        if sp.reduction_type == 'percentage':
            price2 = price * (1 - sp.reduction)
            print("reducing price {} to {}, price reduction {}".format(price,
                                                                       price2,
                                                                      sp.reduction))
            if price2 > price:
                raise ValueError("bad percentage for SpecificPrice "
                                 "{}".format(sp))
            return price2
        elif sp.reduction_type == 'amount':
            return price - sp.reduction
        raise NotImplemented("reduction type {} is not "
                             "implemented/supported".format(sp.reduction_type))
    id_specific_price_rule = 0
    reduction_tax = 1
    price = product['price']
    price_before = price
    for sp in prices:
        #print("product {} date_from {} date_to {}".format(product,
        #                                                  sp.date_from,
        #                                                  sp.date_to))
        if (sp.date_from and not (sp.date_from < dt)) or \
            (sp.date_to and not (dt < sp.date_to)):
            continue
        if match_attr(product, sp, 'id_product'):
            """
            TODO: catalog price rules for from_quantity >= 1
            spr = product.get('id_specific_price_rule')
            if spr:
                print("specific price rule id {} present.".format(spr))
                cs = conds.get(spr)
                if cs:
                    print("specific condition detected - skipping sale "
                          "calculation. {}".format(cs))
                    continue
            """
            price = sale(product, sp)
            break
    tax = taxes.get(product['id_tax_rules_group'])
    if tax is None:
        raise ValueError("missing tax info for product id "
                         "{}".format(product['id_product']))
    price = price * (1 + tax)
    price2 = price_before * (1 + tax)
    #print("tax: {} resulting price: {}".format(tax, price))
    return (price, price2)

def img_url(img_id):
    dirs = list(str(img_id))
    return IMAGE_URL_BASE + "/".join(dirs) + '/{}.jpg'.format(img_id)

with Feed('customer', 'out/customers.xml', 'CUSTOMERS') as f:
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
        i.text = str(customer['id_customer'])
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

with Feed('product', 'out/products.xml', 'PRODUCTS') as f:
    specific_prices = load_specific_prices()
    taxes = load_taxes()
    conditions = load_conditions()
    print("loaded specific {} price rules, containing {} conditioned price "
          "rules ".format(len(specific_prices), len(conditions)))
    dt_now = datetime.datetime.now()
    for product in Product.select(Product,
                                  peewee.fn.min(Image.id_image).alias('image'), ProductLang)\
                   .join(ProductLang).join(Image, on=(Product.id_product ==
                                                      Image.id_product),
                                           attr='image')\
                   .where((ProductLang.id_lang == LANG_ID) &
                          (ProductLang.id_shop ==
                           SHOP_ID)).group_by(Product.id_product).dicts():
        el = Element("PRODUCT")
        product_id = product['id_product']
        i = SubElement(el, "PRODUCT_ID")
        i.text = str(product_id)
        i = SubElement(el, "TITLE")
        i.text = product['name']
        i = SubElement(el, "DESCRIPTION")
        i.text = product['description']
        i = SubElement(el, "URL")
        i.text = PRODUCT_URL_TEMPLATE.format(id_product = product_id)
        i = SubElement(el, "IMAGE")
        i.text = img_url(product['image'])
        stock = product['quantity']
        active = product['active']
        if not active:
            stock = 0
        if product['visibility'] == 'none':
            stock = 0
        if product['show_price'] <=0:
            stock = 0
        price, price_before = specific_price(product, dt_now, specific_prices,
                                             taxes, conditions)
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
        f.write(el)

with Feed('order', 'out/orders.xml', 'ORDERS') as f:
    for order in Order.select() \
                 .join(Address, on=(Order.id_address_delivery ==
                                    Address.id_address)):
        el = Element("ORDER")
        i = SubElement(el, "ORDER_ID")
        i.text = str(order.id_order)
        i = SubElement(el, "CUSTOMER_ID")
        i.text = str(order.id_customer)
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
            i.text = str(item.product_id)
            i = SubElement(i2, "PRICE")
            i.text = str(item.total_price_tax_incl)
            i = SubElement(i2, "AMOUNT")
            i.text = str(int(item.product_quantity))

        f.write(el)

with Feed('category', 'out/categories.xml', 'CATEGORIES') as f:
    def subtree(node_id):
        node = nodes[node_id]
        subnodes = subcats[node_id]
        for subnode in subnodes:
            node.append(nodes[subnode])
            subtree(subnode)
    root_id = None
    nodes = {}
    subcats = collections.defaultdict(list)
    for category in Category.select(Category, CategoryLang.name).join(CategoryLang, on = (Category.id_category ==
                                            CategoryLang.id_category)) \
            .where(CategoryLang.id_lang == LANG_ID and \
            CategoryLang.id_shop == SHOP_ID).dicts():
        node = Element("ITEM")
        node_id = category['id_category']
        i = SubElement(node, "URL")
        i.text = CATEGORY_URL_TEMPLATE.format(id_category =
                                              category['id_category'])
        i = SubElement(node, "TITLE")
        i.text = category['name']
        i = SubElement(node, "ID")
        i.text = str(node_id)
        subcats[category['id_parent']].append(node_id)
        nodes[node_id] = node
        if category['is_root_category']:
            if root_id is None:
                root_id = category['id_category']
            else:
                raise ValueError("More than one root for category tree")
    if not root_id:
        raise ValueError("Missing category tree root")
    for node in subcats[root_id]:
        subtree(node)
        f.write(nodes[node])

