from datetime import datetime

import frappe
from frappe.query_builder import Interval, Order
from frappe.query_builder.functions import Date, Sum, UnixTimestamp
from frappe.utils import getdate, nowdate, cint, flt
import calendar
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

@frappe.whitelist()
def get_employee_info(user=None, checkin_type=None, half_day=None):
	if not user: user = frappe.session.user
	FMT = '%H:%M:%S'
	data = []
	flag = 0
	office_out_flag = 0
	date = datetime.strptime(str(nowdate()), "%Y-%m-%d")
	t = datetime.now().time().strftime(FMT)
	time = datetime.strptime(str(t),FMT)
	emp = frappe.db.sql("""
				select e.name as employee, e.employee_name, e.department,
    			ifnull((select b.shift_type from `tabAssign Shift` b, `tabShift Details` sd, `tabShift Type` st where sd.parent = b.name and sd.employee = e.employee and b.shift_type = st.name and MONTHNAME('{1}') = b.month and YEAR('{1}') = b.fiscal_year and sd.{2} = 1 and b.docstatus = 1),e.default_shift) as shift_type,
				e.division, e.section, e.designation
				from `tabEmployee` e
				where e.user_id = "{3}"
	""".format(time, date, str(date.day), user), as_dict=True)
	# frappe.throw(str(emp))
 
	leave = frappe.db.sql("""
		select name from `tabLeave Application` where half_day = 1 and employee = '{0}' and '{1}' between from_date and to_date and docstatus = 1
					""".format(emp[0].employee, date), as_dict=True)
	# frappe.throw(str(leave))

	att_request = frappe.db.sql("""
		select name from `tabAttendance Request` where employee = '{0}'
		and '{1}' between from_date and to_date and half_day = 1
    """.format(emp[0].employee, date.date()), as_dict=1)
	# frappe.throw(str(att_request))

	if leave and leave[0].name != None and leave[0].name != '' and emp[0].shift_type == "General Shift":
		leave_type = frappe.db.get_value("Leave Application",leave[0].name,"half_day_type")
		if leave_type == "Second Half":
			actual_start_time = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "start_time")), FMT)
			actual_start_time = actual_start_time.time()
			actual_et = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "first_half_time")),FMT)
			actual_end_time = actual_et.time()
		elif leave_type == "First Half":
			actual_st = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "second_half_time")),FMT)
			actual_start_time = actual_st.time()
			actual_end_time = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "end_time")),FMT)
			actual_end_time = actual_end_time.time()
	elif att_request and att_request[0].name != None and att_request[0].name != '':
		half_day_type = frappe.db.get_value("Attendance Request", att_request[0].name,"half_day_type")
		if half_day_type == "Second Half":
			actual_start_time = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "start_time")), FMT)
			actual_start_time = actual_start_time.time()
			actual_et = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "first_half_time")),FMT)
			actual_end_time = actual_et.time()
		elif half_day_type == "First Half":
			actual_st = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "second_half_time")),FMT)
			actual_start_time = actual_st.time()
			actual_end_time = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "end_time")),FMT)
			actual_end_time = actual_end_time.time()
	elif int(half_day) == 1:
		actual_start_time = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "start_time")), FMT)
		actual_start_time = actual_start_time.time()
		actual_et = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "first_half_time")),FMT)
		actual_end_time = actual_et.time()
	else:
		if not emp[0].shift_type:
			emp[0].shift_type="General Shift"
		actual_start_time = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "start_time")),FMT)
		actual_start_time = actual_start_time.time()
		actual_end_time = datetime.strptime(str(frappe.db.get_value("Shift Type", emp[0].shift_type, "end_time")),FMT)
		actual_end_time = actual_end_time.time()

	ct = checkin_type.split(" ")

	if ct[0] == "Office" and ct[1] == "IN":
		if not emp[0].shift_type:
			emp[0].shift_type="General Shift"
		if time.time() > actual_end_time:
			frappe.throw("Your {shift} has Expired at {actual_end_time} ".format(shift =emp[0].shift_type ,actual_end_time=actual_end_time),title="Cannot Checkin")
		tdelta = time - datetime.strptime(str(actual_start_time), FMT)
	elif ct[0] == "Office" and ct[1] == "OUT":
		tdelta = datetime.strptime(str(actual_end_time), FMT) - time
	else:
		tdelta = 0



	if time.time() > actual_start_time:
		flag = 1
		if tdelta != 0:
			time_difference = (tdelta.seconds/60/60)
		else:
			time_difference = 0
	else:
		time_difference = 0

	if time.time() < actual_end_time:
		office_out_flag = 1
	else:
		time_difference = 0

	data.append({"employee": emp[0].employee, "employee_name": emp[0].employee_name, "shift_type": emp[0].shift_type, "time":str(time.time()), "time_difference": flt(time_difference,2), "actual_start_time":str(actual_start_time), "flag": flag, "oo_flag":office_out_flag})

	return data if data else data
