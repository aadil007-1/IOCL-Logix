from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.middleware.auth import login_required
import app.extensions as ext

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = f"{username}@worklog.com"
        if not ext.supabase:
            flash('Supabase is not configured.', 'error')
            return render_template('login.html')
            
        try:
            # Initialize a separate client for the user sign-in to prevent polluting the global ext.supabase client
            from flask import current_app
            from supabase import create_client
            auth_client = create_client(
                current_app.config['SUPABASE_URL'], 
                current_app.config['SUPABASE_KEY']
            )
            auth_response = auth_client.auth.sign_in_with_password({"email": email, "password": password})
            
            session['user'] = {
                'id': auth_response.user.id,
                'email': auth_response.user.email
            }
            # Fetch profile to store roles in session
            profile_response = ext.supabase.table('profiles').select('*').eq('id', auth_response.user.id).single().execute()
            session['profile'] = profile_response.data
            
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
            
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return redirect(url_for('dashboard.index'))
        
    if new_password != confirm_password:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('dashboard.index'))
        
    try:
        from supabase_auth.types import AdminUserAttributes
        ext.supabase.auth.admin.update_user_by_id(
            session['user']['id'],
            AdminUserAttributes(password=new_password)
        )
        flash('Your password has been changed successfully.', 'success')
    except Exception as e:
        flash(f'Error changing password: {str(e)}', 'error')
        
    return redirect(url_for('dashboard.index'))

