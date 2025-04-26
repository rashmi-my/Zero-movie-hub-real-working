from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import uuid
from datetime import datetime, timedelta
import functools

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Default admin credentials
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'admin123'

# File-based data storage for Vercel serverless environment
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
MOVIES_FILE = os.path.join(DATA_DIR, 'movies.json')

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize empty data files if they don't exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump([], f)

if not os.path.exists(MOVIES_FILE):
    with open(MOVIES_FILE, 'w') as f:
        json.dump([], f)

# Helper functions for data management
def get_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def get_movies():
    try:
        with open(MOVIES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_movies(movies):
    with open(MOVIES_FILE, 'w') as f:
        json.dump(movies, f)

def get_user_by_username(username):
    users = get_users()
    for user in users:
        if user['username'] == username:
            return user
    return None

def get_user_by_id(user_id):
    users = get_users()
    for user in users:
        if user['id'] == user_id:
            return user
    return None

def get_movie_by_id(movie_id):
    movies = get_movies()
    for movie in movies:
        if movie['id'] == movie_id:
            return movie
    return None

# Create default admin user if not exists
def ensure_admin_exists():
    users = get_users()
    admin_exists = False
    for user in users:
        if user['username'] == DEFAULT_ADMIN_USERNAME:
            admin_exists = True
            break
    
    if not admin_exists:
        admin_user = {
            'id': str(uuid.uuid4()),
            'username': DEFAULT_ADMIN_USERNAME,
            'email': 'admin@zeromovies.com',
            'password_hash': generate_password_hash(DEFAULT_ADMIN_PASSWORD),
            'is_admin': True,
            'created_at': datetime.now().isoformat()
        }
        users.append(admin_user)
        save_users(users)

ensure_admin_exists()

# Authentication decorator
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    @functools.wraps(view)
    @login_required
    def wrapped_view(**kwargs):
        user = get_user_by_id(session.get('user_id'))
        if not user or not user.get('is_admin', False):
            flash('You do not have permission to access this page', 'danger')
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view

# Convert ISO format strings to formatted date strings
def format_date(iso_date_string):
    try:
        dt = datetime.fromisoformat(iso_date_string)
        return dt.strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return iso_date_string

# Routes - Main
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    movies = get_movies()
    movies.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    search_query = request.args.get('q', '')
    if search_query:
        movies = [movie for movie in movies if search_query.lower() in movie['title'].lower()]
    
    # Manual pagination
    total = len(movies)
    pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = min(start + per_page, total)
    paginated_movies = movies[start:end]
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages,
        'items': paginated_movies,
        'has_prev': page > 1,
        'has_next': page < pages,
        'prev_num': page - 1,
        'next_num': page + 1
    }
    
    return render_template('index.html', movies=pagination, search_query=search_query)

@app.route('/movie/<movie_id>')
def movie_detail(movie_id):
    movie = get_movie_by_id(movie_id)
    if not movie:
        flash('Movie not found', 'danger')
        return redirect(url_for('index'))
    
    # Format the date for display
    if 'created_at' in movie:
        movie['created_at_formatted'] = format_date(movie['created_at'])
    
    return render_template('movie_detail.html', movie=movie)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('index'))
    
    return redirect(url_for('index', q=query))

# Routes - Auth
@app.route('/auth/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form data
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('auth/signup.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/signup.html')
            
        # Check if username or email already exists
        users = get_users()
        for user in users:
            if user['username'] == username or user['email'] == email:
                flash('Username or email already exists', 'danger')
                return render_template('auth/signup.html')
            
        # Create new user
        new_user = {
            'id': str(uuid.uuid4()),
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'is_admin': False,
            'created_at': datetime.now().isoformat()
        }
        
        users.append(new_user)
        save_users(users)
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('auth/signup.html')

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = get_user_by_username(username)
        
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html')
            
        session.permanent = remember
        session['user_id'] = user['id']
        
        flash('Logged in successfully!', 'success')
        next_page = request.args.get('next')
        
        if next_page:
            return redirect(next_page)
        return redirect(url_for('index'))
        
    return render_template('auth/login.html')

@app.route('/auth/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Routes - Admin
@app.route('/admin/')
@admin_required
def admin_dashboard():
    movies = get_movies()
    movies.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Format dates for display
    for movie in movies:
        if 'created_at' in movie:
            movie['created_at_formatted'] = format_date(movie['created_at'])
    
    return render_template('admin/admin_dashboard.html', movies=movies)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        if user and user.get('is_admin', False):
            return redirect(url_for('admin_dashboard'))
    
    return login()

@app.route('/admin/add_movie', methods=['GET', 'POST'])
@admin_required
def add_movie():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        thumbnail_url = request.form.get('thumbnail_url')
        video_url = request.form.get('video_url')
        download_url = request.form.get('download_url')
        
        # Validate form data
        if not title or not description or not thumbnail_url or not video_url or not download_url:
            flash('All fields are required', 'danger')
            return render_template('admin/add_movie.html')
            
        # Create new movie
        new_movie = {
            'id': str(uuid.uuid4()),
            'title': title,
            'description': description,
            'thumbnail_url': thumbnail_url,
            'video_url': video_url,
            'download_url': download_url,
            'created_at': datetime.now().isoformat()
        }
        
        movies = get_movies()
        movies.append(new_movie)
        save_movies(movies)
        
        flash('Movie added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/add_movie.html')

@app.route('/admin/delete_movie/<movie_id>', methods=['POST'])
@admin_required
def delete_movie(movie_id):
    movies = get_movies()
    updated_movies = [movie for movie in movies if movie['id'] != movie_id]
    
    if len(updated_movies) < len(movies):
        save_movies(updated_movies)
        flash('Movie deleted successfully!', 'success')
    else:
        flash('Movie not found', 'danger')
    
    return redirect(url_for('admin_dashboard'))

# Context processors
@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
    return {'current_user': user}

# Create data directory in Vercel
@app.before_first_request
def create_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(MOVIES_FILE):
        with open(MOVIES_FILE, 'w') as f:
            json.dump([], f)
    ensure_admin_exists()

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, message="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, message="Internal server error"), 500

if __name__ == '__main__':
    app.run(debug=True)
