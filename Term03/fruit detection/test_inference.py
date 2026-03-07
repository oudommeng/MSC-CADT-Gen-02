import os
import glob
import xml.etree.ElementTree as ET
import numpy as np
import torch
import torch.nn as nn
import torchvision
from PIL import Image
from sklearn.cluster import KMeans

# 1. Define model architecture classes exactly as in notebook
class Anchors:
    def __init__(self, boxes: np.array, n_clusters: int = 5):
        self.boxes = boxes
        self.n_clusters = n_clusters
        self.cluster_model = KMeans(
            n_clusters=self.n_clusters, n_init=30, max_iter=1000)

    def get(self):
        wh = self.get_boxes_wh()
        self.cluster_model.fit(wh)
        return self.cluster_model.cluster_centers_

    def get_boxes_wh(self):
        box_wh = self.boxes[:, 2:]
        return box_wh

class Upsample(nn.Module):
    def __init__(self, scale_factor, mode='nearest'):
        super(Upsample, self).__init__()
        self.interp = nn.functional.interpolate
        self.scale_factor = scale_factor
        self.mode = mode

    def forward(self, x, target_size=None):
        if target_size is not None:
            x = self.interp(x, size=target_size, mode=self.mode)
        else:
            x = self.interp(x, scale_factor=self.scale_factor, mode=self.mode)
        return x

from torchvision.models.resnet import ResNet, BasicBlock

class FeatureMapper(ResNet):
    def __init__(self, input_channels, n_anchors_per_scale, n_classes, pretrained=True):
        super(FeatureMapper, self).__init__(BasicBlock, [2, 2, 2, 2])
        self.input_channels = input_channels
        self.n_anchors_per_scale = n_anchors_per_scale
        self.n_classes = n_classes
        self.output_channels = self.n_anchors_per_scale*(5 + self.n_classes)

        if pretrained == True and self.input_channels == 3:
            # We will load the state dict later, but let's init without errors
            pass

        self.conv1 = nn.Conv2d(
            self.input_channels, 64,
            kernel_size=(7, 7),
            stride=(2, 2),
            padding=(3, 3),
            bias=False)

        self.conv2 = nn.Conv2d(
            64, 64,
            kernel_size=(7, 7),
            stride=(2, 2),
            padding=(3, 3),
            bias=False)

        sm_c, md_c, lg_c = 512, 256, 128

        self.lg_fmapper = nn.Conv2d(
            sm_c, self.output_channels,
            kernel_size=(1, 1),
            stride=(1, 1),
            bias=False)

        self.md_fmapper = nn.Conv2d(
            sm_c+md_c, self.output_channels,
            kernel_size=(1, 1),
            stride=(1, 1),
            bias=False)

        self.sm_fmapper = nn.Conv2d(
            sm_c+md_c+lg_c, self.output_channels,
            kernel_size=(1, 1),
            stride=(1, 1),
            bias=False)

        self.upsampler = Upsample(2)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.layer1(x)

        addon_1 = self.layer2(x)
        addon_2 = self.layer3(addon_1)

        fmap = self.layer4(addon_2)
        lg_scale_pred = self.lg_fmapper(fmap)

        fmap = self.upsampler(fmap, target_size=addon_2.shape[2:])
        fmap = torch.cat((fmap, addon_2), dim=1)
        md_scale_pred = self.md_fmapper(fmap)

        fmap = self.upsampler(fmap, target_size=addon_1.shape[2:])
        fmap = torch.cat((fmap, addon_1), dim=1)
        sm_scale_pred = self.sm_fmapper(fmap)

        return lg_scale_pred, md_scale_pred, sm_scale_pred

class BoundingBoxPredictor(nn.Module):
    def __init__(self, anchors):
        super(BoundingBoxPredictor, self).__init__()
        self.anchors = anchors
        self.n_anchors_per_scale = len(self.anchors)

    def forward(self, feature_map):
        feature_map = torch.permute(feature_map, (0, 2, 3, 1))
        fmap_shape = feature_map.shape
        feature_map = feature_map.reshape(
            *fmap_shape[0:3], self.n_anchors_per_scale, -1)
        obj_scores = feature_map[..., 0].unsqueeze(dim=-1)
        boxlocs = feature_map[..., 1:5]
        class_scores = feature_map[..., 5:]

        obj_scores = torch.sigmoid(obj_scores)

        idx = self.getOffset(fmap_shape[1:3])
        boxXY = torch.sigmoid(boxlocs[..., :2]) + idx
        boxWH = torch.exp(boxlocs[..., 2:4]) * self.anchors

        class_scores = torch.sigmoid(class_scores)

        bboxes = torch.cat((boxXY, boxWH), dim=-1)
        predictions = torch.cat((obj_scores, bboxes, class_scores), dim=-1)
        predictions = predictions.reshape(
            predictions.shape[0], -1, predictions.shape[-1])
        return predictions

    def getOffset(self, shape):
        h, w = shape
        hindex = torch.Tensor([i for i in range(0, h)]).unsqueeze(dim=-1)
        windex = torch.Tensor([i for i in range(0, w)]).unsqueeze(dim=0)
        hindex = hindex.tile(1, w)
        windex = windex.tile(h, 1)
        idx = torch.stack((windex, hindex), dim=-1).reshape(1, h, w, 1, 2)
        return idx

