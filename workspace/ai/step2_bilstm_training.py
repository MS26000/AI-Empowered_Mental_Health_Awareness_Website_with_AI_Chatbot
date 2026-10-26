"""
AI-Empowered Mental Health Awareness Website with AI Chatbot - Mood Tracker
Step 2: Build & train the BiLSTM emotion classifier

Loads the artifacts saved by Step 1 (processed_data.npz, tokenizer.pkl,
label_encoder.pkl), builds an Embedding + BiLSTM model, trains it, and
saves the trained model for Step 3 (evaluation) and later Flask integration.

Requirements:
    pip install tensorflow scikit-learn numpy
"""

import pickle
import numpy as np
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Bidirectional, LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.utils import to_categorical

# ---------------------------------------------------------------------
# 1. Load Step 1 outputs
# ---------------------------------------------------------------------
data = np.load("processed_data.npz")
X_train, y_train = data["X_train"], data["y_train"]
X_val, y_val = data["X_val"], data["y_val"]
X_test, y_test = data["X_test"], data["y_test"]

with open("tokenizer.pkl", "rb") as f:
    tokenizer = pickle.load(f)

with open("label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

NUM_CLASSES = len(label_encoder.classes_)
VOCAB_SIZE = min(len(tokenizer.word_index) + 1, tokenizer.num_words or 15000)
MAX_LEN = X_train.shape[1]

print(f"Vocab size: {VOCAB_SIZE}  Max length: {MAX_LEN}  Classes: {NUM_CLASSES}")

# One-hot encode labels for categorical_crossentropy
y_train_cat = to_categorical(y_train, num_classes=NUM_CLASSES)
y_val_cat = to_categorical(y_val, num_classes=NUM_CLASSES)
y_test_cat = to_categorical(y_test, num_classes=NUM_CLASSES)

# ---------------------------------------------------------------------
# 2. Handle class imbalance
#    (Step 1's output showed 'surprise' and 'love' have far fewer
#    examples than 'joy'/'sadness' - class weights correct for this
#    instead of the model just learning to predict the majority classes)
# ---------------------------------------------------------------------
class_weights_array = compute_class_weight(
    class_weight="balanced",
    classes=np.unique(y_train),
    y=y_train,
)
class_weights = {i: w for i, w in enumerate(class_weights_array)}
print("Class weights:", class_weights)

# ---------------------------------------------------------------------
# 3. Build the BiLSTM model
# ---------------------------------------------------------------------
EMBEDDING_DIM = 128

model = Sequential([
    Embedding(input_dim=VOCAB_SIZE, output_dim=EMBEDDING_DIM, input_length=MAX_LEN),
    Bidirectional(LSTM(64, return_sequences=True)),
    Dropout(0.4),
    Bidirectional(LSTM(32)),
    Dropout(0.4),
    Dense(64, activation="relu"),
    Dropout(0.3),
    Dense(NUM_CLASSES, activation="softmax"),
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"],
)

model.summary()

# ---------------------------------------------------------------------
# 4. Train
# ---------------------------------------------------------------------
callbacks = [
    EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
    ModelCheckpoint("emotion_bilstm_best.keras", monitor="val_accuracy",
                     save_best_only=True, verbose=1),
]

history = model.fit(
    X_train, y_train_cat,
    validation_data=(X_val, y_val_cat),
    epochs=20,
    batch_size=64,
    class_weight=class_weights,
    callbacks=callbacks,
)

# ---------------------------------------------------------------------
# 5. Quick test-set check (full evaluation happens in Step 3)
# ---------------------------------------------------------------------
test_loss, test_acc = model.evaluate(X_test, y_test_cat, verbose=0)
print(f"\nTest accuracy: {test_acc:.4f}  Test loss: {test_loss:.4f}")

# ---------------------------------------------------------------------
# 6. Save final model + training history
# ---------------------------------------------------------------------
model.save("emotion_bilstm_final.keras")

with open("training_history.pkl", "wb") as f:
    pickle.dump(history.history, f)

print("\nSaved: emotion_bilstm_best.keras, emotion_bilstm_final.keras, training_history.pkl")
print("Ready for Step 3 (full evaluation: confusion matrix, per-class metrics).")
