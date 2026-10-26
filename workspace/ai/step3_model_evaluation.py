"""
AI-Empowered Mental Health Awareness Website with AI Chatbot - Mood Tracker
Step 3: Full evaluation of the trained BiLSTM emotion classifier

Loads the trained model from Step 2 and produces the evaluation artifacts
you'll want for your FYP report: classification report (precision/recall/
F1 per emotion), confusion matrix, and training curves.

Requirements:
    pip install tensorflow scikit-learn matplotlib seaborn numpy
"""

import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from tensorflow.keras.models import load_model

# ---------------------------------------------------------------------
# 1. Load model, data, and label encoder from Steps 1-2
# ---------------------------------------------------------------------
model = load_model("emotion_bilstm_best.keras")

data = np.load("processed_data.npz")
X_test, y_test = data["X_test"], data["y_test"]

with open("label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

emotion_names = list(label_encoder.classes_)

# ---------------------------------------------------------------------
# 2. Predict on the test set
# ---------------------------------------------------------------------
y_pred_probs = model.predict(X_test)
y_pred = np.argmax(y_pred_probs, axis=1)

# ---------------------------------------------------------------------
# 3. Overall accuracy
# ---------------------------------------------------------------------
acc = accuracy_score(y_test, y_pred)
print(f"Overall test accuracy: {acc:.4f}\n")

# ---------------------------------------------------------------------
# 4. Per-class report (precision / recall / F1) - this is the table
#    you'll want to drop straight into your report's "Results" chapter
# ---------------------------------------------------------------------
report = classification_report(
    y_test, y_pred, target_names=emotion_names, digits=3
)
print("Classification report:\n")
print(report)

with open("classification_report.txt", "w") as f:
    f.write(f"Overall test accuracy: {acc:.4f}\n\n")
    f.write(report)

# ---------------------------------------------------------------------
# 5. Confusion matrix (saved as an image for your report)
# ---------------------------------------------------------------------
cm = confusion_matrix(y_test, y_pred)

plt.figure(figsize=(8, 6))
sns.heatmap(
    cm, annot=True, fmt="d", cmap="Blues",
    xticklabels=emotion_names, yticklabels=emotion_names,
)
plt.xlabel("Predicted emotion")
plt.ylabel("Actual emotion")
plt.title("Confusion Matrix - Emotion Classifier")
plt.tight_layout()
plt.savefig("confusion_matrix.png", dpi=150)
plt.close()
print("Saved: confusion_matrix.png")

# ---------------------------------------------------------------------
# 6. Training curves (loss & accuracy over epochs)
# ---------------------------------------------------------------------
with open("training_history.pkl", "rb") as f:
    history = pickle.load(f)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].plot(history["loss"], label="Train Loss")
axes[0].plot(history["val_loss"], label="Val Loss")
axes[0].set_title("Loss over epochs")
axes[0].set_xlabel("Epoch")
axes[0].legend()

axes[1].plot(history["accuracy"], label="Train Accuracy")
axes[1].plot(history["val_accuracy"], label="Val Accuracy")
axes[1].set_title("Accuracy over epochs")
axes[1].set_xlabel("Epoch")
axes[1].legend()

plt.tight_layout()
plt.savefig("training_curves.png", dpi=150)
plt.close()
print("Saved: training_curves.png")

# ---------------------------------------------------------------------
# 7. Sanity-check on a few custom sentences
# ---------------------------------------------------------------------
with open("tokenizer.pkl", "rb") as f:
    tokenizer = pickle.load(f)

from tensorflow.keras.preprocessing.sequence import pad_sequences

sample_texts = [
    "I feel so anxious about my final year project deadline",
    "I am so happy and grateful today",
    "I miss my friends so much",
]

seqs = tokenizer.texts_to_sequences(sample_texts)
padded = pad_sequences(seqs, maxlen=X_test.shape[1], padding="post", truncating="post")
preds = model.predict(padded)

print("\nSample predictions:")
for text, pred in zip(sample_texts, preds):
    emotion = emotion_names[np.argmax(pred)]
    confidence = np.max(pred)
    print(f"  '{text}' -> {emotion} ({confidence:.2%})")

print("\nEvaluation complete. Files ready for your report:")
print("  classification_report.txt, confusion_matrix.png, training_curves.png")
print("Next: Step 4 - the RNN/LSTM mood-forecasting model.")
