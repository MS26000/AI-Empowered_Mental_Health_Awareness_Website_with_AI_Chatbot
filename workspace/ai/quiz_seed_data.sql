-- AI-Empowered Mental Health Awareness Website with AI Chatbot - Mood Tracker
-- Seed data: example "Weekly Wellness Check-in" quiz
-- Original questions (not a reproduction of any clinical instrument).
-- Each question has 4 options scored 0-3 (0 = best, 3 = most strain).

INSERT INTO quizzes (title, description) VALUES
('Weekly Wellness Check-in', 'A quick self-reflection on how your week has been going.');

-- Assumes the quiz above got id = 1. Adjust if your table already has rows.

INSERT INTO quiz_questions (quiz_id, question_text, question_order) VALUES
(1, 'How has your energy level been this week?', 1),
(1, 'How well have you been sleeping?', 2),
(1, 'How connected have you felt to friends or family?', 3),
(1, 'How manageable has your workload felt?', 4),
(1, 'How often have you felt overwhelmed?', 5),
(1, 'How much have you enjoyed your usual activities?', 6);

-- Q1: energy level
INSERT INTO quiz_options (question_id, option_text, score_value) VALUES
(1, 'Energetic, felt good most days', 0),
(1, 'Okay, a few tired days', 1),
(1, 'Low energy most of the week', 2),
(1, 'Exhausted almost every day', 3);

-- Q2: sleep
INSERT INTO quiz_options (question_id, option_text, score_value) VALUES
(2, 'Slept well and felt rested', 0),
(2, 'Mostly fine, occasional bad night', 1),
(2, 'Struggled to sleep several nights', 2),
(2, 'Barely slept / sleep felt broken', 3);

-- Q3: connection
INSERT INTO quiz_options (question_id, option_text, score_value) VALUES
(3, 'Felt close and supported', 0),
(3, 'Had some good moments with others', 1),
(3, 'Felt a bit distant from people', 2),
(3, 'Felt isolated or alone', 3);

-- Q4: workload
INSERT INTO quiz_options (question_id, option_text, score_value) VALUES
(4, 'Felt on top of things', 0),
(4, 'Busy but manageable', 1),
(4, 'Behind and stressed about it', 2),
(4, 'Completely overwhelmed by it', 3);

-- Q5: overwhelm frequency
INSERT INTO quiz_options (question_id, option_text, score_value) VALUES
(5, 'Rarely or never', 0),
(5, 'A couple of times', 1),
(5, 'Frequently', 2),
(5, 'Almost constantly', 3);

-- Q6: enjoyment
INSERT INTO quiz_options (question_id, option_text, score_value) VALUES
(6, 'Enjoyed things as usual', 0),
(6, 'Enjoyed most things, less than usual for some', 1),
(6, 'Struggled to enjoy most things', 2),
(6, 'Nothing felt enjoyable this week', 3);
