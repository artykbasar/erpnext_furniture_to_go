# -*- coding: utf-8 -*-
# Copyright (c) 2021, Artyk Basarov and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
# from erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_methods import find_new_products
from frappe.model.document import Document

class FurnitureToGoSettings(Document):
	def find_new_products(self):
		if self.enable == 1:
			frappe.enqueue('erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_methods.find_new_products')

	def find_product_group(self):
		if self.enable == 1:
			frappe.enqueue('erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_methods.product_group_finder')

	def find_product_range(self):
		if self.enable == 1:
			frappe.enqueue('erpnext_furniture_to_go.erpnext_furniture_to_go.doctype.furniture_to_go_settings.furniture_to_go_methods.product_range_finder')


			
