import torch.cuda

import cv2
from matplotlib import pyplot as plt
from torch.nn import functional as F
import time
import numpy as np
import torch
import albumentations as A
from albumentations.pytorch import ToTensorV2

def load_image(uploaded_file):
    if uploaded_file is not None:
        root = uploaded_file
        ds = root
        data = ds.pixel_array.astype(np.float32)
        trans = A.Compose([A.Resize(256, 256), ToTensorV2(transpose_mask=True)])
        transformed = trans(image=data)
        data = transformed['image']
        max_val = torch.max(data)
        data[data < 0] = 0
        data = data / max_val if max_val > 0 else data

        return data.float()
    else:
        return None

class Metrics():

    def __init__(self, pred, gt, loss_fn, eps=1e-10, n_cls=2):

        self.pred, self.gt = torch.argmax(pred, dim=1) > 0, gt  # (batch, width, height)
        self.loss_fn, self.eps, self.n_cls, self.pred_, self.device = loss_fn, eps, n_cls, pred, device

    def to_contiguous(self, inp):
        return inp.contiguous().view(-1)

    def PA(self):

        with torch.no_grad():
            match = torch.eq(self.pred, self.gt).int()

        return float(match.sum()) / float(match.numel())

    def mIoU(self):

        with torch.no_grad():

            pred, gt = self.to_contiguous(self.pred), self.to_contiguous(self.gt)

            iou_per_class = []

            for c in range(self.n_cls):

                match_pred = pred == c
                match_gt = gt == c

                if match_gt.long().sum().item() == 0:
                    iou_per_class.append(np.nan)

                else:

                    intersect = torch.logical_and(match_pred, match_gt).sum().float().item()
                    union = torch.logical_or(match_pred, match_gt).sum().float().item()

                    iou = (intersect + self.eps) / (union + self.eps)
                    iou_per_class.append(iou)

            return np.nanmean(iou_per_class)

    def loss(self):
        return self.loss_fn(self.pred_, self.gt.squeeze(1))


def tic_toc(start_time=None): return time.time() if start_time == None else time.time() - start_time

def load_model():
    model = torch.load('model/DeepLabV3Plus_model.pth', map_location= torch.device('cpu'), weights_only = False)
    return model

@torch.inference_mode()
def get_DeepLabV3Plus_pred(m, img, model):
    m.eval()
    return torch.argmax(model(img.to(device)), dim=1).cpu().squeeze(0)


def ans_show(model, batch, convert_pred=None):
    model.eval()

    img_x = batch.unsqueeze(0)

    if convert_pred != None:
        pred = convert_pred(model, img_x, model)
    else:
        pred = model(img_x.cuda())
        pred = F.sigmoid(pred.detach()).cpu().numpy()[0].transpose(1, 2, 0)

    img_np = img_x.detach().cpu().numpy()[0].transpose(1, 2, 0)

    pred_np = pred.numpy()

    pred_8uc1 = (pred_np.squeeze() * 255).astype(np.uint8)
    contours_pred, _ = cv2.findContours(pred_8uc1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    fig, ax = plt.subplots(1, 1, figsize=(15, 8))
    ax.imshow(img_np, cmap='gray')

    plt.axis('off')

    plt.savefig('static/uploads/scan.png',
                bbox_inches='tight',
                pad_inches=0,
                dpi=100,
                facecolor='black')

    for contour in contours_pred:
        ax.plot(contour[:, 0, 0], contour[:, 0, 1], 'r', linewidth=2)

    # Сохраняем без отступов и рамок
    plt.savefig('static/uploads/contour.png',
                bbox_inches='tight',
                pad_inches=0,
                dpi=100,
                facecolor='black')

    plt.close()
    return


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def predict_mask(image_array):
    # Загрузка модели
    model = torch.load('model/DeepLabV3Plus_model.pth')
    model.eval()

    # Препроцессинг для вашей модели
    input_tensor = torch.from_numpy(image_array).unsqueeze(0).unsqueeze(0)

    # Предсказание
    with torch.no_grad():
        output = model(input_tensor)

    # Постобработка маски
    mask = (output.squeeze().numpy() > 0.5).astype(np.uint8)
    return cv2.resize(mask, (image_array.shape[1], image_array.shape[0]))