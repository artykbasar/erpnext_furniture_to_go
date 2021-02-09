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
                                        },
                                        fields=['product_sku'],
                                        as_list=True
                                    )
        if not response:
            new_product_links.append(each)
    if new_product_links:        
        import_products_list(new_product_links)
    else:
        print('There is no new products')
    
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
    item.supplier_url = product_details['product_link']
    item.insert(ignore_permissions=True)



