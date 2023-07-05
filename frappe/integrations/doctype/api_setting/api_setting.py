# Copyright (c) 2023, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests, json
import requests
import base64

class APISetting(Document):
	def validate(self):
		pass

	@frappe.whitelist()
	def generate_token(self):
		url = self.url

		bearer_token = self.generate_bearer_token(self.username, self.password)
		if bearer_token:
			self.db_set("bearer_token", bearer_token)

	def generate_bearer_token(self, username, password):
		url = self.url
		
		credentials = f'{username}:{password}'
		encoded_credentials = credentials.encode('utf-8')
		base64_credentials = base64.b64encode(encoded_credentials).decode('utf-8')
		frappe.throw("{} and {} Hello {} and {}".format(username, password, base64_credentials, url))

		headers = {
			'Authorization': f'Basic {base64_credentials}',
			'Content-Type': 'application/x-www-form-urlencoded',
		}

		data = {
			'grant_type': 'client_credentials',
		}

		response = requests.post(url, headers=headers, data=data)

		if response.status_code == 200:
			token = response.json().get('access_token')
			return token
		else:
			frappe.throw(f"Failed to generate bearer token. Status code: {response.status_code}")
			return None

