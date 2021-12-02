# -*- coding: utf-8 -*-
"""03_generate_txt_from_model.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/14EUUrTnVJ-pKrMUn5HtWENgQZUHBAkVg
"""



import json
import numpy as np
from tensorflow import keras
from tqdm.notebook import tqdm

seed = np.loadtxt('super_mario_as_a_string/data_preprocessed/seed.txt', dtype=float)[:3*17 - 1].copy()

with open('super_mario_as_a_string/data_preprocessed/ix_to_char.json', 'r') as json_f:
    ix_to_char = json.load(json_f)
    
with open('super_mario_as_a_string/data_preprocessed/char_to_ix.json', 'r') as json_f:
    char_to_ix = json.load(json_f)
    
model = keras.models.load_model(
    'super_mario_as_a_string/trained_models/mario_lstm.h5', 
    compile=False
)

def onehot_to_string(onehot):
    ints = np.argmax(onehot, axis=-1)
    chars = [ix_to_char[str(ix)] for ix in ints]
    string = "".join(chars)
    char_array = []
    for line in string.rstrip().split('\n')[:-1]:
        if len(line) == 16:
            char_array.append(list(line))
        elif len(line) > 16:
            char_array.append(list(line[:16]))
        elif len(line) < 16:
            char_array.append(['-'] * (16 - len(line)) + list(line))
    char_array = np.array(char_array).T
    string = ""
    for row in char_array:
        string += "".join(row) + "\n"
    return string

seed[17+14] = 0
seed[17+14][char_to_ix['x']] = 1
seed[17*2+14] = 0
seed[17*2+14][char_to_ix['x']] = 1
print(onehot_to_string(seed))

def get_seed():
    seed = np.loadtxt('super_mario_as_a_string/data_preprocessed/seed.txt', dtype=float)[:3*17 - 1]
    seed[17+14] = 0
    seed[17+14][char_to_ix['x']] = 1
    seed[17*2+14] = 0
    seed[17*2+14][char_to_ix['x']] = 1
    return seed

seed = get_seed()
seed.shape

num_levels_to_gen = 10

num_chunks = 10
num_cols_per_chunk = 16
num_rows_per_col = 17
num_chars_to_gen = num_chunks * num_cols_per_chunk * num_rows_per_col - len(seed)
print(num_chars_to_gen)

"""## Generate multiple levels at once"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

hidden_size = 128
vocab_size = 15

seed = get_seed()
seed = np.expand_dims(seed, axis=0)
seed = np.repeat(seed, num_levels_to_gen, axis=0)

gen = seed.copy()

# initialize all hidden and cell states to zeros
lstm1_h = np.zeros((num_levels_to_gen, hidden_size))
lstm1_c = np.zeros((num_levels_to_gen, hidden_size))
lstm2_h = np.zeros((num_levels_to_gen, hidden_size))
lstm2_c = np.zeros((num_levels_to_gen, hidden_size))
lstm3_h = np.zeros((num_levels_to_gen, hidden_size))
lstm3_c = np.zeros((num_levels_to_gen, hidden_size))

for i in tqdm(range(num_chars_to_gen), leave=False):

    # predict probas and update hidden and cell states
    probas, lstm1_h, lstm1_c, lstm2_h, lstm2_c, lstm3_h, lstm3_c = model.predict([
        seed, lstm1_h, lstm1_c, lstm2_h, lstm2_c, lstm3_h, lstm3_c
    ])
    
    probas = probas[:, -1]  # all batches, last timestep
    # before: probas.shape == (num_levels_to_gen, length_of_seed, vocab_size)
    # after: probas.shape == (num_levels_to_gen, vocab_size)
    
    seed = np.zeros((num_levels_to_gen, 1, vocab_size))
    for b in range(num_levels_to_gen):
        p = probas[b]
        idx = np.random.choice(np.arange(len(p)), p=p)
        seed[b][0] = 0
        seed[b][0][idx] = 1
        
    # TODO :Change this so that after the first seed, all seed has a seq_length axis of 1
    # [batch, timesteps, feature]

    gen = np.concatenate([gen, seed], axis=1)

gen.shape

for i, g in enumerate(gen):
    with open(f'super_mario_as_a_string/generated_levels_txt/{i+1}.txt', 'w+') as txt_f:
        txt_f.write(onehot_to_string(g))
