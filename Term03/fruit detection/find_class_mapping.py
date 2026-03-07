import os
import glob
import xml.etree.ElementTree as ET
import numpy as np
import torch
import torch.nn as nn
from sklearn.cluster import KMeans
from itertools import permutations

# Define model architecture classes exactly as in notebook
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

# Recompute anchors
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

model = YOLOv8(input_channels=3, anchors=anchor_boxes, n_classes=4)
state_dict = torch.load("yolo_model_checkpoint.pth", map_location="cpu")
model.load_state_dict(state_dict)
model.eval()

# Let's collect predictions and ground truths for the first 15 images
from PIL import Image

data_samples = []
class_labels = ['banana', 'dragon fruit', 'pineapple', 'snake fruit']

for i in range(15):
    img_path = f"images/fruit{i}.png"
    xml_path = f"annotations/fruit{i}.xml"
    if not os.path.exists(img_path) or not os.path.exists(xml_path):
        continue
        
    img = Image.open(img_path).convert('RGB')
    W, H = img.size
    
    # Load ground truths
    gts = []
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for obj in root.findall('object'):
        name = obj.find('name').text
        bnd = obj.find('bndbox')
        xmin = int(float(bnd.find('xmin').text))
        ymin = int(float(bnd.find('ymin').text))
        xmax = int(float(bnd.find('xmax').text))
        ymax = int(float(bnd.find('ymax').text))
        gts.append((name, [xmin, ymin, xmax, ymax]))
        
    # Model inference
    img_resized = img.resize((416, 416))
    img_t = torch.from_numpy(np.array(img_resized)).permute(2, 0, 1).float() / 255.0
    img_t = img_t.unsqueeze(0)
    
    with torch.no_grad():
        predictions = model(img_t)
        
    # Decode predictions
    decoded_preds = []
    # Let's decode predictions on all 3 scales
    # lg: stride 32, md: stride 16, sm: stride 8
    # lg is first 507, md is next 2028, sm is next 8112
    lg_pred = predictions[0, :507]
    md_pred = predictions[0, 507:2535]
    sm_pred = predictions[0, 2535:]
    
    for pred_scale, stride in [(lg_pred, 32), (md_pred, 16), (sm_pred, 8)]:
        obj_scores = pred_scale[:, 0]
        boxlocs = pred_scale[:, 1:5]
        class_scores = pred_scale[:, 5:]
        
        # Get highest class scores
        max_prob, class_idx = class_scores.max(dim=-1)
        
        for j in range(len(pred_scale)):
            obj_score = obj_scores[j].item()
            if obj_score < 0.1: # filter out very low objectness
                continue
                
            cx_grid, cy_grid, w_pix, h_pix = boxlocs[j]
            cx_pix = cx_grid.item() * stride
            cy_pix = cy_grid.item() * stride
            w = w_pix.item()
            h = h_pix.item()
            
            xmin_416 = cx_pix - w/2
            ymin_416 = cy_pix - h/2
            xmax_416 = cx_pix + w/2
            ymax_416 = cy_pix + h/2
            
            xmin = (xmin_416 / 416.0) * W
            ymin = (ymin_416 / 416.0) * H
            xmax = (xmax_416 / 416.0) * W
            ymax = (ymax_416 / 416.0) * H
            
            decoded_preds.append({
                'box': [xmin, ymin, xmax, ymax],
                'obj_score': obj_score,
                'class_scores': class_scores[j].tolist() # length 4
            })
            
    data_samples.append((gts, decoded_preds))

def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[0]) # wait, height and width area calculation
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    
    unionArea = boxAArea + boxBArea - interArea
    if unionArea == 0:
        return 0
    return interArea / unionArea

# Try all 24 permutations of mapping from predicted class index (0,1,2,3) to class_labels
best_perm = None
best_score = -1

for perm in permutations(range(4)):
    # perm is a tuple of length 4, e.g. (2, 0, 1, 3).
    # This means predicted index i maps to class_labels[perm[i]].
    total_matches = 0
    total_score = 0
    
    for gts, preds in data_samples:
        for gt_name, gt_box in gts:
            best_iou = 0
            best_pred_cls = None
            for p in preds:
                p_box = p['box']
                ov = iou(gt_box, p_box)
                if ov > best_iou:
                    best_iou = ov
                    # Find which predicted class has highest score
                    best_pred_cls = np.argmax(p['class_scores'])
                    
            if best_iou > 0.2:
                mapped_name = class_labels[perm[best_pred_cls]]
                if mapped_name == gt_name:
                    total_matches += 1
                    total_score += best_iou
                    
    if total_score > best_score:
        best_score = total_score
        best_perm = perm
        print(f"Permutation {perm} -> Match score: {total_score:.4f} (Matches: {total_matches})")

print("\nBest permutation mapping:")
for pred_idx, label_idx in enumerate(best_perm):
    print(f"  Predicted Index {pred_idx} maps to class: '{class_labels[label_idx]}'")
