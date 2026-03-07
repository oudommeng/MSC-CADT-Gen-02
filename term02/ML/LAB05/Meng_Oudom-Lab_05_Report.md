# Lab 05: Wine Quality Neural Network Classifier Report

**Student Name**: Meng Oudom  
**Date**: January 30, 2026  
**Google Colab Notebook**: [View on Google Drive](https://drive.google.com/file/d/1CVIy1m8JCvGgfxFzgGyD9-drVXXye-_V/view?usp=sharing)

---

## Objective

This project developed a Multi-Layer Perceptron (MLP) neural network to classify wine quality (Medium, Good, Excellent) based on 11 chemical features. The dataset was split into training (60%), validation (10%), and testing (30%) subsets, with systematic hyperparameter tuning to identify the optimal architecture.

## Dataset

The wine quality dataset contained 4,898 samples. Data cleaning removed 937 duplicates, resulting in 3,961 unique samples for analysis. No missing values were found. The preprocessing pipeline included label encoding (Medium→0, Good→1, Excellent→2) and feature standardization using StandardScaler to ensure proper neural network training.

## Model Selection

A grid search evaluated nine architectures with varying hidden layers (2, 3, 4) and units per layer (25, 50, 100). Each model was trained on the training set and evaluated on the validation set. The 2-layer architecture with 50 units per layer achieved the best performance with a validation error of 44.19%. Deeper networks (3-4 layers) did not outperform the simpler 2-layer model, suggesting that additional complexity was unnecessary for this dataset.

## Results

The selected model (2 layers, 50 units) achieved a test error rate of 45.75%, corresponding to 54.25% accuracy. The close alignment between validation error (44.19%) and test error (45.75%) indicates good generalization without overfitting. The moderate accuracy reflects the inherent difficulty of wine quality prediction, which involves subjective assessment and complex chemical interactions.

## Conclusion

The systematic model selection process successfully identified an optimal neural network architecture. While the 54.25% accuracy is moderate, it demonstrates that the model learned meaningful patterns from the data. Future improvements could include regularization techniques, ensemble methods, or feature engineering to capture chemical interactions more effectively.

---

## Key Results

- **Final Dataset**: 3,961 samples (937 duplicates removed)
- **Data Split**: Training 60% (2,376) | Validation 10% (396) | Test 30% (1,189)
- **Best Model**: 2 hidden layers, 50 units each
- **Test Accuracy**: 54.25% (Error Rate: 45.75%)
- **Validation Accuracy**: 55.81% (Error Rate: 44.19%)
