import os
import cv2
import joblib
import numpy as np

from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "..", "models")

svm_model = joblib.load(os.path.join(MODEL_DIR, "svm_model.pkl"))
scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
pca = joblib.load(os.path.join(MODEL_DIR, "pca.pkl"))

base_model = MobileNetV2(
    weights="imagenet",
    include_top=False,
    input_shape=(224, 224, 3)
)

base_model.trainable = False

feature_extractor = Model(
    inputs=base_model.input,
    outputs=base_model.output
)

pool = GlobalAveragePooling2D()

def recommend_shoes(prediction):
    if prediction == 0:
        return {
            "foot_type": "Flat Foot",
            "recommended": ["Motion Control Shoes", "Stability Shoes", "Max Cushioning Shoes"],
            "avoid": ["Minimalist Shoes", "Neutral Cushioning Only"]
        }
    else:
        return {
            "foot_type": "Normal Foot",
            "recommended": ["Neutral Running Shoes", "Moderate Cushioning Shoes"],
            "avoid": ["Heavy Motion Control Shoes"]
        }

def predict_xray(image_path):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Image not found or unreadable.")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (224, 224))
    image = np.expand_dims(image.astype("float32"), axis=0)
    image = preprocess_input(image)

    feature_map = feature_extractor.predict(image, verbose=0)
    features = pool(feature_map).numpy()

    features_scaled = scaler.transform(features)
    features_pca = pca.transform(features_scaled)

    prediction = svm_model.predict(features_pca)[0]
    confidence = svm_model.predict_proba(features_pca).max() * 100

    recommendation = recommend_shoes(prediction)

    return {
        "prediction": recommendation["foot_type"],
        "confidence": round(confidence, 2),
        "recommended_shoes": recommendation["recommended"],
        "avoid": recommendation["avoid"]
    }