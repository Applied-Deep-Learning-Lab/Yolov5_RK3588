########## Camera const ##########
CAM_WIDTH = 640
CAM_HEIGHT = 480
CAM_FPS = 120
SOURCE = 0
###################################

######### Inference const #########
# Count of inference and post_process processes
INF_PROC = 3
POST_PROC = 3

# Mode for async inference on NPU cores
ASYNC_MODE = True

# Path to model
RKNN_MODEL = 'models/yolov5m_leaky_352x352.rknn'

# Thresh coefs
OBJ_THRESH = 0.25
NMS_THRESH = 0.45

# Lenght of buffer for recorded frames
BUF_SIZE = 3

# Size of input images to model
NET_SIZE = 352

# inference classes of loaded model
CLASSES = ('person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
        'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
        'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
        'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
        'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
        'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
        'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
        'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
        'hair drier', 'toothbrush')

# Debug
VERBOSE = False
VERBOSE_FILE = 'verbose.txt'
PRINT_TIME = False
PRINT_DIF = False
###################################