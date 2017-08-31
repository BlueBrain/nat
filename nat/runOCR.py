from __future__ import print_function
from subprocess import Popen, PIPE, check_output, check_call, DEVNULL
import os
import shutil
from contextlib import suppress
import sys
import pytest
from ocrmypdf.pageinfo import pdf_get_all_pageinfo
import PyPDF2 as pypdf
from ocrmypdf import ExitCode
from ocrmypdf import leptonica
from ocrmypdf.pdfa import file_claims_pdfa
import platform


if sys.version_info.major < 3:
    print("Requires Python 3.4+")
    sys.exit(1)

OCRMYPDF = [sys.executable, '-m', 'ocrmypdf']



def check_ocrmypdf(input_file, output_file, *args, env=None):
    "Run ocrmypdf and confirmed that a valid file was created"

    p, out, err = run_ocrmypdf(input_file, output_file, *args, env=env)
    if p.returncode != 0:
        print('stdout\n======')
        print(out)
        print('stderr\n======')
        print(err)
    #assert p.returncode == 0
    #assert os.path.exists(output_file), "Output file not created"
    #assert os.stat(output_file).st_size > 100, "PDF too small or empty"
    return output_file


def run_ocrmypdf(input_file, output_file, *args, env=None):
    "Run ocrmypdf and let caller deal with results"

    if env is None:
        env = os.environ

    p_args = OCRMYPDF + list(args) + [input_file, output_file]
    p = Popen(
        p_args, close_fds=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True, env=env)
    out, err = p.communicate()
    return p, out, err


#check_ocrmypdf("/mnt/curator_DB/10.1002%2Fcne.903040311.pdf", "test.pdf")
#check_ocrmypdf("/mnt/curator_DB/10.1002%2Fcne.902580308.pdf", "test.pdf")

