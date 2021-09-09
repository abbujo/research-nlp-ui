from flask import Flask, request, render_template, redirect, url_for, make_response
import io
import time
import zipfile
import os
import pandas as pd
import NLP
import spacy
from spacy.lang.en import English
from pymongo import MongoClient

app = Flask(__name__)

my_path = os.getcwd()+'\static'
client = MongoClient(
    "mongodb+srv://abbu93:itsmeabbu20@cluster0.bafsc.mongodb.net/TestPyMongo?retryWrites=true&w=majority")
client.list_database_names()
db = client["TestPyMongo"]

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if request.files:
            dfdataset = pd.read_excel(request.files.get('dataset'))
            if not dfdataset.empty:
                info = NLP.processor(dfdataset)
                zipped_file = zipFiles(info['files'],info['names'])
                response = make_response(zipped_file)
                response.headers["Content-Type"] = "application/octet-stream"
                response.headers["Content-Disposition"] = "attachment; filename=OutputFiles.zip"
                return response
        else:
            return redirect(url_for('dashboard'))
    return render_template('upload.html')


def zipFiles(files, names):
    outfile = io.BytesIO()
    with zipfile.ZipFile(outfile, 'w') as zf:
        for name, data in zip(names, files):
            zf.writestr(name, data.to_csv(index=False))
    return outfile.getvalue()


@app.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')


@app.route('/',)
def home():
    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
