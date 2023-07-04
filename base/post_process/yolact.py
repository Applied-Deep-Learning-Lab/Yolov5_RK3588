import math
from multiprocessing import Queue
import cv2
from base.inference.utils import (after_nms_numpy, make_anchors, nms_numpy,
                                  np_softmax, rknn_draw)

rknn_postprocess_cfg = {'img_size' : 544,
                        'scales' : [24, 48, 96, 192, 384],
                        'aspect_ratios': [1, 0.5, 2],
                        'top_k' : 200,
                        'max_detections' : 100,
                        'nms_score_thre' : 0.5,
                        'nms_iou_thre' : 0.5,
                        'visual_thre' : 0.3,
                    }


def yolact_post_process(q_in: Queue, q_out: Queue):
    while True:
        outputs, raw_frame, frame_id = q_in.get()
        # dets = None
        class_p, box_p, coef_p, proto_p = outputs
        class_p = class_p[0]
        box_p = box_p[0]
        coef_p = coef_p[0]
        class_p = np_softmax(class_p)
        anchors = []
        fpn_fm_shape = [
            math.ceil(544 / stride) for stride in (8, 16, 32, 64, 128)
        ]
        for i, size in enumerate(fpn_fm_shape):
            anchors += make_anchors(
                rknn_postprocess_cfg,
                size,
                size,
                rknn_postprocess_cfg['scales'][i]
            )
        results = nms_numpy(
            class_pred=class_p,
            box_pred=box_p,
            coef_pred=coef_p,
            proto_out=proto_p,
            anchors=anchors,
            cfg=rknn_postprocess_cfg
        )
        new_results = after_nms_numpy(*results, 544, 544, rknn_postprocess_cfg)
        frame = cv2.resize(raw_frame, (544, 544))
        frame = rknn_draw(frame, *new_results)
        q_out.put((raw_frame, frame, frame_id))