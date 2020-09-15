import random
import json
import csv
import numpy as np
import os
import regression
import spacy

import dr_api
import mlm_api
import arguments

# Eval prep
nlp = spacy.load('en')
def tokenize(data):
  new_data = []
  print("Tokenizing")
  data = [s.replace("_go", "").replace("_eos", "").strip() for s in data]
  docs = nlp.tokenizer.pipe([' '.join(s.lower().split()) for s in data])
  for doc in docs:
    # Tokenize with spacy
    tokenized = ' '.join([e.text for e in doc])

    # Fix mis-tokenized tags
    tokenized = "_go " + tokenized + " _eos"
    new_data.append(tokenized)

  return new_data

def prep_mlm(context, response):
  outputs = tokenize(response)
  valid_src = [e.strip().split("_eos ")[-1] for e in context]
  output_lines = [s + " " + r + "\n" for s,r in zip(valid_src, outputs)]
  #open("undr/test.lm", "w+").writelines([' '.join(e.split()) + "\n" for e in output_lines])
  output_lines = [' '.join(e.split()) + "\n" for e in output_lines]
  return ''.join(output_lines)

def sanity(rows):
  # TODO:
  # In this function, rows and rows2 are different, while they are supposed to be the same.
  # Exp: rows = 'it is an apple', rows2 = '"it is an apple"' 
  # Notes that in original version written by shikib, results will be rows2.
  # In current version, we use 'rows' version as it makes more sense. (we don't need "")
  import sys
  csv.writer(open('dev.tsv', 'w+'), delimiter='\t').writerows(rows)
  def read_tsv(input_file, quotechar=None):
    """Reads a tab separated value file."""
    #with open(input_file, "r", encoding="utf-8-sig") as f:
    with open(input_file, "r", encoding="utf-8") as f:
      reader = csv.reader(f, delimiter="\t", quotechar=quotechar)
      lines = []
      for line in reader:
          if sys.version_info[0] == 2:
              line = list(unicode(cell, 'utf-8') for cell in line)
          lines.append(line)
      return lines
  rows2 = read_tsv('dev.tsv')

def prep_both(context, response):
  outputs = tokenize(response)
  valid_src = [e.strip().split("_eos ")[-1] for e in context]
  valid_fct = [e.strip() for e in context] 

  valid_ctx = [s+" " +f+" _eos" for s,f in zip(valid_src, valid_fct)]

  rows = [['0','1','2',c,o,'0'] for c,o in zip(valid_ctx, outputs)]
  rows = [rows[0]] + rows
  #sanity(rows)
  return rows

def prep_uk(context, response):
  outputs = tokenize(response)

  valid_fct = [e.strip() for e in context] 

  valid_ctx = [f+" _eos" for f in valid_fct]

  rows = [['0','1','2',c,o,'0'] for c,o in zip(valid_ctx, outputs)]
  rows = [rows[0]] + rows
  return rows

def init_args():
  # Here we handcraft where the pretrained models are
  prefix = '/home/yiting/usr/'
  drc_args = arguments.arc_args(prefix + 'pretrained_models/ctx')
  drf_args = arguments.arf_args(prefix + 'pretrained_models/uk')
  mlm_args = arguments.mlm_args(prefix + 'pretrained_models/roberta_ft')

  return drc_args, drf_args, mlm_args

def init_models(drc_args, drf_args, mlm_args):
  drc_args, drc_model, drc_tokenizer = dr_api.init(drc_args)
  drf_args, drf_model, drf_tokenizer = dr_api.init(drf_args)
  mlm_args, mlm_model, mlm_tokenizer = mlm_api.init(mlm_args)

  return drc_args, drc_model, drc_tokenizer, \
         drf_args, drf_model, drf_tokenizer, \
         mlm_args, mlm_model, mlm_tokenizer


def get_dr_score(args, model, tokenizer, context, response, model_type='drc'):
  if model_type == 'drc':
    data = prep_both(context, response)
  elif model_type == 'drf':
    data = prep_uk(context, response)
  else:
    raise Exception("No such dialog retrival metric. Choose from drc / drf")
  
  scores = dr_api.get_scores(args, model, tokenizer, data)
  return scores

def get_mlm_score(args, model, tokenizer, context, response):
  data = prep_mlm(context, response)
  scores = mlm_api.get_scores(args, model, tokenizer, data)
  return scores

def get_scores(context, response,
               drc_args, drc_model, drc_tokenizer,
               drf_args, drf_model, drf_tokenizer,
               mlm_args, mlm_model, mlm_tokenizer):
  scores = {}
  drc_scores = get_dr_score(drc_args, drc_model, drc_tokenizer, 
                      context, response, model_type='drc')
  drf_scores = get_dr_score(drf_args, drf_model, drf_tokenizer,
                      context, response, model_type='drf')
  mlm_scores = get_mlm_score(mlm_args, mlm_model, mlm_tokenizer,
                      context, response)

  scores['USR-DRc'], scores['USR-DRf'], scores['USR-MLM'] = np.mean(drc_scores), np.mean(drf_scores), np.mean(mlm_scores)
  # Regression
  regr_scores = regression.scores(mlm_scores, drc_scores, drf_scores)
  scores['USR'] = np.mean(regr_scores)
  print(scores)
  return scores
  
