import requests
from bs4 import BeautifulSoup
import re

f2g_url = 'https://furniture-to-go.co.uk/customer/account/login/'
# Login link for furniture to go
f2g_url_login = 'https://furniture-to-go.co.uk/customer/account/loginPost/'
# Link for login forum post from
ranges_link = 'https://furniture-to-go.co.uk/ranges.html'
# Link for page of all the range_links
load = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/" \
       "537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
# This variable saves header for imitating browser


class F2G:
    """ This class helps to extract product details, order details,
    submit orders to Furniture to go website"""
    def __init__(self):
        self.s = requests.Session()
    #     When cass is initiated requests session is being opened.

    def login(self, login_user, password, url=f2g_url, post_url=f2g_url_login, header=load):
        """ This function helps to login to Furniture to go website so other functions can get
         stock levels and prices"""
        browser_headers = {"user-agent": header}
        # Browser headers are saved as dictionary in this variable
        response = self.s.get(url)
        # We are doing request from login page as we need to retrieve form key
        soup = BeautifulSoup(response.text, 'lxml')
        # Parsing the response through BeautifulSoup library
        form_key = soup.find('input', attrs={'name': 'form_key'})['value']
        # We are retrieving from key from this location.
        login = {
            "form_key": form_key,
            "login[username]": login_user,
            "login[password]": password,
            "send": ''
        }
        # This dictionary will be posted to the server as data
        return self.s.post(post_url, data=login, headers=browser_headers)
    #     we are returning login response

    def clear_cart(self):
        """ Clear the Shopping cart """
        cart_url='https://furniture-to-go.co.uk/checkout/cart/'
        cart_response = self.s.get(url=cart_url)
        soup = BeautifulSoup(cart_response.text, 'lxml')
        products_in_cart = soup.findAll(title='Remove item')
        if products_in_cart:
            for each in products_in_cart:
                remove_link = each['href']
                self.s.get(url=remove_link)
        return True

    def add_products_to_cart(self, products_details):
        """ Function accepts list of dictionaries.
        each dictionary must consist product: \n
        link, qty"""
        if type(products_details) == list:
            self.clear_cart()
            for product_details in products_details:
                link = product_details['link']
                qty = product_details['qty']
                r = self.s.get(link)
                soup = BeautifulSoup(r.text, 'lxml')
                form_link = soup.find('div', class_='product-essential').find('form')['action']
                product_number = soup.find('input', type='hidden')['value']
                # print(product_number)
                form_data = {
                    "product": product_number,
                    "related_product": '',
                    "qty": qty
                }
                self.s.post(form_link, form_data)

        elif type(products_details) != list:
            print("In correct entry!!!\n"
                  "Entry to a function needs to be entered as list object")

    def fetch_ranges_links(self, ranges=ranges_link):
        """ This function spits out range links as a List"""
        html = self.s.get(ranges)
        links = []
        soup = BeautifulSoup(html.text, 'lxml')
        links_html = soup.find('ul', id='vert-menu').findAll('a', href=True)
        for link_html in links_html:
            links.append(link_html['href'])
        return links

    def product_link_extractor(self, range_url=None):
        """ This Function accepts Url of the Range as list and
            spits out links of the product."""
        if not range_url:
            range_url = self.fetch_ranges_links()
        
        links = []
        for each_link in range_url:
            each_link = each_link + '?infinitescroll=1&limit=all'
            html = self.s.get(each_link)
            soup = BeautifulSoup(html.text, 'lxml')
            links_html = soup.findAll('h2', class_='item fn product-name')
            for link_html in links_html:
                product = link_html.a['href']
                links.append(product)
        return links
    

    def product_data_extractor(self, link):
        """This function accepts Furniture to go product url and
            returns product details as dict
            Here are the following steps happening:
            \n 1. We make http request and we parse the response through BeautifulSoup
            \n 2. We Extract SKU of the product"""

        html = self.s.get(link)
        # Gets response of the url from Furniture to go
        soup = BeautifulSoup(html.text, 'lxml')
        # Parses the html request
        sku = soup.find('div', class_="sku").text.split('SKU: ')[1].strip()
        # Gets the SKU of the Product
        descriptions = soup.find('div', class_="description")
        # Gets the description section from parsed HTML
        rex_bullet_point_search = r"li|strong"
        # This rex helps to find "li" or 'strong' tags in html
        bullet_points = descriptions.findAll(re.compile(rex_bullet_point_search))
        # This variable finds in descriptions html all the bullet points and boldly written headers
        title_status = 0
        # This variable helps to identify sections of the bullet points.
        bullet_points_list = []
        # This variable sends list of bullets points.
        rex_box_search = r"(box\s*:?\s*\d)"
        # This variable contains rex for finding box in bullet points.
        rex_width_search = r"((w\b|width\b)(\s*)(\d+(,|\.|\\|\/)?\d*)|" \
                           r"(\d+(,|\.|\\|\/)?\d*)(\s*)(w\b|width\b))"
        # This variable contains rex for width search
        rex_height_search = r"((h\b|height\b)(\s*)(\d+(,|\.|\\|\/)?\d*)|" \
                            r"(\d+(,|\.|\\|\/)?\d*)(\s*)(h\b|height\b))"
        # This variable contains rex for height search
        rex_length_search = r"((l\b|length\b)(\s*)(\d+(,|\.|\\|\/)?\d*)|" \
                            r"(\d+(,|\.|\\|\/)?\d*)(\s*)(l\b|length\b))"
        # This variable contains rex for length search
        rex_depth_search = r"((d\b|depth\b)(\s*)(\d+(\.|\\|\/)?\d*)|" \
                           r"(\d+(\.|\\|\/)?\d*)(\s*)(d\b|depth\b))"
        # This variable contains rex for depth search
        rex_dimension_number_search = r"(\d+(,|\.|\\|\/)?\d*)"
        # This variable contains rex for dimension search
        rex_dimension_unit_search = r"(cm|mm)\b"
        # This variable contains rex for dimension unit search
        rex_ean_search = r'(ean).*(\d+)'
        # This variable contains rex for ean search
        rex_ean_number_search = r'(\d+)'
        # This variable contains rex for ean number search
        rex_box_weight_search = r"weight.*\d(\.|,)?.*"
        # This variable contains rex for box weight search
        rex_weight_number_search = r"(\d+(,|\.)?\d*)"
        # This variable contains rex for weight number search
        product_assembled_weight_list = []

        product_assembled_size_rex = r'(.*((d\b|depth\b|h\b|height\b|w\b|width\b)' \
                                     r'.*\d+(,|\.|\\)?\d*.*x.*' \
                                     r'(d\b|depth\b|h\b|height\b|w\b|width\b)' \
                                     r'.*\d+(,|\.|\\)?\d*.*x.*' \
                                     r'(d\b|depth\b|h\b|height\b|w\b|width\b)' \
                                     r'.*\d+(,|\.|\\)?\d*.*)(mm)?.*|.*' \
                                     r'(\d+(,|\.|\\)?\d*.*(d\b|depth\b|h\b|height\b|w\b|width\b)' \
                                     r'.*x.*\d+(,|\.|\\)?' \
                                     r'\d*.*(d\b|depth\b|h\b|height\b|w\b|width\b)' \
                                     r'.*x.*\d+(,|\.|\\)?\d*.*' \
                                     r'(d\b|depth\b|h\b|height\b|w\b|width\b).*)(mm)?.*)'
        rex_product_assembled_weight_search = r'.*(assembled)\b\s*weight\s*\(*(kg)?\)' \
                                              r'*:*\s*\d+(,|.)?\d*(kg)?.*|.*kg' \
                                              r'\s*\d+(,|.)?\d*\s*(kg)*.*|.*weight' \
                                              r'\s*:*\s*\d+(,|.)?\d*\s(kg).*?|' \
                                              r'(box)\b\s*\d|(weight)\b\s*\d+(\.|,)?\d*'
        # This Rex is looking for a Patten of the
        rex_product_box_dimensions_search = r'(.*((l\b|length\b|h\b|height\b|w\b|width\b)' \
                                            r'.*\d+(,|\.|\\)?\d*.*x?.*' \
                                            r'(l\b|length\b|h\b|height\b|w\b|width\b)' \
                                            r'.*\d+(,|\.|\\)?\d*.*x?.*' \
                                            r'(l\b|length\b|h\b|height\b|w\b|width\b)' \
                                            r'.*\d+(,|\.|\\)?\d*.*)(cm)?.*|.*' \
                                            r'(\d+(,|\.|\\)?\d*.*' \
                                            r'(l\b|length\b|h\b|height\b|w\b|width\b)' \
                                            r'.*x?.*\d+' \
                                            r'(,|\.|\\)?\d*.*' \
                                            r'(l\b|length\b|h\b|height\b|w\b|width\b)' \
                                            r'.*x?.*\d+' \
                                            r'(,|\.|\\)?\d*.*' \
                                            r'(l\b|length\b|h\b|height\b|w\b|width\b)' \
                                            r'.*)(cm)?.*)'
        box_number_count = 0
        box = {}
        product_assembled_size = {}
        product_assembled_size_count = 0
        ean_number_count = 0
        ean = ''
        for each in bullet_points:
            loop_soup = BeautifulSoup(str(each), 'lxml')
            if loop_soup.find('strong') is not None and title_status is 0:
                title_status += 1
            elif loop_soup.find('strong',
                                text=re.compile(rex_box_search,
                                                re.IGNORECASE)) is not None and title_status is 1:
                title_status += 1
                box_number_count += 1
            elif title_status is 1:
                bullet_point = each.text.replace('\xa0', ' ').strip()
                if bullet_point:
                    bullet_points_list.append(bullet_point)
                    product_assembled_size_tester = re.findall(product_assembled_size_rex,
                                                               bullet_point,
                                                               re.IGNORECASE)
                    product_assembled_weight_tester = re.findall(rex_product_assembled_weight_search,
                                                                 bullet_point,
                                                                 re.IGNORECASE)
                    product_ean_search_tester = re.findall(rex_ean_search,
                                                           bullet_point,
                                                           re.IGNORECASE)
                    if product_assembled_size_tester and product_assembled_size_count is 0:
                        try:
                            product_assembled_size_w = re.findall(rex_width_search,
                                                                  bullet_point,
                                                                  re.IGNORECASE)[0][0]
                            product_assembled_size_w = re.findall(rex_dimension_number_search,
                                                                  product_assembled_size_w)[0][0]
                        except IndexError:
                            print('Assembled size width is missing I need human help.'
                                  'here is the product link:\n', html.url)
                            product_assembled_size_w = 0
                        try:
                            product_assembled_size_h = re.findall(rex_height_search,
                                                                  bullet_point,
                                                                  re.IGNORECASE)[0][0]
                            product_assembled_size_h = re.findall(rex_dimension_number_search,
                                                                  product_assembled_size_h)[0][0]
                        except IndexError:
                            print('Assembled size height is missing I need human help.'
                                  'here is the product link:\n', html.url)
                            product_assembled_size_h = 0
                        try:
                            product_assembled_size_d = re.findall(rex_depth_search,
                                                                  bullet_point,
                                                                  re.IGNORECASE)[0][0]
                            product_assembled_size_d = re.findall(rex_dimension_number_search,
                                                                  product_assembled_size_d)[0][0]
                        except IndexError:
                            print('Assembled size depth is missing I need human help.'
                                  'here is the product link:\n', html.url)
                            product_assembled_size_d = 0

                        product_assembled_size = {
                            'with': product_assembled_size_w,
                            'height': product_assembled_size_h,
                            'depth': product_assembled_size_d
                        }
                        product_assembled_size_count = 1
                    elif product_assembled_weight_tester:
                        product_assembled_weight = re.findall(rex_weight_number_search,
                                                              bullet_point,
                                                              re.IGNORECASE)[0][0].replace(',', '.')
                        product_assembled_weight = float(product_assembled_weight)
                        product_assembled_weight_list.append(product_assembled_weight)

                    elif ean_number_count is 0 and product_ean_search_tester:
                        try:
                            ean = list(re.findall(rex_ean_number_search,
                                                  bullet_point,
                                                  re.IGNORECASE))[0]
                        except IndexError:
                            ean = ''
                            print('Extraction of ean code was not successful.'
                                  'I need human help. Here is the product link:\n',
                                  html.url)
                        ean_number_count = 1
            elif title_status is 2:
                if loop_soup.find('strong',
                                  text=re.compile(rex_box_search,
                                                  re.IGNORECASE)) is not None:
                    box_number_count += 1
                else:
                    box_number = 'box_{}'.format(box_number_count)
                    if re.match(rex_product_box_dimensions_search,
                                each.text,
                                re.IGNORECASE) is not None:
                        try:
                            box_dimension_unit = re.findall(rex_dimension_unit_search,
                                                            each.text,
                                                            re.IGNORECASE)[0]
                        except IndexError:
                            print('Box unit value extraction was not successful.'
                                  'I need human help. Here is the product link:\n', html.url)
                            box_dimension_unit = 'Null'
                        try:
                            box_dimension_l = re.findall(rex_length_search,
                                                         each.text,
                                                         re.IGNORECASE)[0][0]
                            box_dimension_l = re.findall(rex_dimension_number_search,
                                                         box_dimension_l,
                                                         re.IGNORECASE)[0][0].replace(",", ".")
                        except IndexError:
                            print('Box dimension length extraction was not successful'
                                  'I need human help. Here is the product link:\n', html.url)
                            box_dimension_l = 0
                        try:
                            box_dimension_w = re.findall(rex_width_search,
                                                         each.text,
                                                         re.IGNORECASE)[0][0]
                            box_dimension_w = re.findall(rex_dimension_number_search,
                                                         box_dimension_w,
                                                         re.IGNORECASE)[0][0].replace(",", ".")
                        except IndexError:
                            print('Box dimension width extraction was not successful'
                                  'I need human help. Here is the product link:\n', html.url)
                            box_dimension_w = 0
                        try:
                            box_dimension_h = re.findall(rex_height_search,
                                                         each.text,
                                                         re.IGNORECASE)[0][0]
                            box_dimension_h = re.findall(rex_dimension_number_search,
                                                         box_dimension_h,
                                                         re.IGNORECASE)[0][0].replace(",", ".")
                        except IndexError:
                            print('Box dimension height extraction was not successful'
                                  'I need human help. Here is the product link:\n', html.url)
                            box_dimension_h = 0
                        box_dimension_l = round(float(box_dimension_l), 2)
                        box_dimension_w = round(float(box_dimension_w), 2)
                        box_dimension_h = round(float(box_dimension_h), 2)
                        if "mm" in str(box_dimension_unit).lower():
                            box_dimension_l = box_dimension_l / 10
                            box_dimension_w = box_dimension_w / 10
                            box_dimension_h = box_dimension_h / 10
                        box_dimension = {
                            'unit': 'cm',
                            "length": box_dimension_l,
                            "width": box_dimension_w,
                            "height": box_dimension_h
                        }
                        if box.get(box_number) is None:
                            box[box_number] = {}
                            box[box_number]['box_dimensions'] = box_dimension
                        else:
                            box[box_number]['box_dimensions'] = box_dimension
                    elif re.match(rex_ean_search,
                                  each.text,
                                  re.IGNORECASE) is not None:
                        box_ean_code = re.findall(rex_ean_number_search,
                                                  each.text,
                                                  re.IGNORECASE)[0]
                        if box.get(box_number) is None:
                            box[box_number] = {}
                            box[box_number]['box_ean_code'] = box_ean_code
                        else:
                            box[box_number]['box_ean_code'] = box_ean_code
                    elif re.match(rex_box_weight_search,
                                  each.text,
                                  re.IGNORECASE) is not None:
                        box_weight = re.findall(rex_weight_number_search,
                                                each.text,
                                                re.IGNORECASE)[0][0]
                        box_weight = float(box_weight.replace(',', '.'))
                        if box.get(box_number) is None:
                            box[box_number] = {}
                            box[box_number]['box_weight'] = box_weight
                        else:
                            box[box_number]['box_weight'] = box_weight

        description = descriptions.find('strong')
        if description:
            description = description.next_sibling
        else:
            description = descriptions
        # In this HTML location we tend to find the descriptions of the product
        rex_br_search = r'<(br)\/?>'
        # Rex is looking for '<br>' or '<br\>'
        if re.match(rex_br_search, str(description)) is not None:
            # Sometimes description value is <br> or <br\>.
            # if that is the case this filter gets activated
            description = description.next_sibling
            # after <br\> we get description
        elif description is None:
            # Sometimes description value is None.
            # If that is the case this filter gets activated
            try:
                description = descriptions.findAll('span')[1].text
            except IndexError:
                description = descriptions.findAll('div')[1].text
            # looks for the description in this location
        qty = 0
        next_delivery_date = ""
        stock_status = "Unknown"
        available_stock = soup.find('div',
                                    class_='qty-available').text.strip()
        rex_stock_status_search = r'(stock)\b\s*:?\s*(\d+)|' \
                                  r'(awaiting\s*delivery\s*date)|' \
                                  r'(next\s*delivery)\b\s*:?\s*([\d]{2})' \
                                  r'(-|\/|\\)?([\d]{2})(-|\/|\\)?([\d]{4})'
        stock = list(re.findall(rex_stock_status_search,
                                available_stock,
                                re.IGNORECASE)[0])
        if 'stock' in stock[0].lower():
            stock_status = 'In Stock'
            qty = stock[1]
        elif 'awaiting delivery date' in stock[2].lower():
            stock_status = "No stock awaiting delivery date"
        elif 'next delivery' in stock[3].lower():
            stock_status = "No stock next delivery date is available"
            next_delivery_date = str(stock[4]) + r'/' + str(stock[6]) + r'/' + str(stock[8])
        else:
            print(html.url)
            print('Stock status is {}. This link needs to be checked for errors'.
                  format(stock_status))
        stock_dictionary = {'qty': qty,
                            'stock_status': stock_status,
                            'next_delivery_date': next_delivery_date}

        product_prices_html = soup.find('span',
                                        class_='show-me-the-prices-container').\
            findAll('td',
                    class_='right')
        price_list = {}
        for index, price in enumerate(product_prices_html):
            price = price.text.strip('£ ').replace(',', '.')
            if index is 0:
                price_list['home_delivery'] = price
            elif index is 1:
                price_list['store_delivery'] = price
            elif index is 2:
                price_list['order_over_250'] = price
            elif index is 3:
                price_list['order_over_500'] = price
            elif index is 4:
                price_list['order_over_1000'] = price
            elif index is 5:
                price_list['order_over_2000'] = price

        product_name = soup.find('h1',
                                 class_='item name fn').text

        file_list = []
        try:
            product_files_html = soup.find('div',
                                           class_='mainDiv')

            product_file_names = product_files_html.findAll('td',
                                                            class_="fileTitleDiv")
            product_file_links = product_files_html.findAll('a', href=True)
            for file_id, file in enumerate(product_file_names):
                file_name = file.text
                file_link = product_file_links[file_id]['href']
                file_dict = {
                    'name': file_name,
                    'link': file_link
                }
                file_list.append(file_dict)
        except AttributeError:
            pass

        image_list = []

        try:
            product_images_html = soup.find('div',
                                            class_='more-views')
            product_image_links = product_images_html.findAll('a', href=True)
            
            for image in product_image_links:
                image_link = image['href']
                image_list.append(image_link)
        except AttributeError:
            pass

        # print(image_list)

        data = {
            'product_name': product_name,
            'prices': price_list,
            'stock': stock_dictionary,
            'ean': ean,
            'sku': sku,
            'box': box,
            'product_assembled_weight': product_assembled_weight_list,
            'product_assembled_size': product_assembled_size,
            'product_description': str(description).strip(),
            'product_bullet_points': bullet_points_list,
            'product_link': html.url,
            'product_file': file_list,
            'product_images': image_list
        }

        return data
