#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
from cv2 import dnn_superres
import numpy as np
import io
from subprocess import run
import face_recognition

def supper_res(path):
	sr = dnn_superres.DnnSuperResImpl_create()
	image = cv2.imread(path)
	modelPath = "ESPCN_x4.pb"
	sr.readModel(modelPath)
	sr.setModel("espcn", 4)
	imls=np.array_split(image,4)
	for i in range(len(imls)):
		imls[i]=sr.upsample(imls[i])
		print(i)
	result=np.concatenate(imls)
	#result = cv2.merge((sr.upsample(b),sr.upsample(g),sr.upsample(r)))
	cv2.imwrite(path[:-4]+"_Large.jpg", result)
	return path[:-4]+"_Large.jpg"

def stackImagesStatic(file_list, update):
	stacked_images = []
	for file in file_list:
		stacked_images.append(cv2.imread(file,1))
	stacked_images = np.asarray(stacked_images)
	return np.median(stacked_images, axis=0)

def stackImages(file_list, update, mode='comb'):
	if mode=='static': return stackImagesStatic(file_list, update)
	mode=mode.lower()
	if mode=='comb' or mode=='orb':
		orb = cv2.ORB_create(nfeatures=5000)
	stacked_images = []
	first_kp = None
	first_des = None
	if mode=='comb' or mode=='ecc':
		termination_eps = 1e-5
		criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 700, termination_eps)
	for file in file_list:
		update.message.reply_text(str(file_list.index(file)+1)+'/'+str(len(file_list)), disable_notification=True)
		image = cv2.imread(file,1)
		if mode=='comb' or mode=='orb':
			# compute the descriptors with ORB
			kp = orb.detect(image, None)
			kp, des = orb.compute(image, kp)
			# create BFMatcher object
			matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

		if file is file_list[0]:
			# Save keypoints for first image
			w, h, _ = image.shape
			stacked_images.append(image)
			first_image = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
			if mode=='comb' or mode=='orb':
				first_kp = kp
				first_des = des
		else:
			if mode=='comb' or mode=='orb':
				# Find matches and sort them in the order of their distance
				matches = matcher.match(first_des, des)
				matches = sorted(matches, key=lambda x: x.distance)
				#matches = matches[:int(len(matches)*0.9)]
				src_pts = np.float32(
					[first_kp[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
				dst_pts = np.float32(
					[kp[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

				# Estimate perspective transformation
				M, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 4.0)
			if mode=='comb' or mode=='ecc':
				try: s, M = cv2.findTransformECC(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY), first_image, M.astype(np.float32), cv2.MOTION_HOMOGRAPHY, criteria, inputMask=None, gaussFiltSize=1)
				except: pass
			# Align image to first image
			#image = cv2.resize(image, (h*2, w*2), interpolation=cv2.INTER_LINEAR)
			image = cv2.warpPerspective(image, M, (h, w))
			stacked_images.append(image)
	# Convert images to 4d ndarray, size(n, nrows, ncols, 3)
	stacked_images = np.asarray(stacked_images)

	# Take the median over the first dim
	#avg = np.mean(stacked_images, axis=0)
	med = np.median(stacked_images, axis=0)
	#med = (med*255).astype(np.uint8)
	return med

def stitchImages(imagePaths, output):
	images=[]
	for path in imagePaths:
		images.append(cropBlackBorder(cv2.imread(path), ratio=10))
	stitcher = cv2.Stitcher_create()
	(status, stitched) = stitcher.stitch(images)
	if status == 0:
		#stitched=cropBlackBorder(stitched)
	# write the output stitched image to disk
		cv2.imwrite(output, stitched)
		#-ProjectionType="equirectangular" -UsePanoramaViewer="True"
		run(["exiftool", "-ProjectionType=\"equirectangular\"", "-UsePanoramaViewer=\"True\"", output])
	return status
def getFacesSimple(image):
	Fimage = face_recognition.load_image_file(image)
	image = cv2.imread(image)
	face_locations = face_recognition.face_locations(Fimage)
	for top, right, bottom, left in face_locations:
		# Draw a box around the face
		cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)
	return image, face_locations

def getFaces(path, known_faces):
	image = cv2.imread(path)
	Fimage = face_recognition.load_image_file(path)
	face_locations = face_recognition.face_locations(Fimage, number_of_times_to_upsample=0, model="cnn")
	face_encodings = face_recognition.face_encodings(Fimage, face_locations)
	face_names = []
	i=0
	faceCrop=[]
	unknownFaceCrop=[]
	for face_encoding in face_encodings:
		# See if the face is a match for the known face(s)
		matches = face_recognition.compare_faces([f[1] for f in known_faces], face_encoding)
		top, right, bottom, left = face_locations[i]
		# If a match was found in known_face_encodings, just use the first one.
		if True in matches:
			first_match_index = matches.index(True)
			name = known_faces[first_match_index][0]
			face_names.append(name)
			faceCrop.append(image[top:bottom, left:right].copy())
		else:
			unknownFaceCrop.append(image[top:bottom, left:right].copy())
		i+=1
		"""# Or instead, use the known face with the smallest distance to the new face
		face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
		best_match_index = np.argmin(face_distances)
		if matches[best_match_index]:
			name = known_face_names[best_match_index]"""
	
	"""for (top, right, bottom, left), name in zip(face_locations, face_names):
		# Draw a box around the face
		cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)
		
		# Draw a label with a name below the face
		cv2.rectangle(image, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
		
		font = cv2.FONT_HERSHEY_DUPLEX
		cv2.putText(image, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)"""
	
	return face_locations, face_names, faceCrop, unknownFaceCrop

def saveFace(image):
	Fimage = face_recognition.load_image_file(image)
	face_locations = face_recognition.face_locations(Fimage)
	face_encodings = face_recognition.face_encodings(Fimage, face_locations, num_jitters=100)
	return face_encodings[0] if face_encodings  else None

def load_image_to_memory(img):
	#print(type(img))
	if isinstance(img, np.ndarray):
		buff = cv2.imencode(".jpg", img)
		return io.BytesIO(buff[1])
	elif isinstance(img, str):
		return open(img, 'rb') #remember to close this
	else: return None

def cropBlackBorder(img,ratio=0):
	cimg = cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, (0, 0, 0))
	gray = cv2.cvtColor(cimg, cv2.COLOR_BGR2GRAY)
	thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)[1]
	cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	if len(cnts) == 2:
		cnts = cnts[0]
	elif len(cnts) == 3:
		cnts = cnts[1]
	c = max(cnts, key=cv2.contourArea)
	mask = np.zeros(thresh.shape,dtype="uint8")
	(x, y, w, h) = cv2.boundingRect(c)
	cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
	minRect = mask.copy()
	sub = mask.copy()
	while cv2.countNonZero(sub) > ratio:
		minRect = cv2.erode(minRect, None)
		sub = cv2.subtract(minRect, thresh)
	cnts = cv2.findContours(minRect.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	if len(cnts) == 2:
		cnts = cnts[0]
	elif len(cnts) == 3:
		cnts = cnts[1]
	c = max(cnts, key=cv2.contourArea)
	(x, y, w, h) = cv2.boundingRect(c)
	cimg = cimg[y:y + h, x:x + w]
	return cimg

def classify_image(image, context):
	img_types=dict()
	if 'faces' not in context.chat_data: context.chat_data['faces']=[]
	face_locations, face_names, faces_imgs, unknow_faces_imgs = getFaces(image, context.chat_data['faces'])
	if len(face_locations)!=0:
		img_types['face']=([(faces_imgs[i],face_names[i]) for i in range(len(face_names))],[(face, None) for face in unknow_faces_imgs])
	return img_types
