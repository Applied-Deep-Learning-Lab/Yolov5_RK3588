######### DEBUG FOR FRAME #########
PRINT_IDS = True
FRAMES_IDS_FILE = "frames_ids.txt"
###################################

########## Camera const ##########
PIXEL_FORMAT = "MJPG"
CAM_WIDTH = 640
CAM_HEIGHT = 480
CAM_FPS = 120
SOURCE = 0
###################################

######### Database params #########
DATA_AMOUNT = 100
NUM_DETS = 100
###################################

######## ByteTracker const ########
BYTETRACKER_FPS = 60
TRACKING_CLASSES = [62]
#  0 - person           # 20 - elephant          # 40 - wine glass      # 60 - dining table
#  1 - bicycle          # 21 - bear              # 41 - cup             # 61 - toilet      
#  2 - car              # 22 - zebra             # 42 - fork            # 62 - tv          
#  3 - motorcycle       # 23 - giraffe           # 43 - knife           # 63 - laptop      
#  4 - airplane         # 24 - backpack          # 44 - spoon           # 64 - mouse       
#  5 - bus              # 25 - umbrella          # 45 - bowl            # 65 - remote      
#  6 - train            # 26 - handbag           # 46 - banana          # 66 - keyboard    
#  7 - truck            # 27 - tie               # 47 - apple           # 67 - cell phone  
#  8 - boat             # 28 - suitcase          # 48 - sandwich        # 68 - microwave   
#  9 - traffic light    # 29 - frisbee           # 49 - orange          # 69 - oven        
# 10 - fire hydrant     # 30 - skis              # 50 - broccoli        # 70 - toaster     
# 11 - stop sign        # 31 - snowboard         # 51 - carrot          # 71 - sink        
# 12 - parking meter    # 32 - sports ball       # 52 - hot dog         # 72 - refrigerator
# 13 - bench            # 33 - kite              # 53 - pizza           # 73 - book        
# 14 - bird             # 34 - baseball bat      # 54 - donut           # 74 - clock       
# 15 - cat              # 35 - baseball glove    # 55 - cake            # 75 - vase        
# 16 - dog              # 36 - skateboard        # 56 - chair           # 76 - scissors    
# 17 - horse            # 37 - surfboard         # 57 - couch           # 77 - teddy bear  
# 18 - sheep            # 38 - tennis racket     # 58 - potted plant    # 78 - hair drier  
# 19 - cow              # 39 - bottle            # 59 - bed             # 79 - toothbrush  
###################################

######### Inference const #########
# Count of inference and post_process processes
INF_PROC = 3
POST_PROC = 3

# Mode for async inference on NPU cores
ASYNC_MODE = True

# Path to model
RKNN_MODEL = 'models/yolov5m_leaky_352x352.rknn'
NEW_MODEL = '/home/orangepi/workspace/Yolov5_RK3588/RK3588/rknpu2_python3/models/new_model.rknn'

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