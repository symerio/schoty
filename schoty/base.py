# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import sys
import os.path
from glob import glob

from subprocess import Popen, PIPE

import pandas as pd

from .parsers import LCLMonthlyAccountStatement

# http://blog.alivate.com.au/poppler-windows/
DEFAULT_PDFTOTEXT = '/usr/bin/pdftotext'

class BankStatementSerie(object):
    def __init__(self, path, bank_name, lang='fr', verbose=False, work_dir='/tmp/', 
                    pdftotext=DEFAULT_PDFTOTEXT):
        """ Path can be a glob expression """
        dataset_list = sorted(glob(path))

        # parse serie
        N_tot = len(dataset_list)
        N_valid = 0
        self.elements = []
        if verbose:
            print('Processing dataset:')
        for path in dataset_list:
            short_path = '-'.join((path[-12:-8],path[-8:-6],path[-6:-4]))
            if verbose:
                print(  ' - ', short_path, end='')
                sys.stdout.flush()
            try: 
                st = bank_statement(path, bank_name, lang=lang, pdftotext=pdftotext)
                self.elements.append(st)
                N_valid += 1
                if verbose:
                    print(' ->  [ok]')
            except:
                if verbose:
                    print(' ->  [failed]')

        if verbose:
            print('     successfully parsed {}/{} files.'.format(N_valid, N_tot))

        self._assemble_statements()

    def _assemble_statements(self):
        self.data = pd.concat([el.data for el in self.elements], axis=0)






def bank_statement(path, bank_name, lang='fr', debug=False, work_dir='/tmp/', pdftotext=DEFAULT_PDFTOTEXT,
        hide_matched=False):

    basedir, basename = os.path.split(path)
    basename, _ = os.path.splitext(basename)

    txt_path = os.path.join(work_dir, basename + '.txt')


    p = Popen([pdftotext, '-layout', path, txt_path], stderr=PIPE)

    p.wait()

    # get the right parser
    if bank_name == 'LCL':
        st = LCLMonthlyAccountStatement(lang=lang)
    else:
        raise NotImplementedError

    with open(txt_path, 'rt') as fh:
        txt = fh.readlines()
        for line in txt:
            st.detect_credit_debit_positions(line)
        for line in txt:
             st.process_line(line, debug=debug, hide_matched=hide_matched)


        st.finalize()


    os.remove(txt_path)

    return st