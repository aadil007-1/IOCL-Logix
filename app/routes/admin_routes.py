from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from app.middleware.auth import login_required
import app.extensions as ext

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/')
@login_required
def dashboard():
    profile = session.get('profile', {})
    is_admin = profile.get('is_admin', False)
    
    if not is_admin:
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard.index'))
        
    sort_by = request.args.get('sort_by', 'timestamp')
    order = request.args.get('order', 'desc')
    group_by = request.args.get('group_by', 'none')
    
    grouped_logs = []
    try:
        logs_response = ext.supabase.table('work_logs').select('*, profiles(name, username)').order('timestamp', desc=True).execute()
        all_logs = logs_response.data
        
        # Sort results in python for flexible sorting across relations
        reverse = (order == 'desc')
        if sort_by == 'timestamp':
            all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=reverse)
        elif sort_by == 'hours':
            all_logs.sort(key=lambda x: float(x.get('hours') or 0), reverse=reverse)
        elif sort_by == 'name':
            all_logs.sort(key=lambda x: ((x.get('profiles') or {}).get('name') or '').lower(), reverse=reverse)
        elif sort_by == 'status':
            status_priority = {'pending': 0, 'approved': 1, 'rejected': 2}
            all_logs.sort(key=lambda x: status_priority.get(x.get('status', 'pending'), 9), reverse=reverse)
        elif sort_by == 'type':
            all_logs.sort(key=lambda x: x.get('work_type', '').lower(), reverse=reverse)
        elif sort_by == 'date_type':
            all_logs.sort(key=lambda x: (x.get('timestamp', '')[:10], x.get('work_type', '').lower()), reverse=reverse)
        elif sort_by == 'name_date':
            all_logs.sort(key=lambda x: (((x.get('profiles') or {}).get('name') or '').lower(), x.get('timestamp', '')[:10]), reverse=reverse)
            
        if all_logs:
            if group_by == 'date':
                from collections import OrderedDict
                groups = OrderedDict()
                for log in all_logs:
                    date_key = log.get('timestamp', '')[:10]
                    if date_key not in groups:
                        groups[date_key] = []
                    groups[date_key].append(log)
                for name, logs_in_group in groups.items():
                    grouped_logs.append({'group_name': name, 'logs': logs_in_group})
            elif group_by == 'type':
                from collections import OrderedDict
                groups = OrderedDict()
                for log in all_logs:
                    type_key = log.get('work_type', 'OTHER')
                    if type_key not in groups:
                        groups[type_key] = []
                    groups[type_key].append(log)
                for name, logs_in_group in groups.items():
                    grouped_logs.append({'group_name': name, 'logs': logs_in_group})
            elif group_by == 'employee':
                from collections import OrderedDict
                groups = OrderedDict()
                for log in all_logs:
                    emp_name = (log.get('profiles') or {}).get('name') or 'Unknown'
                    if emp_name not in groups:
                        groups[emp_name] = []
                    groups[emp_name].append(log)
                for name, logs_in_group in groups.items():
                    grouped_logs.append({'group_name': name, 'logs': logs_in_group})
            else:
                grouped_logs = [{'group_name': None, 'logs': all_logs}]
            
    except Exception as e:
        grouped_logs = []
        flash(f'Error fetching all logs: {str(e)}', 'error')
        
    return render_template('admin.html', grouped_logs=grouped_logs, sort_by=sort_by, order=order, group_by=group_by)

@bp.route('/review_log/<log_id>', methods=['POST'])
@login_required
def review_log(log_id):
    profile = session.get('profile', {})
    if not profile.get('is_admin'):
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard.index'))
        
    action = request.form.get('action') # 'approve' or 'reject'
    status = 'approved' if action == 'approve' else 'rejected'
    
    try:
        ext.supabase.table('work_logs').update({'status': status}).eq('id', log_id).execute()
        flash(f'Log {status} successfully.', 'success')
    except Exception as e:
        flash(f'Error updating log: {str(e)}', 'error')
        
    return redirect(url_for('admin.dashboard'))

@bp.route('/users')
@login_required
def users_list():
    profile = session.get('profile', {})
    is_admin = profile.get('is_admin', False)
    
    if not is_admin:
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard.index'))
        
    try:
        profiles_response = ext.supabase.table('profiles').select('*').order('username').execute()
        all_users = profiles_response.data
    except Exception as e:
        all_users = []
        flash(f'Error fetching users: {str(e)}', 'error')
        
    return render_template('admin_users.html', users=all_users)

@bp.route('/users/update/<user_id>', methods=['POST'])
@login_required
def update_user_roles(user_id):
    profile = session.get('profile', {})
    is_admin = profile.get('is_admin', False)
    
    if not is_admin:
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard.index'))
        
    name = request.form.get('name')
    is_employee = 'is_employee' in request.form
    is_admin_role = 'is_admin' in request.form
    is_cipl = 'is_cipl' in request.form
    
    try:
        # Check to prevent active admin from removing their own admin privilege
        if user_id == session['user']['id'] and not is_admin_role:
            flash('You cannot remove admin privileges from yourself.', 'error')
            return redirect(url_for('admin.users_list'))
            
        update_data = {
            'is_employee': is_employee,
            'is_admin': is_admin_role,
            'is_cipl': is_cipl
        }
        if name is not None:
            update_data['name'] = name
            
        ext.supabase.table('profiles').update(update_data).eq('id', user_id).execute()
        
        # If updating ourselves, reload the session profile
        if user_id == session['user']['id']:
            profile_response = ext.supabase.table('profiles').select('*').eq('id', user_id).single().execute()
            session['profile'] = profile_response.data
            
        flash('User updated successfully.', 'success')
    except Exception as e:
        flash(f'Error updating user: {str(e)}', 'error')
        
    return redirect(url_for('admin.users_list'))

@bp.route('/users/create', methods=['POST'])
@login_required
def create_user():
    profile = session.get('profile', {})
    if not profile.get('is_admin'):
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard.index'))
        
    username = request.form.get('username')
    password = request.form.get('password')
    email = f"{username}@worklog.com"
    
    try:
        # Use admin auth API to create user without logging them in
        ext.supabase.auth.admin.create_user({
            "email": email, 
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "username": username,
                "name": username # default name to username
            }
        })
        flash(f'User {username} created successfully.', 'success')
    except Exception as e:
        flash(f'Error creating user: {str(e)}', 'error')
        
    return redirect(url_for('admin.users_list'))

@bp.route('/users/delete/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    profile = session.get('profile', {})
    if not profile.get('is_admin'):
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard.index'))
        
    if user_id == session['user']['id']:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users_list'))
        
    try:
        ext.supabase.auth.admin.delete_user(user_id)
        flash('User deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
        
    return redirect(url_for('admin.users_list'))

@bp.route('/users/update_password/<user_id>', methods=['POST'])
@login_required
def update_password(user_id):
    profile = session.get('profile', {})
    if not profile.get('is_admin'):
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard.index'))
        
    new_password = request.form.get('new_password', '').strip()
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('admin.users_list'))
    
    try:
        from supabase_auth.types import AdminUserAttributes
        ext.supabase.auth.admin.update_user_by_id(
            user_id,
            AdminUserAttributes(password=new_password)
        )
        flash('Password updated successfully.', 'success')
    except Exception as e:
        flash(f'Error updating password: {str(e)}', 'error')
        
    return redirect(url_for('admin.users_list'))
