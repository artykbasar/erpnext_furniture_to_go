from __future__ import unicode_literals
import frappe, time, dateutil, math, csv
from six import StringIO
import erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_api as f2g
from frappe import _


user_details = frappe.get_doc('Furniture To Go Settings')
f2g_ins = f2g.F2G()
f2g_ins.login(user_details.user_name, user_details.get_password('password'))


def find_new_products():
    list_of_product = f2g_ins.product_link_extractor()
    new_product_links = []
    for each in list_of_product:
        response = frappe.db.get_list('Furniture To Go Products',
                                        filters={
                                            'supplier_url': each
                                        }
                                    )
        if not response:
            new_product_links.append(each)
        else:
            for name in response:
                item_code = name['name']
                frappe.enqueue('erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_methods.sync_product', link=each, name=item_code)

    if new_product_links:        
        import_products_list(new_product_links)
    else:
        print('There is no new products')

def product_group_finder():
    group_data = f2g_ins.fetch_category_links()
    group_data_list = group_data.keys()
    response = frappe.db.get_list('Furniture To Go Products',fields=['name', 'supplier_url'])
    for each in response:
        if each['supplier_url'] in group_data_list:
            name = each['name']
            item = frappe.get_doc('Furniture To Go Products', name)
            group = frappe.new_doc('Furniture To Go Product Group')
            group_names = group_data[each['supplier_url']]
            parent_group = group_names['parent']
            group_name = '{} - {}'.format(group_names['child'],parent_group)
            parent_check = frappe.db.get_list('Furniture To Go Product Group', filters={'f2g_group_name': parent_group})
            child_check = frappe.db.get_list('Furniture To Go Product Group', filters={'f2g_group_name': group_name})
            if not parent_check:
                group.f2g_group_name = parent_group
                group.is_group = 1
                group.insert(ignore_permissions=True)
            if not child_check:
                group.f2g_group_name = group_name
                group.parent_f2g_product_group = parent_group
                group.old_parent = parent_group
                group.is_group = 0
                group.insert(ignore_permissions=True)
            item.f2g_group = group_name
            item.save()
            print(name)

def product_range_finder():
    range_data = f2g_ins.fetch_category_links(True)
    range_data_list = range_data.keys()
    response = frappe.db.get_list('Furniture To Go Products',fields=['name', 'supplier_url'])
    for each in response:
        if each['supplier_url'] in range_data_list:
            name = each['name']
            item = frappe.get_doc('Furniture To Go Products', name)
            f2g_range = frappe.new_doc('Furniture To Go Range')
            range_names = range_data[each['supplier_url']]
            range_name = range_names['child']
            child_check = frappe.db.get_list('Furniture To Go Range', filters={'range_name': range_name})
            if not child_check:
                f2g_range.range_name = range_name
                f2g_range.insert(ignore_permissions=True)
            item.range_name = range_name
            item.save(ignore_permissions=True)
            print(name, range_name)
    
def import_products_list(product_links):
    for product_link in product_links:
        frappe.enqueue('erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_methods.import_product',product_link=product_link)

