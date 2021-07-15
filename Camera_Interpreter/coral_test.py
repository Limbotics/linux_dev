import os
import pathlib
from pycoral.utils import edgetpu
from pycoral.utils import dataset
from pycoral.adapters import common
from pycoral.adapters import classify
from PIL import Image

# Specify the TensorFlow model, labels, and image
script_dir = "/home/mendel/linux_dev"
model_file = os.path.join(script_dir, 'Camera_Interpreter/Coco/detect.tflite')
print(str(model_file))
label_file = os.path.join(script_dir, 'Camera_Interpreter/Coco/labelmap.txt')
print(str(label_file))
image_file = os.path.join(script_dir, '/cell.jpg')
print(str(image_file))

# Initialize the TF interpreter
interpreter = edgetpu.make_interpreter(model_file)
interpreter.allocate_tensors()

# Resize the image
size = common.input_size(interpreter)
print("Image size is " + str(size))
image = Image.open(image_file).convert('RGB').resize(size, Image.ANTIALIAS)
image.show()
default_image = Image.open(image_file)
default_image.show()

# Run an inference
common.set_input(interpreter, image)
interpreter.invoke()
classes = classify.get_classes(interpreter, top_k=10)

# Print the result
labels = dataset.read_label_file(label_file)
for c in classes:
  print('%s: %.5f' % (labels.get(c.id, c.id), c.score))