import pydicom
from flask import Flask, render_template, request, redirect, send_file, url_for, make_response
import os
import utils.segmentation
import base64
from pathlib import Path

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'dcm'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET'])
def index():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    # Загрузка файла
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Сохраняем DICOM файл
        dcm_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp.dcm')
        file.save(dcm_path)

        img = utils.segmentation.load_image(pydicom.dcmread(dcm_path))

        model = utils.segmentation.load_model()

        utils.segmentation.ans_show(model, img, convert_pred=utils.segmentation.get_DeepLabV3Plus_pred)

        png_path = Path('static/uploads/contour.png')
        ct_base64 = base64.b64encode(png_path.read_bytes()).decode('utf-8')
        return render_template('display.html', original_ct_base64=ct_base64, contour_base64=ct_base64)


    return redirect(request.url)

@app.route('/original_image')
def original_image():
    with open("static/uploads/scan.png", "rb") as f:
        img_bytes = f.read()
    response = make_response(img_bytes)
    response.headers.set('Content-Type', 'image/png')
    response.headers.set('Content-Length', len(img_bytes))
    response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
    return response

@app.route('/contour_image')
def contour_image():
    with open("static/uploads/contour.png", "rb") as f:
        img_bytes = f.read()
    response = make_response(img_bytes)
    response.headers.set('Content-Type', 'image/png')
    response.headers.set('Content-Length', len(img_bytes))
    response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
    return response

@app.route('/display')
def display_image():
    return render_template('display.html')


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['RESULTS_FOLDER'], 'user_results'), exist_ok=True)
    os.makedirs(os.path.join(app.config['RESULTS_FOLDER'], 'system_results'), exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
