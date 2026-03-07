import os
import glob
import xml.etree.ElementTree as ET
import numpy as np
from sklearn.cluster import KMeans

# 1. Load all annotations
ann_dir = "annotations"
xml_paths = sorted(glob.glob(os.path.join(ann_dir, "*.xml")))

all_boxes = []
class_names = set()

for xp in xml_paths:
    try:
        tree = ET.parse(xp)
        root = tree.getroot()
    except Exception:
        continue

    for obj in root.findall('object'):
        name_tag = obj.find('name')
        bnd = obj.find('bndbox')
        if name_tag is None or bnd is None:
            continue
        try:
            xmin = int(float(bnd.find('xmin').text))
            ymin = int(float(bnd.find('ymin').text))
            xmax = int(float(bnd.find('xmax').text))
            ymax = int(float(bnd.find('ymax').text))
            
            # VOC format: [xmin, ymin, xmax, ymax]
            # Convert to [x_center, y_center, width, height] as expected by Anchors?
            # Wait, let's look at the class Anchors in the notebook:
            # def get_boxes_wh(self):
            #     box_wh = self.boxes[:, 2:]
            #     return box_wh
            # This means the box format passed to Anchors should be N x 4, where index 2 and 3 are width and height!
            width = xmax - xmin
            height = ymax - ymin
            x_center = xmin + width / 2
            y_center = ymin + height / 2
            
            all_boxes.append([x_center, y_center, width, height])
            class_names.add(name_tag.text)
        except Exception as e:
            continue

print("Found class names:", sorted(list(class_names)))
print("Total bounding boxes:", len(all_boxes))

if len(all_boxes) > 0:
    boxes_np = np.array(all_boxes)
    # Let's cluster using KMeans to find 9 anchors
    wh = boxes_np[:, 2:]
    kmeans = KMeans(n_clusters=9, n_init=30, max_iter=1000, random_state=42)
    kmeans.fit(wh)
    anchors = kmeans.cluster_centers_
    # Let's sort anchors by area (width * height) so we can map them to scales: small, medium, large.
    # Small scale predictor gets self.anchors[:3] (small anchors)
    # Medium scale predictor gets self.anchors[3:6]
    # Large scale predictor gets self.anchors[6:9]
    areas = anchors[:, 0] * anchors[:, 1]
    sorted_idx = np.argsort(areas)
    sorted_anchors = anchors[sorted_idx]
    
    print("Sorted Anchors (W, H):")
    for i, a in enumerate(sorted_anchors):
        print(f"  Anchor {i}: {a[0]:.2f} x {a[1]:.2f} (Area: {areas[sorted_idx[i]]:.2f})")