@frappe.whitelist()
def make_employee_checkin(employee, employee_name, shift_type, time, time_difference, reason=None, checkin_type = None):
	if checkin_type != "":
		ct = str(checkin_type).split(" ")
		doc = frappe.new_doc("Employee Checkin")
		doc.employee = employee
		doc.emplyoee_name = frappe.db.get_value("Employee", employee, "employee_name")
		doc.log_type = ct[1]
		doc.type = ct[0]
		doc.shift = shift_type
		doc.date = datetime.strptime(str(nowdate()), "%Y-%m-%d")
		doc.time_difference = flt(time_difference, 2)
		if reason != None:
			doc.reason = reason
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.new_doc("Employee Checkin")
		doc.employee = employee
		doc.emplyoee_name = frappe.db.get_value("Employee", employee, "employee_name")
		doc.log_type = "IN"
		doc.type = "Office"
		doc.shift = shift_type
		doc.date = datetime.strptime(str(nowdate()), "%Y-%m-%d")
		doc.time_difference = flt(time_difference, 2)
		if reason != None:
			doc.reason = reason
		doc.save(ignore_permissions=True)

@frappe.whitelist()
def get_energy_points_heatmap_data(user, date):
	try:
		date = getdate(date)
	except Exception:
		date = getdate()

	eps_log = frappe.qb.DocType("Energy Point Log")

	return dict(
		frappe.qb.from_(eps_log)
		.select(UnixTimestamp(Date(eps_log.creation)), Sum(eps_log.points))
		.where(eps_log.user == user)
		.where(eps_log["type"] != "Review")
		.where(Date(eps_log.creation) > Date(date) - Interval(years=1))
		.where(Date(eps_log.creation) < Date(date) + Interval(years=1))
		.groupby(Date(eps_log.creation))
		.orderby(Date(eps_log.creation), order=Order.asc)
		.run()
	)


@frappe.whitelist()
def get_display_time():
	d_time = []
	curr_time = frappe.format_value(now(),{'fieldtype':'Time'})
	d_time.append({"d_time": curr_time})
	# frappe.throw(d_time)
	return d_time

@frappe.whitelist()
def get_checkin_info(user):
	data = []
	office_in = lunch_out = lunch_in = office_out = "00:00:00"
	cur_date = datetime.strptime(str(nowdate()), "%Y-%m-%d")

	checkin_data = frappe.db.sql("""
				select ec.type,ec.log_type,date_format(ec.date, '%d-%m-%Y') as att_date,time_format(ec.time, "%H:%i %p") as att_time
				from `tabEmployee Checkin` ec
				where ec.date = "{}" and ec.owner = "{}"
	""".format(cur_date, user), as_dict=True)

	for a in checkin_data:
		if a.type == "Office" and a.log_type == "IN":
			office_in = a.att_time
		elif a.type == "Lunch" and a.log_type == "OUT":
			lunch_out = a.att_time
		elif a.type == "Lunch"  and a.log_type == "IN":
			lunch_in = a.att_time
		elif a.type == "Office" and a.log_type == "OUT":
			office_out =a.att_time

	data.append({"office_in": office_in, "lunch_out": lunch_out, "lunch_in": lunch_in, "office_out": office_out, "date": str(cur_date).split(' ')[0]})

	return data

@frappe.whitelist()
def get_checkin_data(user, month):
	# frappe.throw(month)
	default_shift = frappe.db.get_value("Employee",{'user_id':user},"default_shift")
	in_time = frappe.db.get_value("Shift Type", {'name': default_shift}, "start_time")
	out_time = frappe.db.get_value("Shift Type", {'name': default_shift}, "end_time")
	# frappe.throw(str(otime))
	data = []
	cur_date = datetime.strptime(str(nowdate()), "%Y-%m-%d")
	year = str(cur_date).split("-")[0]
	checkin_list = frappe.db.sql("""
				select ec.employee, date_format(ec.date, '%d-%m-%Y') as att_date, date_format(ec.date, '%M') as cmonth,
				date_format(ec.date, '%Y') as cyr
				from `tabEmployee Checkin` ec
				where  ec.owner = "{}"
				and date_format(ec.date, '%M') = "{}"
				and date_format(ec.date, '%Y') = "{}"
	""".format(user, month, year), as_dict=True)

	for b in checkin_list:		
		office_in = lunch_out = lunch_in = office_out = "Not Punch"
		employee = b.employee
		month = b.cmonth
		year = b.cyr
		checkin_data = frappe.db.sql("""
				select ec.type,ec.log_type,date_format(ec.date, '%d-%m-%Y') as att_date,time_format(ec.time, "%H:%i %p") as att_time
				from `tabEmployee Checkin` ec
				where  ec.employee = "{}"
				and date_format(ec.date, '%M') = "{}"
				and date_format(ec.date, '%Y') = "{}"
				""".format(employee, month, year), as_dict=True)
		for a in checkin_data:
			if b.att_date == a.att_date:
				if a.type == "Office" and a.log_type == "IN":
					office_in = a.att_time
				elif a.type == "Lunch" and a.log_type == "OUT":
					lunch_out = a.att_time
				elif a.type == "Lunch"  and a.log_type == "IN":
					lunch_in = a.att_time
				elif a.type == "Office" and a.log_type == "OUT":
					office_out = a.att_time
		data.append({"office_in": office_in, "lunch_out": lunch_out, "lunch_in": lunch_in, "office_out": office_out, "date": b.att_date})
	
	new_data = []
	for a in data:
		if a not in new_data:
			new_data.append(a)
	data = new_data
	#sorting the data based on date in descending
	data.sort(key=lambda r: r["date"], reverse=True)
	
	return data