class YOLOv8(nn.Module):
    def __init__(self, input_channels, anchors, n_classes):
        super(YOLOv8, self).__init__()
        self.input_channels = input_channels
        self.anchors = anchors
        self.n_anchors_per_scale = len(self.anchors)//3
        self.n_classes = n_classes

        self.feature_mapper = FeatureMapper(
            self.input_channels, self.n_anchors_per_scale, self.n_classes, pretrained=False)
        self.sm_box_predictor = BoundingBoxPredictor(self.anchors[:3])
        self.md_box_predictor = BoundingBoxPredictor(self.anchors[3:6])
        self.lg_box_predictor = BoundingBoxPredictor(self.anchors[6:9])

    def forward(self, x):
        lg_scale_pred, md_scale_pred, sm_scale_pred = self.feature_mapper(x)
        lg_scale_pred = self.lg_box_predictor(lg_scale_pred)
        md_scale_pred = self.md_box_predictor(md_scale_pred)
        sm_scale_pred = self.sm_box_predictor(sm_scale_pred)
        pred_bbox = torch.cat(
            (lg_scale_pred, md_scale_pred, sm_scale_pred), dim=1)
        return pred_bbox

# 2. Recompute actual anchors exactly
ann_dir = "annotations"
xml_paths = sorted(glob.glob(os.path.join(ann_dir, "*.xml")))
all_boxes = []
for xp in xml_paths:
    try:
        tree = ET.parse(xp)
        root = tree.getroot()
        for obj in root.findall('object'):
            bnd = obj.find('bndbox')
            xmin = int(float(bnd.find('xmin').text))
            ymin = int(float(bnd.find('ymin').text))
            xmax = int(float(bnd.find('xmax').text))
            ymax = int(float(bnd.find('ymax').text))
            width = xmax - xmin
            height = ymax - ymin
            x_center = xmin + width / 2
            y_center = ymin + height / 2
            all_boxes.append([x_center, y_center, width, height])
    except:
        pass

boxes_np = np.array(all_boxes)
wh = boxes_np[:, 2:]
kmeans = KMeans(n_clusters=9, n_init=30, max_iter=1000, random_state=42)
kmeans.fit(wh)
anchors = kmeans.cluster_centers_
areas = anchors[:, 0] * anchors[:, 1]
sorted_idx = np.argsort(areas)
sorted_anchors = anchors[sorted_idx]
anchor_boxes = torch.from_numpy(sorted_anchors).float()

# 3. Instantiate model and load checkpoint
model = YOLOv8(input_channels=3, anchors=anchor_boxes, n_classes=4)
state_dict = torch.load("yolo_model_checkpoint.pth", map_location="cpu")
model.load_state_dict(state_dict)
model.eval()
print("Model loaded successfully!")

# 4. Load first sample
img_path = "images/fruit0.png"
img = Image.open(img_path).convert('RGB')
img_np = np.array(img)
print("Original image size:", img.size)

# Resize to 416x416 for YOLO input
img_resized = img.resize((416, 416))
img_t = torch.from_numpy(np.array(img_resized)).permute(2, 0, 1).float() / 255.0
img_t = img_t.unsqueeze(0) # batch dim

with torch.no_grad():
    predictions = model(img_t)

print("Predictions shape:", predictions.shape)
# Print predictions with high objectness
obj_scores = predictions[0, :, 0]
high_idx = (obj_scores > 0.05).nonzero(as_tuple=True)[0]
print(f"Found {len(high_idx)} boxes with objectness > 0.05")
for idx in high_idx[:10]:
    pred = predictions[0, idx]
    print(f"Obj: {pred[0]:.4f} | Box: {pred[1]:.2f}, {pred[2]:.2f}, {pred[3]:.2f}, {pred[4]:.2f} | Classes: {pred[5:]}")