def import_product(product_link):
    product_details = f2g_ins.product_data_extractor(product_link)
    print(product_details)
    item = frappe.new_doc("Furniture To Go Products")
    sku_check = frappe.db.get_list('Furniture To Go Products',
                                        filters={
                                            'product_sku': product_details['sku']
                                        },
                                        fields=['product_sku'],
                                        as_list=True
                                    )
    if sku_check:
        return
    item.product_sku = product_details['sku']
    item.product_name = product_details['product_name']
    if product_details['stock']['next_delivery_date']:
        item.next_delivery = dateutil.parser.parse(product_details['stock']['next_delivery_date']).strftime("%Y-%m-%d")
    item.availability = product_details['stock']['stock_status']
    item.stock_level = product_details['stock']['qty']
    item.barcode = product_details['ean']
    if product_details['box']:
        box_keys = product_details["box"].keys()
        for box_key in box_keys:
            height, width, length, unit, weight, box_ean = ['', '', '', '', '', '']
            if product_details['box'][box_key].get('box_dimensions'):
                height = product_details['box'][box_key]['box_dimensions']['height']
                width = product_details['box'][box_key]['box_dimensions']['width']
                length = product_details['box'][box_key]['box_dimensions']['length']
                unit = product_details['box'][box_key]['box_dimensions']['unit']
            if product_details['box'][box_key].get('box_weight'):
                weight = product_details['box'][box_key]['box_weight']
            if product_details['box'][box_key].get('box_ean_code'):
                box_ean = product_details['box'][box_key]['box_ean_code']
            box_name = box_key.replace('box_','')
            item.append('box',
                        {'box_number': box_name,
                        'barcode': box_ean,
                        'height': height,
                        'width': width,
                        'depth': length,
                        'unit': unit,
                        'weight': weight})
    if product_details['product_bullet_points']:
        for bullet_point in product_details['product_bullet_points']:
            item.append('product_bullet_points',{'bullet_point': bullet_point})
    
    if product_details['product_file']:
        for product_file in product_details['product_file']:
            item.append('product_attachments',{'attachment_name': product_file['name'],
                                               'attachment_file': product_file['link']})
    images = product_details['product_images']
    if images:
        item.main_image = product_details['product_images'][0]
        for i in range(len(images)):
            if i > 0:
                item.append('product_images', {'image_name': images[i].rsplit('/', 1)[1],
                                               'image_file': images[i]})
    item.description = product_details['product_description']
    price = product_details['prices']
    hd_price = price['home_delivery']
    store_price = price['store_delivery']
    over_250 = price['order_over_250']
    over_500 = price['order_over_500']
    over_1000 = price['order_over_1000']
    over_2000 = price['order_over_2000']
    item.hd_price = hd_price
    item.store_delivery_price = store_price
    item.over_250 = over_250
    item.over_500 = over_500
    item.over_1000 = over_1000
    item.over_2000 = over_2000
    item.supplier_url = product_details['product_link']
    item.insert(ignore_permissions=True)

def no_change(field_name):
    pass
    # print('In {} feild, No chage has been detected'.format(field_name))

