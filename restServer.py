#!flask/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 14:50:40 2016

@author: oreilly
"""


from flask import Flask, jsonify, abort, make_response, request, Response, send_file
import json, os
from subprocess import check_call
import difflib as dl
import time

import zipfile
import io
from os.path import join, isfile
dbPath = "/mnt/curator_DB/"

app = Flask(__name__)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

"""
@app.route('/neurocurator/api/v1.0/localize', methods=['POST'])
def localizeAnnotation():

    if not request.json        or
       not'id' in request.json or
       not 'annotStr' in request.json:
        abort(400)

    id       = request.json['id']
    annotStr = request.json['annotStr']


    return jsonify({'tasks': tasks})
    if ...:
        abort(404)
    return ...

"""


@app.route('/neurocurator/api/v1.0/localize', methods=['POST'])
def localizeAnnotation():
    if (not request.json         or
        not 'id' in request.json or
        not 'annotStr' in request.json):
        abort(400)

    id       = request.json['id']
    annotStr = request.json['annotStr']

    return jsonify({'test': "localize"})


@app.route('/neurocurator/api/v1.0/get_context', methods=['POST'])
def getContext():
    if (not request.json         or
        not 'id' in request.json or
        not 'annotStr' in request.json):
        abort(400)


    # paperId, contextLength, annotStart, annotText
    id       = request.json['id']
    annotStr = request.json['annotStr']

    return jsonify({'test': "get_context"})



@app.route('/neurocurator/api/v1.0/is_pdf_in_db/<string:paperId>', methods=['GET'])
def is_pdf_in_db(paperId):
    return jsonify({"result":isPDFInDb(paperId)})


@app.route('/neurocurator/api/v1.0/import_pdf', methods=['POST'])
def importPDF():
    if (not request.files       or
        not request.form        or
        not "file" in request.files or
        not "json" in request.form  or
        not 'paperId' in request.form["json"]):
        abort(400)

    paperId  = json.loads(request.form["json"])["paperId"]
    pdf      = request.files["file"]
    fileName = join(dbPath, paperId)

    if not isPDFInDb(paperId):
        pdf.save(fileName + ".pdf")
        # check_call is blocking
        check_call(['pdftotext', '-enc', 'UTF-8', fileName + ".pdf", fileName + ".txt"])
        importMsg = "PDF importation has been sucessful."
    else:
        if not isUserPDFValid(paperId, pdf):
            return jsonify(**{"status"  : "error",
                            "errorNo" :     2,
                            "message" : "The database already contains a PDF "   +
                                        "for this publication and the provided " +
                                        "PDF does not correspond to the stored " +
                                        "version."
                           })
        #else:
        #    importMsg = "The PDF was already in the server database. " + \
                        "A copy has been saved locally."


    #with open(fileName + ".pdf", 'rb') as f:
    #    pdfFile = f.read()
    #with open(fileName + ".txt", 'r', encoding="utf8") as f:
    #    txtFile = f.read()


    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:

        with open(fileName + ".pdf", 'rb') as f:
            data = zipfile.ZipInfo(fileName + ".pdf")
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(data, f)

        with open(fileName + ".txt", 'r', encoding="utf8") as f:
            data = zipfile.ZipInfo(fileName + ".txt")
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(data, f)

    memory_file.seek(0)
    return send_file(memory_file, attachment_filename='paper.zip', as_attachment=True)


    """
    js = json.dumps({"status"  : "success",
                     "errorNo" : 0,
                     "message" : importMsg,
                     "paperId" : paperId,
                     "txtFile" : txtFile,
                     "pdfFile" : pdfFile
                     })


    return Response(js, status=200, mimetype="application/json")
    """



@app.route('/neurocurator/api/v1.0/check_similarity', methods=['POST'])
def checkSimilarity():
    if (not request.files    or
        not request.form        or
        not "file" in request.files or
        not "json" in request.form  or
        not 'paperId' in request.form["json"]):
        abort(400)

    paperId = json.loads(request.form["json"])["paperId"]
    pdf     = request.files["file"] #.read()

    if isPDFInDb(paperId):
        similarity = computePDFSimilarity(paperId, pdf)
        return str(similarity)
    
    return None







@app.route('/neurocurator/api/v1.0/get_pdf', methods=['POST'])
def getServerPDF():
    if (not request.json         or
        not 'id' in request.json or
        not 'annotStr' in request.json):
        abort(400)

    id       = request.json['id']
    annotStr = request.json['annotStr']

    return jsonify({'test': "get_pdf"})


def runRESTServer():
    app.run(debug=True, host= '0.0.0.0')





def isPDFInDb(paperId):
    return isfile(join(dbPath, paperId) + ".pdf")




def isUserPDFValid(paperId, userPDF):
    if not isPDFInDb(paperId):
         return None

    if computePDFSimilarity(paperId, userPDF) >= 0.5:
         return True
    return False




def computePDFSimilarity(paperId, userPDF):
    if not isPDFInDb(paperId):
         return None

    userPDF.save("temp.pdf")
    # check_call is blocking
    check_call(['pdftotext', '-enc', 'UTF-8', "temp.pdf", "temp.txt"])
    os.remove("temp.pdf")
    
    a = open("temp.txt", 'r').read()
    b = open(join(dbPath, paperId) + ".txt", 'r').read()

    import nltk, string
    from sklearn.feature_extraction.text import TfidfVectorizer

    stemmer = nltk.stem.porter.PorterStemmer()
    remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)

    def stem_tokens(tokens):
        return [stemmer.stem(item) for item in tokens]

    '''remove punctuation, lowercase, stem'''
    def normalize(text):
        return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))

    vectorizer = TfidfVectorizer(tokenizer=normalize, stop_words='english')

    def cosine_sim(text1, text2):
        tfidf = vectorizer.fit_transform([text1, text2])
        return ((tfidf * tfidf.T).A)[0,1]

    similarity = cosine_sim(a, b)

    os.remove("temp.txt")

    return similarity

    

def getDbTxt(paperId):
    return open(join(dbPath, paperId) + ".txt", 'r')


# copy this script at /usr/local/neurocurator and run with "curl -i bbpca063.epfl.ch:5000/neurocurator/api/v1.0/tasks"
