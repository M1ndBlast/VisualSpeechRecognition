# ##### Copyright 2023 The MediaPipe Authors. All Rights Reserved.
import cv2
import numpy as np
import mediapipe as mp
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from mediapipe import solutions
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from operator import itemgetter
from mediapipe.framework.formats import landmark_pb2

import torch
from pipelines.pipeline import InferencePipeline
# from google.colab.patches import cv2_imshow

mouthOuter = [
		164, 167, 98, 165, 203, 206, 92, 216, 186, 57, 212, 43, 202, 
		106, 204, 182, 194, 83, 201, 18, 200, 313, 421, 406, 418, 335, 
		424, 273, 422, 287, 432, 410, 436, 322, 426, 423, 391, 327, 393,
]

def draw_landmarks_on_image(rgb_image, detection_result):
	face_landmarks_list = detection_result.face_landmarks
	annotated_image = np.copy(rgb_image)
	cp_image = np.copy(rgb_image)


  # Loop through the detected faces to visualize.
	for idx in range(len(face_landmarks_list)):
		face_landmarks = face_landmarks_list[idx]

		points = itemgetter(*mouthOuter)(face_landmarks)
		# get the min and max x and y values
		x_min = min(points, key=lambda x: x.x).x
		x_max = max(points, key=lambda x: x.x).x
		y_min = min(points, key=lambda x: x.y).y
		y_max = max(points, key=lambda x: x.y).y
		# crop the image
		cp_image = cp_image[int(y_min * cp_image.shape[0]):int(y_max * cp_image.shape[0]), int(x_min * cp_image.shape[1]):int(x_max * cp_image.shape[1])]
		# resize the image
		#   cp_image = cv2.resize(cp_image, (256, 256))
		# show the image
		# cv2_imshow(cv2.cvtColor(cp_image, cv2.COLOR_RGB2BGR))

		# Draw the face landmarks.
		face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
		face_landmarks_proto.landmark.extend([
			landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in face_landmarks
		])

		face_landmarks_mouth = landmark_pb2.NormalizedLandmarkList()
		face_landmarks_mouth.landmark.extend([
			landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in itemgetter(*mouthOuter)(face_landmarks)
		])

		solutions.drawing_utils.draw_landmarks(
			image=annotated_image,
			landmark_list=face_landmarks_proto,
			connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
			landmark_drawing_spec=None,
			connection_drawing_spec=mp.solutions.drawing_utils.
				DrawingSpec(thickness=1, circle_radius=0, color=(247, 197, 54)))

		for point in itemgetter(*mouthOuter)(face_landmarks):
			cv2.circle(annotated_image, (int(point.x * annotated_image.shape[1]), int(point.y * annotated_image.shape[0])), 2, (79, 225, 212), -1)
		# solutions.drawing_utils.draw_landmarks(
		# 	image=annotated_image,
		# 	landmark_list=face_landmarks_mouth,
		# 	landmark_drawing_spec=mp.solutions.drawing_utils.
		# 		DrawingSpec(thickness=1, circle_radius=1, color=(79, 225, 212),))
		
	return annotated_image, cp_image

def plot_face_blendshapes_bar_graph(face_blendshapes):
  # Extract the face blendshapes category names and scores.
  face_blendshapes_names = [face_blendshapes_category.category_name for face_blendshapes_category in face_blendshapes]
  face_blendshapes_scores = [face_blendshapes_category.score for face_blendshapes_category in face_blendshapes]
  # The blendshapes are ordered in decreasing score value.
  face_blendshapes_ranks = range(len(face_blendshapes_names))

  fig, ax = plt.subplots(figsize=(12, 12))
  bar = ax.barh(face_blendshapes_ranks, face_blendshapes_scores, label=[str(x) for x in face_blendshapes_ranks])
  ax.set_yticks(face_blendshapes_ranks, face_blendshapes_names)
  ax.invert_yaxis()

  # Label each bar with values
  for score, patch in zip(face_blendshapes_scores, bar.patches):
    plt.text(patch.get_x() + patch.get_width(), patch.get_y(), f"{score:.4f}", va="top")

#   ax.set_xlabel('Score')
#   ax.set_title("Face Blendshapes")
#   plt.tight_layout()
#   plt.show()

def cv2_imshow(img):
	plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
	# plt.imshow(img)
	plt.axis('off')
	plt.show()
        

def landmark_image(filename):
	# STEP 2: Create an FaceLandmarker object.
	base_options = python.BaseOptions(model_asset_path='face_landmarker_v2_with_blendshapes.task')
	options = vision.FaceLandmarkerOptions(base_options=base_options,
										output_face_blendshapes=True,
										output_facial_transformation_matrixes=True,
										num_faces=2)
	detector = vision.FaceLandmarker.create_from_options(options)

	# STEP 3: Load the input image.
	image = mp.Image.create_from_file(filename)

	# STEP 4: Detect face landmarks from the input image.
	detection_result = detector.detect(image)

	print(detection_result)
	# Check if the detection result is valid.
	if detection_result.face_landmarks == []:
		print('No face is detected.')
		raise Exception('Ningún rostro no detectado')

	# STEP 5: Process the detection result. In this case, visualize it.
	annotated_image, croped_image = draw_landmarks_on_image(image.numpy_view(), detection_result)

	plot_face_blendshapes_bar_graph(detection_result.face_blendshapes[0])

	print(detection_result.facial_transformation_matrixes)

	# cv2_imshow(cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
        
	# save image
	cv2.imwrite('landmark.jpg', cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
	cv2.imwrite('croped.jpg', cv2.cvtColor(croped_image, cv2.COLOR_RGB2BGR))
    

def infer(
		gpu_idx= None,
		detector= 'mediapipe',
		data_filename= './terror.mp4', 
		config_filename= './configs/CMUMOSEAS_V_ES_WER44.5.ini', 
		landmarks_filename= None, 
	):
	device = torch.device(f"cuda:{gpu_idx}" if torch.cuda.is_available() and gpu_idx >= 0 else "cpu")
	output = InferencePipeline(config_filename, device=device, detector=detector, face_track=True)(data_filename, landmarks_filename)
	print(f"hyp: {output}")
	return output


if __name__ == '__main__':
	landmark_image('sample-2f.jpg')