#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
from cv2 import dnn_superres
from numpy import concatenate,array_split

def supper_res(path):
	sr = dnn_superres.DnnSuperResImpl_create()
	image = cv2.imread(path)
	modelPath = "ESPCN_x4.pb"
	sr.readModel(modelPath)
	sr.setModel("espcn", 4)
	imls=array_split(image,4)
	for i in range(len(imls)):
		imls[i]=sr.upsample(imls[i])
		print(i)
	result=concatenate(imls)
	#result = cv2.merge((sr.upsample(b),sr.upsample(g),sr.upsample(r)))
	cv2.imwrite(path[:-4]+"_Large.jpg", result)
	return path[:-4]+"_Large.jpg"

def classify_image():
	pass
