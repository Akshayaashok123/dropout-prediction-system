from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(role):
    """
    Decorator that checks if the current_user has the required role.
    Returns 403 Forbidden if not.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
                
            # Allow checking against a list of roles
            if isinstance(role, list):
                if current_user.role not in role:
                    abort(403)
            else:
                if current_user.role != role:
                    abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
