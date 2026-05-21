import frappe
from datetime import timedelta
from frappe.mobile_auth_util import (
    check_rate_limit,
    generate_otp,
    OTP_EXPIRY_MINUTES,
    strip_phone
)

@frappe.whitelist(allow_guest=True)
def request_otp(username, phone):
    check_rate_limit(username)

    phone = strip_phone(phone)

    user = frappe.db.get_value(
        "User",
        {
            "name": username,
            "phone": phone,
            "enabled": 1
        },
        "name"
    )

    if not user:
        frappe.throw("Invalid username or phone number")

    frappe.db.sql("""
        UPDATE `tabLogin OTP`
        SET is_used = 1
        WHERE user = %s AND is_used = 0
    """, user)

    otp = generate_otp()

    frappe.get_doc({
        "doctype": "Login OTP",
        "user": user,
        "phone": phone,
        "otp": otp,
        "expires_at": frappe.utils.now_datetime()
                        + timedelta(minutes=OTP_EXPIRY_MINUTES),
        "is_used": 0,
        "docstatus" : 1
    }).insert(ignore_permissions=True)

    # send_sms(phone, f"Your OTP is {otp}")
    frappe.call(
        "erpnext.custom_utils.queue_sms",
        mobile=phone,
        message="Your OTP is " + str(otp)
        )

    return {"message": "OTP sent successfully"}

@frappe.whitelist(allow_guest=True)
def verify_otp(username, phone, otp):
    record = frappe.db.get_value(
        "Login OTP",
        {
            "user": username,
            "phone": strip_phone(phone),
            "otp": otp,
            "is_used": 0
        },
        ["name", "expires_at"],
        as_dict=True
    )

    if not record:
        frappe.throw("Invalid OTP")

    if record.expires_at < frappe.utils.now_datetime():
        frappe.throw("OTP expired")

    frappe.db.set_value("Login OTP", record.name, "is_used", 1)

    # Ensure API key
    api_key = frappe.db.get_value(
        "User",
        username,
        "api_key"
    )

    if not api_key:
        api_key = frappe.generate_hash(length=15)

    api_secret = frappe.generate_hash(length=15)

    user = frappe.get_doc("User", username)
    user.api_key = api_key
    user.api_secret = api_secret
    user.save(ignore_permissions=True, ignore_version=True)

    return {
        "message": "Login successful",
        "api_key": api_key,
        "api_secret": api_secret,
        "user": username
    }

