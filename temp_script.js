
        // API connection config
        const API_URL = window.location.protocol === 'file:' ? 'http://127.0.0.1:5001' : '';
        
        // Cache object holding current state
        let currentUser = null;
        let activeUsers = []; // Stores list of users dynamically fetched
        let currentGuestViewRole = 'Admin';

        function getEffectiveUserRole() {
            if (currentUser && currentUser.role === 'Guest') {
                return currentGuestViewRole || 'Admin';
            }
            return currentUser ? currentUser.role : 'Intern';
        }

        function isTestUser(username, fullName) {
            const uname = (username || '').toLowerCase().trim();
            const fname = (fullName || '').toLowerCase().trim();
            return uname.startsWith('mgr_') ||
                   uname.startsWith('emp_') ||
                   uname.startsWith('int_') ||
                   uname.startsWith('user_') ||
                   uname.includes('test') ||
                   uname.includes('collab') ||
                   fname.includes('test') ||
                   fname.includes('collab') ||
                   fname.includes('pending intern') ||
                   (fname.startsWith('pending') && /\d/.test(fname)) ||
                   uname.includes('pending');
        }
        let editingLogId = null; // Holds the ID of the log currently being updated
        let currentTaskView = 'team'; // Tracks workspace view: 'team' vs 'my'
        
        let state = {
            logs: [],
            tasks: [],
            skills: [],
            feedback: [],
            notifications: []
        };

        const START_DATE = new Date("2026-06-22");

        // Helper: Fetch API wrapper with credentials (cookies)
        async function apiFetch(endpoint, options = {}) {
            options.credentials = 'include';
            if (options.body && typeof options.body === 'object') {
                options.body = JSON.stringify(options.body);
                options.headers = options.headers || {};
                options.headers['Content-Type'] = 'application/json';
            }
            const res = await fetch(`${API_URL}${endpoint}`, options);
            if (res.status === 401) {
                // Not authenticated, show auth view
                showAuthOverlay();
                throw new Error("Unauthorized access");
            }
            return res;
        }

        // Toggle Sign In vs Sign Up views
        function toggleAuthView(view) {
            if (view === 'signup') {
                document.getElementById('login-card').style.display = 'none';
                document.getElementById('signup-card').style.display = 'flex';
            } else {
                document.getElementById('signup-card').style.display = 'none';
                document.getElementById('login-card').style.display = 'flex';
            }
        }

        // Show Auth Overlay
        function showAuthOverlay() {
            document.getElementById('app-container').style.display = 'none';
            document.getElementById('auth-container').style.display = 'flex';
        }

        // Hide Auth Overlay
        function hideAuthOverlay() {
            document.getElementById('auth-container').style.display = 'none';
            document.getElementById('app-container').style.display = 'flex';
        }

        // UI Tabs Navigator and Tab Switching Helper
        function switchTab(tabId) {
            const item = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
            if (item) {
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                
                item.classList.add('active');
                document.getElementById(tabId).classList.add('active');

                const role = getEffectiveUserRole();
                const titles = {
                    'dashboard': role === 'Admin' ? 'Admin Control Panel' : (role === 'Manager' ? 'Manager Overview' : (role === 'Employee' ? 'Employee Workspace' : 'Internship Dashboard')),
                    'daily-logs': 'Daily Logs Tracker',
                    'activity-logs': 'Activity Updates Logs',
                    'tasks': 'Task & Project Tracker',
                    'skills': 'Skills & Learnings Log',
                    'feedback': 'Mentor & Supervisor Feedback',
                    'announcements': 'General Announcements Feed',
                    'direct-messages': 'Secure Private Messaging',
                    'leaves': 'Leave Management & Balances',
                    'employees-directory': 'Employees Directory',
                    'attendance-matrix': 'Attendance & Payroll Matrix'
                };
                const subtitles = {
                    'dashboard': role === 'Admin' ? 'Complete system overview and login tracking' : (role === 'Manager' ? 'Subordinate tracking & operations statistics' : (role === 'Employee' ? 'Personal progress & tasks tracking' : 'Dynamic Summary Analytics')),
                    'daily-logs': 'Daily check-in, deliverables, and progress logs',
                    'activity-logs': 'Review daily check-in, deliverables, and progress logs of Employees and Interns',
                    'tasks': 'Manage and update project deliverables',
                    'skills': 'Track online courses and proficiency changes',
                    'feedback': 'Chronological record of supervisor feedback and action items',
                    'announcements': 'Post messages, links, images, video, and audio notes to the entire team',
                    'direct-messages': 'End-to-End Encrypted (E2EE) secure direct chat',
                    'leaves': 'Apply for leaves, view balances, and manage team approvals',
                    'employees-directory': 'Browse and manage staff member profiles, designations, and leave balances',
                    'attendance-matrix': 'Review daily attendance statuses, set LOP days, and compute monthly payroll net salaries'
                };
                document.getElementById('tab-title').innerText = titles[tabId] || 'Workspace';
                document.getElementById('tab-subtitle').innerText = subtitles[tabId] || '';

                if (tabId === 'announcements') {
                    fetchAnnouncements();
                } else if (tabId === 'direct-messages') {
                    fetchDMUsersList();
                } else if (tabId === 'leaves') {
                    loadLeavesData();
                } else if (tabId === 'hosting-details') {
                    loadHostingDetails();
                } else if (tabId === 'employees-directory') {
                    loadEmployeesDirectory();
                } else if (tabId === 'attendance-matrix') {
                    setupAttendanceSelectors();
                    loadAttendanceMatrixData(true);
                } else {
                    fetchData(); // Only dynamically fetch latest workspace data for non-messaging tabs
                }
            }
        }

        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const tabId = item.dataset.tab;
                switchTab(tabId);
            });
        });

        // Guest View Switcher
        function switchGuestViewRole(newRole) {
            currentGuestViewRole = newRole;
            
            // Reconfigure sidebar layout, theme, and headers for the simulated role
            setupPortalForRole();
            
            // Check if current tab is still valid for this simulated role
            const activeTabItem = document.querySelector('.nav-item.active');
            let tabId = activeTabItem ? activeTabItem.dataset.tab : 'dashboard';
            
            // Intern/Employee don't have access to activity-logs and feedback
            if (newRole === 'Intern' || newRole === 'Employee') {
                if (tabId === 'activity-logs' || tabId === 'feedback') {
                    tabId = 'dashboard';
                }
            } else {
                // Admin/Manager don't have daily-logs or skills tabs
                if (tabId === 'daily-logs' || tabId === 'skills') {
                    tabId = 'dashboard';
                }
            }
            
            // Switch to the target tab
            switchTab(tabId);
        }

        // Excel Export Function
        function exportActivityLogsToExcel() {
            // Determine active view
            const view = currentActivityView; // 'employees', 'interns', or 'sessions'
            const activityFilter = document.getElementById('activity-user-filter');
            const selectedUser = activityFilter ? activityFilter.value : 'ALL';

            let csvContent = "";
            let filename = "";

            function escapeCsvValue(val) {
                if (val === null || val === undefined) return "";
                let str = String(val);
                // Escape double quotes
                str = str.replace(/"/g, '""');
                // Quote if it contains comma, double-quote, or newline
                if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
                    str = `"${str}"`;
                }
                return str;
            }

            if (view === 'sessions') {
                // EXPORT SESSION LOGS
                const role = getEffectiveUserRole();
                let rawLogs = (state.sessionLogs || []).filter(log => {
                    if (role === 'Admin') {
                        return log.role === 'Manager' || log.role === 'Employee' || log.role === 'Intern';
                    } else if (role === 'Manager') {
                        return log.role === 'Employee' || log.role === 'Intern' || log.username === currentUser.username;
                    }
                    return false;
                });
                rawLogs = rawLogs.filter(log => !isTestUser(log.username, log.full_name));
                if (selectedUser !== 'ALL') {
                    rawLogs = rawLogs.filter(log => (log.username || '').toLowerCase().trim() === selectedUser.toLowerCase().trim());
                }

                // Inject approved leaves
                let approvedLeaves = (state.leaveRequests || []).filter(r => r.status === 'Approved');
                approvedLeaves = approvedLeaves.filter(r => {
                    if (role === 'Admin') {
                        return r.role === 'Manager' || r.role === 'Employee' || r.role === 'Intern';
                    } else if (role === 'Manager') {
                        return r.role === 'Employee' || r.role === 'Intern' || r.username === currentUser.username;
                    }
                    return false;
                });
                if (selectedUser !== 'ALL') {
                    approvedLeaves = approvedLeaves.filter(r => (r.username || '').toLowerCase().trim() === selectedUser.toLowerCase().trim());
                }

                const virtualLogs = [];
                approvedLeaves.forEach(r => {
                    let start = new Date(r.start_date);
                    let end = new Date(r.end_date);
                    let curr = new Date(start);
                    while (curr <= end) {
                        const dateIso = curr.toISOString().split('T')[0];
                        const dateLocal = curr.toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
                        
                        const hasSession = rawLogs.some(log => 
                            log.username.toLowerCase().trim() === r.username.toLowerCase().trim() &&
                            new Date(log.login_time).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' }) === dateLocal
                        );
                        
                        if (!hasSession) {
                            virtualLogs.push({
                                username: r.username,
                                full_name: r.full_name,
                                role: r.role,
                                login_time: `${dateIso}T09:00:00`,
                                logout_time: `${dateIso}T09:00:00`,
                                isLeave: true,
                                leaveType: r.leave_type,
                                leaveDuration: r.leave_type === 'Hours' ? `${r.hours_requested} hrs` : `${r.days_requested} days`,
                                leaveReason: r.reason
                            });
                        }
                        curr.setDate(curr.getDate() + 1);
                    }
                });
                rawLogs = [...rawLogs, ...virtualLogs];

                // Group by username and local date (same logic as renderSessionAttendanceLogs)
                const groups = {};
                rawLogs.forEach(log => {
                    const loginDate = new Date(log.login_time);
                    const localDateStr = loginDate.toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
                    const key = `${log.username}_${localDateStr}`;
                    if (!groups[key]) {
                        groups[key] = {
                            username: log.username,
                            full_name: log.full_name,
                            role: log.role,
                            localDateStr: localDateStr,
                            sessions: [],
                            isLeave: log.isLeave || false,
                            leaveType: log.leaveType || null,
                            leaveDuration: log.leaveDuration || null,
                            leaveReason: log.leaveReason || null
                        };
                    }
                    if (!log.isLeave) {
                        groups[key].isLeave = false;
                    }
                    groups[key].sessions.push(log);
                });

                const aggregatedLogs = Object.values(groups);
                aggregatedLogs.forEach(group => {
                    group.sessions.sort((a, b) => new Date(a.login_time) - new Date(b.login_time));
                    group.earliestLoginTime = new Date(group.sessions[0].login_time);

                    // Scan for approved leaves for this user on this day
                    const matchingLeave = (state.leaveRequests || []).find(r => 
                        r.status === 'Approved' &&
                        r.username.toLowerCase().trim() === group.username.toLowerCase().trim() &&
                        new Date(r.start_date).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' }) === group.localDateStr
                    );
                    
                    if (matchingLeave) {
                        group.hasLeaveApplied = true;
                        group.leaveType = matchingLeave.leave_type;
                        group.leaveDuration = matchingLeave.leave_type === 'Hours' ? `${matchingLeave.hours_requested} hrs` : `${matchingLeave.days_requested} days`;
                        group.leaveReason = matchingLeave.reason;
                    }
                });
                aggregatedLogs.sort((a, b) => b.earliestLoginTime - a.earliestLoginTime);

                const headers = ["User", "Role", "Login Date", "Check-In Time", "Check-Out Time", "Active Duration", "Status", "Leave Type", "Leave Duration"];
                csvContent += headers.map(escapeCsvValue).join(",") + "\n";

                aggregatedLogs.forEach(group => {
                    let checkInTimeStr = '-';
                    let checkOutTimeStr = '-';
                    let durationStr = '-';
                    let status = '';
                    let leaveTypeStr = '';
                    let leaveDurationStr = '';

                    if (group.isLeave) {
                        checkInTimeStr = `Leave: ${group.leaveType}`;
                        checkOutTimeStr = '-';
                        durationStr = group.leaveDuration;
                        status = 'Approved Leave';
                        leaveTypeStr = group.leaveType;
                        leaveDurationStr = group.leaveDuration;
                    } else {
                        const firstSession = group.sessions[0];
                        const lastSession = group.sessions[group.sessions.length - 1];
                        const loginTimeObj = new Date(firstSession.login_time);
                        checkInTimeStr = loginTimeObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                        
                        if (!lastSession.logout_time) {
                            checkOutTimeStr = '-';
                            status = 'Active';
                        } else {
                            const logoutTimeObj = new Date(lastSession.logout_time);
                            checkOutTimeStr = logoutTimeObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                            status = 'Completed';
                        }

                        let totalDurationMs = 0;
                        group.sessions.forEach(s => {
                            const loginTime = new Date(s.login_time);
                            if (s.logout_time) {
                                totalDurationMs += (new Date(s.logout_time) - loginTime);
                            } else {
                                totalDurationMs += (new Date() - loginTime);
                            }
                        });

                        const diffMins = Math.round(totalDurationMs / 1000 / 60);
                        const hours = Math.floor(diffMins / 60);
                        const mins = diffMins % 60;
                        durationStr = hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;

                        if (group.hasLeaveApplied) {
                            status = 'Completed (Permission)';
                            leaveTypeStr = group.leaveType;
                            leaveDurationStr = group.leaveDuration;
                        }
                    }

                    const row = [
                        `${group.full_name} (@${group.username})`,
                        group.role,
                        group.localDateStr,
                        checkInTimeStr,
                        checkOutTimeStr,
                        durationStr,
                        status,
                        leaveTypeStr,
                        leaveDurationStr
                    ];
                    csvContent += row.map(escapeCsvValue).join(",") + "\n";
                });

                filename = `Session_Attendance_Logs_${selectedUser}_${new Date().toISOString().slice(0, 10)}.csv`;
            } else {
                // EXPORT WORK LOGS
                let logsToRender = state.logs.filter(log => {
                    const userObj = activeUsers.find(u => u.username.toLowerCase().trim() === (log.intern_name || '').toLowerCase().trim());
                    const userRole = userObj ? userObj.role : 'Intern';
                    if (selectedUser !== 'ALL' && (log.intern_name || '').toLowerCase().trim() !== selectedUser.toLowerCase().trim()) {
                        return false;
                    }
                    if (view === 'employees') {
                        return userRole === 'Employee';
                    } else {
                        return userRole === 'Intern';
                    }
                });

                const headers = ["User", "Date", "Check-In", "Check-Out", "Hours Worked", "Tasks Completed", "Deliverable Completed", "Blockers", "Skills Used", "Mood", "Additional Notes"];
                csvContent += headers.map(escapeCsvValue).join(",") + "\n";

                logsToRender.forEach(log => {
                    const userObj = activeUsers.find(u => u.username.toLowerCase().trim() === (log.intern_name || '').toLowerCase().trim());
                    const displayName = userObj ? `${userObj.full_name} (@${userObj.username})` : log.intern_name;
                    const moodVal = parseInt(log.daily_mood || 5);
                    const moodStr = moodVal === 5 ? '5 - Excellent' : moodVal === 4 ? '4 - Good' : moodVal === 3 ? '3 - Neutral' : moodVal === 2 ? '2 - Low' : '1 - Struggling';

                    const row = [
                        displayName,
                        log.date_logged,
                        log.check_in || '-',
                        log.check_out || '-',
                        `${log.hours_worked} hrs`,
                        log.tasks_completed,
                        log.deliverable_completed || 'No',
                        log.blockers || 'None',
                        log.skills_used || 'None',
                        moodStr,
                        log.additional_notes || ''
                    ];
                    csvContent += row.map(escapeCsvValue).join(",") + "\n";
                });

                const viewLabel = view === 'employees' ? 'Employees' : 'Interns';
                filename = `${viewLabel}_Work_Logs_${selectedUser}_${new Date().toISOString().slice(0, 10)}.csv`;
            }

            // Trigger download
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement("a");
            if (link.download !== undefined) {
                const url = URL.createObjectURL(blob);
                link.setAttribute("href", url);
                link.setAttribute("download", filename);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        }

        // Initialize Forms Dates
        const d = new Date();
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const todayStr = `${year}-${month}-${day}`;

        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yestYear = yesterday.getFullYear();
        const yestMonth = String(yesterday.getMonth() + 1).padStart(2, '0');
        const yestDay = String(yesterday.getDate()).padStart(2, '0');
        const yesterdayStr = `${yestYear}-${yestMonth}-${yestDay}`;

        document.getElementById('log_date').value = todayStr;
        document.getElementById('log_date').min = yesterdayStr;
        document.getElementById('log_date').max = todayStr;
        document.getElementById('task_due').value = todayStr;
        document.getElementById('task_due').min = todayStr; // Prevent selecting past dates
        document.getElementById('fb_date').value = todayStr;
        const fbFollowDateInput = document.getElementById('fb_followdate');
        if (fbFollowDateInput) {
            fbFollowDateInput.min = todayStr; // Prevent selecting past dates
        }

        // Custom Mood Rating Selection Handler
        document.querySelectorAll('#log_mood_group .rating-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#log_mood_group .rating-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        document.querySelectorAll('#edit_log_mood_group .rating-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('#edit_log_mood_group .rating-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Toast alert builder
        function showToast(message, type = 'success') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            const icon = type === 'success' ? 'fa-circle-check' : 'fa-circle-exclamation';
            toast.innerHTML = `<i class="fa-solid ${icon}"></i><span>${message}</span>`;
            container.appendChild(toast);
            setTimeout(() => {
                toast.classList.add('fade-out');
                setTimeout(() => toast.remove(), 300);
            }, 3500);
        }

        function openProfileModal(requireEmpId = false) {
            if (!currentUser) return;
            document.getElementById('profile_username').value = currentUser.username || '';
            document.getElementById('profile_fullname').value = currentUser.full_name || '';
            document.getElementById('profile_email').value = currentUser.email || '';
            document.getElementById('profile_empid').value = currentUser.employee_id || '';
            document.getElementById('profile_password').value = '';
            
            const alertEl = document.getElementById('profile-modal-alert');
            if (requireEmpId) {
                alertEl.style.display = 'block';
            } else {
                alertEl.style.display = 'none';
            }
            
            document.getElementById('profile-modal').style.display = 'flex';
        }

        function closeProfileModal() {
            document.getElementById('profile-modal').style.display = 'none';
        }

        async function handleProfileSubmit(e) {
            e.preventDefault();
            const submitBtn = e.target.querySelector('.btn-submit');
            submitBtn.disabled = true;
            
            const payload = {
                full_name: document.getElementById('profile_fullname').value,
                email: document.getElementById('profile_email').value,
                employee_id: document.getElementById('profile_empid').value
            };
            
            const password = document.getElementById('profile_password').value;
            if (password) {
                payload.password = password;
            }
            
            try {
                const res = await apiFetch(`/users/${currentUser.username}/profile`, {
                    method: 'PUT',
                    body: payload
                });
                
                if (res.ok) {
                    showToast("Profile settings saved successfully!", "success");
                    closeProfileModal();
                    
                    // Refresh current user cache
                    currentUser.full_name = payload.full_name;
                    currentUser.email = payload.email;
                    currentUser.employee_id = payload.employee_id;
                    
                    document.getElementById('user-display-name').innerText = currentUser.full_name;
                    fetchData();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to update profile", "error");
                }
            } catch (err) {
                showToast("Failed to connect to profile gateway", "error");
            } finally {
                submitBtn.disabled = false;
            }
        }

        function openEditSessionModal(username, fullName, dateStr, loginIso, logoutIso) {
            document.getElementById('edit_session_username').value = username;
            document.getElementById('edit_session_date_raw').value = dateStr;
            document.getElementById('edit_session_user_display').value = `${fullName} (${username})`;
            document.getElementById('edit_session_date_display').value = dateStr;
            
            // Format ISO times to local datetime-local input format (YYYY-MM-DDTHH:MM)
            const formatForInput = (isoStr) => {
                if (!isoStr) return '';
                const d = new Date(isoStr);
                const pad = (n) => String(n).padStart(2, '0');
                return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
            };
            
            document.getElementById('edit_session_login').value = formatForInput(loginIso);
            document.getElementById('edit_session_logout').value = formatForInput(logoutIso);
            
            document.getElementById('session-edit-modal').style.display = 'flex';
        }

        function closeEditSessionModal() {
            document.getElementById('session-edit-modal').style.display = 'none';
        }

        async function handleSessionEditSubmit(e) {
            e.preventDefault();
            const submitBtn = e.target.querySelector('.btn-submit');
            submitBtn.disabled = true;
            
            const payload = {
                username: document.getElementById('edit_session_username').value,
                date: document.getElementById('edit_session_date_raw').value,
                login_time: new Date(document.getElementById('edit_session_login').value).toISOString(),
                logout_time: new Date(document.getElementById('edit_session_logout').value).toISOString()
            };
            
            try {
                const res = await apiFetch('/session_logs/edit', {
                    method: 'PUT',
                    body: payload
                });
                
                if (res.ok) {
                    showToast("Attendance session log updated!", "success");
                    closeEditSessionModal();
                    fetchData();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to update session log", "error");
                }
            } catch (err) {
                showToast("Failed to update session log", "error");
            } finally {
                submitBtn.disabled = false;
            }
        }

        // Check authentication status on startup
        async function checkAuth() {
            try {
                const res = await apiFetch('/current_user');
                if (res.ok) {
                    currentUser = await res.json();
                    setupPortalForRole();
                    fetchData();
                    if (!currentUser.employee_id) {
                        setTimeout(() => {
                            showToast("Please update your Employee ID in your profile settings.", "warning");
                            openProfileModal(true);
                        }, 1500);
                    }
                } else {
                    showAuthOverlay();
                }
            } catch (err) {
                showAuthOverlay();
            }
        }

        function calculateHoursFromTime(checkInId, checkOutId, hoursId, force = false) {
            const role = getEffectiveUserRole();
            const hoursInput = document.getElementById(hoursId);
            if (!hoursInput) return;

            // Only run if force is true, or user is a Manager, or hoursInput is readOnly (which means it's a manager's log)
            if (!force && role !== 'Manager' && !hoursInput.readOnly) return;

            const checkInVal = document.getElementById(checkInId).value;
            const checkOutVal = document.getElementById(checkOutId).value;

            if (!checkInVal || !checkOutVal) return;

            const [inH, inM] = checkInVal.split(':').map(Number);
            const [outH, outM] = checkOutVal.split(':').map(Number);

            let diffMinutes = (outH * 60 + outM) - (inH * 60 + inM);
            if (diffMinutes < 0) {
                diffMinutes += 24 * 60; // overnight checkin/checkout calculation support
            }

            const diffHours = diffMinutes / 60;
            hoursInput.value = diffHours.toFixed(2);
        }

        // Setup layouts, forms and sidebars based on logged-in user's role
        function setupPortalForRole() {
            hideAuthOverlay();
            
            const role = getEffectiveUserRole();

            // Handle Guest View Mode Container visibility and badge
            const guestContainer = document.getElementById('guest-view-mode-container');
            if (guestContainer) {
                if (currentUser.role === 'Guest') {
                    guestContainer.style.display = 'flex';
                    const badge = document.getElementById('guest-mode-badge');
                    if (badge) {
                        badge.innerText = `${role} View`;
                        badge.className = 'badge';
                        if (role === 'Admin') badge.classList.add('badge-danger');
                        else if (role === 'Manager') badge.classList.add('badge-warning');
                        else if (role === 'Employee') badge.classList.add('badge-primary');
                        else badge.classList.add('badge-success');
                    }
                } else {
                    guestContainer.style.display = 'none';
                }
            }

            // Hide/show openCreateMemberModal button for Guests
            const createMemberBtn = document.querySelector('button[onclick="openCreateMemberModal()"]');
            if (createMemberBtn) {
                createMemberBtn.style.display = (currentUser.role === 'Guest') ? 'none' : 'flex';
            }

            // Disable all inputs/buttons in active forms if user is a Guest
            const formIds = ['logForm', 'skillForm', 'feedbackForm', 'announcementForm', 'taskForm', 'dmForm', 'createMemberForm'];
            formIds.forEach(id => {
                const form = document.getElementById(id);
                if (form) {
                    const elements = form.querySelectorAll('input, select, textarea, button');
                    elements.forEach(el => {
                        if (currentUser.role === 'Guest') {
                            el.disabled = true;
                            if (el.tagName === 'BUTTON') {
                                el.style.opacity = '0.5';
                                el.style.cursor = 'not-allowed';
                            }
                        } else {
                            el.disabled = false;
                            if (el.tagName === 'BUTTON') {
                                el.style.opacity = '';
                                el.style.cursor = '';
                            }
                        }
                    });
                }
            });

            // Apply role-based theme class to body and update branding
            document.body.className = ''; // Reset previous themes
            
            const logoTitle = document.getElementById('logo-title');
            const logoSubtitle = document.getElementById('logo-subtitle');
            
            let brandTitle = "Sanna Innovations Portal";
            let brandSubtitle = "Internship System";

            if (role === 'Admin') {
                document.body.classList.add('theme-admin');
                brandTitle = "Sanna Innovations Admin";
                brandSubtitle = "System Console";
            } else if (role === 'Manager') {
                document.body.classList.add('theme-manager');
                brandTitle = "Sanna Innovations Manager";
                brandSubtitle = "Team Management";
            } else if (role === 'Employee') {
                document.body.classList.add('theme-employee');
                brandTitle = "Sanna Innovations Employee";
                brandSubtitle = "Associate Portal";
            } else {
                document.body.classList.add('theme-intern');
            }

            if (logoTitle) logoTitle.innerText = brandTitle;
            if (logoSubtitle) logoSubtitle.innerText = brandSubtitle;

            // Set user profile footer info
            document.getElementById('user-display-name').innerText = currentUser.full_name;
            if (currentUser.role === 'Guest') {
                document.getElementById('user-display-role').innerText = `Guest View (${role} Mode)`;
            } else {
                document.getElementById('user-display-role').innerText = `${currentUser.role} (${currentUser.title || ''})`;
            }

            // Enforce visibility of navigation options
            if (role === 'Intern' || role === 'Employee') {
                document.getElementById('nav-logs').style.display = 'block';
                document.getElementById('nav-skills').style.display = 'block';
                document.getElementById('nav-tasks').style.display = 'block';
                document.getElementById('nav-activity-logs').style.display = 'none';
                document.getElementById('nav-employees-directory').style.display = 'none';
                document.getElementById('nav-attendance-matrix').style.display = 'none';
                document.getElementById('nav-hosting-details').style.display = 'none';
                
                // Move task creation panel to Tasks page & display it
                const taskGrid = document.querySelector('#tasks .grid-2');
                const assignPanel = document.getElementById('task-assign-panel');
                if (taskGrid && assignPanel) {
                    taskGrid.insertBefore(assignPanel, document.getElementById('tasks-list-panel'));
                    assignPanel.style.display = 'block';
                    assignPanel.style.marginTop = '0';
                }
                document.getElementById('tasks-list-panel').style.gridColumn = '';
                
                document.getElementById('feedback-form-panel').style.display = 'none';
                document.getElementById('feedback-list-panel').style.gridColumn = 'span 2';

                document.getElementById('dash-filter-panel').style.display = 'none';
                document.getElementById('team-roster-panel').style.display = 'none';
                document.getElementById('task-view-toggle-container').style.display = 'none';

                // Leave elements visibility
                if (role === 'Intern') {
                    document.getElementById('nav-leaves').style.display = 'none';
                } else {
                    document.getElementById('nav-leaves').style.display = 'block';
                }
                document.getElementById('leave-review-panel').style.display = 'none';
                document.getElementById('leave-team-balances-panel').style.display = 'none';
                document.getElementById('leave-history-panel').style.gridColumn = 'span 1';
                document.querySelector('#leaves .grid-2').style.gridTemplateColumns = '1fr';
            } else if (role === 'Manager') {
                // Manager needs separate workspace for daily logs, but also reviews subordinates
                document.getElementById('nav-logs').style.display = 'block'; // Show personal logs
                document.getElementById('nav-skills').style.display = 'none';
                document.getElementById('nav-tasks').style.display = 'none';
                document.getElementById('nav-activity-logs').style.display = 'block';
                document.getElementById('nav-employees-directory').style.display = 'block';
                document.getElementById('nav-attendance-matrix').style.display = 'block';
                document.getElementById('nav-hosting-details').style.display = 'none';

                // Move task assignment panel to Activity Logs page & display it
                const activityLogsSection = document.getElementById('activity-logs');
                const assignPanel = document.getElementById('task-assign-panel');
                if (activityLogsSection && assignPanel) {
                    activityLogsSection.prepend(assignPanel);
                    assignPanel.style.display = 'block';
                    assignPanel.style.marginTop = '20px';
                }
                document.getElementById('tasks-list-panel').style.gridColumn = 'span 1';
                
                document.getElementById('feedback-form-panel').style.display = 'block';
                document.getElementById('feedback-list-panel').style.gridColumn = 'span 1';

                // Show Admin Overview filter panel on Dashboard
                document.getElementById('dash-filter-panel').style.display = 'block';
                document.getElementById('team-roster-panel').style.display = 'block';
                
                document.getElementById('task-view-toggle-container').style.display = 'flex';
                setTaskView('team'); // Reset view to team tasks by default

                // Leave elements visibility
                document.getElementById('nav-leaves').style.display = 'block';
                document.getElementById('leave-review-panel').style.display = 'block';
                document.getElementById('leave-team-balances-panel').style.display = 'block';
                document.getElementById('leave-history-panel').style.gridColumn = 'span 1';
                document.querySelector('#leaves .grid-2').style.gridTemplateColumns = 'repeat(auto-fit, minmax(400px, 1fr))';
            } else {
                // Admin
                document.getElementById('nav-logs').style.display = 'none';
                document.getElementById('nav-skills').style.display = 'none';
                document.getElementById('nav-tasks').style.display = 'none';
                document.getElementById('nav-activity-logs').style.display = 'block';
                document.getElementById('nav-employees-directory').style.display = 'block';
                document.getElementById('nav-attendance-matrix').style.display = 'block';
                document.getElementById('nav-hosting-details').style.display = 'block';

                // Move task assignment panel back to Activity Logs page & display it
                const activityLogsSection = document.getElementById('activity-logs');
                const assignPanel = document.getElementById('task-assign-panel');
                if (activityLogsSection && assignPanel) {
                    activityLogsSection.prepend(assignPanel);
                    assignPanel.style.display = 'block';
                    assignPanel.style.marginTop = '20px';
                }
                document.getElementById('tasks-list-panel').style.gridColumn = 'span 1';
                
                document.getElementById('feedback-form-panel').style.display = 'block';
                document.getElementById('feedback-list-panel').style.gridColumn = 'span 1';

                // Show Admin Overview filter panel on Dashboard
                document.getElementById('dash-filter-panel').style.display = 'block';
                document.getElementById('team-roster-panel').style.display = 'block';
                
                document.getElementById('task-view-toggle-container').style.display = 'none';
                setTaskView('team');

                // Leave elements visibility
                document.getElementById('nav-leaves').style.display = 'block';
                document.getElementById('leave-review-panel').style.display = 'block';
                document.getElementById('leave-team-balances-panel').style.display = 'block';
                document.getElementById('leave-history-panel').style.display = 'none';
                document.querySelector('#leaves .grid-2').style.gridTemplateColumns = '1fr';
            }

            // Customize create-task panel titles/buttons based on role
            const taskFormTitle = document.querySelector('#task-assign-panel .panel-title span');
            const taskSubmitBtn = document.querySelector('#task-assign-panel .btn-submit');
            if (role === 'Intern' || role === 'Employee') {
                if (taskFormTitle) taskFormTitle.innerText = "Create Task";
                if (taskSubmitBtn) taskSubmitBtn.innerHTML = '<i class="fa-solid fa-circle-plus"></i> Create Task';
            } else {
                if (taskFormTitle) taskFormTitle.innerText = "Create Project Task";
                if (taskSubmitBtn) taskSubmitBtn.innerHTML = '<i class="fa-solid fa-list-check"></i> Assign Task';
            }

            // Update main header text for active tab
            const activeTabItem = document.querySelector('.nav-item.active');
            const tabId = activeTabItem ? activeTabItem.dataset.tab : 'dashboard';
            const titles = {
                'dashboard': role === 'Admin' ? 'Admin Control Panel' : (role === 'Manager' ? 'Manager Overview' : (role === 'Employee' ? 'Employee Workspace' : 'Internship Dashboard')),
                'daily-logs': 'Daily Logs Tracker',
                'activity-logs': 'Activity Updates Logs',
                'tasks': 'Task & Project Tracker',
                'skills': 'Skills & Learnings Log',
                'feedback': 'Mentor & Supervisor Feedback'
            };
            const subtitles = {
                'dashboard': role === 'Admin' ? 'Complete system overview and login tracking' : (role === 'Manager' ? 'Subordinate tracking & operations statistics' : (role === 'Employee' ? 'Personal progress & tasks tracking' : 'Dynamic Summary Analytics')),
                'daily-logs': 'Daily check-in, deliverables, and progress logs',
                'activity-logs': 'Review daily check-in, deliverables, and progress logs of Employees and Interns',
                'tasks': 'Manage and update project deliverables',
                'skills': 'Track online courses and proficiency changes',
                'feedback': 'Chronological record of supervisor feedback and action items'
            };
            document.getElementById('tab-title').innerText = titles[tabId];
            document.getElementById('tab-subtitle').innerText = subtitles[tabId];

            // Initialize E2EE Keys
            initializeE2EE().catch(err => console.error("E2EE init error:", err));

            // Enforce Manager hours worked auto-calculation constraint
            const logHours = document.getElementById('log_hours');
            const editLogHours = document.getElementById('edit_log_hours');
            if (role === 'Manager') {
                if (logHours) {
                    logHours.readOnly = true;
                    logHours.style.background = 'rgba(255, 255, 255, 0.05)';
                    logHours.style.color = 'var(--text-muted)';
                    logHours.style.cursor = 'not-allowed';
                    logHours.title = '';
                }
                if (editLogHours) {
                    editLogHours.readOnly = true;
                    editLogHours.style.background = 'rgba(255, 255, 255, 0.05)';
                    editLogHours.style.color = 'var(--text-muted)';
                    editLogHours.style.cursor = 'not-allowed';
                    editLogHours.title = '';
                }
                // Compute initial values based on current inputs
                calculateHoursFromTime('log_checkin', 'log_checkout', 'log_hours');
            } else {
                if (logHours) {
                    logHours.readOnly = false;
                    logHours.style.background = '';
                    logHours.style.color = '';
                    logHours.style.cursor = '';
                    logHours.title = '';
                }
                if (editLogHours) {
                    editLogHours.readOnly = false;
                    editLogHours.style.background = '';
                    editLogHours.style.color = '';
                    editLogHours.style.cursor = '';
                    editLogHours.title = '';
                }
            }

            // Populate assignment select options dynamically
            populateDropdowns();
        }

        // Populate dropdown selectors dynamically from backend users list
        async function populateDropdowns() {
            try {
                const res = await apiFetch('/users');
                const allUsers = await res.json();
                activeUsers = allUsers.filter(u => !isTestUser(u.username, u.full_name));

                // Save currently selected values before rebuilding
                const dashFilter = document.getElementById('dash-user-filter');
                const previousDashVal = dashFilter ? dashFilter.value : 'ALL';

                const activityFilter = document.getElementById('activity-user-filter');
                const previousActivityVal = activityFilter ? activityFilter.value : 'ALL';

                const taskSelect = document.getElementById('task_intern_name');
                const previousTaskVal = taskSelect ? taskSelect.value : '';

                const fbSelect = document.getElementById('fb_intern_name');
                const previousFbVal = fbSelect ? fbSelect.value : '';

                // 1. Dashboard Filter options (Interns + Employees + Managers for Admin)
                dashFilter.innerHTML = '<option value="ALL">All Active Users</option>';
                
                // 2. Activity User Filter options
                if (activityFilter) {
                    activityFilter.innerHTML = '<option value="ALL">All Team Members</option>';
                }

                // 3. Task Assign To selector
                taskSelect.innerHTML = '<option value="">Choose the person...</option>';

                // 4. Feedback Target selector
                fbSelect.innerHTML = '<option value="">Choose the person...</option>';

                const role = getEffectiveUserRole();

                activeUsers.forEach(u => {
                    const optionHtml = `<option value="${u.username}">${escapeHTML(u.full_name)} (${u.role})</option>`;
                    
                    // Dashboard filter population based on user role
                    if (role === 'Admin') {
                        if (u.role === 'Manager' || u.role === 'Employee' || u.role === 'Intern') {
                            dashFilter.innerHTML += optionHtml;
                        }
                    } else if (role === 'Manager') {
                        if (u.role === 'Employee' || u.role === 'Intern') {
                            dashFilter.innerHTML += optionHtml;
                        }
                    }

                    // Activity filter population based on user role (Employee and Intern logs are visible to Admin/Manager)
                    if (activityFilter) {
                        if (role === 'Admin' || role === 'Manager') {
                            if (u.role === 'Employee' || u.role === 'Intern') {
                                activityFilter.innerHTML += optionHtml;
                            }
                        }
                    }

                    // Task assignment & Feedback target dropdown population based on user role
                    if (role === 'Admin') {
                        // Admin can assign to Manager, Employee, Intern
                        if (u.role === 'Manager' || u.role === 'Employee' || u.role === 'Intern') {
                            taskSelect.innerHTML += optionHtml;
                            fbSelect.innerHTML += optionHtml;
                        }
                    } else if (role === 'Manager') {
                        // Manager can assign to Employee, Intern
                        if (u.role === 'Employee' || u.role === 'Intern') {
                            taskSelect.innerHTML += optionHtml;
                            fbSelect.innerHTML += optionHtml;
                        }
                    } else if (role === 'Employee') {
                        // Employee can assign to Intern only or themselves
                        if (u.role === 'Intern' || u.username === currentUser.username) {
                            taskSelect.innerHTML += optionHtml;
                        }
                        if (u.role === 'Intern') {
                            fbSelect.innerHTML += optionHtml;
                        }
                    } else if (role === 'Intern') {
                        // Intern can only assign to themselves
                        if (u.username === currentUser.username) {
                            taskSelect.innerHTML += optionHtml;
                        }
                    }
                });

                // Restore previous selections
                if (dashFilter) {
                    dashFilter.value = previousDashVal;
                    if (dashFilter.value !== previousDashVal) {
                        // Attempt case-insensitive/trimmed match to prevent resetting when username casing differs
                        let found = false;
                        for (let i = 0; i < dashFilter.options.length; i++) {
                            if (dashFilter.options[i].value.toLowerCase().trim() === previousDashVal.toLowerCase().trim()) {
                                dashFilter.value = dashFilter.options[i].value;
                                found = true;
                                break;
                            }
                        }
                        if (!found) {
                            dashFilter.value = 'ALL';
                        }
                    }
                }
                if (activityFilter) {
                    activityFilter.value = previousActivityVal;
                    if (activityFilter.value !== previousActivityVal) {
                        let found = false;
                        for (let i = 0; i < activityFilter.options.length; i++) {
                            if (activityFilter.options[i].value.toLowerCase().trim() === previousActivityVal.toLowerCase().trim()) {
                                activityFilter.value = activityFilter.options[i].value;
                                found = true;
                                break;
                            }
                        }
                        if (!found) {
                            activityFilter.value = 'ALL';
                        }
                    }
                }
                if (taskSelect) {
                    if (role === 'Intern') {
                        taskSelect.value = currentUser.username;
                    } else if (role === 'Employee' && !previousTaskVal) {
                        taskSelect.value = currentUser.username;
                    } else {
                        taskSelect.value = previousTaskVal;
                    }
                }
                if (fbSelect) fbSelect.value = previousFbVal;

                renderTeamRoster();

            } catch (err) {
                console.error("Failed to load user rosters for dropdowns", err);
            }
        }

        // Render the Team Roster & User Management Table
        function renderTeamRoster() {
            const tbody = document.getElementById('team-roster-table-body');
            if (!tbody) return;
            tbody.innerHTML = '';

            const role = getEffectiveUserRole();

            activeUsers.forEach(u => {
                // Determine visibility in roster: Admin sees all users. Manager sees Employees and Interns.
                let visible = false;
                if (role === 'Admin') {
                    visible = true;
                } else if (role === 'Manager') {
                    if (u.role === 'Employee' || u.role === 'Intern') {
                        visible = true;
                    }
                }

                if (!visible) return;

                const tr = document.createElement('tr');
                
                // Set actions (Approve, Restrict, Delete buttons)
                let actionHtml = '';
                if (currentUser.role === 'Guest') {
                    actionHtml = `<span style="color: var(--text-muted); font-size: 12px; font-style: italic;">Read-Only</span>`;
                } else if (u.username === currentUser.username) {
                    actionHtml = `<span style="color: var(--text-muted); font-size: 13px; font-style: italic;">(You)</span>`;
                } else {
                    let canDelete = false;
                    if (role === 'Admin') {
                        canDelete = true; // Admin can delete any other user
                    } else if (role === 'Manager') {
                        if (u.role === 'Employee' || u.role === 'Intern') {
                            canDelete = true; // Manager can delete Employee and Intern
                        }
                    }

                    let approveBtn = '';
                    if (role === 'Admin' && !u.approved) {
                        approveBtn = `
                            <button class="btn btn-success btn-sm" onclick="approveUser('${u.id}', '${escapeHTML(u.full_name)}')">
                                <i class="fa-solid fa-check"></i> Approve
                            </button>
                        `;
                    }

                    let restrictBtn = '';
                    if (u.approved) {
                        let canRestrict = false;
                        if (role === 'Admin') {
                            canRestrict = true;
                        } else if (role === 'Manager') {
                            if (u.role === 'Employee' || u.role === 'Intern') {
                                canRestrict = true;
                            }
                        }

                        if (canRestrict) {
                            if (u.restricted) {
                                restrictBtn = `
                                    <button class="btn btn-success btn-sm" onclick="unrestrictUser('${u.id}', '${escapeHTML(u.full_name)}')">
                                        <i class="fa-solid fa-user-check"></i> Unrestrict
                                    </button>
                                `;
                            } else {
                                restrictBtn = `
                                    <button class="btn btn-warning btn-sm" onclick="restrictUser('${u.id}', '${escapeHTML(u.full_name)}')">
                                        <i class="fa-solid fa-user-slash"></i> Restrict
                                    </button>
                                `;
                            }
                        }
                    }

                    if (canDelete) {
                        actionHtml = `
                            <div style="display: flex; gap: 8px; justify-content: center; align-items: center;">
                                ${approveBtn}
                                ${restrictBtn}
                                <button class="btn btn-danger btn-sm" onclick="removeUser('${u.id}', '${escapeHTML(u.full_name)}')">
                                    <i class="fa-solid fa-trash-can"></i> Remove
                                </button>
                            </div>
                        `;
                    } else if (approveBtn || restrictBtn) {
                        actionHtml = `
                            <div style="display: flex; gap: 8px; justify-content: center; align-items: center;">
                                ${approveBtn}
                                ${restrictBtn}
                            </div>
                        `;
                    } else {
                        actionHtml = `<span style="color: var(--text-muted); font-size: 13px;">No Access</span>`;
                    }
                }

                // Render role badges or role select dropdown (Admin only, excluding the original main admin 'admin')
                let roleHtml = '';
                if (role === 'Admin' && u.username !== 'admin') {
                    const disabledAttr = currentUser.role === 'Guest' ? 'disabled' : '';
                    roleHtml = `
                        <select ${disabledAttr} onchange="updateUserRole('${u.id}', this.value)" style="padding: 6px 10px; font-size: 13px; border-radius: 8px; background: rgba(255,255,255,0.05); color: #fff; border: 1px solid var(--card-border); cursor: pointer; font-weight: 500; outline: none; width: auto;">
                            <option value="Intern" ${u.role === 'Intern' ? 'selected' : ''}>Intern</option>
                            <option value="Employee" ${u.role === 'Employee' ? 'selected' : ''}>Employee</option>
                            <option value="Manager" ${u.role === 'Manager' ? 'selected' : ''}>Manager</option>
                            <option value="Admin" ${u.role === 'Admin' ? 'selected' : ''}>Admin</option>
                        </select>
                    `;
                } else {
                    let badgeClass = 'badge-primary';
                    if (u.role === 'Admin') badgeClass = 'badge-danger';
                    else if (u.role === 'Manager') badgeClass = 'badge-warning';
                    else if (u.role === 'Employee') badgeClass = 'badge-primary';
                    else if (u.role === 'Intern') badgeClass = 'badge-success';
                    roleHtml = `<span class="badge ${badgeClass}">${u.role}</span>`;
                }

                // Render approval / account status badge
                let approvalHtml = '';
                if (!u.approved) {
                    approvalHtml = `<span class="badge badge-warning"><i class="fa-solid fa-user-clock"></i> Pending</span>`;
                } else if (u.restricted) {
                    approvalHtml = `<span class="badge badge-danger"><i class="fa-solid fa-user-slash"></i> Restricted</span>`;
                } else {
                    approvalHtml = `<span class="badge badge-success"><i class="fa-solid fa-user-check"></i> Approved</span>`;
                }

                // Calculate activity metrics
                let activityHtml = '';
                if (u.role === 'Admin' || u.role === 'Manager' || u.role === 'Employee') {
                    const assignedTasks = state.tasks.filter(t => t.assigned_by === u.username).length;
                    const feedbackReviews = state.feedback.filter(f => f.feedback_from === u.username).length;
                    activityHtml = `<span style="font-size:12px; color:var(--text-muted);">Assigned: ${assignedTasks} tasks, ${feedbackReviews} reviews</span>`;
                } else if (u.role === 'Intern') {
                    const myTasks = state.tasks.filter(t => t.intern_name && t.intern_name.toLowerCase().trim() === u.username.toLowerCase().trim()).length;
                    const loggedHours = state.logs.filter(l => l.intern_name && l.intern_name.toLowerCase().trim() === u.username.toLowerCase().trim()).length;
                    activityHtml = `<span style="font-size:12px; color:var(--text-muted);">${myTasks} tasks, ${loggedHours} logs</span>`;
                }

                // Render status badge
                const isOnline = u.status === 'Available';
                let timeDetailHtml = '';
                if (isOnline && u.last_login) {
                    timeDetailHtml = `<div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Active: ${formatSessionTime(u.last_login)}</div>`;
                } else if (!isOnline && u.last_logout) {
                    timeDetailHtml = `<div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Logout: ${formatSessionTime(u.last_logout)}</div>`;
                }
                const statusBadgeHtml = `
                    <span class="badge ${isOnline ? 'badge-success' : 'badge-primary'}" style="${isOnline ? '' : 'opacity: 0.6;'}">
                        <i class="fa-solid ${isOnline ? 'fa-circle-check' : 'fa-circle-xmark'}"></i> ${u.status || 'Logged Out'}
                    </span>
                    ${timeDetailHtml}
                `;

                tr.innerHTML = `
                    <td style="font-weight: 600;">${escapeHTML(u.full_name)}</td>
                    <td>
                        <div style="font-weight:600;">${escapeHTML(u.username)}</div>
                        <div style="font-size:11px; color:var(--text-muted);">${escapeHTML(u.email || '-')}</div>
                    </td>
                    <td style="font-weight:600; color:var(--primary);">${escapeHTML(u.employee_id || '-')}</td>
                    <td style="font-size:13px; color:var(--text-muted);">${escapeHTML(u.title || '-')}</td>
                    <td>${roleHtml}</td>
                    <td>${approvalHtml}</td>
                    <td>${activityHtml}</td>
                    <td>${statusBadgeHtml}</td>
                    <td style="text-align: center;">${actionHtml}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        function setTaskView(view) {
            currentTaskView = view;
            
            const btnTeam = document.getElementById('btn-view-team-tasks');
            const btnMy = document.getElementById('btn-view-my-tasks');
            
            if (btnTeam && btnMy) {
                if (view === 'team') {
                    btnTeam.classList.remove('btn-secondary');
                    btnTeam.classList.add('btn-primary');
                    btnMy.classList.remove('btn-primary');
                    btnMy.classList.add('btn-secondary');
                } else {
                    btnMy.classList.remove('btn-secondary');
                    btnMy.classList.add('btn-primary');
                    btnTeam.classList.remove('btn-primary');
                    btnTeam.classList.add('btn-secondary');
                }
            }
            
            renderTasks();
        }

        // Fetch logs, tasks, skills, feedback in parallel to optimize speed and resolve latency
        async function fetchData() {
            try {
                // Only fetch session logs for Admin and Manager roles
                let sessionLogsPromise = Promise.resolve([]);
                if (currentUser && (getEffectiveUserRole() === 'Admin' || getEffectiveUserRole() === 'Manager')) {
                    sessionLogsPromise = apiFetch('/session_logs').then(r => r.json());
                }

                const promises = [
                    apiFetch('/logs').then(r => r.json()),
                    apiFetch('/tasks').then(r => r.json()),
                    apiFetch('/skills').then(r => r.json()),
                    apiFetch('/feedback').then(r => r.json()),
                    apiFetch('/notifications').then(r => r.json()),
                    sessionLogsPromise,
                    apiFetch('/leaves/requests').then(r => r.json())
                ];

                const results = await Promise.all(promises);
                
                state.logs = results[0].filter(l => !isTestUser(l.intern_name, l.intern_fullname));
                state.tasks = results[1].filter(t => !isTestUser(t.intern_name));
                state.skills = results[2].filter(s => !isTestUser(s.intern_name));
                state.feedback = results[3].filter(f => !isTestUser(f.intern_name));
                
                const newNotifs = results[4].filter(n => !isTestUser(n.username) && !n.message.toLowerCase().includes('test'));
                state.sessionLogs = results[5].filter(s => !isTestUser(s.username, s.full_name));
                state.leaveRequests = results[6].filter(l => !isTestUser(l.username, l.full_name));

                // Show toasts for new notifications if not the initial load
                if (state.notifications && state.notifications.length > 0) {
                    newNotifs.forEach(notif => {
                        if (!notif.read) {
                            const alreadyKnown = state.notifications.find(n => n.id === notif.id);
                            if (!alreadyKnown) {
                                showToast(notif.message, "info");
                            }
                        }
                    });
                }
                state.notifications = newNotifs;

                // Render views
                renderDashboard();
                renderLogs();
                renderTasks();
                renderActivityLogs();
                renderSkills();
                renderFeedback();
                renderNotifications();

            } catch (err) {
                console.error("Fetch Data failed", err);
            }
        }

        // Render Dashboard KPIs & Tables
        function renderDashboard() {
            const role = getEffectiveUserRole();
            let filteredLogs = [...state.logs];
            let filteredTasks = [...state.tasks];
            let filteredSkills = [...state.skills];

            // If Admin/Manager is logged in, they can filter the stats by a selected user
            if (role === 'Admin' || role === 'Manager') {
                const userVal = document.getElementById('dash-user-filter').value;
                if (userVal !== 'ALL') {
                    filteredLogs = filteredLogs.filter(l => l.intern_name && l.intern_name.toLowerCase().trim() === userVal.toLowerCase().trim());
                    filteredTasks = filteredTasks.filter(t => t.intern_name && t.intern_name.toLowerCase().trim() === userVal.toLowerCase().trim());
                    filteredSkills = filteredSkills.filter(s => s.intern_name && s.intern_name.toLowerCase().trim() === userVal.toLowerCase().trim());
                }
            } else {
                // Employees and Interns should only see their own personal statistics on their dashboard
                const myUname = currentUser.username.toLowerCase().trim();
                filteredLogs = filteredLogs.filter(l => l.intern_name && l.intern_name.toLowerCase().trim() === myUname);
                filteredTasks = filteredTasks.filter(t => t.intern_name && t.intern_name.toLowerCase().trim() === myUname);
                filteredSkills = filteredSkills.filter(s => s.intern_name && s.intern_name.toLowerCase().trim() === myUname);
            }

            // 1. Calculate KPIs
            const totalHours = filteredLogs.reduce((sum, item) => sum + parseFloat(item.hours_worked || 0), 0);
            const daysWorked = new Set(filteredLogs.map(item => item.date_logged)).size;
            const completedTasks = filteredTasks.filter(t => t.status === 'Completed').length;
            const skillsLogged = filteredSkills.length;

            document.getElementById('stat-hours').innerText = `${totalHours.toFixed(1)}h`;
            document.getElementById('stat-days').innerText = daysWorked;
            document.getElementById('stat-tasks').innerText = completedTasks;
            document.getElementById('stat-skills').innerText = skillsLogged;

            // Pending Deliverables: people who have NOT marked deliverable_completed = 'Yes' today
            const todayStr = new Date().toISOString().split('T')[0];
            
            // For admin/manager: check across all visible subordinates
            // For employee/intern: check only themselves
            let pendingDeliverableCount = 0;
            let pendingDeliverableNames = [];

            if (role === 'Admin' || role === 'Manager') {
                const subordinateUsers = activeUsers.filter(u => {
                    if (!u.approved) return false;
                    if (role === 'Admin') return u.role === 'Manager' || u.role === 'Employee' || u.role === 'Intern';
                    if (role === 'Manager') return u.role === 'Employee' || u.role === 'Intern';
                    return false;
                });

                subordinateUsers.forEach(u => {
                    // Check if this user has a log today with deliverable_completed = 'Yes'
                    const todayLog = state.logs.find(l =>
                        l.intern_name && l.intern_name.toLowerCase().trim() === u.username.toLowerCase().trim() &&
                        l.date_logged === todayStr && l.deliverable_completed === 'Yes'
                    );
                    if (!todayLog) {
                        pendingDeliverableCount++;
                        pendingDeliverableNames.push(u.full_name);
                    }
                });
            } else {
                // For employee/intern: just count their own logs where deliverable = No
                const myPending = filteredLogs.filter(l => l.deliverable_completed !== 'Yes').length;
                pendingDeliverableCount = myPending;
            }

            const statPendingEl = document.getElementById('stat-pending-deliverables');
            if (statPendingEl) {
                statPendingEl.innerText = pendingDeliverableCount;
                statPendingEl.style.color = pendingDeliverableCount > 0 ? 'var(--danger)' : 'var(--success)';
            }

            // Set tooltip for admin/manager hover
            const tooltipEl = document.getElementById('stat-pending-deliverables-names');
            const statCard = document.getElementById('stat-pending-deliverables-card');
            if (tooltipEl && statCard) {
                if ((role === 'Admin' || role === 'Manager') && pendingDeliverableNames.length > 0) {
                    tooltipEl.innerHTML = `<div style="font-weight:700; margin-bottom:6px; color:var(--danger);"><i class="fa-solid fa-triangle-exclamation"></i> Not submitted today:</div>` +
                        pendingDeliverableNames.map(n => `<div style="display:flex; align-items:center; gap:6px;"><i class="fa-solid fa-circle-xmark" style="color:var(--danger); font-size:10px;"></i> ${escapeHTML(n)}</div>`).join('');
                    statCard.addEventListener('mouseenter', () => { tooltipEl.style.display = 'block'; });
                    statCard.addEventListener('mouseleave', () => { tooltipEl.style.display = 'none'; });
                    statCard.style.cursor = 'pointer';
                } else {
                    statCard.style.cursor = 'default';
                    statCard.removeEventListener('mouseenter', () => {});
                    statCard.removeEventListener('mouseleave', () => {});
                }
            }

            // 2. Task Status Breakdown
            const taskCounts = {
                'Not Started': 0,
                'In Progress': 0,
                'Completed': 0,
                'On Hold': 0,
                'Cancelled': 0
            };
            filteredTasks.forEach(t => {
                if (taskCounts[t.status] !== undefined) taskCounts[t.status]++;
            });
            const taskTableBody = document.getElementById('dash-task-status-table');
            taskTableBody.innerHTML = '';
            Object.entries(taskCounts).forEach(([status, count]) => {
                let badgeClass = 'badge-primary';
                if (status === 'Completed') badgeClass = 'badge-success';
                if (status === 'In Progress') badgeClass = 'badge-primary';
                if (status === 'On Hold') badgeClass = 'badge-warning';
                if (status === 'Cancelled') badgeClass = 'badge-danger';
                
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><span class="badge ${badgeClass}">${status}</span></td>
                    <td style="font-weight:700;">${count}</td>
                `;
                taskTableBody.appendChild(tr);
            });

            // 3. Weekly Hours Table
            // Calculate weeks to display dynamically (at least 6, or up to the current calendar week or logged week)
            const diffTimeToday = new Date() - START_DATE;
            let currentWeekNum = 1;
            if (diffTimeToday >= 0) {
                const diffDaysToday = Math.floor(diffTimeToday / (1000 * 60 * 60 * 24));
                currentWeekNum = Math.floor(diffDaysToday / 7) + 1;
            }

            let maxLogWeek = 1;
            filteredLogs.forEach(log => {
                const logDate = new Date(log.date_logged);
                const diffTime = logDate - START_DATE;
                if (diffTime >= 0) {
                    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
                    const weekNum = Math.floor(diffDays / 7) + 1;
                    if (weekNum > maxLogWeek) {
                        maxLogWeek = weekNum;
                    }
                }
            });

            const weeksToDisplay = Math.max(6, currentWeekNum, maxLogWeek);

            const weeklyData = {};
            for (let w = 1; w <= weeksToDisplay; w++) {
                weeklyData[w] = { hours: 0, days: new Set(), deliverables: 0, deliverableNames: [] };
            }

            filteredLogs.forEach(log => {
                const logDate = new Date(log.date_logged);
                const diffTime = logDate - START_DATE;
                if (diffTime >= 0) {
                    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
                    // Week starts on Monday. Since START_DATE is Monday, week transitions every 7 days.
                    const weekNum = Math.floor(diffDays / 7) + 1;
                    if (weekNum >= 1 && weekNum <= weeksToDisplay) {
                        weeklyData[weekNum].hours += parseFloat(log.hours_worked || 0);
                        weeklyData[weekNum].days.add(log.date_logged);
                        if (log.deliverable_completed === 'Yes') {
                            weeklyData[weekNum].deliverables++;
                            // Track name for tooltip
                            const uObj = activeUsers.find(u => u.username.toLowerCase().trim() === (log.intern_name || '').toLowerCase().trim());
                            const uName = uObj ? uObj.full_name : (log.intern_name || 'Unknown');
                            if (!weeklyData[weekNum].deliverableNames.includes(uName)) {
                                weeklyData[weekNum].deliverableNames.push(uName);
                            }
                        }
                    }
                }
            });

            const weeklyTableBody = document.getElementById('dash-weekly-table');
            weeklyTableBody.innerHTML = '';
            for (let w = 1; w <= weeksToDisplay; w++) {
                const weekInfo = weeklyData[w];
                const daysCount = weekInfo.days.size;
                const hoursVal = weekInfo.hours;
                const avgHours = daysCount > 0 ? (hoursVal / daysCount).toFixed(1) : '-';
                const status = hoursVal >= 30 ? 'On Track' : (hoursVal > 0 ? 'Behind' : 'Not Started');
                const badgeClass = status === 'On Track' ? 'badge-success' : (status === 'Behind' ? 'badge-warning' : 'badge-primary');

                // Build deliverable cell — hover tooltip for admin/manager
                let deliverableCell = '';
                if ((role === 'Admin' || role === 'Manager') && weekInfo.deliverables > 0) {
                    const namesList = weekInfo.deliverableNames.map(n => `<div style='display:flex;align-items:center;gap:6px;'><i class='fa-solid fa-circle-check' style='color:var(--success);font-size:10px;'></i>${escapeHTML(n)}</div>`).join('');
                    const tooltipHtml = `<div style='font-weight:700;margin-bottom:6px;color:var(--success);'><i class='fa-solid fa-circle-check'></i> Completed deliverables:</div>${namesList}`;
                    deliverableCell = `<span class='deliverable-count-tip' style='cursor:pointer; font-weight:700; color:var(--success); position:relative;' 
                        onmouseenter="this.querySelector('.del-tip').style.display='block'" 
                        onmouseleave="this.querySelector('.del-tip').style.display='none'">
                        ${weekInfo.deliverables}
                        <div class='del-tip' style='display:none; position:absolute; left:0; top:100%; z-index:9999; background:var(--bg-card); border:1px solid var(--border-color); border-radius:10px; padding:12px 16px; min-width:200px; box-shadow:0 8px 30px rgba(0,0,0,0.4); font-size:13px; line-height:1.8; font-weight:400;'>${tooltipHtml}</div>
                    </span>`;
                } else {
                    deliverableCell = `<span style='font-weight:700;'>${weekInfo.deliverables}</span>`;
                }

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>Week ${w}</td>
                    <td>${hoursVal.toFixed(1)} hrs</td>
                    <td>${daysCount} days</td>
                    <td>${avgHours}</td>
                    <td>${deliverableCell}</td>
                    <td><span class="badge ${badgeClass}">${status}</span></td>
                `;
                weeklyTableBody.appendChild(tr);
            }

            // 4. Team Work Hours & Tasks Summary (for Admin/Manager) or Mood Trend (for Intern/Employee)
            const summaryTitle = document.getElementById('dash-summary-title');
            const summaryThead = document.getElementById('dash-summary-thead');
            const summaryTbody = document.getElementById('dash-summary-table');

            if (summaryTitle && summaryThead && summaryTbody) {
                if (role === 'Admin' || role === 'Manager') {
                    summaryTitle.innerHTML = `<i class="fa-solid fa-users"></i> <span>Team Work Hours & Tasks Summary</span>`;
                    summaryThead.innerHTML = `
                        <tr>
                            <th>User</th>
                            <th>Role</th>
                            <th>Total Hours</th>
                            <th>Days Logged</th>
                            <th>Tasks Progress</th>
                            <th>Status</th>
                        </tr>
                    `;
                    summaryTbody.innerHTML = '';

                    // Filter users according to role permissions:
                    // Admin sees Manager, Employee, Intern (only approved users)
                    // Manager sees Employee, Intern (only approved users)
                    const subordinateUsers = activeUsers.filter(u => {
                        if (!u.approved) return false;
                        if (role === 'Admin') {
                            return u.role === 'Manager' || u.role === 'Employee' || u.role === 'Intern';
                        } else if (role === 'Manager') {
                            return u.role === 'Employee' || u.role === 'Intern';
                        }
                        return false;
                    });

                    const userVal = document.getElementById('dash-user-filter').value;
                    let displayUsers = [...subordinateUsers];
                    if (userVal !== 'ALL') {
                        displayUsers = displayUsers.filter(u => u.username.toLowerCase().trim() === userVal.toLowerCase().trim());
                    }

                    if (displayUsers.length === 0) {
                        summaryTbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No team members found.</td></tr>';
                    } else {
                        displayUsers.forEach(u => {
                            // Calculate total hours logged by this user
                            const userLogs = state.logs.filter(l => l.intern_name && l.intern_name.toLowerCase().trim() === u.username.toLowerCase().trim());
                            const userHours = userLogs.reduce((sum, item) => sum + parseFloat(item.hours_worked || 0), 0);
                            const userDays = new Set(userLogs.map(item => item.date_logged)).size;

                            // Calculate tasks progress
                            const userTasks = state.tasks.filter(t => t.intern_name && t.intern_name.toLowerCase().trim() === u.username.toLowerCase().trim());
                            const compTasks = userTasks.filter(t => t.status === 'Completed').length;
                            const totTasks = userTasks.length;

                            const isOnline = u.status === 'Available';
                            let timeDetail = '';
                            if (isOnline && u.last_login) {
                                timeDetail = `<div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Active: ${formatSessionTime(u.last_login)}</div>`;
                            } else if (!isOnline && u.last_logout) {
                                timeDetail = `<div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Logout: ${formatSessionTime(u.last_logout)}</div>`;
                            }
                            const statusBadge = `
                                <span class="badge ${isOnline ? 'badge-success' : 'badge-primary'}" style="${isOnline ? '' : 'opacity: 0.6;'}">
                                    <i class="fa-solid ${isOnline ? 'fa-circle-check' : 'fa-circle-xmark'}"></i> ${u.status || 'Logged Out'}
                                </span>
                                ${timeDetail}
                            `;

                            let roleBadgeClass = 'badge-primary';
                            if (u.role === 'Manager') roleBadgeClass = 'badge-warning';
                            else if (u.role === 'Employee') roleBadgeClass = 'badge-primary';
                            else if (u.role === 'Intern') roleBadgeClass = 'badge-success';

                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td style="font-weight:600;">${escapeHTML(u.full_name)}</td>
                                <td><span class="badge ${roleBadgeClass}">${u.role}</span></td>
                                <td style="font-weight:600; color: var(--primary);">${userHours.toFixed(1)} hrs</td>
                                <td>${userDays} days</td>
                                <td>
                                    <strong>${compTasks}</strong> / ${totTasks}
                                    <span style="font-size: 11px; color: var(--text-muted); margin-left: 4px;">(${totTasks > 0 ? Math.round((compTasks/totTasks)*100) : 0}%)</span>
                                </td>
                                <td>${statusBadge}</td>
                            `;
                            summaryTbody.appendChild(tr);
                        });
                    }
                } else {
                    // Intern/Employee: Mood Trend - Last 10 Logs
                    summaryTitle.innerHTML = `<i class="fa-solid fa-face-smile"></i> <span>Mood Trend — Last 10 Logs</span>`;
                    summaryThead.innerHTML = `
                        <tr>
                            <th>Intern Username</th>
                            <th>Date</th>
                            <th>Mood Score</th>
                            <th>Visual Rating</th>
                        </tr>
                    `;
                    summaryTbody.innerHTML = '';
                    
                    const last10Logs = [...filteredLogs]
                        .sort((a, b) => new Date(b.date_logged) - new Date(a.date_logged))
                        .slice(0, 10);

                    if (last10Logs.length === 0) {
                        summaryTbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No logs logged yet.</td></tr>';
                    } else {
                        last10Logs.forEach(log => {
                            const moodVal = log.mood || 5;
                            const percent = moodVal * 20;
                            let fillCol = 'var(--danger)';
                            if (moodVal >= 4) fillCol = 'var(--success)';
                            else if (moodVal >= 3) fillCol = 'var(--warning)';

                            const userObj = activeUsers.find(u => u.username.toLowerCase().trim() === (log.intern_name || '').toLowerCase().trim());
                            const displayName = userObj ? userObj.full_name : log.intern_name;

                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td style="font-weight:600;">${escapeHTML(displayName)}</td>
                                <td>${log.date_logged}</td>
                                <td style="font-weight:700;">${moodVal} / 5</td>
                                <td>
                                    <div class="mood-bar"><div class="mood-fill" style="width: ${percent}%; background-color: ${fillCol};"></div></div>
                                    <span style="font-size:12px; color:var(--text-muted);">${moodVal === 5 ? 'Excellent' : moodVal === 4 ? 'Good' : moodVal === 3 ? 'Neutral' : moodVal === 2 ? 'Low' : 'Struggling'}</span>
                                </td>
                            `;
                            summaryTbody.appendChild(tr);
                        });
                    }
                }
            }
        }

        // Render Logs table list
        function renderLogs() {
            const tbody = document.getElementById('logs-table-body');
            tbody.innerHTML = '';
            
            // Only show personal logs for the logged-in user in their Daily Tracker
            const personalLogs = state.logs.filter(log => (log.intern_name || '').toLowerCase().trim() === currentUser.username.toLowerCase().trim());
            
            if (personalLogs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--text-muted);">No activity logs entered.</td></tr>';
                return;
            }
            personalLogs.forEach(log => {
                const userObj = activeUsers.find(u => u.username.toLowerCase().trim() === (log.intern_name || '').toLowerCase().trim());
                const displayName = userObj ? userObj.full_name : log.intern_name;

                // Interns/Employees can edit/delete their own logs. Admins/Managers can edit/delete any log.
                const canEditDelete = currentUser.role !== 'Guest' && (getEffectiveUserRole() === 'Admin' || getEffectiveUserRole() === 'Manager' || (log.intern_name && log.intern_name.toLowerCase().trim() === currentUser.username.toLowerCase().trim()));
                let actionButtons = '';
                if (canEditDelete) {
                    actionButtons = `
                        <button onclick="editLog('${log.id}')" class="btn-action edit" title="Edit Log" style="background: rgba(99, 102, 241, 0.1); color: var(--primary); padding: 5px 8px; border-radius: 4px; border: none; cursor: pointer; margin-right: 4px;"><i class="fa-solid fa-pen-to-square"></i></button>
                        <button onclick="deleteLog('${log.id}')" class="btn-action delete" title="Delete Log" style="background: rgba(239, 68, 68, 0.1); color: var(--danger); padding: 5px 8px; border-radius: 4px; border: none; cursor: pointer;"><i class="fa-solid fa-trash"></i></button>
                    `;
                } else {
                    actionButtons = `<span style="color:var(--text-muted); font-size:11px;">No Actions</span>`;
                }

                // Find if there is an approved Hours (Timing Leave / Permission) request on this date
                const approvedHoursReq = (state.leaveRequests || []).find(r => 
                    r.username.toLowerCase().trim() === log.intern_name.toLowerCase().trim() &&
                    r.leave_type === 'Hours' &&
                    r.status === 'Approved' &&
                    r.start_date === log.date_logged
                );

                let hoursDisplay = `${log.hours_worked} hrs`;
                if (approvedHoursReq) {
                    hoursDisplay = `
                        <div style="font-weight: 700; color: var(--success);">${log.hours_worked} hrs worked</div>
                        <div style="font-size: 11px; color: var(--warning); font-weight: 600; margin-top: 2px;"><i class="fa-solid fa-clock"></i> ${approvedHoursReq.hours_requested} hrs permission</div>
                    `;
                }

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight: 600;">${escapeHTML(displayName)}</td>
                    <td>${log.date_logged}</td>
                    <td>${log.check_in || '-'}</td>
                    <td>${log.check_out || '-'}</td>
                    <td style="font-weight:700; min-width: 140px;">${hoursDisplay}</td>
                    <td>
                        <strong>${escapeHTML(log.tasks_completed)}</strong>
                        ${log.blockers && log.blockers !== 'None' && log.blockers !== '' ? `<div style="color:var(--danger); font-size:12px; margin-top:4px;"><i class="fa-solid fa-triangle-exclamation"></i> ${escapeHTML(log.blockers)}</div>` : ''}
                    </td>
                    <td><span class="badge ${log.deliverable_completed === 'Yes' ? 'badge-success' : 'badge-warning'}">${log.deliverable_completed || 'No'}</span></td>
                    <td style="text-align: center; white-space: nowrap;">${actionButtons}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // --- Activity Updates Logs (Admin & Manager) functions ---
        let currentActivityView = 'employees';

        function setActivityView(view) {
            currentActivityView = view;
            const btnEmployees = document.getElementById('btn-view-employees');
            const btnInterns = document.getElementById('btn-view-interns');
            const btnSessions = document.getElementById('btn-view-sessions');
            
            if (btnEmployees && btnInterns && btnSessions) {
                btnEmployees.className = 'btn btn-secondary btn-sm';
                btnInterns.className = 'btn btn-secondary btn-sm';
                btnSessions.className = 'btn btn-secondary btn-sm';

                if (view === 'employees') {
                    btnEmployees.className = 'btn btn-primary btn-sm';
                } else if (view === 'interns') {
                    btnInterns.className = 'btn btn-primary btn-sm';
                } else if (view === 'sessions') {
                    btnSessions.className = 'btn btn-primary btn-sm';
                }
            }
            renderActivityLogs();
        }

        function formatSessionDuration(loginStr, logoutStr) {
            if (!loginStr || !logoutStr) return '-';
            const login = new Date(loginStr);
            const logout = new Date(logoutStr);
            const diffMs = logout - login;
            if (diffMs < 0) return '-';
            const diffMins = Math.round(diffMs / 1000 / 60);
            const hours = Math.floor(diffMins / 60);
            const mins = diffMins % 60;
            
            if (hours > 0) {
                return `${hours}h ${mins}m`;
            }
            return `${mins}m`;
        }

        function renderSessionAttendanceLogs() {
            const tbody = document.getElementById('activity-session-logs-table-body');
            if (!tbody) return;
            tbody.innerHTML = '';
            
            // Filter by user selection if applicable
            const activityFilter = document.getElementById('activity-user-filter');
            const selectedUser = activityFilter ? activityFilter.value : 'ALL';
            
            // Enforce hierarchical monitoring for session attendance:
            // Admin sees Manager, Employee, and Intern logs.
            // Manager sees Employee and Intern logs (plus their own sessions).
            const role = getEffectiveUserRole();
            let rawLogs = (state.sessionLogs || []).filter(log => {
                if (role === 'Admin') {
                    return log.role === 'Manager' || log.role === 'Employee' || log.role === 'Intern';
                } else if (role === 'Manager') {
                    return log.role === 'Employee' || log.role === 'Intern' || log.username === currentUser.username;
                }
                return false;
            });
            
            // Filter out test IDs / test usernames
            rawLogs = rawLogs.filter(log => !isTestUser(log.username, log.full_name));
            
            if (selectedUser !== 'ALL') {
                rawLogs = rawLogs.filter(log => (log.username || '').toLowerCase().trim() === selectedUser.toLowerCase().trim());
            }
            
            let approvedLeaves = (state.leaveRequests || []).filter(r => r.status === 'Approved');
            approvedLeaves = approvedLeaves.filter(r => {
                if (role === 'Admin') {
                    return r.role === 'Manager' || r.role === 'Employee' || r.role === 'Intern';
                } else if (role === 'Manager') {
                    return r.role === 'Employee' || r.role === 'Intern' || r.username === currentUser.username;
                }
                return false;
            });
            if (selectedUser !== 'ALL') {
                approvedLeaves = approvedLeaves.filter(r => (r.username || '').toLowerCase().trim() === selectedUser.toLowerCase().trim());
            }

            // Inject virtual leave session logs for dates with approved leaves but no session logs
            const virtualLogs = [];
            approvedLeaves.forEach(r => {
                let start = new Date(r.start_date);
                let end = new Date(r.end_date);
                let curr = new Date(start);
                while (curr <= end) {
                    const dateIso = curr.toISOString().split('T')[0];
                    const dateLocal = curr.toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
                    
                    const hasSession = rawLogs.some(log => 
                        log.username.toLowerCase().trim() === r.username.toLowerCase().trim() &&
                        new Date(log.login_time).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' }) === dateLocal
                    );
                    
                    if (!hasSession) {
                        virtualLogs.push({
                            username: r.username,
                            full_name: r.full_name,
                            role: r.role,
                            login_time: `${dateIso}T09:00:00`,
                            logout_time: `${dateIso}T09:00:00`,
                            isLeave: true,
                            leaveType: r.leave_type,
                            leaveDuration: r.leave_type === 'Hours' ? `${r.hours_requested} hrs` : `${r.days_requested} days`,
                            leaveReason: r.reason
                        });
                    }
                    curr.setDate(curr.getDate() + 1);
                }
            });
            rawLogs = [...rawLogs, ...virtualLogs];

            if (rawLogs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding: 20px;">No session attendance logs found.</td></tr>';
                return;
            }

            // Group by username and local date
            const groups = {};
            
            rawLogs.forEach(log => {
                const loginDate = new Date(log.login_time);
                const localDateStr = loginDate.toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
                
                const key = `${log.username}_${localDateStr}`;
                if (!groups[key]) {
                    groups[key] = {
                        username: log.username,
                        full_name: log.full_name,
                        role: log.role,
                        localDateStr: localDateStr,
                        sessions: [],
                        isLeave: log.isLeave || false,
                        leaveType: log.leaveType || null,
                        leaveDuration: log.leaveDuration || null,
                        leaveReason: log.leaveReason || null
                    };
                }
                if (!log.isLeave) {
                    groups[key].isLeave = false;
                }
                groups[key].sessions.push(log);
            });

            const aggregatedLogs = Object.values(groups);

            aggregatedLogs.forEach(group => {
                group.sessions.sort((a, b) => new Date(a.login_time) - new Date(b.login_time));
                group.earliestLoginTime = new Date(group.sessions[0].login_time);
                
                // Scan for approved leaves for this user on this day
                const matchingLeave = (state.leaveRequests || []).find(r => 
                    r.status === 'Approved' &&
                    r.username.toLowerCase().trim() === group.username.toLowerCase().trim() &&
                    new Date(r.start_date).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' }) === group.localDateStr
                );
                
                if (matchingLeave) {
                    group.hasLeaveApplied = true;
                    group.leaveType = matchingLeave.leave_type;
                    group.leaveDuration = matchingLeave.leave_type === 'Hours' ? `${matchingLeave.hours_requested} hrs` : `${matchingLeave.days_requested} days`;
                    group.leaveReason = matchingLeave.reason;
                }
            });

            aggregatedLogs.sort((a, b) => b.earliestLoginTime - a.earliestLoginTime);

            aggregatedLogs.forEach(group => {
                let checkInTimeStr = '-';
                let checkOutTimeStr = '-';
                let durationStr = '-';
                let statusBadge = '';
                
                let roleBadgeClass = 'badge-success'; // Intern
                if (group.role === 'Admin') roleBadgeClass = 'badge-danger';
                else if (group.role === 'Manager') roleBadgeClass = 'badge-warning';
                else if (group.role === 'Employee') roleBadgeClass = 'badge-primary';

                if (group.isLeave) {
                    checkInTimeStr = `<span style="color: var(--primary); font-weight:600;"><i class="fa-solid fa-umbrella-beach"></i> ${group.leaveType}</span>`;
                    checkOutTimeStr = '-';
                    
                    let durationClean = group.leaveDuration.replace('.0', '');
                    if (durationClean === '1 days') {
                        durationClean = '1 day';
                    }
                    
                    durationStr = `<span style="font-weight:700; color: var(--primary);">${durationClean}</span>`;
                    
                    // Display details about the leave type in status e.g. "Leave for 2 days"
                    let statusLabel = `Leave for ${durationClean}`;
                    if (group.leaveType === 'Hours') {
                        statusLabel = `Permission for ${durationClean}`;
                    }
                    
                    statusBadge = `<span class="badge" style="background: rgba(99, 102, 241, 0.15); color: var(--primary); font-weight:600;"><i class="fa-solid fa-circle-check"></i> ${statusLabel}</span>`;
                } else {
                    const firstSession = group.sessions[0];
                    const lastSession = group.sessions[group.sessions.length - 1];
                    const loginTimeObj = new Date(firstSession.login_time);
                    checkInTimeStr = loginTimeObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    
                    let isCurrentlyActive = false;
                    if (!lastSession.logout_time) {
                        checkOutTimeStr = '-';
                        statusBadge = '<span class="badge badge-success">Active</span>';
                        isCurrentlyActive = true;
                    } else {
                        const logoutTimeObj = new Date(lastSession.logout_time);
                        checkOutTimeStr = logoutTimeObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                        statusBadge = '<span class="badge badge-primary">Completed</span>';
                    }

                    let totalDurationMs = 0;
                    group.sessions.forEach(s => {
                        const loginTime = new Date(s.login_time);
                        if (s.logout_time) {
                            totalDurationMs += (new Date(s.logout_time) - loginTime);
                        } else {
                            totalDurationMs += (new Date() - loginTime);
                        }
                    });

                    const diffMins = Math.round(totalDurationMs / 1000 / 60);
                    const hours = Math.floor(diffMins / 60);
                    const mins = diffMins % 60;
                    durationStr = hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;

                    if (isCurrentlyActive) {
                        durationStr = `<span style="color: var(--success); font-style: italic; font-weight: 600;">Active: ${durationStr}</span>`;
                    }

                    if (group.hasLeaveApplied) {
                        let durationClean = group.leaveDuration.replace('.0', '');
                        if (durationClean === '1 days') {
                            durationClean = '1 day';
                        }
                        
                        durationStr = `
                            <div style="font-weight: 700;">${durationStr} worked</div>
                            <div style="font-size: 11px; color: var(--warning); font-weight: 600; margin-top: 2px;"><i class="fa-solid fa-clock"></i> ${durationClean} Permission</div>
                        `;
                        statusBadge = `<span class="badge badge-warning" style="font-weight:600;"><i class="fa-solid fa-circle-info"></i> Permission for ${durationClean}</span>`;
                    }
                }

                let actionHtml = '';
                if (getEffectiveUserRole() === 'Admin' && !group.isLeave) {
                    const firstSession = group.sessions[0];
                    const lastSession = group.sessions[group.sessions.length - 1];
                    const loginIso = firstSession.login_time;
                    const logoutIso = lastSession.logout_time || new Date().toISOString();
                    
                    actionHtml = `
                        <button onclick="openEditSessionModal('${escapeHTML(group.username)}', '${escapeHTML(group.full_name || group.username)}', '${escapeHTML(group.localDateStr)}', '${loginIso}', '${logoutIso}')" class="btn btn-warning btn-sm" style="display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px;">
                            <i class="fa-solid fa-pen-to-square"></i> Edit
                        </button>
                    `;
                } else {
                    actionHtml = `<span style="color: var(--text-muted); font-size: 12px;">-</span>`;
                }

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight: 600;">${escapeHTML(group.full_name || group.username)}</td>
                    <td><span class="badge ${roleBadgeClass}">${group.role}</span></td>
                    <td>${group.localDateStr}</td>
                    <td style="font-weight: 500;">${checkInTimeStr}</td>
                    <td style="font-weight: 500; color: var(--text-muted);">${checkOutTimeStr}</td>
                    <td style="font-weight: 700; min-width: 130px;">${durationStr}</td>
                    <td>${statusBadge}</td>
                    <td style="text-align: center;">${actionHtml}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        function renderActivityLogs() {
            const workLogsContainer = document.getElementById('activity-work-logs-container');
            const sessionLogsContainer = document.getElementById('activity-session-logs-container');
            
            if (currentActivityView === 'sessions') {
                if (workLogsContainer) workLogsContainer.style.display = 'none';
                if (sessionLogsContainer) sessionLogsContainer.style.display = 'block';
                renderSessionAttendanceLogs();
                return;
            }

            if (workLogsContainer) workLogsContainer.style.display = 'block';
            if (sessionLogsContainer) sessionLogsContainer.style.display = 'none';

            const tbody = document.getElementById('activity-logs-table-body');
            if (!tbody) return;
            tbody.innerHTML = '';
            
            // Filter by user selection if applicable
            const activityFilter = document.getElementById('activity-user-filter');
            const selectedUser = activityFilter ? activityFilter.value : 'ALL';
            
            let logsToRender = state.logs.filter(log => {
                const userObj = activeUsers.find(u => u.username.toLowerCase().trim() === (log.intern_name || '').toLowerCase().trim());
                const userRole = userObj ? userObj.role : 'Intern';
                
                if (selectedUser !== 'ALL' && (log.intern_name || '').toLowerCase().trim() !== selectedUser.toLowerCase().trim()) {
                    return false;
                }
                
                if (currentActivityView === 'employees') {
                    return userRole === 'Employee' || userRole === 'Manager';
                } else {
                    return userRole === 'Intern';
                }
            });

            if (logsToRender.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding: 20px;">No activity logs found matching the filter.</td></tr>`;
                return;
            }

            logsToRender.forEach(log => {
                const userObj = activeUsers.find(u => u.username.toLowerCase().trim() === (log.intern_name || '').toLowerCase().trim());
                const userRole = userObj ? userObj.role : 'Intern';
                const displayName = userObj ? userObj.full_name : log.intern_name;

                // Admin can edit/delete any log. Managers can edit/delete subordinate logs (Interns/Employees) but NOT other Managers or themselves.
                const canEditDelete = currentUser.role !== 'Guest' && (
                    getEffectiveUserRole() === 'Admin' || 
                    (getEffectiveUserRole() === 'Manager' && userRole !== 'Manager')
                );
                let actionButtons = '';
                if (canEditDelete) {
                    actionButtons = `
                        <button onclick="openEditLogModal('${log.id}')" class="btn-action edit" title="Edit Log" style="background: rgba(99, 102, 241, 0.1); color: var(--primary); padding: 5px 8px; border-radius: 4px; border: none; cursor: pointer; margin-right: 4px;"><i class="fa-solid fa-pen-to-square"></i></button>
                        <button onclick="deleteLog('${log.id}')" class="btn-action delete" title="Delete Log" style="background: rgba(239, 68, 68, 0.1); color: var(--danger); padding: 5px 8px; border-radius: 4px; border: none; cursor: pointer;"><i class="fa-solid fa-trash"></i></button>
                    `;
                } else {
                    actionButtons = `<span style="color:var(--text-muted); font-size:11px;">No Actions</span>`;
                }

                // Find if there is an approved Hours (Timing Leave / Permission) request on this date
                const approvedHoursReq = (state.leaveRequests || []).find(r => 
                    r.username.toLowerCase().trim() === log.intern_name.toLowerCase().trim() &&
                    r.leave_type === 'Hours' &&
                    r.status === 'Approved' &&
                    r.start_date === log.date_logged
                );

                let hoursDisplay = `${log.hours_worked} hrs`;
                if (approvedHoursReq) {
                    hoursDisplay = `
                        <div style="font-weight: 700; color: var(--success);">${log.hours_worked} hrs worked</div>
                        <div style="font-size: 11px; color: var(--warning); font-weight: 600; margin-top: 2px;"><i class="fa-solid fa-clock"></i> ${approvedHoursReq.hours_requested} hrs permission</div>
                    `;
                }

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight: 600;">${escapeHTML(displayName)}</td>
                    <td>${log.date_logged}</td>
                    <td>${log.check_in || '-'}</td>
                    <td>${log.check_out || '-'}</td>
                    <td style="font-weight:700; min-width: 140px;">${hoursDisplay}</td>
                    <td>
                        <strong>${escapeHTML(log.tasks_completed)}</strong>
                        ${log.blockers && log.blockers !== 'None' && log.blockers !== '' ? `<div style="color:var(--danger); font-size:12px; margin-top:4px;"><i class="fa-solid fa-triangle-exclamation"></i> ${escapeHTML(log.blockers)}</div>` : ''}
                    </td>
                    <td><span class="badge ${log.deliverable_completed === 'Yes' ? 'badge-success' : 'badge-warning'}">${log.deliverable_completed || 'No'}</span></td>
                    <td style="text-align: center; white-space: nowrap;">${actionButtons}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        let editingLogIdModal = null;

        function openEditLogModal(logId) {
            const log = state.logs.find(l => l.id === logId);
            if (!log) return;

            editingLogIdModal = logId;
            
            const userObj = activeUsers.find(u => u.username.toLowerCase().trim() === (log.intern_name || '').toLowerCase().trim());
            const displayName = userObj ? `${userObj.full_name} (${userObj.role})` : log.intern_name;

            document.getElementById('edit_log_intern_name').value = displayName;
            document.getElementById('edit_log_date').value = log.date_logged;
            document.getElementById('edit_log_checkin').value = log.check_in || "09:00";
            document.getElementById('edit_log_checkout').value = log.check_out || "18:00";
            document.getElementById('edit_log_category').value = log.task_category || "Other";
            document.getElementById('edit_log_tasks').value = log.tasks_completed;
            document.getElementById('edit_log_deliverable').value = log.deliverable_completed || "No";
            document.getElementById('edit_log_blockers').value = log.blockers || "None";
            document.getElementById('edit_log_skills').value = log.skills_used || "";
            document.getElementById('edit_log_notes').value = log.notes || "";

            // For Managers: lock hours and auto-calculate from check-in/out
            const editHoursEl = document.getElementById('edit_log_hours');
            const isManagerLog = userObj && userObj.role === 'Manager';
            if (isManagerLog) {
                editHoursEl.readOnly = true;
                editHoursEl.style.background = 'rgba(255, 255, 255, 0.05)';
                editHoursEl.style.color = 'var(--text-muted)';
                editHoursEl.style.cursor = 'not-allowed';
                editHoursEl.title = '';
                // Calculate hours from check-in/out
                calculateHoursFromTime('edit_log_checkin', 'edit_log_checkout', 'edit_log_hours');
            } else {
                editHoursEl.readOnly = false;
                editHoursEl.style.background = '';
                editHoursEl.style.color = '';
                editHoursEl.style.cursor = '';
                editHoursEl.title = '';
                editHoursEl.value = log.hours_worked;
            }

            // Populate mood rating buttons
            document.querySelectorAll('#edit_log_mood_group .rating-btn').forEach(btn => {
                if (parseInt(btn.dataset.value) === parseInt(log.mood || 5)) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });

            document.getElementById('edit-log-modal').style.display = 'flex';
        }

        function closeEditLogModal() {
            editingLogIdModal = null;
            document.getElementById('edit-log-modal').style.display = 'none';
        }

        // Register edit form submit listener for modal
        // (Runs directly as elements are already in the DOM)
        const editFormModal = document.getElementById('editLogFormModal');
        if (editFormModal) {
            editFormModal.addEventListener('submit', async function(e) {
                e.preventDefault();
                if (!editingLogIdModal) return;

                const selectedLogDate = document.getElementById('edit_log_date').value;
                const d = new Date();
                const year = d.getFullYear();
                const month = String(d.getMonth() + 1).padStart(2, '0');
                const day = String(d.getDate()).padStart(2, '0');
                const localTodayStr = `${year}-${month}-${day}`;

                const yesterday = new Date();
                yesterday.setDate(yesterday.getDate() - 1);
                const yestYear = yesterday.getFullYear();
                const yestMonth = String(yesterday.getMonth() + 1).padStart(2, '0');
                const yestDay = String(yesterday.getDate()).padStart(2, '0');
                const localYesterdayStr = `${yestYear}-${yestMonth}-${yestDay}`;

                if (selectedLogDate && (selectedLogDate < localYesterdayStr || selectedLogDate > localTodayStr)) {
                    showToast("Daily log date must be yesterday or today.", "error");
                    return;
                }

                const hoursLogged = parseFloat(document.getElementById('edit_log_hours').value);
                if (hoursLogged > 9.0) {
                    showToast("Hours cannot exceed 9 hours per day. Please start freshly from next day.", "error");
                    return;
                }

                const selectedMood = document.querySelector('#edit_log_mood_group .rating-btn.active').dataset.value;
                const payload = {
                    date_logged: selectedLogDate,
                    hours_worked: parseFloat(document.getElementById('edit_log_hours').value),
                    check_in: document.getElementById('edit_log_checkin').value,
                    check_out: document.getElementById('edit_log_checkout').value,
                    task_category: document.getElementById('edit_log_category').value,
                    tasks_completed: document.getElementById('edit_log_tasks').value,
                    deliverable_completed: document.getElementById('edit_log_deliverable').value,
                    blockers: document.getElementById('edit_log_blockers').value || 'None',
                    skills_used: document.getElementById('edit_log_skills').value || '',
                    mood: parseInt(selectedMood),
                    notes: document.getElementById('edit_log_notes').value || ''
                };

                try {
                    const res = await apiFetch(`/logs/${editingLogIdModal}`, {
                        method: 'PUT',
                        body: payload
                    });
                    
                    if (res.ok) {
                        showToast("Daily log entry updated!", "success");
                        closeEditLogModal();
                        fetchData();
                    } else {
                        const data = await res.json();
                        showToast(data.error || "Failed to update log", "error");
                    }
                } catch (err) {
                    showToast("Failed to update log", "error");
                }
            });
        }

        // Render Tasks table list
        function renderTasks() {
            const tbody = document.getElementById('tasks-table-body');
            tbody.innerHTML = '';
            
            const role = getEffectiveUserRole();

            // Filter tasks based on role and active workspace view
            let tasksToRender = [...state.tasks];
            if (role === 'Admin' || role === 'Manager') {
                if (currentTaskView === 'my') {
                    tasksToRender = tasksToRender.filter(t => t.intern_name && t.intern_name.toLowerCase().trim() === currentUser.username.toLowerCase().trim());
                } else {
                    tasksToRender = tasksToRender.filter(t => !t.intern_name || t.intern_name.toLowerCase().trim() !== currentUser.username.toLowerCase().trim());
                }
            }

            if (tasksToRender.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No tasks in backlog.</td></tr>';
                return;
            }

            const disabledAttr = currentUser.role === 'Guest' ? 'disabled' : '';

            tasksToRender.forEach(t => {
                const targetUserObj = activeUsers.find(u => u.username.toLowerCase().trim() === (t.intern_name || '').toLowerCase().trim());
                const targetName = targetUserObj ? targetUserObj.full_name : t.intern_name;

                const assignerObj = activeUsers.find(u => u.username.toLowerCase().trim() === (t.assigned_by || '').toLowerCase().trim());
                const assignerName = assignerObj ? assignerObj.full_name : t.assigned_by;

                const tr = document.createElement('tr');
                const isCompleted = t.status === 'Completed';
                
                // Assigner can delete task, or admins/managers.
                const canDelete = currentUser.role !== 'Guest' && (role === 'Admin' || role === 'Manager' || t.assigned_by === currentUser.username);
                const deleteButton = canDelete ? `<button onclick="deleteTask('${t.id}')" class="btn-action delete" title="Delete Task"><i class="fa-solid fa-trash"></i></button>` : '';

                // Construct timeline details
                let timelineHtml = `<div style="font-size:11px; line-height:1.4; color:var(--text-muted);">`;
                timelineHtml += `<div><strong>Assigned:</strong> ${t.assigned_date || '-'}</div>`;
                if (t.started_at) {
                    const startedStr = new Date(t.started_at).toLocaleString();
                    timelineHtml += `<div><strong>Started:</strong> ${startedStr}</div>`;
                }
                if (t.completed_at) {
                    const completedStr = new Date(t.completed_at).toLocaleString();
                    timelineHtml += `<div><strong>Ended:</strong> ${completedStr}</div>`;
                    
                    const durationMs = new Date(t.completed_at) - new Date(t.started_at || t.assigned_date);
                    const durationStr = formatDuration(durationMs);
                    if (durationStr) {
                        timelineHtml += `<div style="margin-top:4px;"><span class="badge badge-success" style="font-size:10px; padding:2px 6px;">Took: ${durationStr}</span></div>`;
                    }
                }
                timelineHtml += `</div>`;

                tr.innerHTML = `
                    <td style="font-weight:600;">${escapeHTML(targetName)}</td>
                    <td>
                        <strong style="${isCompleted ? 'text-decoration: line-through; color: var(--text-muted);' : ''}">${escapeHTML(t.task_name)}</strong>
                        <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">
                            By ${escapeHTML(assignerName || 'Supervisor')} | <strong>Due:</strong> ${t.due_date || '-'}
                        </div>
                    </td>
                    <td><span class="badge ${t.priority === 'High' ? 'badge-danger' : (t.priority === 'Low' ? 'badge-primary' : 'badge-warning')}">${t.priority}</span></td>
                    <td>${timelineHtml}</td>
                    <td>
                        <select ${disabledAttr} onchange="updateTaskStatus('${t.id}', this.value)" style="padding: 6px 10px; font-size:12px; border-radius:6px; width:auto; background:rgba(255,255,255,0.02)">
                            <option value="Not Started" ${t.status === 'Not Started' ? 'selected' : ''}>Not Started</option>
                            <option value="In Progress" ${t.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                            <option value="Completed" ${t.status === 'Completed' ? 'selected' : ''}>Completed</option>
                            <option value="On Hold" ${t.status === 'On Hold' ? 'selected' : ''}>On Hold</option>
                            <option value="Cancelled" ${t.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                        </select>
                    </td>
                    <td>
                        <input ${disabledAttr} type="number" value="${t.percent_done || 0}" min="0" max="100" step="10" 
                               onchange="updateTaskPercent('${t.id}', this.value)" 
                               style="width: 70px; padding: 6px; font-size:12px; border-radius:6px; background:rgba(255,255,255,0.02); text-align:center;">
                    </td>
                    <td class="actions-cell">
                        ${deleteButton}
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function formatDuration(ms) {
            if (isNaN(ms) || ms < 0) return '';
            const totalMinutes = Math.floor(ms / 60000);
            if (totalMinutes === 0) return 'less than 1m';
            const days = Math.floor(totalMinutes / (24 * 60));
            const hours = Math.floor((totalMinutes % (24 * 60)) / 60);
            const minutes = totalMinutes % 60;
            
            let parts = [];
            if (days > 0) parts.push(`${days}d`);
            if (hours > 0) parts.push(`${hours}h`);
            if (minutes > 0 || parts.length === 0) parts.push(`${minutes}m`);
            
            return parts.join(' ');
        }

        function formatSessionTime(isoStr) {
            if (!isoStr) return '-';
            const date = new Date(isoStr);
            const today = new Date();
            const isToday = date.getDate() === today.getDate() &&
                            date.getMonth() === today.getMonth() &&
                            date.getFullYear() === today.getFullYear();
            const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            if (isToday) {
                return `Today at ${timeStr}`;
            } else {
                const month = date.toLocaleDateString([], { month: 'short' });
                const day = date.getDate();
                return `${month} ${day}, ${timeStr}`;
            }
        }

        // Render Skills table list
        function renderSkills() {
            const tbody = document.getElementById('skills-table-body');
            tbody.innerHTML = '';
            if (state.skills.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No learning metrics logged.</td></tr>';
                return;
            }
            state.skills.forEach(s => {
                const userObj = activeUsers.find(u => u.username.toLowerCase().trim() === (s.intern_name || '').toLowerCase().trim());
                const displayName = userObj ? userObj.full_name : s.intern_name;

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight: 600;">${escapeHTML(displayName)}</td>
                    <td>
                        <strong>${escapeHTML(s.skill_tool)}</strong>
                        ${s.certificate === 'Yes' ? `<span class="badge badge-success" style="padding: 2px 6px; font-size:10px; margin-left:8px;"><i class="fa-solid fa-medal"></i> Cert</span>` : ''}
                    </td>
                    <td><span class="badge badge-primary">${escapeHTML(s.category)}</span></td>
                    <td style="color:var(--text-muted);">${escapeHTML(s.resource_course || 'Self Study')}</td>
                    <td style="font-weight:700;">${s.hours_spent} hrs</td>
                    <td>
                        <span style="font-weight:600; color:var(--text-muted);">${s.proficiency_before || 1}</span> 
                        <i class="fa-solid fa-arrow-right-long" style="font-size:10px; margin: 0 6px; color: var(--primary);"></i> 
                        <span style="font-weight:700; color:var(--success);">${s.proficiency_after || 1}</span>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        // Render Feedback table list
        function renderFeedback() {
            const tbody = document.getElementById('feedback-table-body');
            tbody.innerHTML = '';
            if (state.feedback.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No feedback records registered.</td></tr>';
                return;
            }
            state.feedback.forEach(f => {
                const targetObj = activeUsers.find(u => u.username.toLowerCase().trim() === (f.intern_name || '').toLowerCase().trim());
                const targetName = targetObj ? targetObj.full_name : f.intern_name;

                const reviewerObj = activeUsers.find(u => u.username.toLowerCase().trim() === (f.feedback_from || '').toLowerCase().trim());
                const reviewerName = reviewerObj ? reviewerObj.full_name : f.feedback_from;

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight:600;">${escapeHTML(targetName)}</td>
                    <td>${f.date_logged}</td>
                    <td style="font-weight:600;">${escapeHTML(reviewerName)}</td>
                    <td><span class="badge badge-primary">${escapeHTML(f.type)}</span></td>
                    <td>
                        <strong>${escapeHTML(f.feedback_summary)}</strong>
                        ${f.action_taken ? `<div style="font-size:12px; color:var(--text-muted); margin-top:4px;"><strong>Action Plan:</strong> ${escapeHTML(f.action_taken)}</div>` : ''}
                    </td>
                    <td>
                        ${f.strength_noted ? `<div style="font-size:12px; color:#34d399;"><i class="fa-solid fa-plus-circle"></i> Strength: ${escapeHTML(f.strength_noted)}</div>` : ''}
                        ${f.area_to_improve ? `<div style="font-size:12px; color:#fbbf24; margin-top:2px;"><i class="fa-solid fa-pen-circle"></i> Improve: ${escapeHTML(f.area_to_improve)}</div>` : ''}
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }


        // Toggle Notifications Dropdown
        function toggleNotifDropdown(event) {
            event.stopPropagation();
            const dropdown = document.getElementById('notif-dropdown');
            if (dropdown) {
                const isShowing = dropdown.style.display === 'block';
                dropdown.style.display = isShowing ? 'none' : 'block';
            }
        }

        // Fetch and Render Notifications
        async function fetchNotifications(showToasts = false) {
            if (!currentUser) return;
            try {
                const res = await apiFetch('/notifications');
                if (res.ok) {
                    let newNotifications = await res.json();
                    
                    // Filter out test notifications
                    newNotifications = newNotifications.filter(notif => {
                        const msg = (notif.message || '').toLowerCase();
                        return !msg.includes('test') && 
                               !msg.includes('pending intern') && 
                               !msg.includes('mgr_') && 
                               !msg.includes('emp_') && 
                               !msg.includes('int_') && 
                               !msg.includes('user_');
                    });
                    
                    if (showToasts && state.notifications && state.notifications.length > 0) {
                        newNotifications.forEach(notif => {
                            if (!notif.read) {
                                const alreadyKnown = state.notifications.find(n => n.id === notif.id);
                                if (!alreadyKnown) {
                                    // Suppress DM toast if we are currently chatting with the sender on the Direct Messages tab
                                    let suppress = false;
                                    const activeTab = document.querySelector('.nav-item.active');
                                    const isDMsActive = activeTab && activeTab.dataset.tab === 'direct-messages';
                                    if (isDMsActive && notif.type === 'direct_message' && dmActiveUser) {
                                        if (notif.message.includes(dmActiveUser.full_name)) {
                                            suppress = true;
                                        }
                                    }
                                    if (!suppress) {
                                        showToast(notif.message, "info");
                                    }
                                }
                            }
                        });
                    }

                    state.notifications = newNotifications;
                    renderNotifications();
                }
            } catch (err) {
                console.error("Failed to load notifications", err);
            }
        }

        // Render Notifications List & Badge
        function renderNotifications() {
            const badge = document.getElementById('notif-badge');
            const listContainer = document.getElementById('notif-list-container');
            if (!badge || !listContainer) return;

            const unreadCount = state.notifications.filter(n => !n.read).length;
            if (unreadCount > 0) {
                badge.innerText = unreadCount;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }

            listContainer.innerHTML = '';
            if (state.notifications.length === 0) {
                listContainer.innerHTML = '<div style="color: var(--text-muted); font-size: 12px; text-align: center; padding: 16px 0;">No new notifications.</div>';
                return;
            }

            state.notifications.forEach(n => {
                const div = document.createElement('div');
                div.style.padding = '8px';
                div.style.borderRadius = '6px';
                div.style.background = n.read ? 'rgba(255,255,255,0.01)' : 'rgba(99,102,241,0.05)';
                div.style.borderLeft = n.read ? '2px solid transparent' : '2px solid var(--primary)';
                div.style.fontSize = '12px';
                div.style.display = 'flex';
                div.style.flexDirection = 'column';
                div.style.gap = '4px';
                div.style.cursor = 'pointer';
                div.style.transition = 'background 0.2s';
                
                div.onclick = async (e) => {
                    e.stopPropagation();
                    if (!n.read) {
                        try {
                            const res = await apiFetch(`/notifications/${n.id}/read`, { method: 'POST' });
                            if (res.ok) {
                                n.read = true;
                                renderNotifications();
                            }
                        } catch (err) {
                            console.error("Failed to mark notification read", err);
                        }
                    }
                };

                const dateStr = new Date(n.created_at).toLocaleString();
                div.innerHTML = `
                    <div style="color: var(--text); font-weight: ${n.read ? '400' : '600'}; line-height: 1.3;">${escapeHTML(n.message)}</div>
                    <div style="color: var(--text-muted); font-size: 10px;">${dateStr}</div>
                `;
                listContainer.appendChild(div);
            });
        }

        // Mark all notifications as read
        async function markAllNotificationsRead(event) {
            event.stopPropagation();
            try {
                const res = await apiFetch('/notifications/read', { method: 'POST' });
                if (res.ok) {
                    state.notifications.forEach(n => n.read = true);
                    renderNotifications();
                }
            } catch (err) {
                console.error("Failed to mark all notifications read", err);
            }
        }

        // Close dropdown when clicking outside
        window.addEventListener('click', function(e) {
            const dropdown = document.getElementById('notif-dropdown');
            if (dropdown && dropdown.style.display === 'block') {
                const container = document.getElementById('notif-bell-container');
                if (container && !container.contains(e.target)) {
                    dropdown.style.display = 'none';
                }
            }
        });

        // Action Helpers: Update task status
        async function updateTaskStatus(taskId, status) {
            try {
                let percent = undefined;
                if (status === 'Not Started') {
                    percent = 0;
                } else if (status === 'In Progress') {
                    percent = 50;
                } else if (status === 'Completed') {
                    percent = 100;
                }

                const res = await apiFetch(`/tasks/${taskId}`, {
                    method: 'PUT',
                    body: {
                        status: status,
                        percent_done: percent
                    }
                });
                if (res.ok) {
                    showToast("Task status updated successfully!");
                    fetchData();
                }
            } catch (err) {
                showToast("Failed to update status on server", "error");
            }
        }

        // Action Helpers: Update task completion percentage
        async function updateTaskPercent(taskId, percent) {
            try {
                const res = await apiFetch(`/tasks/${taskId}`, {
                    method: 'PUT',
                    body: {
                        percent_done: parseInt(percent),
                        status: parseInt(percent) === 100 ? 'Completed' : undefined
                    }
                });
                if (res.ok) {
                    showToast("Task progress saved!");
                    fetchData();
                }
            } catch (err) {
                showToast("Failed to save progress", "error");
            }
        }

        // Action Helpers: Delete task
        async function deleteTask(taskId) {
            if (!confirm("Are you sure you want to delete this task?")) return;
            try {
                const res = await apiFetch(`/tasks/${taskId}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    showToast("Task removed from backlog.");
                    fetchData();
                }
            } catch (err) {
                showToast("Failed to delete task", "error");
            }
        }

        // Logout Session Handler
        async function handleLogout() {
            try {
                const res = await apiFetch('/logout', { method: 'POST' });
                if (res.ok) {
                    currentUser = null;
                    showToast("Session closed successfully!");
                    showAuthOverlay();
                }
            } catch (err) {
                showAuthOverlay();
            }
        }

        // Periodically verify session authentication status (forces re-login if deleted by Admin)
        setInterval(async () => {
            if (currentUser) {
                try {
                    const res = await fetch(`${API_URL}/current_user`, { credentials: 'include' });
                    if (res.status === 401) {
                        currentUser = null;
                        showAuthOverlay();
                    }
                } catch (err) {
                    console.error("Session verification failed", err);
                }
            }
        }, 5000);

        // Periodically refresh user presence and directories (every 10 seconds for Admins/Managers)
        setInterval(async () => {
            if (currentUser && (getEffectiveUserRole() === 'Admin' || getEffectiveUserRole() === 'Manager')) {
                try {
                    await populateDropdowns(); // Dynamic user status fetch and roster update
                } catch (err) {
                    console.error("Failed to automatically refresh directory status", err);
                }
            }
        }, 10000);

        // Periodically check for new notifications (every 10 seconds for all users)
        setInterval(async () => {
            if (currentUser) {
                await fetchNotifications(true);
            }
        }, 10000);

        // Automatically calculate hours from check-in/out (for all roles as a helpful suggestion)
        function autoCalculateHours() {
            const role = getEffectiveUserRole();
            // For Manager: already handled by calculateHoursFromTime (locked field)
            // For others: only auto-fill if the hours field is empty or default
            if (role === 'Manager') return; // Manager handled by calculateHoursFromTime

            const checkinVal = document.getElementById('log_checkin').value;
            const checkoutVal = document.getElementById('log_checkout').value;
            if (!checkinVal || !checkoutVal) return;

            const [inH, inM] = checkinVal.split(':').map(Number);
            const [outH, outM] = checkoutVal.split(':').map(Number);

            let diffMin = (outH * 60 + outM) - (inH * 60 + inM);
            if (diffMin < 0) {
                diffMin += 24 * 60; // Handle overnight shifts
            }

            const diffHours = diffMin / 60;
            // Round to the nearest 0.5 hours (e.g. 8.25 becomes 8.5) and clamp between 0.5 and 24
            const finalHours = Math.min(Math.max(Math.round(diffHours * 2) / 2, 0.5), 24);
            
            document.getElementById('log_hours').value = finalHours;
        }

        document.getElementById('log_checkin').addEventListener('change', autoCalculateHours);
        document.getElementById('log_checkout').addEventListener('change', autoCalculateHours);
        autoCalculateHours(); // Run once initially

        // Make clicking anywhere inside the time input box trigger the browser timepicker popup
        document.getElementById('log_checkin').addEventListener('click', function() {
            try { this.showPicker(); } catch(e) {}
        });
        document.getElementById('log_checkout').addEventListener('click', function() {
            try { this.showPicker(); } catch(e) {}
        });

        // ----------------- SUBMIT SUBMISSIONS -----------------

        // Auth Form: Sign In
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const submitBtn = this.querySelector('.btn-submit');
            submitBtn.disabled = true;
            
            const payload = {
                username: document.getElementById('login_username').value,
                password: document.getElementById('login_password').value
            };

            try {
                const res = await fetch(`${API_URL}/login`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload),
                    credentials: 'include'
                });
                
                const data = await res.json();
                if (res.ok) {
                    currentUser = data.user;
                    showToast("Access approved!", "success");
                    setupPortalForRole();
                    fetchData();
                    this.reset();
                    if (!currentUser.employee_id) {
                        setTimeout(() => {
                            showToast("Please update your Employee ID in your profile settings.", "warning");
                            openProfileModal(true);
                        }, 1500);
                    }
                } else {
                    showToast(data.error || "Authentication failed", "error");
                }
            } catch (err) {
                showToast("Failed to reach auth gateway", "error");
            } finally {
                submitBtn.disabled = false;
            }
        });

        // Auth Form: Sign Up
        document.getElementById('signupForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const submitBtn = this.querySelector('.btn-submit');
            submitBtn.disabled = true;

            const payload = {
                full_name: document.getElementById('signup_fullname').value,
                username: document.getElementById('signup_username').value,
                password: document.getElementById('signup_password').value,
                role: document.getElementById('signup_role').value,
                email: document.getElementById('signup_email').value,
                title: document.getElementById('signup_title').value,
                employee_id: document.getElementById('signup_empid').value
            };

            try {
                const res = await fetch(`${API_URL}/signup`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                
                const data = await res.json();
                if (res.ok) {
                    showToast("Registration successful! Please login.", "success");
                    toggleAuthView('login');
                    this.reset();
                } else {
                    showToast(data.error || "Signup failed", "error");
                }
            } catch (err) {
                showToast("Failed to reach auth gateway", "error");
            } finally {
                submitBtn.disabled = false;
            }
        });

        // Form Submit: Save Daily Log
        document.getElementById('logForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const submitBtn = this.querySelector('.btn-submit');
            submitBtn.disabled = true;

            const selectedLogDate = document.getElementById('log_date').value;
            const d = new Date();
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            const localTodayStr = `${year}-${month}-${day}`;

            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            const yestYear = yesterday.getFullYear();
            const yestMonth = String(yesterday.getMonth() + 1).padStart(2, '0');
            const yestDay = String(yesterday.getDate()).padStart(2, '0');
            const localYesterdayStr = `${yestYear}-${yestMonth}-${yestDay}`;

            if (selectedLogDate && (selectedLogDate < localYesterdayStr || selectedLogDate > localTodayStr)) {
                showToast("Daily log date must be yesterday or today.", "error");
                submitBtn.disabled = false;
                return;
            }

            const hoursLogged = parseFloat(document.getElementById('log_hours').value);
            if (hoursLogged > 9.0) {
                showToast("Hours cannot exceed 9 hours per day. Please start freshly from next day.", "error");
                submitBtn.disabled = false;
                return;
            }

            const selectedMood = document.querySelector('#log_mood_group .rating-btn.active').dataset.value;
            const payload = {
                date_logged: selectedLogDate,
                hours_worked: parseFloat(document.getElementById('log_hours').value),
                check_in: document.getElementById('log_checkin').value,
                check_out: document.getElementById('log_checkout').value,
                task_category: document.getElementById('log_category').value,
                tasks_completed: document.getElementById('log_tasks').value,
                deliverable_completed: document.getElementById('log_deliverable').value,
                blockers: document.getElementById('log_blockers').value || 'None',
                skills_used: document.getElementById('log_skills').value || '',
                mood: parseInt(selectedMood),
                notes: document.getElementById('log_notes').value || ''
            };

            // If Admin/Manager is logging on behalf, supply target username
            const behalfSelect = document.getElementById('log_intern_name');
            if (behalfSelect && behalfSelect.style.display !== 'none' && behalfSelect.value) {
                payload.intern_name = behalfSelect.value;
            }

            try {
                let url = '/submit';
                let method = 'POST';
                if (editingLogId) {
                    url = `/logs/${editingLogId}`;
                    method = 'PUT';
                }

                const res = await apiFetch(url, {
                    method: method,
                    body: payload
                });
                
                if (res.ok) {
                    showToast(editingLogId ? "Daily log entry updated!" : "Daily log saved!", "success");
                    cancelEditLog(); // Reset form and states
                    fetchData();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to save daily log", "error");
                }
            } catch (err) {
                showToast("Failed to reach daily log endpoint", "error");
            } finally {
                submitBtn.disabled = false;
            }
        });

        // Edit Log Handler
        function editLog(logId) {
            const log = state.logs.find(l => l.id === logId);
            if (!log) return;

            editingLogId = logId;
            
            // Populate form fields
            document.getElementById('log_date').value = log.date_logged;
            document.getElementById('log_hours').value = log.hours_worked;
            document.getElementById('log_checkin').value = log.check_in || "09:00";
            document.getElementById('log_checkout').value = log.check_out || "18:00";
            document.getElementById('log_category').value = log.task_category || "Other";
            document.getElementById('log_tasks').value = log.tasks_completed;
            document.getElementById('log_deliverable').value = log.deliverable_completed || "No";
            document.getElementById('log_blockers').value = log.blockers || "None";
            document.getElementById('log_skills').value = log.skills_used || "";
            document.getElementById('log_notes').value = log.notes || "";

            // Populate mood rating buttons
            document.querySelectorAll('#log_mood_group .rating-btn').forEach(btn => {
                if (parseInt(btn.dataset.value) === parseInt(log.mood || 5)) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });

            // Adjust buttons UI
            document.getElementById('btn-save-log').innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Update Log Entry';
            document.getElementById('btn-cancel-edit-log').style.display = 'block';

            // Scroll to the daily log form panel for visibility
            document.getElementById('logForm').scrollIntoView({ behavior: 'smooth' });
        }

        // Cancel Edit Log
        function cancelEditLog() {
            editingLogId = null;
            document.getElementById('logForm').reset();
            document.getElementById('log_date').value = todayStr; // reset date to today
            document.getElementById('btn-save-log').innerHTML = '<i class="fa-solid fa-paper-plane"></i> Save Daily Log';
            document.getElementById('btn-cancel-edit-log').style.display = 'none';
        }

        // Delete Log Handler
        async function deleteLog(logId) {
            if (!confirm("Are you sure you want to delete this daily log entry?")) return;
            try {
                const res = await apiFetch(`/logs/${logId}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    showToast("Daily log entry deleted.");
                    fetchData();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to delete log entry", "error");
                }
            } catch (err) {
                showToast("Failed to delete log entry", "error");
            }
        }

        // Remove User Handler (Admin/Manager only)
        async function removeUser(userId, fullName) {
            if (!confirm(`Are you sure you want to completely remove ${fullName} from the portal? This will also delete all their tasks, logs, skills, and feedback.`)) return;
            try {
                const res = await apiFetch(`/users/${userId}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    showToast(`User ${fullName} removed successfully!`);
                    
                    // Re-populate dropdowns and reload rosters
                    await populateDropdowns(); 
                    
                    // Refresh data in other tabs
                    fetchData();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to remove user", "error");
                }
            } catch (err) {
                showToast("Failed to remove user", "error");
            }
        }

        // Approve User Handler (Admin only)
        async function approveUser(userId, fullName) {
            if (!confirm(`Are you sure you want to approve user ${fullName}? They will be allowed to log in to the portal.`)) return;
            try {
                const res = await apiFetch(`/users/${userId}/approve`, {
                    method: 'PUT'
                });
                if (res.ok) {
                    showToast(`User ${fullName} approved successfully!`);
                    
                    // Re-populate dropdowns and reload rosters
                    await populateDropdowns(); 
                    
                    // Refresh data in other tabs
                    fetchData();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to approve user", "error");
                }
            } catch (err) {
                showToast("Failed to approve user", "error");
            }
        }

        // Restrict User Handler (Admin/Manager only)
        async function restrictUser(userId, fullName) {
            if (!confirm(`Are you sure you want to restrict user ${fullName}? They will be temporarily blocked from logging in.`)) return;
            try {
                const res = await apiFetch(`/users/${userId}/restrict`, {
                    method: 'PUT'
                });
                if (res.ok) {
                    showToast(`User ${fullName} has been restricted successfully!`);
                    
                    // Re-populate dropdowns and reload rosters
                    await populateDropdowns(); 
                    
                    // Refresh data in other tabs
                    fetchData();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to restrict user", "error");
                }
            } catch (err) {
                showToast("Failed to restrict user", "error");
            }
        }

        // Unrestrict User Handler (Admin/Manager only)
        async function unrestrictUser(userId, fullName) {
            if (!confirm(`Are you sure you want to unrestrict user ${fullName}? Their access will be restored.`)) return;
            try {
                const res = await apiFetch(`/users/${userId}/unrestrict`, {
                    method: 'PUT'
                });
                if (res.ok) {
                    showToast(`User ${fullName} restriction lifted successfully!`);
                    
                    // Re-populate dropdowns and reload rosters
                    await populateDropdowns(); 
                    
                    // Refresh data in other tabs
                    fetchData();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to unrestrict user", "error");
                }
            } catch (err) {
                showToast("Failed to unrestrict user", "error");
            }
        }

        // --- Supervisor User Creation Modal Logic ---
        function openCreateMemberModal() {
            // Clear inputs
            document.getElementById('create_member_username').value = '';
            document.getElementById('create_member_fullname').value = '';
            document.getElementById('create_member_email').value = '';
            document.getElementById('create_member_title').value = '';
            
            // Populate roles select dropdown based on creator role
            const roleSelect = document.getElementById('create_member_role');
            roleSelect.innerHTML = '';
            const role = getEffectiveUserRole();
            if (role === 'Admin') {
                roleSelect.innerHTML = `
                    <option value="Intern">Intern</option>
                    <option value="Employee">Employee</option>
                    <option value="Manager">Manager</option>
                    <option value="Admin">Admin</option>
                    <option value="Guest">Guest</option>
                `;
            } else if (role === 'Manager') {
                roleSelect.innerHTML = `
                    <option value="Intern">Intern</option>
                    <option value="Employee">Employee</option>
                `;
            }
            
            // Generate a default random password
            generateRandomPassword();
            
            // Show modal
            document.getElementById('create-member-modal').style.display = 'flex';
        }

        function closeCreateMemberModal() {
            document.getElementById('create-member-modal').style.display = 'none';
        }

        function generateRandomPassword() {
            const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*";
            let pass = "";
            for (let i = 0; i < 10; i++) {
                pass += chars.charAt(Math.floor(Math.random() * chars.length));
            }
            document.getElementById('create_member_password').value = pass;
        }

        async function handleCreateMemberSubmit(e) {
            e.preventDefault();
            const username = document.getElementById('create_member_username').value.trim();
            const password = document.getElementById('create_member_password').value;
            const full_name = document.getElementById('create_member_fullname').value.trim();
            const email = document.getElementById('create_member_email').value.trim();
            const role = document.getElementById('create_member_role').value;
            const title = document.getElementById('create_member_title').value.trim();

            const payload = {
                username, password, full_name, email, role, title
            };

            try {
                const res = await apiFetch('/users/create', {
                    method: 'POST',
                    body: payload
                });
                const data = await res.json();
                if (res.ok) {
                    showToast(data.message || "User created successfully!");
                    closeCreateMemberModal();
                    
                    // Re-populate dropdowns and reload rosters
                    await populateDropdowns();
                } else {
                    showToast(data.error || "Failed to create user", "error");
                }
            } catch (err) {
                showToast("Failed to create user", "error");
                console.error(err);
            }
        }

        // Form Submit: Create Project Task
        document.getElementById('taskForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const submitBtn = this.querySelector('.btn-submit');
            submitBtn.disabled = true;

            const selectedDueDate = document.getElementById('task_due').value;
            const d = new Date();
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            const localTodayStr = `${year}-${month}-${day}`;

            if (selectedDueDate && selectedDueDate < localTodayStr) {
                showToast("Due date cannot be in the past!", "error");
                submitBtn.disabled = false;
                return;
            }

            const payload = {
                intern_name: document.getElementById('task_intern_name').value,
                task_name: document.getElementById('task_name').value,
                category: document.getElementById('task_category').value,
                assigned_date: localTodayStr,
                due_date: selectedDueDate,
                priority: document.getElementById('task_priority').value,
                status: 'Not Started',
                percent_done: 0,
                notes: document.getElementById('task_notes').value || ''
            };

            try {
                const res = await apiFetch('/tasks', {
                    method: 'POST',
                    body: payload
                });
                if (res.ok) {
                    showToast("Task assigned successfully!");
                    this.reset();
                    document.getElementById('task_due').value = todayStr;
                    fetchData();
                }
            } catch (err) {
                // Handled
            } finally {
                submitBtn.disabled = false;
            }
        });

        // Form Submit: Log Skill
        document.getElementById('skillForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const submitBtn = this.querySelector('.btn-submit');
            submitBtn.disabled = true;

            const payload = {
                date_logged: new Date().toISOString().split('T')[0],
                skill_tool: document.getElementById('skill_tool').value,
                category: document.getElementById('skill_category').value,
                resource_course: document.getElementById('skill_resource').value || 'Self Study',
                hours_spent: parseFloat(document.getElementById('skill_hours').value),
                proficiency_before: parseInt(document.getElementById('skill_before').value),
                proficiency_after: parseInt(document.getElementById('skill_after').value),
                certificate: document.getElementById('skill_cert').value,
                notes: document.getElementById('skill_notes').value || ''
            };

            try {
                const res = await apiFetch('/skills', {
                    method: 'POST',
                    body: payload
                });
                if (res.ok) {
                    showToast("Skill added to profile!");
                    this.reset();
                    fetchData();
                }
            } catch (err) {
                // Handled
            } finally {
                submitBtn.disabled = false;
            }
        });

        // Form Submit: Save Mentor Feedback
        document.getElementById('feedbackForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const submitBtn = this.querySelector('.btn-submit');
            submitBtn.disabled = true;

            const selectedFollowUpDate = document.getElementById('fb_followdate').value;
            const d = new Date();
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            const localTodayStr = `${year}-${month}-${day}`;

            if (selectedFollowUpDate && selectedFollowUpDate < localTodayStr) {
                showToast("Follow-up date cannot be in the past!", "error");
                submitBtn.disabled = false;
                return;
            }

            const payload = {
                intern_name: document.getElementById('fb_intern_name').value,
                date_logged: document.getElementById('fb_date').value,
                type: document.getElementById('fb_type').value,
                feedback_summary: document.getElementById('fb_summary').value,
                strength_noted: document.getElementById('fb_strengths').value || '',
                area_to_improve: document.getElementById('fb_improve').value || '',
                action_taken: document.getElementById('fb_action').value || '',
                follow_up: document.getElementById('fb_followup').value,
                follow_up_date: selectedFollowUpDate || ''
            };

            try {
                const res = await apiFetch('/feedback', {
                    method: 'POST',
                    body: payload
                });
                if (res.ok) {
                    showToast("Feedback review logged!");
                    this.reset();
                    document.getElementById('fb_date').value = todayStr;
                    fetchData();
                }
            } catch (err) {
                // Handled
            } finally {
                submitBtn.disabled = false;
            }
        });

        // Toggle Password Input Visibility
        function togglePasswordVisibility(inputId, iconId) {
            const input = document.getElementById(inputId);
            const icon = document.getElementById(iconId);
            if (input && icon) {
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                } else {
                    input.type = 'password';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                }
            }
        }

        // Update User Role (Admin only)
        async function updateUserRole(userId, newRole) {
            if (!confirm(`Are you sure you want to change this user's role to ${newRole}?`)) {
                // Re-render to revert dropdown selection if canceled
                renderTeamRoster();
                return;
            }
            try {
                const res = await apiFetch(`/users/${userId}/role`, {
                    method: 'PUT',
                    body: { role: newRole }
                });
                if (res.ok) {
                    showToast("User role updated successfully!");
                    // Re-populate dropdowns and fetch data
                    await populateDropdowns();
                    fetchData();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to update role", "error");
                    renderTeamRoster();
                }
            } catch (err) {
                showToast("Failed to update user role", "error");
                renderTeamRoster();
            }
        }

        // ----------------- COLLABORATION & SECURE MESSAGING LOGIC -----------------

        // Web Crypto Cryptographic Functions for End-to-End Encryption (E2EE)
        function arrayBufferToBase64(buffer) {
            let binary = '';
            const bytes = new Uint8Array(buffer);
            const len = bytes.byteLength;
            for (let i = 0; i < len; i++) {
                binary += String.fromCharCode(bytes[i]);
            }
            return window.btoa(binary);
        }

        function base64ToArrayBuffer(base64) {
            const binary_string = window.atob(base64);
            const len = binary_string.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binary_string.charCodeAt(i);
            }
            return bytes.buffer;
        }

        async function generateKeyPair() {
            return await window.crypto.subtle.generateKey(
                {
                    name: "RSA-OAEP",
                    modulusLength: 2048,
                    publicExponent: new Uint8Array([1, 0, 1]),
                    hash: "SHA-256"
                },
                true,
                ["encrypt", "decrypt"]
            );
        }

        async function exportPublicKey(key) {
            return await window.crypto.subtle.exportKey("jwk", key);
        }

        async function exportPrivateKey(key) {
            return await window.crypto.subtle.exportKey("jwk", key);
        }

        async function importPublicKey(jwk) {
            return await window.crypto.subtle.importKey(
                "jwk",
                jwk,
                {
                    name: "RSA-OAEP",
                    hash: "SHA-256"
                },
                true,
                ["encrypt"]
            );
        }

        async function importPrivateKey(jwk) {
            return await window.crypto.subtle.importKey(
                "jwk",
                jwk,
                {
                    name: "RSA-OAEP",
                    hash: "SHA-256"
                },
                true,
                ["decrypt"]
            );
        }

        async function generateAESKey() {
            return await window.crypto.subtle.generateKey(
                {
                    name: "AES-GCM",
                    length: 256
                },
                true,
                ["encrypt", "decrypt"]
            );
        }

        async function encryptMessage(aesKey, plaintext) {
            const iv = window.crypto.getRandomValues(new Uint8Array(12));
            const encoder = new TextEncoder();
            const ciphertext = await window.crypto.subtle.encrypt(
                {
                    name: "AES-GCM",
                    iv: iv
                },
                aesKey,
                encoder.encode(plaintext)
            );
            return {
                ciphertext: arrayBufferToBase64(ciphertext),
                iv: arrayBufferToBase64(iv)
            };
        }

        async function decryptMessage(aesKey, ciphertextBase64, ivBase64) {
            const ciphertext = base64ToArrayBuffer(ciphertextBase64);
            const iv = base64ToArrayBuffer(ivBase64);
            const decrypted = await window.crypto.subtle.decrypt(
                {
                    name: "AES-GCM",
                    iv: iv
                },
                aesKey,
                ciphertext
            );
            const decoder = new TextDecoder();
            return decoder.decode(decrypted);
        }

        async function encryptAESKeyWithRSA(rsaPublicKey, aesKey) {
            const exportedAES = await window.crypto.subtle.exportKey("raw", aesKey);
            const encryptedKey = await window.crypto.subtle.encrypt(
                {
                    name: "RSA-OAEP"
                },
                rsaPublicKey,
                exportedAES
            );
            return arrayBufferToBase64(encryptedKey);
        }

        async function decryptAESKeyWithRSA(rsaPrivateKey, encryptedKeyBase64) {
            const encryptedKey = base64ToArrayBuffer(encryptedKeyBase64);
            const decryptedAESRaw = await window.crypto.subtle.decrypt(
                {
                    name: "RSA-OAEP"
                },
                rsaPrivateKey,
                encryptedKey
            );
            return await window.crypto.subtle.importKey(
                "raw",
                decryptedAESRaw,
                "AES-GCM",
                true,
                ["encrypt", "decrypt"]
            );
        }

        // Initialize E2EE Keys for Logged-In User
        async function initializeE2EE() {
            if (!currentUser || currentUser.role === 'Guest') return;
            const privKeyKey = 'e2e_private_key_' + currentUser.username;
            const pubKeyKey = 'e2e_public_key_' + currentUser.username;
            
            let privKeyJWK = localStorage.getItem(privKeyKey);
            let pubKeyJWK = localStorage.getItem(pubKeyKey);
            
            if (!privKeyJWK || !pubKeyJWK) {
                console.log("Generating secure E2EE encryption key pair...");
                const pair = await generateKeyPair();
                const exportedPub = await exportPublicKey(pair.publicKey);
                const exportedPriv = await exportPrivateKey(pair.privateKey);
                
                privKeyJWK = JSON.stringify(exportedPriv);
                pubKeyJWK = JSON.stringify(exportedPub);
                
                localStorage.setItem(privKeyKey, privKeyJWK);
                localStorage.setItem(pubKeyKey, pubKeyJWK);
                
                // Upload public key to backend
                await apiFetch('/users/public_key', {
                    method: 'PUT',
                    body: { public_key: exportedPub }
                });
                console.log("E2EE key pair generated and registered successfully!");
            }
        }

        // ----------------- ANNOUNCEMENTS CORE LOGIC -----------------
        let annUploadedMediaUrl = "";
        let annUploadedMediaType = "";
        let annMediaRecorder = null;
        let annRecordedChunks = [];
        let annRecordSeconds = 0;
        let annRecordTimerInterval = null;
        let annRecordStream = null;

        async function startAnnRecording(isVideo) {
            try {
                const constraints = { audio: true, video: isVideo };
                const stream = await navigator.mediaDevices.getUserMedia(constraints);
                annRecordStream = stream;
                annRecordedChunks = [];
                annMediaRecorder = new MediaRecorder(stream);
                
                annMediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) {
                        annRecordedChunks.push(e.data);
                    }
                };

                annMediaRecorder.onstop = async () => {
                    if (annRecordSeconds > 0) {
                        const mime = isVideo ? 'video/webm' : 'audio/webm';
                        const blob = new Blob(annRecordedChunks, { type: mime });
                        const filename = isVideo ? 'video_note.webm' : 'voice_note.webm';
                        
                        showAnnPreview("recording", filename, isVideo ? 'video' : 'audio');
                        
                        const formData = new FormData();
                        formData.append('file', blob, filename);
                        try {
                            const res = await apiFetch('/upload', {
                                method: 'POST',
                                body: formData
                            });
                            if (res.ok) {
                                const data = await res.json();
                                annUploadedMediaUrl = data.url;
                                annUploadedMediaType = isVideo ? 'video' : 'audio';
                                showAnnPreview(data.url, filename, isVideo ? 'video' : 'audio');
                            } else {
                                showToast("Upload failed", "error");
                                clearAnnMedia();
                            }
                        } catch (err) {
                            showToast("Upload failed", "error");
                            clearAnnMedia();
                        }
                    }
                    stream.getTracks().forEach(track => track.stop());
                };

                document.getElementById('ann-recording-bar').style.display = 'flex';
                document.getElementById('ann-recording-type').innerText = isVideo ? 'video' : 'audio';
                annRecordSeconds = 0;
                document.getElementById('ann-recording-timer').innerText = "00:00";
                
                annRecordTimerInterval = setInterval(() => {
                    annRecordSeconds++;
                    const mins = String(Math.floor(annRecordSeconds / 60)).padStart(2, '0');
                    const secs = String(annRecordSeconds % 60).padStart(2, '0');
                    document.getElementById('ann-recording-timer').innerText = `${mins}:${secs}`;
                }, 1000);

                annMediaRecorder.start();
            } catch (err) {
                showToast("Microphone/Camera access denied or unavailable", "error");
                console.error(err);
            }
        }

        function stopAnnRecording(isCancel) {
            if (annRecordTimerInterval) {
                clearInterval(annRecordTimerInterval);
                annRecordTimerInterval = null;
            }
            document.getElementById('ann-recording-bar').style.display = 'none';

            if (annMediaRecorder && annMediaRecorder.state !== 'inactive') {
                if (isCancel) {
                    annRecordSeconds = 0;
                }
                annMediaRecorder.stop();
            }
        }

        function showAnnPreview(url, filename, type) {
            const container = document.getElementById('ann-preview-container');
            const mediaDiv = document.getElementById('ann-preview-media');
            const infoDiv = document.getElementById('ann-preview-info');
            
            container.style.display = 'flex';
            infoDiv.innerText = filename;
            
            if (url === 'recording') {
                mediaDiv.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="font-size:18px;"></i>';
                return;
            }

            if (type === 'image') {
                mediaDiv.innerHTML = `<img src="${url}" />`;
            } else if (type === 'video') {
                mediaDiv.innerHTML = `<i class="fa-solid fa-file-video" style="font-size:24px; color:#f43f5e;"></i>`;
            } else if (type === 'audio') {
                mediaDiv.innerHTML = `<i class="fa-solid fa-file-audio" style="font-size:24px; color:#10b981;"></i>`;
            }
        }

        function clearAnnMedia() {
            annUploadedMediaUrl = "";
            annUploadedMediaType = "";
            document.getElementById('ann-preview-container').style.display = 'none';
            document.getElementById('ann-file-input').value = "";
        }

        async function handleAnnFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            let type = 'image';
            if (file.type.startsWith('video/')) type = 'video';
            else if (file.type.startsWith('audio/')) type = 'audio';

            showAnnPreview('recording', file.name, type);

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await apiFetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                if (res.ok) {
                    const data = await res.json();
                    annUploadedMediaUrl = data.url;
                    annUploadedMediaType = type;
                    showAnnPreview(data.url, file.name, type);
                } else {
                    showToast("Upload failed", "error");
                    clearAnnMedia();
                }
            } catch (err) {
                showToast("Upload failed", "error");
                clearAnnMedia();
            }
        }

        async function fetchAnnouncements() {
            if (!currentUser) return;
            try {
                const res = await apiFetch('/announcements');
                if (!res.ok) return;
                const list = await res.json();
                const feed = document.getElementById('announcements-feed');
                
                const currentHash = list.map(item => item.id).join('_');
                if (currentHash === lastAnnouncementsHash) return;
                lastAnnouncementsHash = currentHash;
                
                if (list.length === 0) {
                    feed.innerHTML = `
                        <div class="chat-empty-view" style="padding: 20px;">
                            <i class="fa-solid fa-bullhorn" style="font-size: 32px; color:rgba(255,255,255,0.05); margin-bottom:8px;"></i>
                            <h4 style="margin:0; font-size:14px; color:var(--text-color);">No announcements yet</h4>
                            <p style="margin:4px 0 0 0; font-size:12px;">Be the first to post something to the team!</p>
                        </div>`;
                    return;
                }

                let html = "";
                list.forEach(item => {
                    const dateStr = formatSessionTime(item.created_at);
                    const initial = (item.sender_fullname || item.sender || "U")[0].toUpperCase();
                    
                    let mediaHtml = "";
                    if (item.media_url) {
                        if (item.media_type === 'image') {
                            mediaHtml = `<div class="announcement-media"><img src="${item.media_url}" onclick="window.open('${item.media_url}')" /></div>`;
                        } else if (item.media_type === 'video') {
                            mediaHtml = `<div class="announcement-media"><video src="${item.media_url}" controls></video></div>`;
                        } else if (item.media_type === 'audio') {
                            mediaHtml = `<div class="announcement-media"><audio src="${item.media_url}" controls></audio></div>`;
                        }
                    }

                    let badgeClass = 'badge-secondary';
                    if (item.sender_role === 'Admin') badgeClass = 'badge-danger';
                    else if (item.sender_role === 'Manager') badgeClass = 'badge-warning';
                    else if (item.sender_role === 'Employee') badgeClass = 'badge-primary';

                    const isAuthorOrSupervisor = currentUser.role !== 'Guest' && (item.sender === currentUser.username || getEffectiveUserRole() === 'Admin' || getEffectiveUserRole() === 'Manager');
                    const deleteBtnHtml = isAuthorOrSupervisor ? `
                        <button class="delete-announcement-btn" onclick="deleteAnnouncement('${item.id}')" title="Delete Announcement" style="background:none; border:none; color:var(--text-muted); cursor:pointer; padding:4px 8px; transition:color 0.2s;" onmouseover="this.style.color='#f43f5e'" onmouseout="this.style.color='var(--text-muted)'">
                            <i class="fa-solid fa-trash" style="font-size:12px;"></i>
                        </button>
                    ` : '';

                    html += `
                        <div class="announcement-card">
                            <div class="announcement-header">
                                <div class="announcement-author">
                                    <div class="chat-user-avatar" style="width:36px; height:36px; margin:0;">${initial}</div>
                                    <div class="announcement-author-details">
                                        <h5>${escapeHTML(item.sender_fullname)} <span class="badge ${badgeClass}" style="font-size:9px; padding:2px 6px; margin-left:5px;">${item.sender_role}</span></h5>
                                        <span>@${escapeHTML(item.sender)}</span>
                                    </div>
                                </div>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <div class="announcement-time">${dateStr}</div>
                                    ${deleteBtnHtml}
                                </div>
                            </div>
                            <div class="announcement-body">
                                ${escapeHTML(item.content)}
                                ${mediaHtml}
                            </div>
                        </div>`;
                });
                
                const wasScrolledToBottom = feed.scrollHeight - feed.clientHeight <= feed.scrollTop + 50;
                feed.innerHTML = html;
                if (wasScrolledToBottom) {
                    feed.scrollTop = feed.scrollHeight;
                }
            } catch (err) {
                console.error("Failed to load announcements", err);
            }
        }

        async function deleteAnnouncement(announcementId) {
            if (!confirm("Are you sure you want to delete this announcement?")) return;
            try {
                const res = await apiFetch(`/announcements/${announcementId}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    showToast("Announcement deleted successfully!");
                    fetchAnnouncements();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to delete announcement", "error");
                }
            } catch (err) {
                showToast("Failed to delete announcement", "error");
                console.error(err);
            }
        }

        document.getElementById('announcementForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const input = document.getElementById('announcement-input');
            const content = input.value.trim();
            if (!content) return;

            const payload = {
                content: content,
                media_url: annUploadedMediaUrl,
                media_type: annUploadedMediaType
            };

            try {
                const res = await apiFetch('/announcements', {
                    method: 'POST',
                    body: payload
                });
                if (res.ok) {
                    input.value = "";
                    clearAnnMedia();
                    fetchAnnouncements();
                } else {
                    showToast("Failed to post announcement", "error");
                }
            } catch (err) {
                showToast("Failed to post announcement", "error");
            }
        });


        // ----------------- DIRECT SECURE MESSAGING (E2EE) LOGIC -----------------
        let dmActiveUser = null;
        let dmUsers = [];
        let dmUploadedMediaUrl = "";
        let dmUploadedMediaType = "";
        let lastAnnouncementsHash = "";
        let lastDMMessagesHash = "";
        const dmDecryptionCache = new Map();
        let dmMediaRecorder = null;
        let dmRecordedChunks = [];
        let dmRecordSeconds = 0;
        let dmRecordTimerInterval = null;
        let dmRecordStream = null;

        async function startDMRecording(isVideo) {
            try {
                const constraints = { audio: true, video: isVideo };
                const stream = await navigator.mediaDevices.getUserMedia(constraints);
                dmRecordStream = stream;
                dmRecordedChunks = [];
                dmMediaRecorder = new MediaRecorder(stream);
                
                dmMediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) {
                        dmRecordedChunks.push(e.data);
                    }
                };

                dmMediaRecorder.onstop = async () => {
                    if (dmRecordSeconds > 0) {
                        const mime = isVideo ? 'video/webm' : 'audio/webm';
                        const blob = new Blob(dmRecordedChunks, { type: mime });
                        const filename = isVideo ? 'video_note.webm' : 'voice_note.webm';
                        
                        showDMPreview("recording", filename, isVideo ? 'video' : 'audio');
                        
                        const formData = new FormData();
                        formData.append('file', blob, filename);
                        try {
                            const res = await apiFetch('/upload', {
                                method: 'POST',
                                body: formData
                            });
                            if (res.ok) {
                                const data = await res.json();
                                dmUploadedMediaUrl = data.url;
                                dmUploadedMediaType = isVideo ? 'video' : 'audio';
                                showDMPreview(data.url, filename, isVideo ? 'video' : 'audio');
                            } else {
                                showToast("Upload failed", "error");
                                clearDMMedia();
                            }
                        } catch (err) {
                            showToast("Upload failed", "error");
                            clearDMMedia();
                        }
                    }
                    stream.getTracks().forEach(track => track.stop());
                };

                document.getElementById('dm-recording-bar').style.display = 'flex';
                document.getElementById('dm-recording-type').innerText = isVideo ? 'video' : 'audio';
                dmRecordSeconds = 0;
                document.getElementById('dm-recording-timer').innerText = "00:00";
                
                dmRecordTimerInterval = setInterval(() => {
                    dmRecordSeconds++;
                    const mins = String(Math.floor(dmRecordSeconds / 60)).padStart(2, '0');
                    const secs = String(dmRecordSeconds % 60).padStart(2, '0');
                    document.getElementById('dm-recording-timer').innerText = `${mins}:${secs}`;
                }, 1000);

                dmMediaRecorder.start();
            } catch (err) {
                showToast("Microphone/Camera access denied or unavailable", "error");
                console.error(err);
            }
        }

        function stopDMRecording(isCancel) {
            if (dmRecordTimerInterval) {
                clearInterval(dmRecordTimerInterval);
                dmRecordTimerInterval = null;
            }
            document.getElementById('dm-recording-bar').style.display = 'none';

            if (dmMediaRecorder && dmMediaRecorder.state !== 'inactive') {
                if (isCancel) {
                    dmRecordSeconds = 0;
                }
                dmMediaRecorder.stop();
            }
        }

        function showDMPreview(url, filename, type) {
            const container = document.getElementById('dm-preview-container');
            const mediaDiv = document.getElementById('dm-preview-media');
            const infoDiv = document.getElementById('dm-preview-info');
            
            container.style.display = 'flex';
            infoDiv.innerText = filename;
            
            if (url === 'recording') {
                mediaDiv.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="font-size:18px;"></i>';
                return;
            }

            if (type === 'image') {
                mediaDiv.innerHTML = `<img src="${url}" />`;
            } else if (type === 'video') {
                mediaDiv.innerHTML = `<i class="fa-solid fa-file-video" style="font-size:24px; color:#f43f5e;"></i>`;
            } else if (type === 'audio') {
                mediaDiv.innerHTML = `<i class="fa-solid fa-file-audio" style="font-size:24px; color:#10b981;"></i>`;
            }
        }

        function clearDMMedia() {
            dmUploadedMediaUrl = "";
            dmUploadedMediaType = "";
            document.getElementById('dm-preview-container').style.display = 'none';
            document.getElementById('dm-file-input').value = "";
        }

        async function handleDMFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            let type = 'image';
            if (file.type.startsWith('video/')) type = 'video';
            else if (file.type.startsWith('audio/')) type = 'audio';

            showDMPreview('recording', file.name, type);

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await apiFetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                if (res.ok) {
                    const data = await res.json();
                    dmUploadedMediaUrl = data.url;
                    dmUploadedMediaType = type;
                    showDMPreview(data.url, file.name, type);
                } else {
                    showToast("Upload failed", "error");
                    clearDMMedia();
                }
            } catch (err) {
                showToast("Upload failed", "error");
                clearDMMedia();
            }
        }

        async function fetchDMUsersList() {
            try {
                const res = await apiFetch('/users');
                if (!res.ok) return;
                const list = await res.json();
                
                dmUsers = list.filter(u => u.username !== currentUser.username && !isTestUser(u.username, u.full_name));
                await refreshDMConversations();
            } catch (err) {
                console.error("Failed to fetch DM users list", err);
            }
        }

        async function refreshDMConversations() {
            if (!currentUser) return;
            try {
                const res = await apiFetch('/direct_messages/conversations');
                if (!res.ok) return;
                const conversations = await res.json();
                
                dmUsers.forEach(u => {
                    const conv = conversations[u.username];
                    if (conv) {
                        u.messageCount = conv.received_count || 0;
                        u.unreadCount = conv.unread_count || 0;
                        u.lastMessageTime = conv.last_message_time ? new Date(conv.last_message_time).getTime() : 0;
                    } else {
                        u.messageCount = 0;
                        u.unreadCount = 0;
                        u.lastMessageTime = 0;
                    }
                });
                
                dmUsers.sort((a, b) => {
                    const timeA = a.lastMessageTime || 0;
                    const timeB = b.lastMessageTime || 0;
                    if (timeA !== timeB) {
                        return timeB - timeA;
                    }
                    return a.full_name.localeCompare(b.full_name);
                });
                
                filterDMUsers();
            } catch (err) {
                console.error("Failed to refresh DM conversations", err);
            }
        }

        function filterDMUsers() {
            const query = document.getElementById('dm-user-search').value.toLowerCase().trim();
            const listDiv = document.getElementById('dm-users-list');
            
            let html = "";
            const filtered = dmUsers.filter(u => u.full_name.toLowerCase().includes(query) || u.username.toLowerCase().includes(query));
            
            if (filtered.length === 0) {
                listDiv.innerHTML = '<div style="font-size:12px; color:var(--text-muted); text-align:center; padding:20px;">No users found</div>';
                return;
            }

            filtered.forEach(u => {
                const initial = (u.full_name || u.username || "U")[0].toUpperCase();
                const isActive = dmActiveUser && dmActiveUser.username === u.username;
                const isOnline = u.status === 'Available';
                const statusDot = isOnline ? 'online' : 'offline';
                
                let badgeHtml = "";
                if (u.unreadCount > 0) {
                    badgeHtml = `<span style="background: #ef4444; color: #fff; font-size: 10px; padding: 1px 6px; border-radius: 10px; font-weight: 600;">${u.unreadCount} new</span>`;
                }

                html += `
                    <div class="chat-user-item ${isActive ? 'active' : ''}" onclick="selectDMUser('${u.username}')">
                        <div class="chat-user-avatar">${initial}</div>
                        <div class="chat-user-info">
                            <div class="chat-user-name">
                                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 130px;">${escapeHTML(u.full_name)}</span>
                                <div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
                                    ${badgeHtml}
                                    <div class="chat-user-dot ${statusDot}"></div>
                                </div>
                            </div>
                            <div class="chat-user-status">${u.role} (${u.title || ''})</div>
                        </div>
                    </div>`;
            });
            listDiv.innerHTML = html;
        }

        async function selectDMUser(username) {
            const targetUser = dmUsers.find(u => u.username === username);
            if (!targetUser) return;

            dmActiveUser = targetUser;
            lastDMMessagesHash = ""; // Reset hash on user selection to force render
            
            document.getElementById('dm-chat-empty-state').style.display = 'none';
            document.getElementById('dm-chat-active-window').style.display = 'flex';
            
            filterDMUsers();

            document.getElementById('dm-active-name').innerText = targetUser.full_name;
            document.getElementById('dm-active-avatar').innerText = targetUser.full_name[0].toUpperCase();
            
            const isOnline = targetUser.status === 'Available';
            document.getElementById('dm-active-status').innerText = isOnline ? 'Active Now' : 'Logged Out';
            document.getElementById('dm-active-status').style.color = isOnline ? '#22c55e' : 'var(--text-muted)';
            
            document.getElementById('dm-message-input').value = "";
            clearDMMedia();

            await fetchDMMessages();
        }

        async function fetchDMMessages() {
            if (!dmActiveUser) return;
            const recipient = dmActiveUser.username;
            
            try {
                const res = await apiFetch(`/direct_messages?recipient=${recipient}`);
                if (!res.ok) return;
                const list = await res.json();
                const feed = document.getElementById('dm-messages-feed');
                
                const currentHash = list.map(item => item.id + "_" + (item.seen ? '1' : '0')).join('_');
                if (currentHash === lastDMMessagesHash) return;
                lastDMMessagesHash = currentHash;

                const privKeyJWK = localStorage.getItem('e2e_private_key_' + currentUser.username);
                if (!privKeyJWK) {
                    feed.innerHTML = '<div style="color:#ef4444; font-size:13px; padding:20px; text-align:center;"><i class="fa-solid fa-triangle-exclamation"></i> E2EE Private Key missing on this browser. Unable to decrypt messages.</div>';
                    return;
                }

                const rsaPrivateKey = await importPrivateKey(JSON.parse(privKeyJWK));
                
                let html = "";
                for (let item of list) {
                    const isSentByMe = item.sender === currentUser.username;
                    const dateStr = formatSessionTime(item.created_at);
                    
                    let decryptedPayloadText = "[Decryption Error: Security key mismatch]";
                    let mediaUrl = "";
                    let mediaType = "";
                    
                    if (dmDecryptionCache.has(item.id)) {
                        const cached = dmDecryptionCache.get(item.id);
                        decryptedPayloadText = cached.text;
                        mediaUrl = cached.media_url;
                        mediaType = cached.media_type;
                    } else {
                        try {
                            const encryptedAESKey = isSentByMe ? item.sender_key_enc : item.recipient_key_enc;
                            const aesKey = await decryptAESKeyWithRSA(rsaPrivateKey, encryptedAESKey);
                            
                            const decryptedStr = await decryptMessage(aesKey, item.ciphertext, item.iv);
                            const payload = JSON.parse(decryptedStr);
                            
                            decryptedPayloadText = payload.text || "";
                            mediaUrl = payload.media_url || "";
                            mediaType = payload.media_type || "";
                            
                            dmDecryptionCache.set(item.id, {
                                text: decryptedPayloadText,
                                media_url: mediaUrl,
                                media_type: mediaType
                            });
                        } catch (decErr) {
                            console.warn("Decryption failed for message", item.id, decErr);
                            decryptedPayloadText = `<span style="color:#f43f5e; font-style:italic;"><i class="fa-solid fa-triangle-exclamation"></i> Decryption failed: Private key mismatch</span>`;
                        }
                    }

                    let mediaHtml = "";
                    if (mediaUrl) {
                        if (mediaType === 'image') {
                            mediaHtml = `<div class="chat-bubble-media"><img src="${mediaUrl}" onclick="window.open('${mediaUrl}')" /></div>`;
                        } else if (mediaType === 'video') {
                            mediaHtml = `<div class="chat-bubble-media"><video src="${mediaUrl}" controls></video></div>`;
                        } else if (mediaType === 'audio') {
                            mediaHtml = `<div class="chat-bubble-media"><audio src="${mediaUrl}" controls></audio></div>`;
                        }
                    }

                    const seenIcon = item.seen ? 
                        `<i class="fa-solid fa-check-double" title="Seen" style="color:#22c55e; margin-left:4px;"></i>` : 
                        `<i class="fa-solid fa-check" title="Sent" style="color:var(--text-muted); margin-left:4px;"></i>`;

                    const deleteBtn = (isSentByMe && currentUser.role !== 'Guest') ? `
                        <span class="delete-msg-btn" onclick="deleteDirectMessage('${item.id}', event)" title="Delete Message" style="cursor: pointer; color: var(--text-muted); opacity: 0.6; transition: opacity 0.2s; margin-left: 8px;" onmouseover="this.style.opacity='1'; this.style.color='#f43f5e'" onmouseout="this.style.opacity='0.6'; this.style.color='var(--text-muted)'">
                            <i class="fa-solid fa-trash" style="font-size: 10px;"></i>
                        </span>
                    ` : '';

                    html += `
                        <div class="chat-bubble ${isSentByMe ? 'sent' : 'received'}">
                            <div class="chat-bubble-content">
                                <div>${decryptedPayloadText}</div>
                                ${mediaHtml}
                            </div>
                            <div class="chat-bubble-time" style="display: flex; align-items: center; justify-content: ${isSentByMe ? 'flex-end' : 'flex-start'}; gap: 4px;">
                                <span>${dateStr}</span>
                                ${isSentByMe ? seenIcon + deleteBtn : ''}
                            </div>
                        </div>`;
                }
                
                if (html === "") {
                    feed.innerHTML = `
                        <div class="chat-empty-view" style="padding: 20px;">
                            <i class="fa-solid fa-lock" style="font-size: 24px; color:rgba(255,255,255,0.05); margin-bottom:8px;"></i>
                            <h4 style="margin:0; font-size:13px; color:var(--text-color);">Secure chat started</h4>
                            <p style="margin:4px 0 0 0; font-size:11px;">Messages are End-to-End Encrypted. Only you and ${escapeHTML(dmActiveUser.full_name)} can read them.</p>
                        </div>`;
                    return;
                }

                const wasScrolledToBottom = feed.scrollHeight - feed.clientHeight <= feed.scrollTop + 50;
                feed.innerHTML = html;
                if (wasScrolledToBottom) {
                    feed.scrollTop = feed.scrollHeight;
                }
            } catch (err) {
                console.error("Failed to load DMs", err);
            }
        }

        async function deleteDirectMessage(messageId, event) {
            if (event) event.stopPropagation();
            if (!confirm("Are you sure you want to delete this message?")) return;
            try {
                const res = await apiFetch(`/direct_messages/${messageId}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    showToast("Message deleted successfully!");
                    await fetchDMMessages();
                    await refreshDMConversations();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to delete message", "error");
                }
            } catch (err) {
                showToast("Failed to delete message", "error");
                console.error(err);
            }
        }

        document.getElementById('dmForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            if (!dmActiveUser) return;
            const input = document.getElementById('dm-message-input');
            const text = input.value.trim();
            if (!text && !dmUploadedMediaUrl) return;

            const sendBtn = document.getElementById('dm-btn-send');
            sendBtn.disabled = true;

            try {
                const pubKeyRes = await apiFetch(`/users/${dmActiveUser.username}/public_key`);
                if (!pubKeyRes.ok) {
                    const errData = await pubKeyRes.json();
                    showToast(errData.error || "Recipient has not activated E2EE keys yet", "error");
                    sendBtn.disabled = false;
                    return;
                }
                const { public_key: recipientPubKeyJWK } = await pubKeyRes.json();

                const senderPubKeyJWK = JSON.parse(localStorage.getItem('e2e_public_key_' + currentUser.username));
                
                const rsaRecipientPub = await importPublicKey(recipientPubKeyJWK);
                const rsaSenderPub = await importPublicKey(senderPubKeyJWK);

                const aesKey = await generateAESKey();

                const payloadStr = JSON.stringify({
                    text: text,
                    media_url: dmUploadedMediaUrl,
                    media_type: dmUploadedMediaType
                });

                const { ciphertext, iv } = await encryptMessage(aesKey, payloadStr);

                const sender_key_enc = await encryptAESKeyWithRSA(rsaSenderPub, aesKey);
                const recipient_key_enc = await encryptAESKeyWithRSA(rsaRecipientPub, aesKey);

                const res = await apiFetch('/direct_messages', {
                    method: 'POST',
                    body: {
                        recipient: dmActiveUser.username,
                        ciphertext: ciphertext,
                        iv: iv,
                        sender_key_enc: sender_key_enc,
                        recipient_key_enc: recipient_key_enc
                    }
                });

                if (res.ok) {
                    input.value = "";
                    clearDMMedia();
                    await fetchDMMessages();
                    await refreshDMConversations();
                } else {
                    showToast("Failed to send message", "error");
                }
            } catch (err) {
                showToast("Failed to send message", "error");
                console.error(err);
            } finally {
                sendBtn.disabled = false;
            }
        });

        // Polling loop
        setInterval(() => {
            if (!currentUser) return;
            const activeTab = document.querySelector('.nav-item.active');
            if (activeTab) {
                const tabId = activeTab.dataset.tab;
                if (tabId === 'announcements') {
                    fetchAnnouncements();
                } else if (tabId === 'direct-messages') {
                    refreshDMConversations();
                    if (dmActiveUser) {
                        fetchDMMessages();
                    }
                }
            }
        }, 5000);

        // Helper: Escape HTML string to prevent XSS
        function escapeHTML(str) {
            if (!str) return '';
            return str.replace(/[&<>'"]/g, 
                tag => ({
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    "'": '&#39;',
                    '"': '&quot;'
                }[tag] || tag)
            );
        }

        // ----------------- LEAVE MANAGEMENT LOGIC -----------------
        function calculateLeaveDuration() {
            const type = document.getElementById('leave_type').value;
            const startVal = document.getElementById('leave_start').value;
            const endVal = document.getElementById('leave_end').value;
            const daysInput = document.getElementById('leave_days');
            const hoursInput = document.getElementById('leave_hours');

            if (!startVal) return;

            // If it is Timing Leave (Hours), make sure start and end date are same date
            if (type === 'Hours') {
                document.getElementById('leave_end').value = startVal;
                document.getElementById('leave_end').disabled = true;
                return;
            } else {
                document.getElementById('leave_end').disabled = false;
            }

            if (!endVal) return;

            const start = new Date(startVal);
            const end = new Date(endVal);

            if (end < start) {
                document.getElementById('leave_end').value = startVal;
                daysInput.value = "1.0";
                return;
            }

            const diffTime = Math.abs(end - start);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
            daysInput.value = diffDays.toFixed(1);
        }

        function handleLeaveTypeChange() {
            const type = document.getElementById('leave_type').value;
            const docGroup = document.getElementById('leave-doc-group');
            const durationLabel = document.getElementById('leave-duration-label');
            const daysInput = document.getElementById('leave_days');
            const hoursInput = document.getElementById('leave_hours');

            if (type === 'SL') {
                docGroup.style.display = 'block';
            } else {
                docGroup.style.display = 'none';
            }

            if (type === 'Hours') {
                durationLabel.innerText = 'Duration (Hours)';
                daysInput.style.display = 'none';
                daysInput.required = false;
                hoursInput.style.display = 'block';
                hoursInput.required = true;
            } else {
                durationLabel.innerText = 'Duration (Days)';
                daysInput.style.display = 'block';
                daysInput.required = true;
                hoursInput.style.display = 'none';
                hoursInput.required = false;
            }

            calculateLeaveDuration();
        }

        async function handleSLUpload() {
            const fileInput = document.getElementById('leave_doc_file');
            const statusSpan = document.getElementById('leave-upload-status');
            const urlInput = document.getElementById('leave_doc_url');

            if (!fileInput.files || fileInput.files.length === 0) return;

            statusSpan.innerText = 'Uploading...';
            statusSpan.style.color = 'var(--text-muted)';

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            try {
                const res = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (res.ok) {
                    const data = await res.json();
                    urlInput.value = data.url;
                    statusSpan.innerText = 'Uploaded successfully!';
                    statusSpan.style.color = 'var(--success)';
                } else {
                    const err = await res.json();
                    statusSpan.innerText = `Upload failed: ${err.error || 'Unknown error'}`;
                    statusSpan.style.color = 'var(--danger)';
                    fileInput.value = '';
                }
            } catch (e) {
                statusSpan.innerText = 'Upload connection failed';
                statusSpan.style.color = 'var(--danger)';
                fileInput.value = '';
            }
        }

        async function applyForLeave(event) {
            event.preventDefault();

            const leaveType = document.getElementById('leave_type').value;
            const startDate = document.getElementById('leave_start').value;
            const endDate = document.getElementById('leave_end').value;
            const reason = document.getElementById('leave_reason').value;
            const docNoteUrl = document.getElementById('leave_doc_url').value || null;

            let daysRequested = 0.0;
            let hoursRequested = 0.0;

            if (leaveType === 'Hours') {
                hoursRequested = parseFloat(document.getElementById('leave_hours').value || 0.0);
            } else {
                daysRequested = parseFloat(document.getElementById('leave_days').value || 0.0);
            }

            const payload = {
                leave_type: leaveType,
                start_date: startDate,
                end_date: endDate,
                reason: reason,
                days_requested: daysRequested,
                hours_requested: hoursRequested,
                doc_note_url: docNoteUrl
            };

            const submitBtn = document.getElementById('btn-submit-leave');
            if (submitBtn) submitBtn.disabled = true;

            try {
                const res = await apiFetch('/leaves/apply', {
                    method: 'POST',
                    body: payload
                });

                showToast('Leave request submitted successfully!', 'success');
                
                // Reset form
                document.getElementById('leaveForm').reset();
                document.getElementById('leave_doc_url').value = '';
                document.getElementById('leave-upload-status').innerText = '';
                handleLeaveTypeChange();

                loadLeavesData();
            } catch (err) {
                showToast(err.message || 'Failed to submit leave request', 'error');
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        }

        async function actionLeaveRequest(requestId, action) {
            try {
                const res = await apiFetch(`/leaves/action/${requestId}`, {
                    method: 'POST',
                    body: { action: action }
                });

                showToast(`Leave request ${action === 'Approve' ? 'approved' : 'rejected'} successfully!`, 'success');
                loadLeavesData();
                
                // Refresh main logs and dashboard data since leave state changed
                if (typeof fetchData === 'function') fetchData();
            } catch (err) {
                showToast(err.message || 'Failed to action leave request', 'error');
            }
        }

        async function loadLeavesData() {
            const role = getEffectiveUserRole();
            const currentUsername = (currentUser && currentUser.username || '').toLowerCase().trim();

            try {
                if (role !== 'Admin') {
                    // Show cards and form
                    document.getElementById('leaves-balance-cards').style.display = 'grid';
                    document.getElementById('leave-apply-panel').style.display = 'block';

                    // 1. Fetch own leave balances
                    const balRes = await (await apiFetch('/leaves/balances')).json();
                    
                    const clRemaining = 12.0 - (balRes.cl_used || 0.0);
                    const slRemaining = 12.0 - (balRes.sl_used || 0.0);
                    const hoursRemaining = 96.0 - (balRes.hours_used || 0.0);

                    document.getElementById('leave-cl-remaining').innerText = clRemaining.toFixed(1);
                    document.getElementById('leave-sl-remaining').innerText = slRemaining.toFixed(1);
                    document.getElementById('leave-hours-remaining').innerText = hoursRemaining.toFixed(1);

                    // Inject annual indicator subtitles
                    const clCard = document.getElementById('leave-cl-remaining').parentElement.nextElementSibling;
                    clCard.innerHTML = `<i class="fa-solid fa-rotate"></i> 12.0 days allocated annually. Use anytime within the calendar year.`;
                    
                    const slCard = document.getElementById('leave-sl-remaining').parentElement.nextElementSibling;
                    slCard.innerHTML = `<i class="fa-solid fa-circle-info"></i> 12.0 days allocated annually. Doctor letter upload optional.`;
                    
                    const hoursCard = document.getElementById('leave-hours-remaining').parentElement.nextElementSibling;
                    hoursCard.innerHTML = `<i class="fa-solid fa-calendar-days"></i> 96.0 hours allocated annually. Hourly permission leaves.`;
                } else {
                    // Hide cards and form for Admin
                    document.getElementById('leaves-balance-cards').style.display = 'none';
                    document.getElementById('leave-apply-panel').style.display = 'none';
                }

                // 2. Fetch requests
                const reqRes = await (await apiFetch('/leaves/requests')).json();
                const requestsList = Array.isArray(reqRes) ? reqRes : [];

                // Filter my requests
                if (role === 'Admin') {
                    document.getElementById('leave-history-panel').style.display = 'none';
                } else {
                    document.getElementById('leave-history-panel').style.display = 'block';
                    const myRequests = requestsList.filter(r => (r.username || '').toLowerCase().trim() === currentUsername);
                    const historyTbody = document.getElementById('leave-history-table-body');
                    historyTbody.innerHTML = '';

                    if (myRequests.length === 0) {
                        historyTbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding: 15px;">No leave requests in history.</td></tr>';
                    } else {
                        myRequests.forEach(r => {
                            const durationStr = r.leave_type === 'Hours' ? `${r.hours_requested || 0.0} hrs` : `${r.days_requested || 0.0} days`;
                            const statusClass = r.status === 'Approved' ? 'badge-success' : (r.status === 'Pending' ? 'badge-warning' : 'badge-danger');
                            const docHtml = r.doc_note_url ? `<a href="${r.doc_note_url}" target="_blank" style="color: var(--primary); font-weight: 500;"><i class="fa-solid fa-file-arrow-down"></i> View Note</a>` : '<span style="color: var(--text-muted);">None</span>';
                            
                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td style="font-weight: 600;">${r.leave_type || '-'}</td>
                                <td>${r.start_date || '-'}</td>
                                <td>${r.end_date || '-'}</td>
                                <td style="font-weight: 700;">${durationStr}</td>
                                <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHTML(r.reason)}">${escapeHTML(r.reason)}</td>
                                <td>${docHtml}</td>
                                <td><span class="badge ${statusClass}">${r.status || 'Pending'}</span></td>
                                <td>${escapeHTML(r.actioned_fullname || '-')}</td>
                            `;
                            historyTbody.appendChild(tr);
                        });
                    }
                }

                // 3. Populate Supervisor Panels if applicable
                if (role === 'Admin' || role === 'Manager') {
                    // Populate pending review board
                    const reviewRequests = requestsList.filter(r => r.status === 'Pending' && (r.username || '').toLowerCase().trim() !== currentUsername);
                    const reviewTbody = document.getElementById('leave-review-table-body');
                    reviewTbody.innerHTML = '';

                    if (reviewRequests.length === 0) {
                        reviewTbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding: 20px;">No pending leave requests to review.</td></tr>';
                    } else {
                        reviewRequests.forEach(r => {
                            const durationStr = r.leave_type === 'Hours' ? `${r.hours_requested || 0.0} hrs` : `${r.days_requested || 0.0} days`;
                            const docHtml = r.doc_note_url ? `<a href="${r.doc_note_url}" target="_blank" style="color: var(--primary); font-weight: 500;"><i class="fa-solid fa-file-arrow-down"></i> View Note</a>` : '<span style="color: var(--text-muted);">None</span>';
                            
                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td style="font-weight: 600;">${escapeHTML(r.full_name || r.username)}</td>
                                <td><span class="badge badge-primary" style="font-size: 11px;">${r.role || 'User'}</span></td>
                                <td style="font-weight: 600; color: var(--primary);">${r.leave_type || '-'}</td>
                                <td style="font-weight: 700;">${durationStr}</td>
                                <td>${r.start_date || '-'} to ${r.end_date || '-'}</td>
                                <td style="max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHTML(r.reason)}">${escapeHTML(r.reason)}</td>
                                <td>${docHtml}</td>
                                <td style="text-align: center; white-space: nowrap;">
                                    <button onclick="actionLeaveRequest('${r.id}', 'Approve')" class="btn-action edit" title="Approve Request" style="background: rgba(16, 185, 129, 0.1); color: var(--success); padding: 6px 10px; border-radius: 6px; border: none; cursor: pointer; margin-right: 6px; font-weight:600;"><i class="fa-solid fa-circle-check"></i> Approve</button>
                                    <button onclick="actionLeaveRequest('${r.id}', 'Reject')" class="btn-action delete" title="Reject Request" style="background: rgba(239, 68, 68, 0.1); color: var(--danger); padding: 6px 10px; border-radius: 6px; border: none; cursor: pointer; font-weight:600;"><i class="fa-solid fa-circle-xmark"></i> Reject</button>
                                </td>
                            `;
                            reviewTbody.appendChild(tr);
                        });
                    }

                    // Fetch team balances
                    const teamRes = await (await apiFetch('/leaves/team-balances')).json();
                    const teamList = Array.isArray(teamRes) ? teamRes : [];
                    const teamTbody = document.getElementById('leave-team-balances-table-body');
                    teamTbody.innerHTML = '';

                    if (teamList.length === 0) {
                        teamTbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding: 15px;">No team members found.</td></tr>';
                    } else {
                        teamList.forEach(t => {
                            const clRem = 12.0 - (t.cl_used || 0.0);
                            const slRem = 12.0 - (t.sl_used || 0.0);
                            const hoursRem = 96.0 - (t.hours_used || 0.0);
                            
                            const tr = document.createElement('tr');
                            tr.innerHTML = `
                                <td style="font-weight: 600;">${escapeHTML(t.full_name || t.username)}</td>
                                <td><span style="font-size:12px; color:var(--text-muted);">${t.role || 'User'} ${t.title ? `(${t.title})` : ''}</span></td>
                                <td style="text-align: center; font-weight: 700; color: var(--text-color);">${clRem.toFixed(1)} / 12.0 days</td>
                                <td style="text-align: center; font-weight: 700; color: var(--text-color);">${slRem.toFixed(1)} / 12.0 days</td>
                                <td style="text-align: center; font-weight: 700; color: var(--primary);">${hoursRem.toFixed(1)} / 96.0 hrs</td>
                            `;
                            teamTbody.appendChild(tr);
                        });
                    }
                }
            } catch (err) {
                console.error("Failed to load leaves data: ", err);
                showToast("Error loading leaves: " + err.message, "error");
            }
        }

        /* ----------------- EMPLOYEE DIRECTORY & ATTENDANCE MATRIX LOGIC ----------------- */

        async function loadEmployeesDirectory() {
            const container = document.getElementById('employees-cards-container');
            if (!container) return;

            const monthSelect = document.getElementById('attendance-month-select');
            const yearSelect = document.getElementById('attendance-year-select');
            const month = monthSelect ? monthSelect.value : (new Date().getMonth() + 1);
            const year = yearSelect ? yearSelect.value : new Date().getFullYear();

            try {
                const res = await apiFetch(`/api/employees?year=${year}&month=${month}`);
                if (!res.ok) {
                    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--danger); padding: 30px;">Failed to load employees list.</div>`;
                    return;
                }
                const employees = await res.json();
                container.innerHTML = '';

                if (employees.length === 0) {
                    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 30px;">No employees registered in system.</div>`;
                    return;
                }

                employees.forEach(emp => {
                    const initials = emp.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
                    const salaryFormatted = new Intl.NumberFormat('en-IN', {
                        style: 'currency',
                        currency: 'INR',
                        minimumFractionDigits: 2
                    }).format(emp.salary || 0.0);

                    const statusClass = emp.active ? 'badge-success' : 'badge-danger';
                    const statusText = emp.active ? 'Active' : 'Inactive';
                    
                    const card = document.createElement('div');
                    card.className = 'employee-card';
                    card.innerHTML = `
                        <div class="employee-card-header">
                            <div class="employee-avatar">${initials}</div>
                            <div>
                                <h3 style="font-size: 15px; font-weight: 700; color: var(--text-color); margin: 0;">${escapeHTML(emp.full_name)}</h3>
                                <span style="font-size: 12px; color: var(--text-muted); font-weight: 500;">${escapeHTML(emp.title || 'Employee')}</span>
                            </div>
                        </div>
                        <div class="employee-card-body">
                            <div class="employee-card-row">
                                <span class="employee-card-label">Employee Code</span>
                                <span class="employee-card-value">@${emp.username}</span>
                            </div>
                            <div class="employee-card-row">
                                <span class="employee-card-label">Monthly Salary</span>
                                <span class="employee-card-value">${salaryFormatted}</span>
                            </div>
                            <div class="employee-card-row">
                                <span class="employee-card-label">Date of Joining</span>
                                <span class="employee-card-value">${emp.date_of_joining || '-'}</span>
                            </div>
                            <div class="employee-card-row">
                                <span class="employee-card-label">Account Status</span>
                                <span class="badge ${statusClass}">${statusText}</span>
                            </div>
                            <div class="employee-leaves-pills">
                                <div class="employee-leaf-pill" style="color: var(--primary);">
                                    CL: ${(emp.cl_remaining ?? 12.0).toFixed(1)} days
                                </div>
                                <div class="employee-leaf-pill" style="color: var(--danger);">
                                    SL: ${(emp.sl_remaining ?? 1.0).toFixed(1)} days
                                </div>
                            </div>
                            
                            <button class="btn btn-secondary btn-sm" onclick="openEditEmployeeModal('${emp.username}', '${escapeHTML(emp.full_name)}', '${escapeHTML(emp.title || '')}', ${emp.salary || 0}, '${emp.date_of_joining || ''}', ${emp.active})" style="margin-top: 10px; width: 100%; border-radius: 8px;">
                                <i class="fa-solid fa-user-pen"></i> Edit Profile
                            </button>
                        </div>
                    `;
                    container.appendChild(card);
                });
            } catch (err) {
                container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--danger); padding: 30px;">Error loading employee directory.</div>`;
            }
        }

        function openAddEmployeeModal() {
            document.getElementById('addEmployeeForm').reset();
            document.getElementById('add-employee-modal').style.display = 'flex';
        }

        function closeAddEmployeeModal() {
            document.getElementById('add-employee-modal').style.display = 'none';
        }

        async function handleAddEmployeeSubmit(e) {
            e.preventDefault();
            const username = document.getElementById('add_emp_username').value;
            const fullname = document.getElementById('add_emp_fullname').value;
            const title = document.getElementById('add_emp_title').value;
            const salary = document.getElementById('add_emp_salary').value;
            const doj = document.getElementById('add_emp_doj').value;
            const active = document.getElementById('add_emp_active').checked;

            try {
                const res = await apiFetch('/api/employees', {
                    method: 'POST',
                    body: {
                        username,
                        fullname,
                        designation: title,
                        salary: parseFloat(salary),
                        date_of_joining: doj,
                        active
                    }
                });

                if (res.ok) {
                    showToast("Employee added successfully!", "success");
                    closeAddEmployeeModal();
                    loadEmployeesDirectory();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to add employee", "error");
                }
            } catch (err) {
                showToast("Failed to add employee", "error");
            }
        }

        function openEditEmployeeModal(username, fullname, title, salary, doj, active) {
            document.getElementById('edit_emp_username').value = username;
            document.getElementById('edit_emp_fullname').value = fullname;
            document.getElementById('edit_emp_title').value = title;
            document.getElementById('edit_emp_salary').value = salary;
            document.getElementById('edit_emp_doj').value = doj;
            document.getElementById('edit_emp_active').checked = active;

            document.getElementById('edit-employee-modal').style.display = 'flex';
        }

        function closeEditEmployeeModal() {
            document.getElementById('edit-employee-modal').style.display = 'none';
        }

        async function handleEditEmployeeSubmit(e) {
            e.preventDefault();
            const username = document.getElementById('edit_emp_username').value;
            const title = document.getElementById('edit_emp_title').value;
            const salary = document.getElementById('edit_emp_salary').value;
            const doj = document.getElementById('edit_emp_doj').value;
            const active = document.getElementById('edit_emp_active').checked;

            try {
                const res = await apiFetch(`/api/employees/${username}`, {
                    method: 'PUT',
                    body: {
                        designation: title,
                        salary: parseFloat(salary),
                        date_of_joining: doj,
                        active: active
                    }
                });

                if (res.ok) {
                    showToast("Employee profile updated successfully!", "success");
                    closeEditEmployeeModal();
                    loadEmployeesDirectory();
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to update profile", "error");
                }
            } catch (err) {
                showToast("Failed to update employee profile", "error");
            }
        }

        function setupAttendanceSelectors() {
            const monthSelect = document.getElementById('attendance-month-select');
            const yearSelect = document.getElementById('attendance-year-select');
            if (!monthSelect || !yearSelect) return;

            const now = new Date();
            const currentYear = now.getFullYear();
            const currentMonth = now.getMonth() + 1; // 1-indexed

            const selectedYear = parseInt(yearSelect.value) || 2026;
            const selectedMonth = parseInt(monthSelect.value) || 6;

            yearSelect.innerHTML = '';
            for (let y = 2025; y <= currentYear; y++) {
                const opt = document.createElement('option');
                opt.value = y;
                opt.innerText = y;
                if (y === selectedYear) {
                    opt.selected = true;
                }
                yearSelect.appendChild(opt);
            }

            function populateMonths(targetYear) {
                const maxMonth = (targetYear === currentYear) ? currentMonth : 12;
                monthSelect.innerHTML = '';
                
                const monthNames = [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ];

                for (let m = 1; m <= maxMonth; m++) {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.innerText = monthNames[m - 1];
                    if (m === selectedMonth && m <= maxMonth) {
                        opt.selected = true;
                    } else if (m === maxMonth && selectedMonth > maxMonth) {
                        opt.selected = true;
                    }
                    monthSelect.appendChild(opt);
                }
            }

            populateMonths(parseInt(yearSelect.value));

            yearSelect.onchange = () => {
                populateMonths(parseInt(yearSelect.value));
                loadAttendanceMatrixData(true);
            };
        }

        async function loadAttendanceMatrixData(resetWorkingDays) {
            const monthSelect = document.getElementById('attendance-month-select');
            const yearSelect = document.getElementById('attendance-year-select');
            if (!monthSelect || !yearSelect) return;

            const month = parseInt(monthSelect.value);
            const year = parseInt(yearSelect.value);
            
            let query = `?year=${year}&month=${month}`;
            if (!resetWorkingDays) {
                const override = document.getElementById('attendance-working-days-input').value;
                if (override) {
                    query += `&total_working_days=${override}`;
                }
            }

            try {
                const res = await apiFetch(`/api/attendance/overview${query}`);
                if (!res.ok) {
                    showToast("Failed to load attendance details", "error");
                    return;
                }

                const data = await res.json();
                
                if (resetWorkingDays) {
                    document.getElementById('attendance-working-days-input').value = data.total_working_days;
                }

                const headerRow = document.getElementById('attendance-table-header-row');
                headerRow.innerHTML = `
                    <th style="min-width: 200px; text-align: left; position: sticky; left: 0; z-index: 20;">Employee Details</th>
                    <th style="min-width: 120px;">Monthly Salary</th>
                `;
                for (let d = 1; d <= data.days_in_month; d++) {
                    const th = document.createElement('th');
                    th.className = 'day-col';
                    th.innerText = d;
                    headerRow.appendChild(th);
                }
                
                const summaries = [
                    "Presents (P)", "Absents (A)", "Half Days (HD)", "Casual Leaves (CL)", "Sick Leaves (SL)", "LOP Days", "LOP Deduction", "Net Payable"
                ];
                summaries.forEach(title => {
                    const th = document.createElement('th');
                    th.style.minWidth = '90px';
                    th.innerText = title;
                    headerRow.appendChild(th);
                });

                const tbody = document.getElementById('attendance-table-body');
                tbody.innerHTML = '';

                if (data.employees.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="${4 + data.days_in_month + 9}" style="text-align:center; padding: 30px; color: var(--text-muted);">No employees to display.</td></tr>`;
                    return;
                }

                data.employees.forEach(emp => {
                    const uname = emp.username;
                    const empLogs = data.attendance_matrix[uname] || {};
                    const empSummary = data.summary[uname] || {
                        "P": 0, "A": 0, "HD": 0, "CL": 0, "SL": 0, "H": 0, "LOP": 0,
                        "daily_rate": 0, "deductions": 0, "net_payable": emp.salary || 0.0
                    };

                    const tr = document.createElement('tr');
                    tr.dataset.username = uname;
                    tr.dataset.fullname = emp.full_name;

                    const salaryFormatted = new Intl.NumberFormat('en-IN', {
                        style: 'currency',
                        currency: 'INR',
                        minimumFractionDigits: 2
                    }).format(emp.salary || 0.0);

                    const deductionsFormatted = new Intl.NumberFormat('en-IN', {
                        style: 'currency',
                        currency: 'INR',
                        minimumFractionDigits: 2
                    }).format(empSummary.deductions || 0.0);

                    const netPayableFormatted = new Intl.NumberFormat('en-IN', {
                        style: 'currency',
                        currency: 'INR',
                        minimumFractionDigits: 2
                    }).format(empSummary.net_payable || 0.0);

                    const tdDetails = document.createElement('td');
                    tdDetails.style.position = 'sticky';
                    tdDetails.style.left = '0';
                    tdDetails.style.zIndex = '10';
                    tdDetails.style.background = '#18181b';
                    tdDetails.innerHTML = `
                        <div style="font-weight: 700; color: var(--text-color);">${escapeHTML(emp.full_name)}</div>
                        <div style="font-size: 11px; color: var(--text-muted); font-weight: 500;">${uname.toUpperCase()} • ${escapeHTML(emp.title || 'Employee')}</div>
                    `;
                    tr.appendChild(tdDetails);

                    const tdSal = document.createElement('td');
                    tdSal.style.fontWeight = '500';
                    tdSal.innerText = salaryFormatted;
                    tr.appendChild(tdSal);

                    for (let d = 1; d <= data.days_in_month; d++) {
                        const cellStatus = empLogs[d] || '';
                        const td = document.createElement('td');
                        td.className = 'day-col';

                        const select = document.createElement('select');
                        const statusClass = cellStatus ? `status-${cellStatus}` : 'status-empty';
                        select.className = `status-pill-select ${statusClass}`;
                        select.innerHTML = `
                            <option value="" ${!cellStatus ? 'selected' : ''}></option>
                            <option value="P" ${cellStatus === 'P' ? 'selected' : ''}>P</option>
                            <option value="A" ${cellStatus === 'A' ? 'selected' : ''}>A</option>
                            <option value="HD" ${cellStatus === 'HD' ? 'selected' : ''}>HD</option>
                            <option value="CL" ${cellStatus === 'CL' ? 'selected' : ''}>CL</option>
                            <option value="SL" ${cellStatus === 'SL' ? 'selected' : ''}>SL</option>
                            <option value="LOP" ${cellStatus === 'LOP' ? 'selected' : ''}>LOP</option>
                            <option value="H" ${cellStatus === 'H' ? 'selected' : ''}>H</option>
                        `;
                        
                        select.onchange = async () => {
                            const val = select.value;
                            select.className = `status-pill-select ${val ? `status-${val}` : 'status-empty'}`;
                            await updateAttendanceCell(uname, d, val);
                        };

                        td.appendChild(select);
                        tr.appendChild(td);
                    }

                    const summaryOrder = ["P", "A", "HD", "CL", "SL", "LOP"];
                    summaryOrder.forEach(key => {
                        const td = document.createElement('td');
                        td.style.textAlign = 'center';
                        td.style.fontWeight = '600';
                        td.innerText = empSummary[key];
                        tr.appendChild(td);
                    });

                    const tdDed = document.createElement('td');
                    tdDed.style.fontWeight = '500';
                    tdDed.style.color = empSummary.deductions > 0 ? 'var(--danger)' : 'var(--text-muted)';
                    tdDed.innerText = deductionsFormatted;
                    tr.appendChild(tdDed);

                    const tdNet = document.createElement('td');
                    tdNet.style.fontWeight = '700';
                    tdNet.style.color = 'var(--text-color)';
                    tdNet.innerText = netPayableFormatted;
                    tr.appendChild(tdNet);

                    tbody.appendChild(tr);
                });

                filterAttendanceRows();

            } catch (err) {
                console.error("Failed to load attendance details: ", err);
            }
        }

        async function updateAttendanceCell(username, day, status) {
            const year = parseInt(document.getElementById('attendance-year-select').value);
            const month = parseInt(document.getElementById('attendance-month-select').value);

            try {
                const res = await apiFetch('/api/attendance', {
                    method: 'POST',
                    body: { username, year, month, day, status }
                });

                if (res.ok) {
                    await loadAttendanceMatrixData(false);
                } else {
                    const data = await res.json();
                    showToast(data.error || "Failed to update attendance cell", "error");
                }
            } catch (err) {
                showToast("Failed to update attendance cell", "error");
            }
        }

        function filterAttendanceRows() {
            const searchInput = document.getElementById('attendance-search-input');
            if (!searchInput) return;
            const query = searchInput.value.toLowerCase().trim();
            const rows = document.querySelectorAll('#attendance-table-body tr');
            
            rows.forEach(row => {
                const uname = row.dataset.username || '';
                const fullname = row.dataset.fullname || '';
                
                if (uname.toLowerCase().includes(query) || fullname.toLowerCase().includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }

        function exportAttendanceMatrixToExcel() {
            const month = document.getElementById('attendance-month-select').value;
            const year = document.getElementById('attendance-year-select').value;
            const override = document.getElementById('attendance-working-days-input').value;
            
            let query = `?year=${year}&month=${month}`;
            if (override) {
                query += `&total_working_days=${override}`;
            }

            window.location.href = `${API_URL}/api/attendance/export${query}`;
        }

        function initLeaveFormKeyboardGuard() {
            const leaveForm = document.getElementById('leaveForm');
            if (leaveForm) {
                leaveForm.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && e.target.tagName.toLowerCase() !== 'textarea') {
                        e.preventDefault();
                    }
                });
            }
        }
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initLeaveFormKeyboardGuard);
        } else {
            initLeaveFormKeyboardGuard();
        }

        // Run initial authentication check on load
        checkAuth();
    
        /* ----------------- HOSTING & DOMAIN DETAILS LOGIC (Admin Only) ----------------- */
        let hostingData = {};
        let currentHostingSheet = 'GoDaddy';

        async function loadHostingDetails() {
            try {
                const res = await apiFetch('/admin/hosting-details');
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    showToast(errData.error || "Failed to load hosting details from server.", "error");
                    return;
                }
                hostingData = await res.json();
                renderHostingTable();
            } catch (err) {
                console.error("Failed to load hosting details:", err);
                showToast("Error loading hosting details: " + err.message, "error");
            }
        }

        function changeHostingSheet() {
            currentHostingSheet = document.getElementById('hosting-sheet-select').value;
            renderHostingTable();
        }

        function renderHostingTable() {
            const rows = hostingData[currentHostingSheet] || [];
            const tableHead = document.getElementById('hosting-table-head');
            const tableBody = document.getElementById('hosting-table-body');
            
            tableHead.innerHTML = '';
            tableBody.innerHTML = '';

            if (rows.length === 0) {
                tableHead.innerHTML = `<tr><th>Domains</th><th>Actions</th></tr>`;
                tableBody.innerHTML = `<tr><td colspan="2" style="text-align:center; color:var(--text-muted); padding:20px;">No details found.</td></tr>`;
                return;
            }

            // Get headers from first row keys, excluding '_row_idx'
            const headers = Object.keys(rows[0]).filter(k => k !== '_row_idx' && k !== 'id');
            
            // Render Headers
            const thr = document.createElement('tr');
            headers.forEach(h => {
                const th = document.createElement('th');
                th.innerText = h;
                if (h === 'Sl No') th.style.width = '70px';
                thr.appendChild(th);
            });
            const thAction = document.createElement('th');
            thAction.innerText = 'Actions';
            thAction.style.textAlign = 'center';
            thAction.style.width = '150px';
            thr.appendChild(thAction);
            tableHead.appendChild(thr);

            // Render Rows
            rows.forEach(r => {
                const tr = document.createElement('tr');
                headers.forEach(h => {
                    const td = document.createElement('td');
                    td.innerText = r[h] || '';
                    if (h === 'Domains') td.style.fontWeight = '600';
                    tr.appendChild(td);
                });

                // Actions cell
                const tdAction = document.createElement('td');
                tdAction.style.textAlign = 'center';
                tdAction.innerHTML = `
                    <button onclick="openHostingModal(true, '${r.id}')" class="btn-action edit" title="Edit" style="background: rgba(99,102,241,0.1); color: var(--primary); padding: 6px 10px; border-radius: 6px; border: none; cursor: pointer; margin-right: 6px; font-weight:600;"><i class="fa-solid fa-pen"></i> Edit</button>
                    <button onclick="deleteHostingRow('${r.id}')" class="btn-action delete" title="Delete" style="background: rgba(239,68,68,0.1); color: var(--danger); padding: 6px 10px; border-radius: 6px; border: none; cursor: pointer; font-weight:600;"><i class="fa-solid fa-trash"></i> Delete</button>
                `;
                tr.appendChild(tdAction);
                tableBody.appendChild(tr);
            });
        }

        function filterHostingTable() {
            const query = document.getElementById('hosting-search').value.toLowerCase().trim();
            const rows = document.querySelectorAll('#hosting-table-body tr');
            rows.forEach(row => {
                const cells = Array.from(row.querySelectorAll('td'));
                if (cells.length <= 1) return;
                const match = cells.some(c => c.innerText.toLowerCase().includes(query));
                row.style.display = match ? '' : 'none';
            });
        }

        function openHostingModal(isEdit = false, itemId = null) {
            const modal = document.getElementById('hosting-modal');
            const titleEl = document.getElementById('hosting-modal-title');
            const form = document.getElementById('hostingForm');
            const fieldsContainer = document.getElementById('hosting-dynamic-fields');
            
            form.reset();
            fieldsContainer.innerHTML = '';
            
            const rows = hostingData[currentHostingSheet] || [];
            const headers = rows.length > 0 ? Object.keys(rows[0]).filter(k => k !== '_row_idx' && k !== 'Sl No' && k !== 'id') : ['Domains'];
            
            let rowData = null;
            if (isEdit && itemId !== null) {
                titleEl.innerText = `Edit ${currentHostingSheet} Detail`;
                document.getElementById('hosting-edit-row-idx').value = itemId;
                rowData = rows.find(r => r.id === itemId);
            } else {
                titleEl.innerText = `Add ${currentHostingSheet} Detail`;
                document.getElementById('hosting-edit-row-idx').value = '';
            }

            headers.forEach(h => {
                const group = document.createElement('div');
                group.className = 'form-group';
                group.style.marginBottom = '12px';
                
                const label = document.createElement('label');
                label.innerText = h;
                label.setAttribute('for', `field_${h}`);
                
                let input;
                if (h.toLowerCase().includes('date')) {
                    input = document.createElement('input');
                    input.type = 'date';
                } else {
                    input = document.createElement('input');
                    input.type = 'text';
                    input.placeholder = `Enter ${h.toLowerCase()}`;
                }
                
                input.id = `field_${h}`;
                input.name = h;
                if (h === 'Domains') input.required = true;
                if (rowData) input.value = rowData[h] || '';

                group.appendChild(label);
                group.appendChild(input);
                fieldsContainer.appendChild(group);
            });

            modal.style.display = 'flex';
        }

        function closeHostingModal() {
            document.getElementById('hosting-modal').style.display = 'none';
        }

        async function handleHostingSubmit(e) {
            e.preventDefault();
            const rowIdx = document.getElementById('hosting-edit-row-idx').value;
            const isEdit = !!rowIdx;
            
            const form = document.getElementById('hostingForm');
            const formData = new FormData(form);
            const values = {};
            formData.forEach((val, key) => {
                if (key !== '') values[key] = val;
            });

            const payload = {
                sheet_name: currentHostingSheet,
                values: values
            };

            const submitBtn = document.getElementById('btn-submit-hosting');
            if (submitBtn) submitBtn.disabled = true;

            try {
                let url = '/admin/hosting-details/add';
                let method = 'POST';
                if (isEdit) {
                    url = '/admin/hosting-details/edit';
                    method = 'PUT';
                    payload.row_idx = rowIdx;
                }

                const res = await apiFetch(url, {
                    method: method,
                    body: payload
                });

                if (res.ok) {
                    showToast(`Hosting detail ${isEdit ? 'updated' : 'added'} successfully!`, 'success');
                    closeHostingModal();
                    loadHostingDetails();
                } else {
                    const errData = await res.json();
                    showToast(errData.error || 'Failed to save hosting detail', 'error');
                }
            } catch (err) {
                showToast(err.message || 'Failed to save hosting detail', 'error');
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        }

        async function deleteHostingRow(itemId) {
            if (!confirm("Are you sure you want to delete this hosting/domain detail? This will update the Excel sheet directly.")) return;

            try {
                const res = await apiFetch('/admin/hosting-details/delete', {
                    method: 'DELETE',
                    body: {
                        sheet_name: currentHostingSheet,
                        row_idx: itemId
                    }
                });

                if (res.ok) {
                    showToast("Hosting detail deleted successfully!", "success");
                    loadHostingDetails();
                } else {
                    const errData = await res.json();
                    showToast(errData.error || 'Failed to delete hosting detail', 'error');
                }
            } catch (err) {
                showToast(err.message || 'Failed to delete hosting detail', 'error');
            }
        }

        