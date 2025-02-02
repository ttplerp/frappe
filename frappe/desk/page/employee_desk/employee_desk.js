frappe.provide('frappe.energy_points');

frappe.pages['employee-desk'].on_page_load = function (wrapper) {

	frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Employee Desk'),
	});

	let user_profile = new UserProfile(wrapper);
	$(wrapper).bind('show', () => {
		user_profile.show();
	});
};

class UserProfile {

	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.page = wrapper.page;
		this.sidebar = this.wrapper.find('.layout-side-section');
		this.main_section = this.wrapper.find('.layout-main-section');
	}

	show() {
		let route = frappe.get_route();
		this.user_id = route[1] || frappe.session.user;

		//validate if user
		if (route.length > 1) {
			frappe.db.exists('User', this.user_id).then(exists => {
				if (exists) {
					this.make_user_profile();
				} else {
					frappe.msgprint(__('User does not exist'));
				}
			});
		} else {
			this.user_id = frappe.session.user;
			this.make_user_profile();
		}
	}

	make_user_profile() {
		frappe.set_route('employee-desk', this.user_id);
		this.user = frappe.user_info(this.user_id);
		this.page.set_title(this.user.fullname);
		this.setup_transaction_link();
		this.main_section.empty().append(frappe.render_template('employee_desk'));
		this.render_user_details();
		if (this.user_id != "Administrator") {
			this.get_open_documents();
			// this.employee_leave_and_job_description();
			this.employee_leave_dashboard();
		}
		this.setup_punching_button();
		this.get_open_documents();
		// this.display_time();
	}

	setup_transaction_link() {
		this.$user_search_button = this.page.set_secondary_action('Home', () => {
			frappe.set_route('')
		});
	}

	//---------------------This section is for To Do List-----------------------------
	get_open_documents() {
		this.open_docs_config = {
			ToDo: { label: __('To Do') },
			Event: { label: __('Calendar'), route: 'List/Event/Calendar' }
		};
		frappe.ui.notifications.get_notification_config().then(r => {
			// this.open_document_list = r;
			this.$to_do_list = this.wrapper.find('.to-do-list');

			var item_list = `<table class="table table-bordered small" style="margin: 0px 0px 10px 0px;">
			<thead style="background-color: #2192be;">
				<tr style="color:white;">
					<th style="width: 80%" class="text-center">${__('Transaction')}</th>
					<th style="width: 20%" class="text-center">${__('Count')}</th>
				</tr>
			</thead>`;
			var open_docs = r.open_count_doctype;
			var docstatus = 'docstatus=Draft'

			for (const key in open_docs) {
				if (open_docs[key] && key != 'Employee Checkin' && key != 'Employee PF' && key != 'Payroll Entry' && key != 'Salary Slip') {
					const keyArr = key.split(" ")
					const ref = keyArr.join("-").toLowerCase()
					item_list += `<tr>
					<td style="width: 80%"><span class="indicator red"></span>
					<a class = "link-content" href="/app/${ref}?${docstatus}" target="_blank">${key}
					</a></td>
					<td class="text-center"><span class="badge" style="background: red; width: 20% color: white;">${open_docs[key]}</span></td>
					</tr>`;
				}
			}
			item_list += '</table>'
			this.$to_do_list.html(item_list);
		});
	}
	//-------------------------------End--------------------------------------------

	employee_attendance_dashboard(month) {
		let $attendance_dashboard = this.wrapper.find('.attendance-dashboard');
		let current_year = this.get_year(frappe.datetime.now_date());
		$attendance_dashboard.empty();
		if (this.user_id) {
			frappe.call({
				method: "frappe.desk.page.employee_desk.employee_desk.get_checkin_data",
				async: false,
				args: {
					user: this.user_id,
					month: month,
				},
				callback: function (r) {
					if (r.message.length > 0) {
						let html = $(__(`
						<table class="table table-bordered small" style="margin: 0px 0px 20px 0px;">
							<thead style="background-color: #9badf052;">
								<tr>
									<th style="width: 20%" class="text-center">${__('Date')}</th>
									<th style="width: 20%" class="text-center">${__('Office In')}</th>
									<th style="width: 20%" class="text-center">${__('Lunch Out')}</th>
									<th style="width: 20%" class="text-center">${__('Lunch In')}</th>
									<th style="width: 20%" class="text-center">${__('Office Out')}</th>
								</tr>
							</thead>
							<tbody style="background-color: white;">
							`));
						for (const [key, value] of Object.entries(r.message)) {

							let office_in_color = "color:#36414c";
							let lunch_out_color = "color:#36414c";
							let lunch_in_color = "color:#36414c";
							let office_out_color = "color:#36414c";

							if (value["office_in"] == "Not Punch")
								office_in_color = "color:red";
							if (value["lunch_out"] == "Not Punch")
								lunch_out_color = "color:red";
							if (value["lunch_in"] == "Not Punch")
								lunch_in_color = "color:red";
							if (value["office_out"] == "Not Punch")
								office_out_color = "color:red";

							html.append($(__(`
										<tr>
											<td>${value["date"]}</td>
											<td class="text-right" style=${office_in_color}>${value["office_in"]}</td>
											<td class="text-right" style=${lunch_out_color}>${value["lunch_out"]}</td>
											<td class="text-right" style=${lunch_in_color}>${value["lunch_in"]}</td>
											<td class="text-right" style=${office_out_color}>${value["office_out"]}</td>
										</tr>
								`)));
						}
						html.append($(__(`
							</tbody>
							</table>
							`)));
						$attendance_dashboard.append(html);
					}
					else {
						let html = $(__(`<p style="margin-top: 30px; color:red;"> No Checkin records in ${month}, ${current_year}. </p>`));
						$attendance_dashboard.append(html);
					}
				}
			});
		}
	}

	get_year(date_str) {
		return date_str.substring(0, date_str.indexOf('-'));
	}

	render_line_chart() {
		this.line_chart_filters = { 'user': this.user_id };
		this.line_chart_config = {
			timespan: 'Last Month',
			time_interval: 'Daily',
			type: 'Line',
			value_based_on: 'points',
			chart_type: 'Sum',
			document_type: 'Energy Point Log',
			name: 'Energy Points',
			width: 'half',
			based_on: 'creation'
		};

		this.line_chart = new frappe.Chart('.performance-line-chart', {
			title: 'Energy Points',
			type: 'line',
			height: 200,
			data: {
				labels: [],
				datasets: [{}]
			},
			colors: ['green'],
			axisOptions: {
				xIsSeries: 1
			}
		});
		this.update_line_chart_data();
		this.create_line_chart_filters();
	}

	disciplinary_records() {
		let $disciplinary_records = this.wrapper.find('.disciplinary-records');
		if (this.user_id) {
			frappe.call({
				method: "frappe.desk.page.employee_desk.employee_desk.get_disciplinary_records",
				async: false,
				args: {
					user: this.user_id,
				},
				callback: function (r) {
					if (r.message.length > 0) {
						let html = $(__(`
						<table class="table table-bordered small" style="margin: 0px 0px 20px 0px;">
							<thead style="background-color: #9badf052;">
								<tr>
									<th style="width: 20%" class="text-center">${__('Disciplinary Action Taken')}</th>
									<th style="width: 20%" class="text-center">${__('Nature')}</th>
									<th style="width: 20%" class="text-center">${__('From Date')}</th>
									<th style="width: 20%" class="text-center">${__('Complaint Frequency')}</th>
									<th style="width: 10%" class="text-center">${__('Action Taken')}</th>
									<th style="width: 10%" class="text-center">${__('Link')}</th>
								</tr>
							</thead>
							<tbody style="background-color: white;">
							`));
						for (const [key, value] of Object.entries(r.message)) {
							html.append($(__(`
										<tr>
											<td class="text-right">${value["disciplinary_action_taken"]}</td>
											<td class="text-right">${value["nature"]}</td>
											<td class="text-right">${value["from_date"]}</td>
											<td class="text-right">${value["complaint_frequency"]}</td>
											<td class="text-right">${value["action_taken"]}</td>
											<td class="text-right"><a href="#Form/Employee%20Disciplinary%20Record/${value["disciplinary_record"]}">${value["disciplinary_record"]}</td>
										</tr>
								`)));
						}
						html.append($(__(`
							</tbody>
							</table>
							`)));
						$disciplinary_records.append(html);
					}
					else {
						let html = $(__(`<p style="margin-top: 30px; color:red;">No Disciplinary Record.</p>`));
						$disciplinary_records.append(html);
					}
				}
			});
		}
	}

	get_year(date_str) {
		return date_str.substring(0, date_str.indexOf('-'));
	}

	create_attendance_dashboard_filters() {
		let filters = [
			{
				label: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
					"December"][frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth()],
				options: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
				action: (selected_item) => {
					this.employee_attendance_dashboard(selected_item);
				}
			},
		];
		this.render_chart_filters(filters, '.filters-container');
	}
	//New
	create_training_dashboard_filters() {
		let filters = [
			{
				label: this.get_year(frappe.datetime.now_date()),
				options: this.get_years_since_creation(),
				action: (selected_item) => {
					this.employee_trainings(frappe.datetime.obj_to_str(selected_item));
				}
			},
		];
		this.render_chart_filters(filters, '.training_filters-container');
	}

	get_years_since_creation() {
		//Get years since user account created
		this.user_creation = frappe.boot.user.creation;
		let creation_year = this.get_year(this.user_creation);
		let current_year = this.get_year(frappe.datetime.now_date());
		let years_list = [];
		for (var year = current_year; year >= creation_year; year--) {
			years_list.push(year);
		}
		return years_list;
	}


	render_chart_filters(filters, container, append) {
		filters.forEach(filter => {
			let chart_filter_html = `<div class="chart-filter pull-right">
				<a class="dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
					<button class="btn btn-default btn-xs">
						<span class="filter-label">${filter.label}</span>
						<span class="caret"></span>
					</button>
				</a>`;
			let options_html;

			if (filter.fieldnames) {
				options_html = filter.options.map((option, i) =>
					`<li><a data-fieldname = "${filter.fieldnames[i]}">${option}</a></li>`).join('');
			} else {
				options_html = filter.options.map(option => `<li><a>${option}</a></li>`).join('');
			}

			let dropdown_html = chart_filter_html + `<ul class="dropdown-menu">${options_html}</ul></div>`;
			let $chart_filter = $(dropdown_html);

			if (append) {
				$chart_filter.prependTo(this.wrapper.find(container));
			} else $chart_filter.appendTo(this.wrapper.find(container));

			$chart_filter.find('.dropdown-menu').on('click', 'li a', (e) => {
				let $el = $(e.currentTarget);
				let fieldname;
				if ($el.attr('data-fieldname')) {
					fieldname = $el.attr('data-fieldname');
				}
				let selected_item = $el.text();
				$el.parents('.chart-filter').find('.filter-label').text(selected_item);
				filter.action(selected_item, fieldname);
			});
		});

	}

	//---------------------Inserting Employee Checkin----------------------------
	make_employee_checkin(checkin_type, half_day, half_day_leave) {
		var ct = ""
		if (checkin_type == "Office IN" && half_day == 0 && half_day_leave == 0) {
			ct = "Lunch OUT"
		}
		else if (checkin_type == "Lunch OUT" && half_day == 0) {
			ct = "Lunch IN"
		}
		else if (checkin_type == "Lunch IN") {
			ct = "Office OUT"
		}
		else if ((half_day == 1 || half_day_leave == 1) && checkin_type == "Office IN") {
			ct = "Office OUT"
		}
		else {
			ct = "Office IN"
		}
		frappe.call({
			method: "frappe.desk.page.employee_desk.employee_desk.get_employee_info",
			args: ({ "user": frappe.session.user, "checkin_type": ct, "half_day": half_day }),
			callback: function (r) {
				if (r.message) {
					if ((r.message[0].flag == 1 && ct == "Office IN") || (r.message[0].oo_flag == 1 && ct == "Office OUT")) {
						let reason_dialog = new frappe.ui.Dialog({
							title: __('Late coming/Early Exit Reason'),
							fields: [
								{
									fieldtype: 'Small Text',
									fieldname: 'reason',
									label: 'Reason',
									reqd: 1,
								}
							],
							primary_action: values => {
								reason_dialog.disable_primary_action();
								frappe.xcall('frappe.desk.page.employee_desk.employee_desk.make_employee_checkin', {
									"employee": r.message[0].employee,
									"employee_name": r.message[0].employee_name,
									"shift_type": r.message[0].shift_type,
									"time": r.message[0].time,
									"time_difference": r.message[0].time_difference,
									reason: values['reason'],
									checkin_type: ct
								}).then(user => {
									reason_dialog.hide();
								}).finally(() => {
									reason_dialog.enable_primary_action();
								});
								let alert_dialog = new frappe.ui.Dialog({
									title: 'Your Record is updated successfully',
									primary_action: values => {
										alert_dialog.disable_primary_action();
										window.location.reload()
									},
									primary_action_label: 'OK'
								});
								alert_dialog.show();
							},
							primary_action_label: __('Save')
						});
						reason_dialog.show();
					}
					else {
						frappe.confirm(
							__('Are you sure?'),
							function () {
								frappe.call({
									method: "frappe.desk.page.employee_desk.employee_desk.make_employee_checkin",
									args: {
										"employee": r.message[0].employee,
										"employee_name": r.message[0].employee_name,
										"shift_type": r.message[0].shift_type,
										"time": r.message[0].time,
										"time_difference": r.message[0].time_difference,
										checkin_type: ct
									},
									callback: function (r) {
										// msgprint('Your Record is updated successfully');
										window.location.reload();
									}
								});
							},
							function () {
							}
						)
					}
				}
			}
		})
	}
	//-----------------------------End-----------------------------------

	edit_profile() {
		let edit_profile_dialog = new frappe.ui.Dialog({
			title: __('Edit Profile'),
			fields: [
				{
					fieldtype: 'Attach Image',
					fieldname: 'user_image',
					label: 'Profile Image',
				},
				{
					fieldtype: 'Data',
					fieldname: 'interest',
					label: 'Interests',
				},
				{
					fieldtype: 'Column Break'
				},
				{
					fieldtype: 'Data',
					fieldname: 'location',
					label: 'Location',
				},
				{
					fieldtype: 'Section Break',
					fieldname: 'Interest',
				},
				{
					fieldtype: 'Small Text',
					fieldname: 'bio',
					label: 'Bio',
				}
			],
			primary_action: values => {
				edit_profile_dialog.disable_primary_action();
				frappe.xcall('frappe.desk.page.employee_desk.employee_desk.update_profile_info', {
					profile_info: values
				}).then(user => {
					user.image = user.user_image;
					this.user = Object.assign(values, user);
					edit_profile_dialog.hide();
					this.render_user_details();
				}).finally(() => {
					edit_profile_dialog.enable_primary_action();
				});
			},
			primary_action_label: __('Save')
		});

		edit_profile_dialog.set_values({
			user_image: this.user.image,
			location: this.user.location,
			interest: this.user.interest,
			bio: this.user.bio
		});
		edit_profile_dialog.show();
	}

	render_user_details() {
		this.sidebar.empty().append(frappe.render_template('employee_desk_sidebar', {
			user_image: frappe.avatar(this.user_id, 'avatar-frame', 'user_image', this.user.image),
			user_abbr: this.user.abbr,
			user_location: this.user.location,
			user_interest: this.user.interest,
			user_bio: this.user.bio,
		}));

		this.setup_user_profile_links();
	}

	// Sidebar Links
	setup_user_profile_links() {
		if (this.user_id !== frappe.session.user) {
			this.wrapper.find('.profile-links').hide();
		} else {
			this.wrapper.find('.edit-profile-link').on('click', () => {
				this.edit_profile();
			});

			this.wrapper.find('.transaction-link').on('click', () => {
				this.go_to_desk();
			});
		}
	}

	go_to_desk() {
		frappe.set_route('');
	}

	// Enabling and disabling employee checkin button
	setup_punching_button() {
		this.wrapper.find('.office-in-button').hide();
		this.wrapper.find('.lunch-out-button').hide();
		this.wrapper.find('.lunch-in-button').hide();
		this.wrapper.find('.office-out-button').hide();
	}

	get_display_time() {
		return frappe.xcall("frappe.desk.page.employee_desk.employee_desk.get_display_time", {
			async: false,
		}).then(r => {
			this.d_time = r[0].d_time;
		});
	}

	display_time() {
		let $display_t = this.wrapper.find('.display-time');

		this.get_display_time().then(() => {
			let html = $(__(`<span>${this.d_time}</span>`, [this.d_time]));
			setInterval(() => this.display_time(), 1000)

			$display_t.html(html);
		});
	}

	get_checkin_info() {
		return frappe.xcall('frappe.desk.page.employee_desk.employee_desk.get_checkin_info', {
			user: this.user_id,
		}).then(r => {
			this.office_in = r[0].office_in;
			this.lunch_out = r[0].lunch_out;
			this.lunch_in = r[0].lunch_in;
			this.office_out = r[0].office_out;
			this.date = r[0].date;
		});
	}

	checkin_info() {
		let $checkin_details = this.wrapper.find('.checkin_details');

		this.get_checkin_info().then(() => {
			let html = $(__(`<p style="color:#1f1e1e; font-size:16px; "><b>${__('Date: ')}</b><span class="rank"><b>${this.date}</b></span></p>
					<p style="color:#15F906; font-size:14px;"><b>${__('Office In: ')}</b><span class="rank"><b>${this.office_in}</b></span></p>
					<p style="color:#bba00a; font-size:14px;"><b>${__('Lunch Out: ')}</b><span class="rank"><b>${this.lunch_out}</b></span></p>
					<p style="color:#bba00a; font-size:14px;"><b>${__('Lunch In: ')}</b><span class="rank"><b>${this.lunch_in}</b></span></p>
					<p style="color:#f44336; font-size:14px;"><b>${__('Office Out: ')}</b><span class="rank"><b>${this.office_out}</b></span></p>
				`, [this.date, this.office_in, this.lunch_out, this.lunch_in, this.office_out]));

			$checkin_details.append(html);
		});
	}

	get_job_description() {
		return frappe.xcall('frappe.desk.page.employee_desk.employee_desk.get_job_description', {
			user: this.user_id,
		}).then(r => {
			this.job_description = r[0].job_description;
		});
	}

	basic_emp_info() {
		let $b_emp_info = this.wrapper.find('.b-emp-info');

		this.get_emp_info().then(() => {
			let html = $(__(`
			<p style="font-size:14px;"><b>${__('EID: ')}</b><a href="#Form/Employee/${this.eid}"><span title="Go to Employee Master">${this.eid}</span></a></p>
			<p style="font-size:14px;"><b>${__('Grade: ')}</b><span class="rank">${this.grade}</span></p>
			<p style="font-size:14px;"><b>${__('Designation: ')}</b><span class="rank">${this.designation}</span></p>
		`, [this.eid, this.grade, this.designation]));

			$b_emp_info.append(html);
		});
	}
}
