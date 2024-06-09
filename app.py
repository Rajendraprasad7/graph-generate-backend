from flask import Flask, render_template, request, redirect, session, send_file, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

import shutil
import subprocess
import os
from pathlib import Path
import zipfile

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
current_directory = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(Path(current_directory)) + '/database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
output_directory = 'output/'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    user_id = int(user_id)
    return db.session.get(User, user_id)
 
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    email = StringField(validators=[InputRequired(), Length(min=4, max=100)], render_kw={"placeholder": "Email"})
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')
        
    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()
        if existing_user_email:
            raise ValidationError('That email already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

class CommandLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    command = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():

    if request.method == 'POST':
        update_nature = request.form['update-nature']
        batch_size = request.form['batch-size']
        batch_size_ratio = request.form['batch-size-ratio']
        edge_insertions = request.form['edge-insertions']
        edge_deletions = request.form['edge-deletions']
        allow_duplicate_edges = 'checked' if 'allow-duplicate-edges' in request.form else 'unchecked'
        vertex_insertions = request.form['vertex-insertions']
        vertex_deletions = request.form['vertex-deletions']
        vertex_growth_rate = request.form['vertex-growth-rate']
        allow_duplicate_vertices = 'checked' if 'allow-duplicate-vertices' in request.form else 'unchecked'
        min_degree = request.form['min-degree']
        max_degree = request.form['max-degree']
        max_diameter = request.form['max-diameter']
        preserve_degree_distribution = 'checked' if 'preserve-degree-distribution' in request.form else 'unchecked'
        preserve_communities = 'checked' if 'preserve-communities' in request.form else 'unchecked'
        preserve_k_core = request.form['preserve-k-core']
        multi_batch = request.form['multi-batch']
        seed = request.form['seed']
        output_format = request.form['output-format']
        input_format = request.form['input-format']
        input_transform = request.form['input-transform']
        probability_distribution = '"'+request.form['probability-distribution']+'"'

        # Clear the entire output directory
        if os.path.exists(output_directory):
            shutil.rmtree(output_directory)
        os.makedirs(output_directory)

        # remove the output zip if it exists
        if os.path.exists(output_directory[:-1] + '.zip'):
            os.remove(output_directory[:-1] + '.zip')

        # Clear the entire uploads directory
        uploads_directory = app.config['UPLOAD_FOLDER']
        if os.path.exists(uploads_directory):
            shutil.rmtree(uploads_directory)
        os.makedirs(uploads_directory)

        # Handle file upload
        if 'file' not in request.files:
            return 'No file uploaded'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        input_file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(input_file_path)

        # Prepare command line arguments
        args = [
            './main',
            '--update-nature', update_nature,
            '--batch-size', batch_size,
            '--batch-size-ratio', batch_size_ratio,
            '--edge-insertions', edge_insertions,
            '--edge-deletions', edge_deletions,
            '--vertex-insertions', vertex_insertions,
            '--vertex-deletions', vertex_deletions,
            '--vertex-growth-rate', vertex_growth_rate,
            '--min-degree', min_degree,
            '--max-degree', max_degree,
            '--max-diameter', max_diameter,
            '--preserve-k-core', preserve_k_core,
            '--multi-batch', multi_batch,
            '--seed', seed,
            '--input-graph', input_file_path,
            '--output-format', output_format,
            '--input-format', input_format,
            '--output-dir', output_directory,
            '--output-prefix', input_file_path.split('/')[-1].split('.')[0],
            '--input-transform', input_transform,
            '--probability-distribution', probability_distribution
        ]

        clean_args = ['./main']
        for i in range(1,len(args)-1,2):
            if args[i+1] != '':
                clean_args.append(args[i])
                clean_args.append(args[i+1])

        if allow_duplicate_edges == 'checked':
            clean_args.append('--allow-duplicate-edges')
        if allow_duplicate_vertices == 'checked':
            clean_args.append('--allow-duplicate-vertices')
        if preserve_degree_distribution == 'checked':
            clean_args.append('--preserve-degree-distribution')
        if preserve_communities == 'checked':
            clean_args.append('--preserve-communities')

        command = " ".join(clean_args)
        print("Command run: ", command)
        command_log = CommandLog(username=current_user.username, command=command)
        db.session.add(command_log)
        db.session.commit()
        subprocess.run(command, shell=True)

        return render_template('home.html', output_file=True)

    return render_template('home.html', output_file = False)

@app.route('/download')
def download():
    shutil.make_archive(output_directory, 'zip', output_directory)
    zip_file_path = output_directory[:-1] + '.zip'
    return send_file(zip_file_path, as_attachment=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('home'))
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password, email=form.email.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()