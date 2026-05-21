import frappe
import random
from datetime import timedelta
from frappe.utils import cint

OTP_EXPIRY_MINUTES = 5
OTP_RATE_LIMIT = 10
OTP_RATE_WINDOW = 600  # seconds (10 minutes)


def get_client_ip():
    return frappe.local.request_ip or "unknown"


def check_rate_limit(username):
    ip = get_client_ip()
    key = f"otp_rate:{username}:{ip}"

    count = cint(frappe.cache().get(key)) or 0
    if count >= OTP_RATE_LIMIT:
        frappe.throw("Too many OTP requests. Try again later.")

    frappe.cache().setex(key, OTP_RATE_WINDOW, count + 1)


def generate_otp():
    return str(random.randint(100000, 999999))


def strip_phone(phone):
    return phone.removeprefix("+975").removeprefix("975")

