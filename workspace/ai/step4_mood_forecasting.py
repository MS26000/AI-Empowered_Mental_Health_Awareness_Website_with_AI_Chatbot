"""
AI-Empowered Mental Health Awareness Website with AI Chatbot - Mood Tracker
Step 4: Mood-forecasting model (RNN/LSTM) - satisfies R1.7

IMPORTANT CONTEXT:
Step 2's BiLSTM classifies a SINGLE journal entry into one of 6 emotions.
This step is a DIFFERENT model: it looks at a user's mood SEQUENCE over
time (e.g. their last 7-14 daily mood scores, logged in MySQL as the app
is used) and forecasts what their mood is trending towards next.

Problem: this kind of longitudinal, per-user mood history doesn't exist
yet, because the app hasn't been used by real users over time. So this
script does two things:

  1. Builds a SYNTHETIC mood-history dataset that mimics what your MySQL
     mood log table will look like once users start using the app
     (needed to build/validate/demo the model architecture now, for your
     report and demo).
  2. Trains an LSTM forecasting model on it.

--> Once your app has real logged mood history (even a few weeks of
    test/demo usage), re-run this script pointing SEQUENCE_SOURCE at a
    CSV exported from your MySQL mood log table instead of the synthetic
    generator - the model architecture stays identical, only the data
    source changes. This is worth stating explicitly in your report as
    "trained on synthetic data pending sufficient real user history."

Requirements:
    pip install tensorflow scikit-learn numpy pandas
"""

import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

SEQUENCE_SOURCE = "synthetic"   # change to "csv" once you have real MySQL export
WINDOW_SIZE = 7                  # look at last 7 mood entries to predict the next

EMOTION_NAMES = ["sadness", "joy", "love", "anger", "fear", "surprise"]
NUM_EMOTIONS = len(EMOTION_NAMES)

# ---------------------------------------------------------------------
# 1. Build the mood-history dataset
# ---------------------------------------------------------------------
def generate_synthetic_users(n_users=300, days_per_user=60, seed=42):
    """
    Simulates daily mood scores per user as a continuous 'valence' score
    (-1 = very negative ... +1 = very positive), with per-user baseline
    mood and realistic day-to-day drift + noise, so sequences have
    learnable structure instead of being pure noise.
    """
    rng = np.random.default_rng(seed)
    all_rows = []
    for user_id in range(n_users):
        baseline = rng.uniform(-0.3, 0.5)          # this user's average mood
        trend = rng.uniform(-0.01, 0.01)            # slow drift up or down
        mood = baseline
        for day in range(days_per_user):
            mood += trend + rng.normal(0, 0.15)      # daily fluctuation
            mood = np.clip(mood, -1, 1)
            all_rows.append({"user_id": user_id, "day": day, "mood_score": mood})
    return pd.DataFrame(all_rows)

if SEQUENCE_SOURCE == "synthetic":
    print("Using SYNTHETIC mood-history data (replace with real MySQL export later).")
    df = generate_synthetic_users()
else:
    # Expected columns once you export from MySQL: user_id, day, mood_score
    # mood_score = numeric mapping of the emotion classifier's daily output,
    # e.g. average valence of that day's Step-2 predictions.
    df = pd.read_csv("mood_history_export.csv")

print(df.head())
print(f"\nTotal users: {df['user_id'].nunique()}  Total rows: {len(df)}")

# ---------------------------------------------------------------------
# 2. Build sliding windows: last WINDOW_SIZE moods -> next mood
# ---------------------------------------------------------------------
X, y = [], []
for user_id, group in df.groupby("user_id"):
    scores = group.sort_values("day")["mood_score"].values
    for i in range(len(scores) - WINDOW_SIZE):
        X.append(scores[i:i + WINDOW_SIZE])
        y.append(scores[i + WINDOW_SIZE])

X = np.array(X).reshape(-1, WINDOW_SIZE, 1)   # (samples, timesteps, features)
y = np.array(y)

print(f"\nSequence samples: {X.shape[0]}  Window size: {WINDOW_SIZE}")

X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

print(f"Train: {len(X_train)}  Val: {len(X_val)}  Test: {len(X_test)}")

# ---------------------------------------------------------------------
# 3. Build the LSTM forecasting model
#    (regression: predicts a continuous next-mood-score, not a class)
# ---------------------------------------------------------------------
model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(WINDOW_SIZE, 1)),
    Dropout(0.3),
    LSTM(32),
    Dropout(0.3),
    Dense(16, activation="relu"),
    Dense(1, activation="tanh"),   # output in [-1, 1], matches mood_score range
])

model.compile(optimizer="adam", loss="mse", metrics=["mae"])
model.summary()

# ---------------------------------------------------------------------
# 4. Train
# ---------------------------------------------------------------------
early_stop = EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)

history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=50,
    batch_size=32,
    callbacks=[early_stop],
)

# ---------------------------------------------------------------------
# 5. Evaluate
# ---------------------------------------------------------------------
test_loss, test_mae = model.evaluate(X_test, y_test, verbose=0)
print(f"\nTest MSE: {test_loss:.4f}  Test MAE: {test_mae:.4f}")
print("(MAE is in the same -1..+1 mood_score units - e.g. 0.1 MAE means")
print(" predictions are off by ~0.1 on average, out of a 2.0-wide range)")

# ---------------------------------------------------------------------
# 6. Helper: convert a continuous forecast back into an emotion label
#    for display in the app (e.g. "trending towards: joy")
# ---------------------------------------------------------------------
def score_to_emotion_bucket(score):
    if score > 0.5:
        return "joy"
    elif score > 0.15:
        return "love"
    elif score > -0.15:
        return "surprise / neutral"
    elif score > -0.5:
        return "fear"
    else:
        return "sadness"

sample_pred = model.predict(X_test[:5])
print("\nSample forecasts:")
for actual, pred in zip(y_test[:5], sample_pred):
    print(f"  actual={actual:.2f}  predicted={pred[0]:.2f}  "
          f"-> trending: {score_to_emotion_bucket(pred[0])}")

# ---------------------------------------------------------------------
# 7. Save model
# ---------------------------------------------------------------------
model.save("mood_forecast_lstm.keras")
print("\nSaved: mood_forecast_lstm.keras")
print("Ready for Step 5 (Flask integration: emotion classifier + forecaster + MySQL logging).")
