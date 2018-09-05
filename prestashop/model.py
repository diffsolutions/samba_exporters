import sys
import config
from config import *
from peewee import *

db = MySQLDatabase(DB_NAME, user = DB_USER, password = DB_PASSWORD,
                  host = DB_HOST, port = DB_PORT)

#we are using the db readonly so we don't have to fill in all the fiels

class Language(Model):
    id_lang = IntegerField(primary_key = True)
    iso_code = CharField()
    name = CharField()
    class Meta:
        db_table = PREFIX + '_lang'
        database = db


class Config(Model):
    id_configuration = IntegerField(primary_key = True)
    name = CharField()
    value = CharField()
    class Meta:
        db_table = PREFIX + '_configuration'
        database = db

class GenderLang(Model):
    id_gender = IntegerField(primary_key = True)
    id_lang = IntegerField()
    name = CharField()
    class Meta:
        db_table = PREFIX + '_gender_lang'
        database = db

class Customer(Model):
    id_customer = AutoField(primary_key = True)
    id_shop = IntegerField()
    gender = ForeignKeyField(GenderLang, column_name = 'id_gender', object_id_name =
                             'id_gender')
    id_lang = IntegerField()
    company = CharField()
    siret = CharField() #bussiness identification number
    firstname = CharField()
    lastname = CharField()
    passwd = CharField()
    birthday = DateTimeField()
    newsletter = IntegerField()
    optin = IntegerField()
    website = CharField()
    active = IntegerField()
    is_guest = IntegerField()
    deleted = IntegerField()
    date_add = DateTimeField()
    date_upd = DateTimeField()
    email = CharField()

    class Meta:
        db_table = PREFIX + '_customer'
        database = db

class Address(Model):
    id_address = IntegerField(primary_key = True)
    id_customer = IntegerField()
    postcode = CharField()
    phone = CharField()
    phone_mobile = CharField()

    class Meta:
        db_table = PREFIX + '_address'
        database = db

class Order(Model):
    id_order = AutoField(primary_key = True)
    id_shop = IntegerField()
    id_customer = IntegerField()
    id_cart = IntegerField()
    id_currency = IntegerField()
    #id_address_delivery = IntegerField()
    id_address_delivery = ForeignKeyField(Address, column_name =
                                          'id_address_delivery')

    current_state = IntegerField()
    date_add = DateTimeField()
    delivery_date = DateTimeField()
    date_add = DateTimeField()
    current_state = IntegerField()

    class Meta:
        db_table = PREFIX + '_orders'
        database = db

class OrderDetail(Model):
    id_order_detail = IntegerField(primary_key = True)
    id_order = ForeignKeyField(Order, column_name = 'id_order', object_id_name =
                          'id_order2', backref = 'items')
    id_shop = IntegerField()
    product_id = IntegerField()
    product_attribute_id = IntegerField()
    total_price_tax_incl = FloatField()
    unit_price_tax_incl = FloatField()
    product_quantity = FloatField()

    class Meta:
        db_table = PREFIX + '_order_detail'
        database = db



class Product(Model):
    id_product = AutoField(primary_key = True)
    #id_shop = IntegerField()
    id_shop_default = IntegerField()
    id_category_default = IntegerField()
    id_tax_rules_group = IntegerField()
    on_sale = IntegerField()
    quantity = IntegerField()
    price = FloatField()
    wholesale_price = FloatField()
    reference = CharField()
    active = IntegerField()
    show_price = IntegerField()
    visibility = CharField()
    location = CharField()
    width = FloatField()
    depth = FloatField()
    height = FloatField()
    weight = FloatField()

    class Meta:
        db_table = PREFIX + '_product'
        database = db


class ProductLang(Model):
    product = ForeignKeyField(Product, column_name = 'id_product', backref =
                                 'description', object_id_name = 'id_product',
                             primary_key = True)
    id_lang = IntegerField()
    id_shop = IntegerField()
    name = CharField()
    description = CharField()
    description_short = CharField()
    link_rewrite = CharField()
    class Meta:
        db_table = PREFIX + '_product_lang'
        database = db

class ProductAttribute(Model):
    id_product = IntegerField()
    id_product_attribute = IntegerField(primary_key = True)
    price = FloatField()
    default_on = IntegerField()

    class Meta:
        db_table = PREFIX + '_product_attribute'
        database = db

class ProductAttributeCombination(Model):
    id_attribute = IntegerField()
    id_product_attribute = IntegerField()

    class Meta:
        db_table = PREFIX + '_product_attribute_combination'
        database = db
        primary_key = False

class Attribute(Model):
    id_attribute = IntegerField(primary_key = True)
    id_attribute_group = IntegerField()

    class Meta:
        db_table = PREFIX + '_attribute'
        database = db


class AttributeLang(Model):
    id_attribute = IntegerField()
    id_lang = IntegerField()
    name = CharField()

    class Meta:
        db_table = PREFIX + '_attribute_lang'
        database = db
        primary_key = False

class AttributeGroupLang(Model):
    id_attribute_group = IntegerField()
    id_lang = IntegerField()
    public_name = CharField()

    class Meta:
        db_table = PREFIX + '_attribute_group_lang'
        database = db
        primary_key = False


class Stock(Model):
    id_stock_available = IntegerField(primary_key = True)
    id_product = IntegerField()
    id_shop = IntegerField()
    id_product_attribute = IntegerField()
    quantity = IntegerField()
    class Meta:
        db_table = PREFIX + '_stock_available'
        database = db

