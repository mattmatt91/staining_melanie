from PIL import Image
from collections import defaultdict
import pprint
import numpy as np
from matplotlib import pyplot as plt



array = np.random.randint(255, size=(500, 500, 3), dtype=np.uint8)
# print(array)
img = Image.fromarray(array, 'RGB')
img.show('RGB')


