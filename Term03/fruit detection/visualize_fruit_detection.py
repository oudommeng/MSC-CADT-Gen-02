import os
import glob
import xml.etree.ElementTree as ET
import numpy as np
import torch
import torch.nn as nn
import torchvision
from PIL import Image, ImageDraw, ImageFont
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
        lg_pred = self.lg_box_predictor(lg_scale_pred)
        md_pred = self.md_box_predictor(md_scale_pred)
        sm_pred = self.sm_box_predictor(sm_scale_pred)
        return lg_pred, md_pred, sm_pred

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

# Initialize model
model = YOLOv8(input_channels=3, anchors=anchor_boxes, n_classes=4)
state_dict = torch.load("yolo_model_checkpoint.pth", map_location="cpu")
model.load_state_dict(state_dict)
model.eval()

class_labels = ['banana', 'dragon fruit', 'pineapple', 'snake fruit']
class_colors = {
    'banana': (255, 215, 0),        # Gold / Yellow
    'dragon fruit': (255, 20, 147), # Deep Pink
    'pineapple': (255, 140, 0),     # Dark Orange
    'snake fruit': (139, 69, 19)    # Saddle Brown
}

output_dir = "/Users/oudommengbycha/.gemini/antigravity-ide/brain/c0713dfa-5f8b-4e45-a29e-b69a96a63fb3"
os.makedirs(output_dir, exist_ok=True)

# Select diverse test images from annotations
test_samples = [
    ("images/fruit0.png", "annotations/fruit0.xml"),
    ("images/fruit10.png", "annotations/fruit10.xml"),
    ("images/fruit100.png", "annotations/fruit100.xml")
]

for idx, (img_path, xml_path) in enumerate(test_samples):
    img = Image.open(img_path).convert('RGB')
    W, H = img.size

    # Load ground truths
    gts = []
    if os.path.exists(xml_path):
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
        lg_pred, md_pred, sm_pred = model(img_t)

    # Decode predictions
    decoded_boxes = []
    decoded_scores = []
    decoded_classes = []

    for pred_scale, stride in [(lg_pred, 32), (md_pred, 16), (sm_pred, 8)]:
        pred_scale = pred_scale[0]
        obj_scores = pred_scale[:, 0]
        boxlocs = pred_scale[:, 1:5]
        class_scores = pred_scale[:, 5:]
        
        prob = class_scores * obj_scores.unsqueeze(-1)
        max_prob, class_idx = prob.max(dim=-1)
        
        for i in range(len(pred_scale)):
            cx_grid, cy_grid, w_pix, h_pix = boxlocs[i]
            
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
            
            decoded_boxes.append([xmin, ymin, xmax, ymax])
            decoded_scores.append(max_prob[i].item())
            decoded_classes.append(class_idx[i].item())

    # Apply NMS
    decoded_boxes_t = torch.tensor(decoded_boxes)
    decoded_scores_t = torch.tensor(decoded_scores)
    decoded_classes_t = torch.tensor(decoded_classes)

    # Since class probabilities are relatively low because it's sigmoid, let's select the top K predictions
    # to show the model's actual best candidates, using a score threshold that fits the distribution.
    # Let's find the best predictions!
    score_threshold = 0.05
    mask = decoded_scores_t > score_threshold
    filtered_boxes = decoded_boxes_t[mask]
    filtered_scores = decoded_scores_t[mask]
    filtered_classes = decoded_classes_t[mask]

    if len(filtered_boxes) > 0:
        keep_idx = torchvision.ops.nms(filtered_boxes, filtered_scores, iou_threshold=0.2)
        final_boxes = filtered_boxes[keep_idx]
        final_scores = filtered_scores[keep_idx]
        final_classes = filtered_classes[keep_idx]
    else:
        final_boxes, final_scores, final_classes = torch.zeros((0, 4)), torch.zeros((0,)), torch.zeros((0,))

    # Draw visual results
    # Create side-by-side visualization: Left = Ground Truth, Right = Model Prediction
    vis_img = Image.new('RGB', (W * 2, H))
    vis_img.paste(img, (0, 0))
    vis_img.paste(img, (W, 0))

    draw = ImageDraw.Draw(vis_img)
    
    # 1. Draw Ground Truths on the Left image
    for name, [xmin, ymin, xmax, ymax] in gts:
        color = class_colors.get(name, (0, 255, 0))
        # Draw box
        draw.rectangle([xmin, ymin, xmax, ymax], outline=color, width=3)
        # Draw label background
        draw.rectangle([xmin, ymin - 15, xmin + len(name)*8 + 10, ymin], fill=color)
        draw.text((xmin + 5, ymin - 13), name, fill=(255, 255, 255))
    
    # Draw Left Label
    draw.rectangle([10, 10, 150, 35], fill=(0, 0, 0))
    draw.text((20, 15), "GROUND TRUTH", fill=(255, 255, 255))

    # 2. Draw Predictions on the Right image (offset by W)
    # Let's sort predictions by score to print/draw top ones first
    if len(final_boxes) > 0:
        # Let's keep at most 5 best detections to avoid cluttered visuals
        sorted_det_indices = torch.argsort(final_scores, descending=True)[:5]
        for det_idx in sorted_det_indices:
            box = final_boxes[det_idx]
            score = final_scores[det_idx].item()
            cls_id = final_classes[det_idx].item()
            cls_name = class_labels[cls_id]
            color = class_colors.get(cls_name, (255, 0, 0))

            pxmin = box[0].item() + W
            pymin = box[1].item()
            pxmax = box[2].item() + W
            pymax = box[3].item()

            # Clip coordinates
            pxmin = max(W, min(pxmin, 2*W))
            pxmax = max(W, min(pxmax, 2*W))
            pymin = max(0, min(pymin, H))
            pymax = max(0, min(pymax, H))

            if (pxmax - pxmin) > 5 and (pymax - pymin) > 5:
                # Draw box
                draw.rectangle([pxmin, pymin, pxmax, pymax], outline=color, width=3)
                label_text = f"{cls_name} ({score*100:.1f}%)"
                # Draw label background
                draw.rectangle([pxmin, pymin - 15, pxmin + len(label_text)*7 + 10, pymin], fill=color)
                draw.text((pxmin + 5, pymin - 13), label_text, fill=(255, 255, 255))
                
                print(f"Sample {idx} prediction - {cls_name}: {score*100:.1f}% | Box: [{box[0]:.1f}, {box[1]:.1f}, {box[2]:.1f}, {box[3]:.1f}]")

    # Draw Right Label
    draw.rectangle([W + 10, 10, W + 150, 35], fill=(0, 0, 0))
    draw.text((W + 20, 15), "MODEL PREDICTION", fill=(255, 255, 255))

    # Save visualization
    save_path = os.path.join(output_dir, f"fruit_detection_res{idx}.png")
    vis_img.save(save_path)
    print(f"Saved visualization to: {save_path}")
