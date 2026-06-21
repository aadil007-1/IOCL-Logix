from functools import wraps
from flask import session, redirect, url_for, flash
import app.extensions as ext

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                flash('Please log in first.', 'error')
                return redirect(url_for('auth.login'))
            
            user_id = session['user']['id']
            try:
                response = ext.supabase.table('profiles').select('*').eq('id', user_id).single().execute()
                profile = response.data
                if not profile or not profile.get(f'is_{role}'):
                    flash(f'You do not have {role} privileges.', 'error')
                    return redirect(url_for('dashboard.index'))
            except Exception as e:
                flash(f'Error verifying role: {str(e)}', 'error')
                return redirect(url_for('dashboard.index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
