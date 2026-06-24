from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.middleware.auth import login_required
import app.extensions as ext

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    user_id = session['user']['id']
    try:
        logs_response = ext.supabase.table('work_logs').select('*').eq('user_id', user_id).order('timestamp', desc=True).execute()
        work_logs = logs_response.data
    except Exception as e:
        work_logs = []
        flash(f'Error fetching logs: {str(e)}', 'error')
        
    return render_template('dashboard.html', logs=work_logs)

@bp.route('/log_work', methods=['POST'])
@login_required
def log_work():
    date = request.form['date']
    location_dept = request.form['location_dept']
    role = request.form['role']
    work_type = request.form['work_type']
    description = request.form['description']
    user_id = session['user']['id']
    
    try:
        ext.supabase.table('work_logs').insert({
            'user_id': user_id,
            'timestamp': date,
            'location_dept': location_dept,
            'role': role,
            'hours': 1.0,
            'work_type': work_type,
            'description': description,
            'status': 'pending'
        }).execute()
        flash('Work logged successfully!', 'success')
    except Exception as e:
        flash(f'Error logging work: {str(e)}', 'error')
        
    return redirect(url_for('dashboard.index'))

@bp.route('/delete_log/<log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    user_id = session['user']['id']
    try:
        ext.supabase.table('work_logs').delete().eq('id', log_id).eq('user_id', user_id).execute()
        flash('Work log deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting log: {str(e)}', 'error')
    return redirect(url_for('dashboard.index'))
