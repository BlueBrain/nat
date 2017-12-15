#!flask/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 14:50:40 2016

@author: oreilly
"""


from flask import Flask, jsonify, abort, make_response, request, Response, send_file
import json, os
from subprocess import check_call, CalledProcessError
import difflib as dl
import time
import zipfile
import io
from os.path import join, isfile
from threading import Lock, Thread

from . import utils
from .runOCR import run_ocrmypdf

#from nat.annotationSearch import AnnotationGetter


dbPath = "/mnt/curator_DB/"

app = Flask(__name__)

app.OCRLock = Lock()
app.OCRFiles = []



def acquireLockWithTimeout(): 
    with app.app_context():
        for i in range(60):
            if app.OCRLock.acquire(blocking=False):
                return
            time.sleep(1)
        if i == 59:
            return genericError(jsonify(**{"status"  : "error",
                                    "errorNo" :     11,
                                    "message" : "The server seems to be dead-locked."
                                   }))         


def runOCR(fileName):
    with app.app_context():

        acquireLockWithTimeout()
        app.OCRFiles.append(fileName)
        app.OCRLock.release()    
                
        # Run OCR
        run_ocrmypdf(fileName + ".pdf", fileName + ".txt")
 
        acquireLockWithTimeout()
        del app.OCRFiles[app.OCRFiles.index(fileName)]
        app.OCRLock.release()    
        


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)



@app.errorhandler(500)
def genericError(error):
    return make_response(jsonify({'error': str(error)}), 500)



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



    def getContext(self, paperId, contextLength, annotStart, annotStr):
        response = requests.post(self.serverURL + "get_context", 
                                 json=json.dumps({"paperId"      : paperId, 
                                                  "annotStr"     : annotStr,
                                                  "contextLength": contextLength,
                                                  "annotStart"   : annotStart}))
@app.route('/neurocurator/api/v1.0/get_context', methods=['POST'])
def getContext():
    if not request.json:
        abort(400)

    requestJSON = json.loads(request.json)

    if (not 'paperId'        in requestJSON or
        not 'annotStr'       in requestJSON or
        not 'contextLength'  in requestJSON or
        not 'annotStart'     in requestJSON):
        abort(400)


    paperId       = utils.Id2FileName(requestJSON['paperId'])
    annotStr      = requestJSON['annotStr']
    contextLength = requestJSON['contextLength']
    annotStart    = requestJSON['annotStart']

    try:
        txtFileName = join(dbPath, paperId + ".txt")
        
        with open(txtFileName, 'r', encoding="utf-8", errors='ignore') as f :
            fileText = f.read()
            contextStart = max(0, annotStart - contextLength)
            contextEnd = min(annotStart + len(annotStr) + contextLength, len(fileText))
            return jsonify({'context': fileText[contextStart:contextEnd]}) 
            
    except OSError: # as e:
        #if e.errno == errno.ENOENT:        
        return make_response(jsonify({"status"  : "error",
                                "errorNo" :     3,
                                "message" : "No paper corresponding to this id. File " +\
                                            txtFileName + " not found." 
                                      }), 500)
    else:
        raise






"""    

    # paperId, contextLength, annotStart, annotText
    annotId       = request.json['annotId']

    try:       
        annot = annotGetter.getAnnot(annotId)
    except ValueError:
        return genericError(jsonify(**{"status"  : "error",
                                "errorNo" :     3,
                                "message" : "Annotation not found."
                               }))
        

    return jsonify({'annotation': annot.toJSON()})
"""




def returnPDF(fileName):        
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:

        with open(fileName + ".pdf", 'rb') as f:
            data = zipfile.ZipInfo(os.path.basename(fileName + ".pdf"))
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(data, f.read())

        with open(fileName + ".txt", 'rb') as f:
            data = zipfile.ZipInfo(os.path.basename(fileName + ".txt"))
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(data, f.read())

    memory_file.seek(0)
    return send_file(memory_file, attachment_filename='paper.zip', as_attachment=True)       
    
    

@app.route('/neurocurator/api/v1.0/check_OCR_finished', methods=['POST'])
def checkOCRFinished():
    if not request.json:
        abort(400)

    requestJSON = json.loads(request.json)

    if not 'paperId' in requestJSON:
        abort(400)    
    
    paperId       = utils.Id2FileName(requestJSON['paperId'])
    fileName = join(dbPath, paperId)

    if fileName in app.OCRFiles:
        return make_response(jsonify({'Response': "Still running OCR for " + fileName + "."}), 201)
    else:
        return returnPDF(fileName)


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
    fileName = join(dbPath, utils.Id2FileName(paperId))

    if not isPDFInDb(paperId):
        pdf.save(fileName + ".pdf")
        # check_call is blocking
        try:
            check_call(['pdftotext', '-enc', 'UTF-8', fileName + ".pdf", fileName + ".txt"])
        except CalledProcessError:
            return genericError(jsonify(**{"status"  : "error",
                                           "errorNo" : 10,
                                           "message" : "pdftotext failed to convert the PDF of this paper to txt. " +
                                                       "Command ran: " +
                                                       " ".join(['pdftotext', '-enc', 'UTF-8', fileName + ".pdf", fileName + ".txt"])}))
        except OSError:
            return genericError(jsonify(**{"status"  : "error",
                                           "errorNo" : 11,
                                           "message" : "pdftotext failed to convert the PDF of this paper to txt. " +
                                                       "Command ran: " +
                                                       " ".join(['pdftotext', '-enc', 'UTF-8', fileName + ".pdf", fileName + ".txt"])}))


            
    else:
        if not isUserPDFValid(paperId, pdf):
            return genericError(jsonify(**{"status"  : "error",
                                    "errorNo" :     2,
                                    "message" : "The database already contains a PDF "   +
                                                "for this publication and the provided " +
                                                "PDF does not correspond to the stored " +
                                                "version."
                                   }))

    if os.path.getsize(fileName + ".txt") < 2024:
        # If file size is smaller than 2kb than it is most likely a scanned PDF
        # with no OCR. We need to perform OCR.    
        thread = Thread(target = runOCR, args = (fileName, ))
        thread.start()            
        return make_response(jsonify({'Response': "Running OCR."}), 201)

    return returnPDF(fileName)



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


# copy this script at /usr/local/neurocurator and run with "curl -i bbpteam.epfl.ch:443/neurocurator/api/v1.0/tasks"



def runRESTServer(port=None):
    #annotGetter = AnnotationGetter(dbPath)
    if port is None:
        app.run(debug=True, host= '0.0.0.0')
    else:
        app.run(debug=True, host='0.0.0.0', port=port)
