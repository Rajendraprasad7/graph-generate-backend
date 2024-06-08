from flask import Flask, render_template, request, redirect, session, send_file
import shutil
import subprocess
import os
import zipfile

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
output_directory = 'output/'

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect('/login')

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
            '--input-transform', input_transform
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

        
        print("Command run: ", " ".join(clean_args))
        output_file_path = 'output.txt'
        subprocess.run(clean_args + ['--output-file', output_file_path])

        return render_template('home.html', output_file=True)

    return render_template('home.html', output_file = False)

@app.route('/download')
def download():
    shutil.make_archive(output_directory, 'zip', output_directory)
    zip_file_path = output_directory[:-1] + '.zip'
    return send_file(zip_file_path, as_attachment=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'password':
            session['logged_in'] = True
            return redirect('/')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email   = request.form['email']

        if username != '' and password != '':
            return redirect('/login')

    return render_template('signup.html')

@app.route('/logout')   
def logout():
    session['logged_in'] = False
    return redirect('/login')

if __name__ == '__main__':
    app.run()