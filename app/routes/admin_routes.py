from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from app.middleware.auth import login_required
import app.extensions as ext

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/')
@login_required
def dashboard():
    profile = session.get('profile', {})
    is_admin = profile.get('is_admin', False)
    is_cipl = profile.get('is_cipl', False)
    
    if not (is_admin or is_cipl):
        flash('Access denied. Admins or CIPL only.', 'error')
        return redirect(url_for('dashboard.index'))
        
    sort_by = request.args.get('sort_by', 'timestamp')
    order = request.args.get('order', 'desc')
    
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
            
    except Exception as e:
        all_logs = []
        flash(f'Error fetching all logs: {str(e)}', 'error')
        
    return render_template('admin.html', logs=all_logs, sort_by=sort_by, order=order)

@bp.route('/review_log/<log_id>', methods=['POST'])
@login_required
def review_log(log_id):
    profile = session.get('profile', {})
    if not (profile.get('is_admin') or profile.get('is_cipl')):
        flash('Access denied.', 'error')
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
