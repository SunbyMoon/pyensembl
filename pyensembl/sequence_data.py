# Copyright (c) 2015. Mount Sinai School of Medicine
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function, division, absolute_import
from os import remove
from os.path import exists, abspath
import gzip
import logging

from six.moves import cPickle as pickle
from skbio import parse_fasta

from .common import require_ensembl_id, load_pickle, dump_pickle

class SequenceData(object):
    """
    Container for reference nucleotide and amino acid sequenes.
    """
    def __init__(self, fasta_path, require_ensembl_ids=False):
        self.fasta_path = abspath(fasta_path)
        if not exists(self.fasta_path):
            raise ValueError("Couldn't find FASTA file %s" % (self.fasta_path,))
        self.require_ensembl_ids = require_ensembl_ids
        self.fasta_dictionary_pickle_path = self.fasta_path + ".pickle"
        self._fasta_dictionary = None
        self._fasta_keys = None

    def clear_cache(self):
        self._fasta_dictionary = None
        if exists(self.fasta_dictionary_pickle_path):
            remove(self.fasta_dictionary_pickle_path)

    def __str__(self):
        return "SequenceData(fasta_path=%s, require_ensembl_ids=%s)" % (
            self.fasta_path,
            self.require_ensembl_ids)

    def __repr__(self):
        return str(self)

    def __contains__(self, sequence_id):
        if self._fasta_keys is None:
            self._fasta_keys = set(self.fasta_dictionary.keys())
        return sequence_id in self._fasta_keys

    def __eq__(self, other):
        return (
            isinstance(other, SequenceData) and
            self.fasta_path == other.fasta_path)

    def __hash__(self):
        return hash(self.fasta_path)

    def _parse_fasta_dictionary(self):
        fasta_dictionary = {}
        if self.fasta_path.endswith(".gz") or self.fasta_path.endswith(".gzip"):
            f = gzip.open(self.fasta_path, "r")
        else:
            f = open(self.fasta_path, "r")

        for (key, seq) in parse_fasta(f, label_to_name=lambda s: s.split()[0]):
            fasta_dictionary[key] = seq
        f.close()
        return fasta_dictionary

    def _load_or_create_fasta_dictionary_pickle(self):
        if exists(self.fasta_dictionary_pickle_path):
            # try loading the cached file
            # but we'll fall back on recreating it if loading fails
            try:
                self._fasta_dictionary = load_pickle(
                    self.fasta_dictionary_pickle_path)
                return
            except pickle.UnpicklingError:
                logging.warn(
                    "Failed to load %s, attempting to read FASTA directly" % (
                        self.fasta_dictionary_pickle_path,))

        self._fasta_dictionary = self._parse_fasta_dictionary()
        dump_pickle(self._fasta_dictionary, self.fasta_dictionary_pickle_path)

    @property
    def fasta_dictionary(self):
        if not self._fasta_dictionary:
            self._load_or_create_fasta_dictionary_pickle()
        return self._fasta_dictionary

    def get(self, sequence_id):
        """Get sequence associated with given ID or return None if missing"""
        # all Ensembl identifiers start with ENS e.g. ENST, ENSP, ENSE
        if self.require_ensembl_ids:
            require_ensembl_id(sequence_id)
        return self.fasta_dictionary.get(sequence_id)