@frappe.whitelist()
def get_employee_checkin_info(user=None):
	half_day = 0
	holiday_flag = 0
	half_day_leave = 0
	if not user: user = frappe.session.user
	date = datetime.strptime(str(nowdate()), "%Y-%m-%d")
	day = calendar.day_name[date.weekday()]
	# frappe.throw(str(date))
	if user not in ("Administrator","System Manager"):
		employee = frappe.db.get_value("Employee",{"user_id": user},"name")
		holiday_list = get_holiday_list_for_employee(employee)

		leave_details = frappe.db.sql("""
			select name, half_day from `tabLeave Application` where employee = '{0}'and '{1}' between from_date and to_date and half_day = 1
			and workflow_state = 'Approved'
		""".format(employee, date.date()))

		if leave_details:
			half_day_leave = 1
		if holiday_list:
			holidays = frappe.db.sql("""
					select a.holiday_date from `tabHoliday` a where a.parent = '{0}' and a.holiday_date = '{1}'
            	""".format(holiday_list, date), as_dict=1)

			if holidays:
				holiday_flag = 1

			# half_working_days = frappe.db.sql("""
			# 	select day from `tabHoliday List Days` where parent = '{0}'
        	# """.format(holiday_list), as_dict=1)
   
			flag = 0

			# for a in half_working_days:
			# 	if day == a.day and flag == 0:
			# 		half_day = 1
			# 		flag = 1
			if half_day == 0:
				attendance_request = frappe.db.sql("""
					select name from `tabAttendance Request` where employee = '{0}'
					and '{1}' >= from_date and '{1}' <= to_date and half_day = 1
					and docstatus = 1
                """.format(employee, date))
				if attendance_request:
					half_day = 1

	data = frappe.db.sql("""
				select ec.type,ec.log_type,ec.date as att_date,ec.time as att_time
				from `tabEmployee Checkin` ec
				where ec.date = "{}" and ec.owner = "{}" order by creation desc limit 1
	""".format(date, user), as_dict=True)
	if data:
		checkin_type = data[0].type+" "+data[0].log_type
	else:
		checkin_type = " "

	return checkin_type, half_day, holiday_flag, half_day_leave

@frappe.whitelist()
def get_holidays(employee, from_date, to_date, holiday_list = None):
	'''get holidays between two dates for the given employee'''
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)
	holidays = frappe.db.sql("""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %s and %s
		and h2.name = %s""", (from_date, to_date, holiday_list))[0][0]

	return holidays


@frappe.whitelist()
def get_energy_points_percentage_chart_data(user, field):
	result = frappe.get_all(
		"Energy Point Log",
		filters={"user": user, "type": ["!=", "Review"]},
		group_by=field,
		order_by=field,
		fields=[field, "ABS(sum(points)) as points"],
		as_list=True,
	)

	return {
		"labels": [r[0] for r in result if r[0] is not None],
		"datasets": [{"values": [r[1] for r in result]}],
	}


@frappe.whitelist()
def get_user_rank(user):
	month_start = datetime.today().replace(day=1)
	monthly_rank = frappe.get_all(
		"Energy Point Log",
		group_by="`tabEnergy Point Log`.`user`",
		filters={"creation": [">", month_start], "type": ["!=", "Review"]},
		fields=["user", "sum(points)"],
		order_by="sum(points) desc",
		as_list=True,
	)

	all_time_rank = frappe.get_all(
		"Energy Point Log",
		group_by="`tabEnergy Point Log`.`user`",
		filters={"type": ["!=", "Review"]},
		fields=["user", "sum(points)"],
		order_by="sum(points) desc",
		as_list=True,
	)

	return {
		"monthly_rank": [i + 1 for i, r in enumerate(monthly_rank) if r[0] == user],
		"all_time_rank": [i + 1 for i, r in enumerate(all_time_rank) if r[0] == user],
	}


@frappe.whitelist()
def update_profile_info(profile_info):
	profile_info = frappe.parse_json(profile_info)
	keys = ["location", "interest", "user_image", "bio"]

	for key in keys:
		if key not in profile_info:
			profile_info[key] = None

	user = frappe.get_doc("User", frappe.session.user)
	user.update(profile_info)
	user.save()
	return user


@frappe.whitelist()
def get_energy_points_list(start, limit, user):
	return frappe.db.get_list(
		"Energy Point Log",
		filters={"user": user, "type": ["!=", "Review"]},
		fields=[
			"name",
			"user",
			"points",
			"reference_doctype",
			"reference_name",
			"reason",
			"type",
			"seen",
			"rule",
			"owner",
			"creation",
			"revert_of",
		],
		start=start,
		limit=limit,
		order_by="creation desc",
	)
