import argparse
import os
import sys
from rknn.api import RKNN

QUANTIZE_ON = True

OBJ_THRESH = 0.25
NMS_THRESH = 0.45
IMG_SIZE = 640

def parse_opt():
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group('required arguments')
    required.add_argument(
        '--input', '-i',
        required=True,
        type=str,
        help='path to ONNX model'
    )
    parser.add_argument(
        '--ouput', '-o',
        default=os.path.abspath(os.getcwd())+"/rknn_model/model.rknn",
        type=str,
        help='path to RKNN model'
    )
    parser.add_argument(
        '--dataset', '-d',
        default=os.path.abspath(os.getcwd())+"/dataset/dataset.txt",
        type=str,
        help='path to calibration dataset (txt file with names of images)'
    )
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return parser.parse_args()

def main(opt):
    # Create RKNN object
    rknn = RKNN(verbose=True)

    # pre-process config
    print('--> Config model')
    rknn.config(mean_values=[[0, 0, 0]], std_values=[[255, 255, 255]], target_platform="rk3588")
    print('done')

    # Load ONNX model
    print('--> Loading model')
    ret = rknn.load_onnx(model=opt.input)
    if ret != 0:
        print('Load model failed!')
        exit(ret)
    print('done')

    # Build model
    print('--> Building model')
    ret = rknn.build(do_quantization=QUANTIZE_ON, dataset=opt.dataset)
    if ret != 0:
        print('Build model failed!')
        exit(ret)
    print('done')

    # Export RKNN model
    print('--> Export rknn model')
    ret = rknn.export_rknn(opt.ouput)
    if ret != 0:
        print('Export rknn model failed!')
        exit(ret)
    print('done')
    rknn.release()

if __name__ == '__main__':
    opt = parse_opt()
    main(opt)