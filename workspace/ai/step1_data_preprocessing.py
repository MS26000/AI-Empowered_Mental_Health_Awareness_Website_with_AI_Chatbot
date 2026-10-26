"""
AI-Empowered Mental Health Awareness Website with AI Chatbot - Mood Tracker
Step 1: Load & preprocess the Kaggle emotion dataset

Dataset (already split by Kaggle into 3 files):
    training.csv    (16,000 rows)
    validation.csv  (2,000 rows)
    test.csv        (2,000 rows)

Columns: text, label
Label mapping: 0=sadness, 1=joy, 2=love, 3=anger, 4=fear, 5=surprise

Just put the zip file you downloaded from Kaggle (e.g. archive.zip) in the
same folder as this script and set ZIP_PATH below - the script will unzip
it automatically. No manual extraction needed.

Requirements:
    pip install pandas scikit-learn tensorflow
"""

import os
import re
import pickle
import zipfile
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

ZIP_PATH = "ai/Dataset.zip" # Fixed backslash to forward slash for safety
DATA_DIR = "data"
# The folder created inside "data" during extraction:
EXTRACTED_SUBDIR = os.path.join(DATA_DIR, "Dataset") 
EMOTION_NAMES = ["sadness", "joy", "love", "anger", "fear", "surprise"]

# ---------------------------------------------------------------------
# 0. Unzip the dataset (only runs if 'data/' doesn't already exist)
# ---------------------------------------------------------------------
if not os.path.isdir(DATA_DIR):
    print(f"Extracting {ZIP_PATH} -> {DATA_DIR}/ ...")
    os.makedirs(DATA_DIR, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(DATA_DIR)
    print("Extraction done. Files found:", os.listdir(EXTRACTED_SUBDIR))
else:
    print(f"'{DATA_DIR}/' already exists, skipping extraction.")

# ---------------------------------------------------------------------
# 1. Load the three pre-split files from the correct subfolder
# ---------------------------------------------------------------------
train_df = pd.read_csv(os.path.join(EXTRACTED_SUBDIR, "training.csv"))
val_df = pd.read_csv(os.path.join(EXTRACTED_SUBDIR, "validation.csv"))
test_df = pd.read_csv(os.path.join(EXTRACTED_SUBDIR, "test.csv"))


print("Train:", train_df.shape, " Val:", val_df.shape, " Test:", test_df.shape)
print("\nTraining class distribution:")
print(train_df["label"].value_counts().sort_index())

# ---------------------------------------------------------------------
# 2. Clean the text
# ---------------------------------------------------------------------
def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", "", text)   # remove URLs
    text = re.sub(r"@\w+", "", text)             # remove @mentions
    text = re.sub(r"#", "", text)                # strip hashtag symbol, keep word
    text = re.sub(r"[^a-z\s']", "", text)         # keep letters, spaces, apostrophes
    text = re.sub(r"\s+", " ", text).strip()
    return text

for d in (train_df, val_df, test_df):
    d["clean_text"] = d["text"].apply(clean_text)
    d.drop(d[d["clean_text"].str.len() == 0].index, inplace=True)

# ---------------------------------------------------------------------
# 3. Encode labels
#    (labels are already numeric 0-5, but we still fit a LabelEncoder so
#    Step 2+ can map predictions back to emotion names consistently)
# ---------------------------------------------------------------------
label_encoder = LabelEncoder()
label_encoder.fit(EMOTION_NAMES)   # fixes the 0..5 -> name mapping explicitly

print("\nLabel mapping:")
for i, name in enumerate(EMOTION_NAMES):
    print(f"  {i} -> {name}")

# ---------------------------------------------------------------------
# 4. Tokenize + pad sequences (ready for the BiLSTM in Step 2)
# ---------------------------------------------------------------------
MAX_VOCAB = 15000
MAX_LEN = 40  # covers the vast majority of entries in this dataset

tokenizer = Tokenizer(num_words=MAX_VOCAB, oov_token="<OOV>")
tokenizer.fit_on_texts(train_df["clean_text"])  # fit ONLY on training data

def to_padded_sequences(texts):
    seqs = tokenizer.texts_to_sequences(texts)
    return pad_sequences(seqs, maxlen=MAX_LEN, padding="post", truncating="post")

X_train = to_padded_sequences(train_df["clean_text"])
X_val = to_padded_sequences(val_df["clean_text"])
X_test = to_padded_sequences(test_df["clean_text"])

y_train = train_df["label"].values
y_val = val_df["label"].values
y_test = test_df["label"].values

# ---------------------------------------------------------------------
# 5. Save everything Step 2 will need
# ---------------------------------------------------------------------
with open("tokenizer.pkl", "wb") as f:
    pickle.dump(tokenizer, f)

with open("label_encoder.pkl", "wb") as f:
    pickle.dump(label_encoder, f)

np.savez(
    "processed_data.npz",
    X_train=X_train, y_train=y_train,
    X_val=X_val, y_val=y_val,
    X_test=X_test, y_test=y_test,
)

print("\nSaved: tokenizer.pkl, label_encoder.pkl, processed_data.npz")
print("Ready for Step 2 (BiLSTM training).")
