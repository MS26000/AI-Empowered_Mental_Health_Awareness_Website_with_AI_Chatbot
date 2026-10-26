# AI-Empowered Mental Health Awareness Website with AI Chatbot

A student mental wellness web app that combines mood tracking, an emotion-aware AI chatbot, mood forecasting, a stress checker, and a self-assessment quiz — built with Flask, MySQL, and TensorFlow.

## Overview

This project helps students check in on their mental wellbeing through:
- **Mood journaling** — write a journal entry and an AI model detects the underlying emotion.
- **Mood forecasting** — an AI model looks at recent mood history and predicts where mood is trending.
- **AI chatbot** — a Gemini-powered chatbot that's aware of the user's most recent logged mood, with built-in crisis-keyword detection that responds supportively and points toward professional help.
- **Stress checker** — a simple vitals-based stress level estimator.
- **Self-assessment quiz** — a scored wellbeing quiz.
- **Admin panel** — view registered users and submitted feedback.

## Tech Stack

- **Frontend:** plain HTML, CSS, JavaScript
- **Backend:** Flask (Python), SQLAlchemy, PyMySQL
- **Database:** MySQL / MariaDB
- **AI / ML:** TensorFlow (Keras), scikit-learn — BiLSTM for emotion classification, LSTM for mood forecasting
- **Chatbot:** Google Gemini API (`google-genai`)
- **Dev environment:** VS Code, Python 3.11, XAMPP

## Project Structure

```
workspace/
├── frontend/     Static site (HTML/CSS/JS)
├── backend/      Flask app, database models, admin setup
└── ai/           Model training scripts + Flask AI routes (mood, chatbot, quiz, recommendations)
```

## Getting Started

1. Install Python 3.11, VS Code, and XAMPP (MySQL + Apache).
2. Create the database: `CREATE DATABASE \`AI-Empowered_Mental_Health_Awareness_Website_with_AI_Chatbot\` CHARACTER SET utf8mb4;`
3. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r backend/requirements.txt
   pip install -r ai/requirements.txt
   ```
4. Set your Gemini API key: `$env:GEMINI_API_KEY="your_key_here"`
5. Create the admin account: `python backend/create_admin.py`
6. Run the backend: `python backend/app.py`
7. Open `frontend/index.html` with Live Server.

The trained AI model files (`tokenizer.pkl`, `label_encoder.pkl`, `emotion_bilstm_best.h5`, `mood_forecast_lstm.h5`) must be present in `ai/models/` before starting the backend — see the Model Training and Results section below for how they were produced.

## Model Training and Results

### Emotion Classifier (BiLSTM)

Trained on the Kaggle "Emotions dataset for NLP" (16,000 training / 2,000 validation / 2,000 test entries) across 6 emotion classes: sadness, joy, love, anger, fear, surprise.

**Overall test accuracy: 89.5%**

Per-class performance on the test set:
- Anger — precision 0.933, recall 0.952, f1-score 0.942 (581 samples)
- Fear — precision 0.958, recall 0.889, f1-score 0.922 (695 samples)
- Joy — precision 0.732, recall 0.843, f1-score 0.784 (159 samples)
- Love — precision 0.912, recall 0.862, f1-score 0.886 (275 samples)
- Sadness — precision 0.837, recall 0.848, f1-score 0.843 (224 samples)
- Surprise — precision 0.630, recall 0.879, f1-score 0.734 (66 samples)

Macro average f1-score: 0.852 · Weighted average f1-score: 0.897

The model performs strongly overall, especially on the larger classes (anger, fear). Joy and surprise — the two smallest classes in the dataset — have lower precision, meaning the model more often mistakes other emotions for them, which is a common effect of class imbalance rather than a modeling flaw.

**Confusion matrix:**

![Confusion Matrix](docs/confusion_matrix.png)

Most predictions fall on the diagonal, confirming the model is correctly separating the 6 emotions in most cases. The clearest confusion is fear being mistaken for joy 48 times, and sadness being mistaken for surprise 24 times.

**Training curves:**

![Training Curves](docs/training_curves.png)

Training accuracy climbs steadily while validation accuracy levels off after epoch 2, and validation loss starts creeping back up slightly after epoch 3 — a sign of mild overfitting past that point, which is why the best-performing checkpoint (not necessarily the final epoch) is the one saved and used by the app.

### Mood Forecasting (LSTM)

A second, separate model that takes a sequence of recent mood scores and predicts the next likely mood trend, used to power the forecasting feature on the mood tracker page.

## Author

Muhammad Shahzad -123muhammmadshahzad26@gmail.com

## License

For academic use.
