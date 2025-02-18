import json
import torch
import nltk
from InferSent.models import InferSent
import numpy as np

def get_infersent(V=2):
    '''
    Builds the infersent model using either GloVe or fastText
    '''
    MODEL_PATH = 'encoder/infersent%s.pkl' %V
    if V == 2:
        W2V_PATH = 'fastText/crawl-300d-2M.vec'
    elif V == 1:
        W2V_PATH = 'GloVe/glove.840B.300d.txt'
    
    params_model = {'bsize': 64, 'word_emb_dim': 300, 'enc_lstm_dim': 2048, \
                    'pool_type': 'max', 'dpout_model': 0.0, 'version': V}
    infersent = InferSent(params_model)
    infersent.load_state_dict(torch.load(MODEL_PATH))
    infersent.set_w2v_path(W2V_PATH)

    return infersent

def get_dataset(loc: str):
    '''
    Get the dataset from file location 'loc'
    '''
    with open(loc) as infile:
        dataset = json.load(infile)
    
    return dataset

def get_embedding(infersent, sentences: list):
    '''
    Use sentences to build a sentence embedding for each context using infersent.
    Returns a list of sentence embeddings
    '''

    print("Getting Sentence Embeddings for %d sentences", len(sentences))
    # outputs a numpy array with n vectors of dimension 4096
    context_embeddings = []
    for sentence in sentences:
        # sentence is actually a list of sentences for context_i
        embeddings = infersent.encode(sentence, tokenize=True)
        context_embeddings.append(embeddings)
    
    return np.asarray(context_embeddings)



def retrieve_datatest(dataset: dict):
    '''
    Retrieves context, questions, and targets from the data
    Context will return a list of lists for each sentence in a given context
    Questions will return a list of lists of questions for each context
    Targets will return a list of target values that correspond to each question.
    Target values are equivalent to the sentence number within the context that contains the answer to the question
    '''
    data = dataset['data']
    target = []
    ctx = [] 
    questions = [] 
    answers = []
    for topic in data:
        sentences = []
        for paragraph in topic['paragraphs']:
            context = paragraph['context']
            cont_sents = nltk.sent_tokenize(context)
            ctx.append(cont_sents)

            c_question = []
            c_answer = []
            c_target = []
            for qas in paragraph['qas']:
                if qas['is_impossible']:
                    # skip impossible questions
                    continue
                question = qas['question']
                answer = qas['answers'][0]['text']
                c_question.append(question)
                c_answer.append(answer)

                ans_pos = qas['answers'][0]['answer_start']
                if ans_pos == 0: ## finding in the test set
                    # find which sentence the answer is part of
                    for i, sent in enumerate(cont_sents):
                        if answer in sent:
                            c_target.append(i)
                            break
                else:
                    acc = 0
                    # find which sentence the answer is part of
                    for i, sent in enumerate(cont_sents):
                        acc += len(sent) + 1
                        if acc > ans_pos:
                            # answer is in sentence i
                            c_target.append(i)
                            break
            target.append(c_target)
            questions.append(c_question)
            answers.append(c_answer)
    
    return ctx, questions, answers, target

def retrieve_datanew(dataset: dict):
    '''
    Retrieves context, questions, and targets from the data
    Context will return a list of lists for each sentence in a given context
    Questions will return a list of lists of questions for each context
    Targets will return a list of target values that correspond to each question.
    Target values are equivalent to the sentence number within the context that contains the answer to the question
    '''
    data = dataset['data']
    target = []
    ctx = [] 
    questions = [] 
    answers = []
    for topic in data:
        sentences = []
        for paragraph in topic['paragraphs']:
            context = paragraph['context']
            cont_sents = nltk.sent_tokenize(context)
            ctx.append(cont_sents)

            c_question = []
            c_answer = []
            c_target = []
            for qas in paragraph['qas']:
                if qas['is_impossible']:
                    # skip impossible questions
                    continue
                question = qas['question']
                answer = qas['answers'][0]['text']
                c_question.append(question)
                c_answer.append(answer)

                ans_pos = qas['answers'][0]['answer_start']

                acc = 0
                # find which sentence the answer is part of
                for i, sent in enumerate(cont_sents):
                    acc += len(sent) + 1
                    if acc > ans_pos:
                        # answer is in sentence i
                        c_target.append(i)
                        break
            target.append(c_target)
            questions.append(c_question)
            answers.append(c_answer)
    
    return ctx, questions, answers, target

def build_vocab(infersent, context: list):
    '''
    Flattens the context and then builds the vocab
    '''
    flat_context = [sentence for c in context for sentence in c] 
    infersent.build_vocab(flat_context, tokenize=True)

    return infersent

def cos_similarity(a,b):
    '''
    Calculate the cosine similiarity between a and b
    cos_sim = a.b / |a||b|
    '''
    return np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b))

def main():
    n = 22
    infersent = get_infersent()
    print("Loading Dataset")
    dataset = get_dataset("train-v2.0.json")
    print("Parsing dataset")
    context, questions, answers, target = retrieve_data(dataset)
    print("Building vocab")
    build_vocab(infersent, context)
    print("Getting sentence embeddings")
    if n == -1:
        ctx_embed = get_embedding(infersent, context)
        q_embed = get_embedding(infersent, questions)
        a_embed = get_embedding(infersent, answers)
    else:
        ctx_embed = get_embedding(infersent, context[:n])
        q_embed = get_embedding(infersent, questions[:n])
        #a_embed = get_embedding(infersent, answers[:n])
    return ctx_embed, q_embed, a_embed
