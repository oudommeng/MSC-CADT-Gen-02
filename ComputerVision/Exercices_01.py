import cv2
import numpy as np
import os

class ColorRecognizer:
    def __init__(self):
        self.train_histograms = {}
        self.labels = {}

    def extract_color_histogram(self, image):
        """
        Extracts a 3D color histogram from the image.
        Concept: 256 bins intensity histogram[cite: 231].
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # Using 8 bins for Hue, 12 for Saturation, and 3 for Value
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 12, 3], [0, 180, 0, 256, 0, 256])
        
        # Normalize the histogram (L1 norm) to handle scale differences [cite: 290]
        cv2.normalize(hist, hist, alpha=1, norm_type=cv2.NORM_L1)
        return hist.flatten()

    def train(self, image_paths, labels):
        """Store histograms for training data."""
        for path, label in zip(image_paths, labels):
            img = cv2.imread(path)
            if img is None: continue
            hist = self.extract_color_histogram(img)
            self.train_histograms[path] = hist
            self.labels[path] = label
            print(f"Learned global feature for: {label}")

    def predict(self, query_image_path):
        """
        Find the nearest neighbor using Histogram Intersection or Correlation.
        """
        query_img = cv2.imread(query_image_path)
        if query_img is None: return "Invalid Image"
        
        query_hist = self.extract_color_histogram(query_img)
        
        best_match_label = None
        min_distance = float('inf')
        
        # Compare with all training images (Nearest Neighbor) [cite: 748]
        for path, train_hist in self.train_histograms.items():
            # cv2.HISTCMP_CHISQR is robust for histograms [cite: 780]
            dist = cv2.compareHist(query_hist, train_hist, cv2.HISTCMP_CHISQR)
            
            if dist < min_distance:
                min_distance = dist
                best_match_label = self.labels[path]
                
        return best_match_label

# --- Usage Example ---
# Assume you have folders 'dataset/train/apple' and 'dataset/test/apple_test.jpg'
recognizer = ColorRecognizer()
recognizer.train(['./img/apple1.jpeg', './img/banana1.jpeg'], ['apple', 'banana'])
result = recognizer.predict('./img/predict_01.jpeg')
print(f"Prediction: {result}")