class SpecificPrice(Model):
    id_specific_price = IntegerField(primary_key = True)
    id_specific_price_rule = IntegerField()
    id_cart = IntegerField()
    id_product = IntegerField()
    id_shop = IntegerField()
    id_shop_group = IntegerField()
    id_currency = IntegerField()
    id_country = IntegerField()
    id_group = IntegerField()
    id_customer = IntegerField()
    id_product_attribute = IntegerField()
    price = FloatField()
    from_quantity = IntegerField()
    reduction = FloatField()
    reduction_tax = FloatField()
    reduction_type = CharField() # 'amount' or 'percentage'
    date_from = DateTimeField(column_name = 'from')
    date_to = DateTimeField(column_name = 'to')
    class Meta:
        db_table = PREFIX + '_specific_price'
        database = db

class SpecificPriceRule(Model):
    id_specific_price_rule = IntegerField(primary_key = True)
    id_shop = IntegerField()
    id_currency = IntegerField()
    id_country = IntegerField()
    id_group = IntegerField()
    price = FloatField()
    name = CharField()
    from_quantity = IntegerField()
    reduction = FloatField()
    reduction_tax = FloatField()
    reduction_type = CharField() # 'amount' or 'percentage'
    date_from = DateTimeField(column_name = 'from')
    date_to = DateTimeField(column_name = 'to')
    class Meta:
        db_table = PREFIX + '_specific_price_rule'
        database = db

class SpecificPriceConditionGroup(Model):
    id_specific_price_rule_condition_group = IntegerField(primary_key = True)
    id_specific_price_rule = ForeignKeyField(SpecificPriceRule,
                                        'id_specific_price_rule',
                                        backref = 'conditiongroups',
                                        column_name = 'id_specific_price_rule',
                                        object_id_name =
                                             'specific_price_rule')
    class Meta:
        db_table = PREFIX + '_specific_price_rule_condition_group'
        database = db

class SpecificPriceCondition(Model):
    id_specific_price_rule_condition = IntegerField(primary_key = True)
    id_specific_price_rule_condition_group = \
        ForeignKeyField(SpecificPriceConditionGroup,
            'id_specific_price_rule_condition_group',
            backref = "conditions",
            column_name = "id_specific_price_rule_condition_group",
            object_id_name = "specific_price_rule_condition_group")
    typ = CharField(column_name = 'type')
    value = CharField()
    class Meta:
        db_table = PREFIX + '_specific_price_rule_condition'
        database = db

class Category(Model):
    id_category = IntegerField(primary_key = True)
    id_parent = IntegerField()
    id_shop_default = IntegerField()
    is_root_category = IntegerField()
    class Meta:
        db_table = PREFIX + '_category'
        database = db

class CategoryLang(Model):
    id_category = IntegerField(primary_key = True)
    id_shop = IntegerField()
    id_lang = IntegerField()
    name = CharField()
    link_rewrite = CharField()
    description = CharField()
    class Meta:
        db_table = PREFIX + '_category_lang'
        database = db

class ProductCategory(Model):
    id_category = IntegerField()
    id_product = IntegerField()

    class Meta:
        db_table = PREFIX + '_category_product'
        database = db
        primary_key = False

class Tax(Model):
    id_tax = IntegerField(primary_key = True)
    rate = FloatField()
    class Meta:
        db_table = PREFIX + '_tax'
        database = db

class TaxRule(Model):
    id_tax_rule = IntegerField(primary_key = True)
    id_tax_rules_group = IntegerField()
    id_country = IntegerField()
    id_tax = IntegerField()
    class Meta:
        db_table = PREFIX + '_tax_rule'
        database = db

class Image(Model):
    id_image = IntegerField(primary_key = True)
    id_product = IntegerField()
    class Meta:
        db_table = PREFIX + '_image'
        database = db

#get language id from db
LANG_ID = config.LANG_ID = int(Language.select().where(Language.iso_code ==
                                                   LANG).get().id_lang)
#get prestashop version from DB
PS_VERSION = config.PS_VERSION = Config.select().where(Config.name ==
                                              'PS_VERSION_DB').get().value

if not config.SHOP_ID:
    SHOP_ID = config.SHOP_ID = int(Config.select().where(Config.name ==
                                              'PS_SHOP_DEFAULT').get().value)
if not config.COUNTRY_ID:
    COUNTRY_ID = config.COUNTRY_ID = int(Config.select().where(Config.name ==
                                              'PS_COUNTRY_DEFAULT').get().value)

PS_SPECIFIC_PRICE_PRIORITY = config.PS_SPECIFIC_PRICE_PRIORITY = Config.select().where(Config.name ==
                                              'PS_SPECIFIC_PRICE_PRIORITIES').get().value

#print(PS_SPECIFIC_PRICE_PRIORITY)

PS_SPECIFIC_PRICE = config.PS_SPECIFIC_PRICE = bool(int(Config.select().where(Config.name ==
                                              'PS_SPECIFIC_PRICE_FEATURE_ACTIVE').get().value))

if config.SPECIFIC_PRICE and not PS_SPECIFIC_PRICE:
    config.SPECIFIC_PRICE = False
    print("PS_SPECIFIC_PRICE is not enabled in PS config, disabling in"
          " exporter", file = sys.stderr)

