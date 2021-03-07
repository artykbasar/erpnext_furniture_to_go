from __future__ import unicode_literals
import frappe, time, dateutil, math, csv, datetime
from six import StringIO
import erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_api as f2g
from frappe import _


user_details = frappe.get_doc('Furniture To Go Settings')
f2g_ins = f2g.F2G()
f2g_ins.login(user_details.user_name, user_details.get_password('password'))

def f2g_to_item():
    create_item_box()
    add_item_box_to_item()
    add_products_to_items()

def add_products_to_items():
    f2g_sku = get_f2g_product_list()
    add_f2g_sku_to_items(f2g_sku)

def add_f2g_sku_to_items(f2g_sku):
    if type(f2g_sku) is list:
        pass
    elif type(f2g_sku) is str:
        f2g_sku = [f2g_sku]
    for each in f2g_sku:
        item_check = frappe.db.get_list(
            "Item Supplier",
            filters={
            'supplier_part_no': each
            }, 
            fields=['parent'])
        if item_check:
            save_status = False
            f2g_settings = frappe.get_doc('Furniture To Go Settings')
            f2g_item = frappe.get_doc('Furniture To Go Products', each)
            item_code = item_check[0]['parent']
            item = frappe.get_doc('Item', item_code)
            new_slideshow = frappe.new_doc('Website Slideshow')
            ####################
            item_name = f2g_item.product_name
            #
            supplier_part_no = f2g_item.product_sku
            #
            image = f2g_item.main_image
            #
            f2g_group = f2g_item.f2g_group
            if not f2g_group:
                f2g_group = f2g_settings.item_group
            else:
                f2g_group = frappe.get_doc('Furniture To Go Product Group',f2g_group).item_group
                if not f2g_group:
                    f2g_group = f2g_settings.item_group
            #    
            f2g_range = f2g_item.range_name
            if not f2g_range:
                f2g_range = f2g_settings.default_brand
            else:
                f2g_range = frappe.get_doc('Furniture To Go Range',f2g_range).brand
                if not f2g_range:
                    f2g_range = f2g_settings.default_brand
            #
            stock = int(f2g_item.stock_level)
            #
            next_delivery = f2g_item.next_delivery
            default_lead_time = int(f2g_settings.default_lead_time)
            today = datetime.datetime.today().date()
            lead_time = 365
            if next_delivery:
                lead_time = next_delivery - today
                lead_time = lead_time.days + default_lead_time
            elif stock > 0:
                lead_time = default_lead_time
            #
            description = f2g_item.description
            #
            item_box = f2g_item.box
            #
            default_warehouse = f2g_settings.default_warehouse
            #
            images = f2g_item.product_images

            ##################################    
            if item.item_name != item_name:
                item.item_name = item_name
                save_status = True
            if item.brand != f2g_range:
                item.brand = f2g_range
                save_status = True
            if item.description != description:
                item.description = description
                save_status = True
            if item.image != image:
                item.image = image
                save_status = True
            if item.item_group != f2g_group:
                item.item_group = f2g_group
                save_status = True
            if item_box:
                for each_item_box in item_box:
                    if item.item_box:
                        box = item.item_box[each_item_box.idx - 1]
                        if box.box_ean != each_item_box.barcode:
                            box.box_ean = each_item_box.barcode
                            save_status = True
                        if float(box.box_height) != float(each_item_box.height):
                            box.box_height = float(each_item_box.height)
                            save_status = True
                        if float(box.box_width) != float(each_item_box.width):
                            box.box_width = float(each_item_box.width)
                            save_status = True
                        if float(box.box_depth) != float(each_item_box.depth):
                            box.box_depth = float(each_item_box.depth)
                            save_status = True
                        if box.box_dim_unit != each_item_box.unit:
                            box.box_dim_unit = each_item_box.unit
                            save_status = True
                        if float(box.box_weight) != float(each_item_box.weight):
                            box.box_weight = each_item_box.weight
                            save_status = True
                    else:
                        item.append('item_box',{
                            'box_number': each_item_box.box_number,
                            'box_ean': each_item_box.barcode,
                            'box_height': each_item_box.height,
                            'box_width': each_item_box.width,
                            'box_depth': each_item_box.depth,
                            'box_dim_unit': each_item_box.unit,
                            'box_weight': each_item_box.weight
                        })
                        save_status = True
            if int(item.lead_time_days) != int(lead_time):
                item.lead_time_days = lead_time
                save_status = True
            # item.show_in_website = 1
            if item.website_image != image:
                item.website_image = image
                save_status = True
            if item.website_warehouse != default_warehouse:
                item.website_warehouse = default_warehouse
                save_status = True
            slideshow_image_list = []
            if item.slideshow:
                web_slideshow = frappe.get_doc('Website Slideshow', item.slideshow)
                slideshow_images = web_slideshow.slideshow_items
                for slideshow_image in slideshow_images:
                    slideshow_image_list.append(slideshow_image.image)
                for each_image in images:
                    if each_image.image_file not in slideshow_image_list:
                        web_slideshow.append('slideshow_items',{
                            'image': each_image.image_file
                        })
                        save_status = True
            elif not item.slideshow and images:
                slideshow_name = "{} - Product Slideshow".format(item_code) 
                new_slideshow.slideshow_name = slideshow_name
                for each_image in images:
                    new_slideshow.append('slideshow_items',{
                        "image": each_image.image_file
                    })
                new_slideshow.insert(ignore_permissions=True)
                item.slideshow = slideshow_name
                save_status = True
            if save_status:
                inserted_item.save(ignore_permissions=True)
        else:
            f2g_settings = frappe.get_doc('Furniture To Go Settings')
            f2g_item = frappe.get_doc('Furniture To Go Products', each)
            new_item = frappe.new_doc('Item')
            new_slideshow = frappe.new_doc('Website Slideshow')
            ####################
            item_name = f2g_item.product_name
            #
            supplier_part_no = f2g_item.product_sku
            #
            image = f2g_item.main_image
            #
            f2g_group = f2g_item.f2g_group
            if not f2g_group:
                f2g_group = f2g_settings.item_group
            else:
                f2g_group = frappe.get_doc('Furniture To Go Product Group',f2g_group).item_group
                if not f2g_group:
                    f2g_group = f2g_settings.item_group
            #    
            f2g_range = f2g_item.range_name
            if not f2g_range:
                f2g_range = f2g_settings.default_brand
            else:
                f2g_range = frappe.get_doc('Furniture To Go Range',f2g_range).brand
                if not f2g_range:
                    f2g_range = f2g_settings.default_brand
            #
            stock = int(f2g_item.stock_level)
            #
            next_delivery = f2g_item.next_delivery
            default_lead_time = int(f2g_settings.default_lead_time)
            today = datetime.datetime.today().date()
            lead_time = 365
            if next_delivery:
                lead_time = next_delivery - today
                lead_time = lead_time.days + default_lead_time
            elif stock > 0:
                lead_time = default_lead_time
            #
            description = f2g_item.description
            #
            item_box = f2g_item.box
            #
            default_warehouse = f2g_settings.default_warehouse
            #
            images = f2g_item.product_images

            ##################################    
            new_item.item_name = item_name
            new_item.brand = f2g_range
            new_item.description = description
            new_item.include_item_in_manufacturing = 0
            new_item.delivered_by_supplier = 1
            new_item.append('supplier_items',
                {'supplier': f2g_settings.default_supplier,
                 'supplier_part_no': supplier_part_no
                })
            new_item.image = image
            new_item.item_group = f2g_group
            if item_box:
                for each_item_box in item_box:
                    new_item.append('item_box',{
                        'box_number': each_item_box.box_number,
                        'box_ean': each_item_box.barcode,
                        'box_height': each_item_box.height,
                        'box_width': each_item_box.width,
                        'box_depth': each_item_box.depth,
                        'box_dim_unit': each_item_box.unit,
                        'box_weight': each_item_box.weight
                    })
            new_item.lead_time_days = lead_time
            new_item.show_in_website = 1
            new_item.website_image = image
            new_item.website_warehouse = default_warehouse
            inserted_item = new_item.insert(ignore_permissions=True)
            item_code = inserted_item.item_code
            slideshow_name = "{} - Product Slideshow".format(item_code) 
            new_slideshow.slideshow_name = slideshow_name
            for each_image in images:
                new_slideshow.append('slideshow_items',{
                    "image": each_image.image_file
                })
            new_slideshow.insert(ignore_permissions=True)
            inserted_item.slideshow = slideshow_name
            inserted_item.save(ignore_permissions=True)
            print(inserted_item.item_code)

