from flask import Blueprint, render_template, request, redirect, url_for, session, flash
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
            auth_response = ext.supabase.auth.sign_in_with_password({"email": email, "password": password})
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
