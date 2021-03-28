import cv2
from cv2 import dnn_superres
# Create an SR object - only function that differs from c++ code
sr = dnn_superres.DnnSuperResImpl_create()
# Read image
image = cv2.imread('./file_250.jpg')
# Read the desired model
path = "ESPCN_x3.pb"
sr.readModel(path)
# Set the desired model and scale to get correct pre- and post-processing
sr.setModel("espcn", 3)
# Upscale the image
result = sr.upsample(image)
# Save the image
cv2.imwrite("./upscaled.jpg", result)