def get_f2g_product_list():
    response = frappe.db.get_list('Furniture To Go Products')
    sku_list = []
    for each in response:
        sku_list.append(each.name)
        # break
    return sku_list

def add_item_box_to_item():
    item_box_check = frappe.db.exists('DocType', 'Item Box')
    item_box_check_in_item = frappe.db.exists('Custom Field', 'Item-item_box')
    sb_item_box_check_in_item = frappe.db.exists('Custom Field', 'Item-item_box_sb')
    frappe.db.exists('Custom Field', 'Item-item_box')
    # print(item_box_check_in_item)
    if item_box_check:
        if item_box_check_in_item:
            # print('item_box feild exists in Item DocType')
            pass
        else:
            doc = frappe.new_doc('Custom Field')
            doc.dt = 'Item'
            doc.label = 'Item Box '
            doc.fieldname = 'item_box'
            doc.insert_after = 'description'
            doc.fieldtype = 'Table'
            doc.options = 'Item Box'
            doc.insert(ignore_permissions=True)
        if sb_item_box_check_in_item:
            # print('sb_item_box feild exists in Item DocType')
            pass
        else:
            doc_2 = frappe.new_doc('Custom Field')
            doc_2.dt = 'Item'
            doc_2.label = 'Item Box sb'
            doc_2.fieldname = 'item_box_sb'
            doc_2.insert_after = 'description'
            doc_2.fieldtype = 'Section Break'
            doc_2.insert(ignore_permissions=True)
    else:
        print('Item Box Doctype has not been created, Please Create it Fist')

