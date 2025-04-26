from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from models import db, Movie

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    movies = Movie.query.order_by(Movie.created_at.desc()).paginate(page=page, per_page=per_page)
    return render_template('index.html', movies=movies)

@main_bp.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return render_template('movie_detail.html', movie=movie)

@main_bp.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 12
    movies = Movie.query.filter(Movie.title.ilike(f'%{query}%')).paginate(page=page, per_page=per_page)
    return render_template('index.html', movies=movies, search_query=query)
