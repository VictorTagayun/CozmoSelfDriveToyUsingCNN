#!/usr/bin/env python
"""
Copyright (c) 2017, benjamin wu 
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Ryan Dellana nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL Ryan Dellana BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import numpy as np
import cv2
import tensorflow as tf
import pickle

from cozmo_cnn_models import cnn_cccccfffff

import os
import cv2
import numpy as np
import time

def load_dataset(path, percent_testing=None):
    assert percent_testing is None or (percent_testing >= 0.0 and percent_testing <= 1.0)
    x, y, fnames = [], [], []
    for i in os.walk(path):
        (d, sub_dirs, files_) = i
        fnames.extend(files_)
    seq_fname = []
    for fname in fnames:
        seq = float(fname.split('_')[0])
        seq_fname.append((seq, fname))
    seq_fname.sort()
    for (seq, fname) in seq_fname:
        #img = cv2.imread(path+'/'+fname, 1) for black and white
        img = cv2.imread(path+'/'+fname)
        img = cv2.resize(img, (200, 150), interpolation=cv2.INTER_CUBIC)
        img = img[35:,:,:]
        x.append(img)
        timestamp, lwheel, rwheel = fname.split('_')
        timestamp, lwheel, rwheel = float(timestamp), float(lwheel)/100.0,float(rwheel.split('.jpg')[0])/100.0

        #y.append([[lwheel], [rwheel]])
        y.append(np.array([lwheel, rwheel]))
        print('( timestamp, lwheel, rwheel):',  timestamp,lwheel,rwheel)

    train_x, train_y, test_x, test_y = [], [], [], []
    if percent_testing is not None:
        tst_strt = int(len(x)*(1.0-percent_testing))
        train_x, train_y, test_x, test_y = x[:tst_strt], y[:tst_strt], x[tst_strt:], y[tst_strt:]
    else:
        train_x, train_y = x, y
    return train_x, train_y, test_x, test_y


#path = '/Users/benja/code/cozmo_sdk_examples_0.15.0/apps/TestImgv2/'
path = '' # plz fill the img dir you want to train 

train_x, train_y, test_x, test_y = load_dataset(path=path, percent_testing=0.20)



num_epochs = 100
batch_size = 100

# Drop items from dataset so that it's divisible by batch_size

train_x = train_x[0:-1*(len(train_x) % batch_size)]
train_y = train_y[0:-1*(len(train_y) % batch_size)]
test_x = test_x[0:-1*(len(test_x) % batch_size)]
test_y = test_y[0:-1*(len(test_y) % batch_size)]

print('len(test_x) =', len(test_x))

batches_per_epoch = int(len(train_x)/batch_size)

sess = tf.InteractiveSession()
model = cnn_cccccfffff()
train_step = tf.train.AdamOptimizer(1e-4).minimize(model.loss)
correct_prediction = tf.equal(tf.argmax(model.y_out,1), tf.argmax(model.y_,1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float32"))
saver = tf.train.Saver()
sess.run(tf.global_variables_initializer())

for i in range(num_epochs):
    for b in range(0, batches_per_epoch):
        batch = [train_x[b*batch_size:b*batch_size+batch_size], train_y[b*batch_size:b*batch_size+batch_size]]
        # --- normalize batch ---
        batch_ = [[],[]]
        for j in range(len(batch[0])):
            batch_[0].append(batch[0][j].astype(dtype=np.float32)/255.0)
            batch_[1].append(batch[1][j].astype(dtype=np.float32))
        batch = batch_
        # ------------------------
        train_step.run(feed_dict={model.x:batch[0], model.y_:batch[1], model.keep_prob_fc1:0.8, model.keep_prob_fc2:0.8, model.keep_prob_fc3:0.8, model.keep_prob_fc4:0.8})

    print('epoch', i, 'complete')
    if i % 5 == 0:
        test_error = 0.0
        for b in range(0, len(test_x), batch_size):
            batch = [test_x[b:b+batch_size], test_y[b:b+batch_size]]
            # --- normalize batch ---
            batch_ = [[],[]]
            for j in range(len(batch[0])):
                batch_[0].append(batch[0][j].astype(dtype=np.float32)/255.0)
                batch_[1].append(batch[1][j].astype(dtype=np.float32))
            batch = batch_

            test_error_ = model.loss.eval(feed_dict={model.x:batch[0], model.y_:batch[1], 
                                                 model.keep_prob_fc1:1.0, model.keep_prob_fc2:1.0, 
                                                 model.keep_prob_fc3:1.0, model.keep_prob_fc4:1.0})

           # y_out =  model.y_out.eval(session=sess, feed_dict={model.x:batch[0] , 
           #                                   model.keep_prob_fc1:1.0, model.keep_prob_fc2:1.0, 
           #                                   model.keep_prob_fc3:1.0, model.keep_prob_fc4:1.0})
           # print("y out is ", y_out)

            # -----------------------
            test_error += test_error_
        test_error /= len(test_x)/batch_size
        test_accuracy = 1.0 - test_error
        print("test accuracy %g"%test_accuracy)


filename = saver.save(sess, './cozmo_run_modelv2.ckpt')