def create_item_box():
    item_box_check = frappe.db.exists('DocType', 'Item Box')
    if item_box_check:
        #print('Item Box already exist')
        pass
    else:
        doc = frappe.new_doc('DocType')
        doc.name = 'Item Box'
        doc.module = 'Stock'
        doc.istable = 1
        doc.editable_grid = 1
        doc.track_views = 1
        doc.custom = 1
        doc.append('fields', 
                {"label":"Box Number",
                "fieldtype": "Data",
                'fieldname': 'box_number',
                'in_list_view': 1,
                'columns': 1
            })
        doc.append('fields',
                {"label": "EAN",
                "fieldtype": "Barcode",
                'fieldname': 'box_ean',
                'in_list_view': 1,
                'columns': 2
            })
        doc.append('fields',
                {"label": "UPC",
                "fieldtype": "Barcode",
                'fieldname': 'box_upc',
                'in_list_view': 1,
                'columns': 2
            })
        doc.append('fields',
                {"label": "Height",
                "fieldtype": "Float",
                'precision': 1,
               'fieldname': 'box_height',
                'in_list_view': 1,
                'columns': 1
            })
        doc.append('fields',
                {"label": "Width",
                "fieldtype": "Float",
                'precision': 1,
                'fieldname': 'box_width',
                'in_list_view': 1,
                'columns': 1
            })
        doc.append('fields',
                {"label": "Depth",
                "fieldtype": "Float",
                'precision': 1,
                'fieldname': 'box_depth',
                'in_list_view': 1,
                'columns': 1
            })
        doc.append('fields',
                {"label": "Unit",
                "fieldtype": "Data",
                'fieldname': 'box_dim_unit',
                'in_list_view': 1,
                'columns': 1
            })
        doc.append('fields',
                {"label": "Weight",
                "fieldtype": "Float",
                'precision': 3,
                'fieldname': 'box_weight',
                'in_list_view': 1,
                'columns': 1
            })
        doc.document_type = 'Document'
        doc.insert(ignore_permissions=True)

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
    # print('I am here 1')
    # print('hellooooo')
    group_data = f2g_ins.fetch_category_links()
    group_data_list = group_data.keys()
    response = frappe.db.get_list('Furniture To Go Products',fields=['name', 'supplier_url'])
    for each in response:
        print(each)
        if each['supplier_url'] in group_data_list:
            name = each['name']
            item = frappe.get_doc('Furniture To Go Products', name)
            group = frappe.new_doc('Furniture To Go Product Group')
            group_names = group_data[each['supplier_url']]
            parent_group = group_names['parent']
            group_name = '{} - {}'.format(group_names['child'],parent_group)
            child_check = frappe.db.get_list('Furniture To Go Product Group', filters={'f2g_group_name': group_name})
            if not child_check:
                group.f2g_group_name = group_name
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
    edited = False
    item = frappe.get_doc('Furniture To Go Products', name)
    # product_sku is being compared in F2G site. If there are any changes it will be changed to New value.
    if item.product_sku == product_details['sku']:
        no_change('product_sku')
    else:
        item.product_sku = product_details['sku']
        edited = True
    # product_name is being compared in F2G site. If there are any changes it will be changed to New value.
    if item.product_name == product_details['product_name']:
        no_change('product_name')
    else:
        item.product_name = product_details['product_name']
        edited = True
    # next_delivery_date is being compared in F2G site. If there are any changes it will be changed to New value.
    if product_details['stock']['next_delivery_date']:
        if item.next_delivery == dateutil.parser.parse(product_details['stock']['next_delivery_date']).strftime("%Y-%m-%d"):
            no_change('next_delivery_date')
        else:
            item.next_delivery = dateutil.parser.parse(product_details['stock']['next_delivery_date']).strftime("%Y-%m-%d")
            edited = True
    # availability is being compared in F2G site. If there are any changes it will be changed to New value. 
    if item.availability == product_details['stock']['stock_status']:
        no_change('availability')
    else:
        item.availability = product_details['stock']['stock_status']
        edited = True
    # stock_level is being compared in F2G site. If there are any changes it will be changed to New value.  
    if int(item.stock_level) == int(product_details['stock']['qty']):
        no_change('stock_level')
    else:
        item.stock_level = product_details['stock']['qty']
        edited = True
    # barcode is being compared in F2G site. If there are any changes it will be changed to New value. 
    if item.barcode == product_details['ean']:
        no_change('barcode')
    else:
        item.barcode = product_details['ean']
        edited = True
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
                if float(item.box[box_int].height) == float(height):
                    no_change('height')
                else:
                    item.box[box_int].heigt = height
                    edited = True
                # Box width is being compared in F2G site. If there are any changes it will be changed to New value.
                if float(item.box[box_int].width) == float(width):
                    no_change('width')
                else:
                    item.box[box_int].width = width
                    edited = True
                # Box depth is being compared in F2G site. If there are any changes it will be changed to New value.
                if float(item.box[box_int].depth) == float(length):
                    no_change('depth')
                else:
                    item.box[box_int].depth = length
                    edited = True
                # Box unit is being compared in F2G site. If there are any changes it will be changed to New value.
                if item.box[box_int].unit == unit:
                    no_change('unit')
                else:
                    item.box[box_int].unit = unit
                    edited = True
                # Box weight is being compared in F2G site. If there are any changes it will be changed to New value.
                if float(item.box[box_int].weight) == float(weight):
                    no_change('weight')
                else:
                    item.box[box_int].weight = weight
                    edited = True
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
                edited = True
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
                edited = True
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
                edited = True
    images = product_details['product_images']
    if images:
        main_image = product_details['product_images'][0]
        if main_image in item.main_image:
            no_change('main_image')
        else:
            item.main_image = product_details['product_images'][0]
            edited = True
        item_images = item.get_value('product_images')
        item_image_list = []
        for each in item_images:
            item_image_list.append(each.image_file)
        for i in range(len(images)):
            if images[i] in item_image_list:
                no_change("images")
            else:
                item.append('product_images', {'image_name': images[i].rsplit('/', 1)[1],
                                            'image_file': images[i]})
                edited = True
    if item.supplier_url == product_details['product_link']:
        no_change('supplier_url')
    else:
        item.supplier_url = product_details['product_link']
        edited = True
    if item.description == product_details['product_description']:
        no_change('description')
    else:
        item.description = product_details['product_description']
        edited = True
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
        edited = True
    if store_price == item.store_delivery_price:
        no_change('store_delivery_price')
    else:
        item.store_delivery_price = store_price
        edited = True
    if over_250 == item.over_250:
        no_change('over_250')
    else:
        item.over_250 = over_250
        edited = True
    if over_500 == item.over_500:
        no_change('over_500')
    else:
        item.over_500 = over_500
        edited = True
    if over_1000 == item.over_1000:
        no_change('over_1000')
    else:
        item.over_1000 = over_1000
        edited = True
    if over_2000 == item.over_2000:
        no_change('over_2000')
    else:
        item.over_2000 = over_2000
        edited = True
    # print(product_details)
    if edited:
        item.save(ignore_permissions=True)
