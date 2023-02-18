import io
from typing import Optional
import json
import PIL
import numpy as np
import cv2
import onnxruntime as ort
import MediaHandler
from typing import NamedTuple, Literal
from controllers import functions as func
import coco_formatter


class myProcessor(MediaHandler.Processor):
    def __init__(self, cfg: NamedTuple):
        super().__init__()

        path_model = cfg.path_model
        ort_session = ort.InferenceSession(path_model)
        ort_session.get_modelmeta()
        # input_name = ort_session.get_inputs()
        # output_name = ort_session.get_outputs()
        self.session = ort_session

        if cfg.path_categories == '' or cfg.path_categories == 'coco':
            self.categories = coco_formatter.get_categories()
        else:
            with open(cfg.path_categories, 'rb') as f:
                self.categories = json.load(f)
        
        # print(self.categories, len(self.categories))
        self.cvt_catid = lambda catid: self.categories[catid]['id']

    
    def get_categories(self):
        return self.categories

  
    
    async def post_BytesIO_process(
        self, \
        process_name : Literal['image-bytesio'], \
        fBytesIO: io.BytesIO, \
        fname_org: str,\
        extension: str = 'jpg',\
        **kwargs
    ):
        if process_name != 'image-bytesio':
            raise ValueError('error')

        img_pil = PIL.Image.open(fBytesIO)
        img_np = np.asarray(img_pil)
        # print(img_np.shape) # (h, w, 3)
        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        # print(img_np.shape) # height, width, chanel

        images = [coco_formatter.create_image(
            id = 0,
            width = img_np.shape[1],
            height = img_np.shape[0],
            file_name = fname_org
        )]

        annotations = func.detection_image(
            self.session,
            img_np,
            (640, 640),
            convert_catid=self.cvt_catid,
            th_conf = kwargs['th_conf'],
            th_nms = kwargs['th_nms']
        )
        
        return dict(
            images = images,
            annotations = annotations
        )


    async def post_file_process(
        self, \
        process_name: Literal['video'], \
        fpath_org: str, \
        fpath_dst: Optional[str] = None, \
        **kwargs
    ) -> dict:

        ret = func.detection_video(
            self.session,
            fpath_org,
            (640, 640),
            convert_catid=self.cvt_catid,
            th_conf = kwargs['th_conf'],
            th_nms = kwargs['th_nms']
        )

        return ret