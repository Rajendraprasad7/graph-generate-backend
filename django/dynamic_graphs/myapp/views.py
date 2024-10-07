from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
# from .models import CommandLog
import os
import json
import shutil
import subprocess
from django.http import HttpResponse
from zipfile import ZipFile
from django.conf import settings
from pathlib import Path
from PIL import Image
import numpy as np


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
        else:
            print(form.errors)
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

# def user_login(request):
#     if request.method == 'POST':
#         form = LoginForm(data=request.POST)
#         if form.is_valid():
#             user = form.get_user()
#             login(request, user)
#             return redirect('home')
#     else:
#         form = LoginForm()
#     return render(request, 'login.html', {'form': form})

# @login_required
def home(request):
    graphs_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sample_graphs')
    graph_files = os.listdir(graphs_directory)
    context = {'graph_files': graph_files}
    if request.method == 'POST':
        update_nature = request.POST.get('update-nature', '')
        batch_size = request.POST.get('batch-size', '')
        batch_size_ratio = request.POST.get('batch-size-ratio', '')
        edge_insertions = request.POST.get('edge-insertions', '')
        edge_deletions = request.POST.get('edge-deletions', '')
        min_degree = request.POST.get('min-degree', '')
        max_degree = request.POST.get('max-degree', '')
        min_diameter = request.POST.get('min-diameter', '')
        max_diameter = request.POST.get('max-diameter', '')
        min_scc = request.POST.get('min-scc', '')
        max_scc = request.POST.get('max-scc', '')
        multi_batch = request.POST.get('multi-batch', '')
        seed = request.POST.get('seed', '')
        output_format = request.POST.get('output-format', '')
        input_format = request.POST.get('input-format', '')
        input_transform = request.POST.get('input-transform', '')
        probability_distribution = '"' + request.POST.get('probability-distribution', '') + '"'
        input_file_name = request.POST.get('graph-file', '')
        graph_type = request.POST.get('graph-type', '')

        properties_directory = os.path.join(settings.MEDIA_ROOT, 'properties')
        if os.path.exists(properties_directory):
            shutil.rmtree(properties_directory)
        os.makedirs(properties_directory)

        output_directory = os.path.join(settings.MEDIA_ROOT, 'output')
        if os.path.exists(output_directory):
            shutil.rmtree(output_directory)
        os.makedirs(output_directory)

        adjacencies_directory = os.path.join(settings.MEDIA_ROOT, 'adjacency_matrices')
        if os.path.exists(adjacencies_directory):
            shutil.rmtree(adjacencies_directory)
        os.makedirs(adjacencies_directory)

        if os.path.exists(output_directory + '.zip'):
            os.remove(output_directory + '.zip')

        uploads_directory = os.path.join(settings.MEDIA_ROOT, 'uploads')
        if os.path.exists(uploads_directory):
            shutil.rmtree(uploads_directory)
        os.makedirs(uploads_directory)

        if input_file_name == '':
            if 'file' not in request.FILES:
                context['output_file'] = False
                return HttpResponse('No file uploaded')
            file = request.FILES['file']
            input_file_name = file.name
            if input_file_name == '':
                context['output_file'] = False
                return HttpResponse('No selected file')
            input_file_path = os.path.join(uploads_directory, input_file_name)
            with open(input_file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
        else:
            input_file_path = os.path.join(graphs_directory, input_file_name)

        args = [
            './main',
            '--update-nature', update_nature,
            '--batch-size', batch_size,
            '--batch-size-ratio', batch_size_ratio,
            '--edge-insertions', edge_insertions,
            '--edge-deletions', edge_deletions,
            '--min-degree', min_degree,
            '--max-degree', max_degree,
            '--min-diameter', min_diameter,
            '--max-diameter', max_diameter,
            '--min-scc', min_scc,
            '--max-scc', max_scc,
            '--multi-batch', multi_batch,
            '--seed', seed,
            '--input-graph', input_file_path,
            '--output-format', output_format,
            '--input-format', input_format,
            '--output-dir', output_directory+os.sep,
            '--output-prefix', input_file_name.split('.')[0],
            '--input-transform', input_transform,
            '--probability-distribution', probability_distribution,
            '--show-properties', properties_directory+os.sep,
            '--graph-type', graph_type

        ]

        clean_args = ['./main']
        for i in range(1, len(args) - 1, 2):
            if args[i + 1] != '':
                clean_args.append(args[i])
                clean_args.append(args[i + 1])

        # Store graph_type in the session
        request.session['graph_type'] = graph_type

        command = " ".join(clean_args)
        print("command: ", command)
        # command_log = CommandLog(username=request.user.username, command=command)
        # command_log.save()
        subprocess.run(command, shell=True)
        context['output_file'] = True
        return redirect('properties')
    context['output_file'] = False
    return render(request, 'home.html', context)

# @login_required
def properties(request):
    properties_directory = os.path.join(settings.MEDIA_ROOT, 'properties')
    graphs = []
    for file in os.listdir(properties_directory):
        json_file_path = os.path.join(properties_directory, file)
        file_ext = Path(json_file_path).suffix
        if os.path.isdir(json_file_path): continue
        # if file_ext == '.png': continue
        with open(json_file_path, 'r') as file:
            graph_properties = json.load(file)

        # Assuming adjacency_matrix is your original matrix
        adjacency_matrix = np.array(graph_properties['adjacencyMatrix'])

        # Convert to uint8 (8-bit unsigned integer) and invert colors
        img_array = ((1 - adjacency_matrix) * 255).astype(np.uint8)

        # Create image
        img = Image.fromarray(img_array, mode='L')

        # Resize image to 250x250
        img_resized = img.resize((250, 250), Image.Resampling.NEAREST)
        
        # Save the image
        img_filename = f"adjacency_matrix_{file.name.split(os.sep)[-1].split('_')[-1]}.png"
        img_path = os.path.join(settings.MEDIA_ROOT, 'adjacency_matrices', img_filename)
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        img_resized.save(img_path)
        
        # Add image path to graph properties
        graph_properties['adjacency_matrix_image'] = os.path.join(settings.MEDIA_URL, 'adjacency_matrices', img_filename)
        graph_properties["KLD"] = max(graph_properties.get('KLD', 0), 0)
        # Add SVD statistics image path to graph properties
        svd_filename = f"svd_statistics_{file.name.split(os.sep)[-1].split('_')[-1]}.png"
        graph_properties['svd_statistics'] = os.path.join(settings.MEDIA_URL, 'properties/svd', svd_filename)
        graphs.append([int(file.name.split(os.sep)[-1].split('_')[-1]), graph_properties])
    context = {'graphs': sorted(graphs), 'graph_type': request.session['graph_type']}
    return render(request, 'properties.html', context)

# @login_required
def download(request):
    output_directory = os.path.join(settings.MEDIA_ROOT, 'output')
    zip_file_path = output_directory + '.zip'
    with ZipFile(zip_file_path, 'w') as zipf:
        for foldername, subfolders, filenames in os.walk(output_directory):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                zipf.write(file_path, os.path.relpath(file_path, output_directory))
    return HttpResponse(open(zip_file_path, 'rb'), content_type='application/zip')

# @login_required
# def user_logout(request):
#     if os.path.exists(settings.MEDIA_ROOT):
#         output_directory = os.path.join(settings.MEDIA_ROOT, 'output')
#         if os.path.exists(output_directory):
#             shutil.rmtree(output_directory)
#         os.makedirs(output_directory)

#         if os.path.exists(output_directory + '.zip'):
#             os.remove(output_directory + '.zip')

#         uploads_directory = os.path.join(settings.MEDIA_ROOT, 'uploads')
#         if os.path.exists(uploads_directory):
#             shutil.rmtree(uploads_directory)
#         os.makedirs(uploads_directory)

#         properties_directory = os.path.join(settings.MEDIA_ROOT, 'properties')
#         if os.path.exists(properties_directory):
#             shutil.rmtree(properties_directory)
#         os.makedirs(properties_directory)

#         adjacencies_directory = os.path.join(settings.MEDIA_ROOT, 'adjacency_matrices')
#         if os.path.exists(adjacencies_directory):
#             shutil.rmtree(adjacencies_directory)
#         os.makedirs(adjacencies_directory)

#     logout(request)
#     return redirect('login')

def instructions(request):
    return render(request, 'instructions.html')
