# -*- coding: utf-8 -*-
# Copyright (c) 2021, Artyk Basarov and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
# import erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_methods as f2g
from frappe.model.document import Document

class FurnitureToGoSettings(Document):
	def find_new_products(self):
		if self.enable == 1:
			frappe.enqueue('erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_methods.find_new_products', timeout=3000)

	def find_product_group(self):
		if self.enable == 1:
			frappe.enqueue('erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_methods.product_group_finder', timeout=3000)

	def find_product_range(self):
		if self.enable == 1:
			frappe.enqueue('erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_methods.product_range_finder', timeout=3000)

	def sync_products_to_items(self):
		if self.enable == 1:
			frappe.enqueue('erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_methods.f2g_to_item', timeout=3000)

