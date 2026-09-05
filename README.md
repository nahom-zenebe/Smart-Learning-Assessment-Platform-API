# Smart Learning Assessment Platform API

FastAPI + MongoDB (Motor, async) backend for quizzes, questions, graded submissions and learner progress.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirement.txt
# edit .env (set MONGODB_URL etc.)
uvicorn app.main:app --reload
```

## Assessment resources & endpoints

The core flow is: **Quiz -> Question -> Submission (auto-graded) -> Progress**.

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/quizzes/` | Create a quiz |
| `GET` | `/quizzes/` | List quizzes |
| `GET` | `/quizzes/{quiz_id}` | Get one quiz |
| `GET` | `/quizzes/{quiz_id}/questions` | Questions of a quiz (take-quiz order) |
| `PUT` | `/quizzes/{quiz_id}` | Update a quiz |
| `DELETE` | `/quizzes/{quiz_id}` | Delete a quiz |
| `POST` | `/questions/` | Create a question (auto-linked to its quiz) |
| `GET` | `/questions/` | List questions |
| `GET` | `/questions/{question_id}` | Get one question |
| `PUT` | `/questions/{question_id}` | Update a question |
| `DELETE` | `/questions/{question_id}` | Delete a question (unlinks from quiz) |
| `POST` | `/submissions/` | Submit answers -> **score computed server-side** |
| `GET` | `/submissions/?user_id=&quiz_id=` | List / filter submissions |
| `GET` | `/submissions/{submission_id}` | Get one submission |
| `DELETE` | `/submissions/{submission_id}` | Delete a submission |
| `POST` | `/progress/` | **Upsert** progress per (user_id, course_id) pair |
| `GET` | `/progress/?user_id=&course_id=` | List / filter progress |
| `GET` | `/progress/{progress_id}` | Get one progress record |
| `PUT` | `/progress/{progress_id}` | Partial update (re-validates counts) |
| `DELETE` | `/progress/{progress_id}` | Delete a progress record |

Other resources: `/courses/*`, `/lessons/*`, `/auth/register`, `/auth/login`, `/payments/create-intent`, `/webhooks/stripe`, `/health`.

Interactive docs: http://127.0.0.1:8000/docs

## Question format

`options` is a list of strings and `correct_option_id` is the **index of the correct option** as a string - e.g. `options=["A","B","C"]`, `correct_option_id="1"` means B.

## Submission format

`answers` is positional: `answers[i]` is the option index (as a string) the user chose for the i-th question of the quiz (in creation order). The score is a percentage `0.0-100.0` rounded to 2 decimals, computed server-side.

```json
POST /submissions/
{
  "quiz_id": "<quiz_id>",
  "user_id": "user_123",
  "answers": ["1", "0"]
}
```