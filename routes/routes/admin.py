from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, Movie
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    movies = Movie.query.order_by(Movie.created_at.desc()).all()
    return render_template('admin/admin_dashboard.html', movies=movies)

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))
        
    from routes.auth import login
    return login()

@admin_bp.route('/add_movie', methods=['GET', 'POST'])
@login_required
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
        new_movie = Movie(
            title=title,
            description=description,
            thumbnail_url=thumbnail_url,
            video_url=video_url,
            download_url=download_url
        )
        
        db.session.add(new_movie)
        db.session.commit()
        
        flash('Movie added successfully!', 'success')
        return redirect(url_for('admin.admin_dashboard'))
        
    return render_template('admin/add_movie.html')

@admin_bp.route('/delete_movie/<int:movie_id>', methods=['POST'])
@login_required
@admin_required
def delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    db.session.delete(movie)
    db.session.commit()
    
    flash('Movie deleted successfully!', 'success')
    return redirect(url_for('admin.admin_dashboard'))