def sync_product(link, name):
    product_details = f2g_ins.product_data_extractor(link)
    item = frappe.get_doc('Furniture To Go Products', name)
    # product_sku is being compared in F2G site. If there are any changes it will be changed to New value.
    if item.product_sku == product_details['sku']:
        no_change('product_sku')
    else:
        item.product_sku = product_details['sku']
    # product_name is being compared in F2G site. If there are any changes it will be changed to New value.
    if item.product_name == product_details['product_name']:
        no_change('product_name')
    else:
        item.product_name = product_details['product_name']
    # next_delivery_date is being compared in F2G site. If there are any changes it will be changed to New value.
    if product_details['stock']['next_delivery_date']:
        if item.next_delivery == dateutil.parser.parse(product_details['stock']['next_delivery_date']).strftime("%Y-%m-%d"):
            no_change('next_delivery_date')
        else:
            item.next_delivery = dateutil.parser.parse(product_details['stock']['next_delivery_date']).strftime("%Y-%m-%d")
    # availability is being compared in F2G site. If there are any changes it will be changed to New value. 
    if item.availability == product_details['stock']['stock_status']:
        no_change('availability')
    else:
        item.availability = product_details['stock']['stock_status']
    # stock_level is being compared in F2G site. If there are any changes it will be changed to New value.  
    if int(item.stock_level) == product_details['stock']['qty']:
        no_change('stock_level')
    else:
        item.stock_level = product_details['stock']['qty']
    # barcode is being compared in F2G site. If there are any changes it will be changed to New value. 
    if item.barcode == product_details['ean']:
        no_change('barcode')
    else:
        item.barcode = product_details['ean']
    # Box is being compared in F2G site. If there are any changes it will be changed to New value.
    if product_details['box']:
        box_keys = product_details["box"].keys()
        for box_key in box_keys:
            height, width, length, unit, weight, box_ean = ['', '', '', '', '', '']
            if product_details['box'][box_key].get('box_dimensions'):
                height = product_details['box'][box_key]['box_dimensions']['height']
                width = product_details['box'][box_key]['box_dimensions']['width']
                length = product_details['box'][box_key]['box_dimensions']['length']
                unit = product_details['box'][box_key]['box_dimensions']['unit']
            if product_details['box'][box_key].get('box_weight'):
                weight = product_details['box'][box_key]['box_weight']
            if product_details['box'][box_key].get('box_ean_code'):
                box_ean = product_details['box'][box_key]['box_ean_code']
            box_name = box_key.replace('box_','')
            box_int = int(box_name)-1
            if item.box[box_int]:
                # Box height is being compared in F2G site. If there are any changes it will be changed to New value.
                if item.box[box_int].height == height:
                    no_change('height')
                else:
                    item.box[box_int].heigt = height
                # Box width is being compared in F2G site. If there are any changes it will be changed to New value.
                if item.box[box_int].width == width:
                    no_change('width')
                else:
                    item.box[box_int].width = width
                # Box depth is being compared in F2G site. If there are any changes it will be changed to New value.
                if item.box[box_int].depth == length:
                    no_change('depth')
                else:
                    item.box[box_int].depth = length
                # Box unit is being compared in F2G site. If there are any changes it will be changed to New value.
                if item.box[box_int].unit == unit:
                    no_change('unit')
                else:
                    item.box[box_int].unit = unit
                # Box weight is being compared in F2G site. If there are any changes it will be changed to New value.
                if item.box[box_int].weight == weight:
                    no_change('weight')
                else:
                    item.box[box_int].weight = weight
            else:
                # If this box was not imported before, it will be imported.        
                item.append('box',
                            {'box_number': box_name,
                            'barcode': box_ean,
                            'height': height,
                            'width': width,
                            'depth': length,
                            'unit': unit,
                            'weight': weight})
    # Requsting from database bullet_points for the each item.
    bullet_check_tuples = frappe.db.get_list('Furniture To Go Product Bullet Points',
                                        filters={
                                            'parent': name
                                        },
                                        fields=['bullet_point'],
                                        as_list=True
                                    )
    # As database returns the results in tuple, we need a list. We are converting it to a list.
    bullet_check = []
    if bullet_check_tuples:
        for bullet_check_tuple in list(bullet_check_tuples):
            bullet_check.append(list(bullet_check_tuple)[0])
    # bullet_point is being compared in F2G site. If there are any changes it will be changed to New value.
    if product_details['product_bullet_points']:
        for bullet_point in product_details['product_bullet_points']:
            if bullet_point in bullet_check:
                no_change('bullet_point')
            else:
                item.append('product_bullet_points',{'bullet_point': bullet_point})
    attachments = item.get_value('product_attachments')
    attachment_list = []
    for each in attachments:
        attachment_list.append(each.attachment_name)
    if product_details['product_file']:
        for product_file in product_details['product_file']:
            if product_file['name'] in attachment_list:
                no_change('product_attachement')
            else:
                item.append('product_attachments',{'attachment_name': product_file['name'],
                                                'attachment_file': product_file['link']})
    images = product_details['product_images']
    if images:
        main_image = product_details['product_images'][0]
        if main_image in item.main_image:
            no_change('main_image')
        else:
            item.main_image = product_details['product_images'][0]
        item_images = item.get_value('product_images')
        item_image_list = []
        for each in item_images:
            item_image_list.append(each.image_file)
        for i in range(len(images)):
            if i > 0:
                if images[i] in item_image_list:
                    no_change("images")
                else:
                    item.append('product_images', {'image_name': images[i].rsplit('/', 1)[1],
                                                'image_file': images[i]})
    if item.supplier_url == product_details['product_link']:
        no_change('supplier_url')
    else:
        item.supplier_url = product_details['product_link']
    if item.description == product_details['product_description']:
        no_change('description')
    else:
        item.description = product_details['product_description']
    price = product_details['prices']
    hd_price = price['home_delivery']
    store_price = price['store_delivery']
    over_250 = price['order_over_250']
    over_500 = price['order_over_500']
    over_1000 = price['order_over_1000']
    over_2000 = price['order_over_2000']
    if hd_price == item.hd_price:
        no_change('hd_price')
    else:
        item.hd_price = hd_price
    if store_price == item.store_delivery_price:
        no_change('store_delivery_price')
    else:
        item.store_delivery_price = store_price
    if over_250 == item.over_250:
        no_change('over_250')
    else:
        item.over_250 = over_250
    if over_500 == item.over_500:
        no_change('over_500')
    else:
        item.over_500 = over_500
    if over_1000 == item.over_1000:
        no_change('over_1000')
    else:
        item.over_1000 = over_1000
    if over_2000 == item.over_2000:
        no_change('over_2000')
    else:
        item.over_2000 = over_2000
    # print(product_details)
    item.save(ignore_permissions=True)



