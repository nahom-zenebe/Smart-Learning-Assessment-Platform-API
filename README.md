# Smart Learning Assessment Platform API

FastAPI + MongoDB (Motor, async) backend for quizzes, questions, graded submissions and learner progress.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirement.txt
# edit .env (set MONGODB_URL etc.)
uvicorn app.main:app --reload
```

## Docker

Copy `.env` from your local environment or create it with at least a strong
`JWT_SECRET`, then start the API and MongoDB together:

```bash
docker compose up --build
```

The API is available at http://127.0.0.1:8000 and its interactive docs are at
http://127.0.0.1:8000/docs. MongoDB data is stored in the named
`mongo_data` volume. Stop the stack with `docker compose down`; add `-v` only
when you also want to delete the database volume.

The GitHub Actions workflow runs dependency installation, Python compilation,
application import, Compose validation, and a Docker build on pull requests
and pushes. A push to `main` also publishes the image to GitHub Container
Registry as `latest` and with its commit SHA.

## Security middleware

All requests flow through a middleware pipeline (outermost first):

```
RateLimit -> JWTAuth -> RoleAccess -> Logging -> route
```

### 1. Authentication (`JWTAuthMiddleware`)

- **Public paths** (no token needed): `/health`, `/docs`, `/redoc`, `/openapi.json`,
  `/auth/register`, `/auth/login`, `/webhooks/stripe`.
- Everything else requires a JWT obtained from `/auth/login`.
- Send it as `Authorization: Bearer <token>` or as an `access_token` cookie.
- On success the user claims (`id`, `email`, `role`) are attached to the request.
- Missing/invalid/expired tokens receive `401`.

```bash
# register
curl -s -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Sam","email":"sam@test.com","password":"pass1234"}'

# login -> access_token
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name":"Sam","email":"sam@test.com","password":"pass1234"}'

# use the token
curl -s -H "Authorization: Bearer <token>" http://127.0.0.1:8000/quizzes/
```

> Admin accounts cannot self-register (returns 400); provision them from an
> existing admin or directly in the database. Roles are `student`, `instructor`, `admin`.

### 2. Rate limiting (`RateLimitMiddleware`)

In-memory fixed-window limiter keyed by client IP (honours `X-Forwarded-For`).
General and `/auth/*` endpoints use **separate budgets**. Exceeding the limit
returns `429` plus a `Retry-After` header.

| Env var | Default | Purpose |
| ------- | ------- | ------- |
| `RATE_LIMIT_MAX` | `120` | Requests per IP per window (general API) |
| `AUTH_RATE_LIMIT_MAX` | `10` | Requests per IP per window (`/auth/*`) |
| `RATE_LIMIT_SECONDS` | `60` | Window length in seconds |

### 3. Role-based access (`RoleAccessMiddleware`)

Declarative policy in `core/middleware.py::ROLE_POLICIES`. Requests that match a
rule need one of the listed roles; everything else needs any authenticated user.

| Method | Path prefix | Roles |
| ------ | ----------- | ----- |
| `POST/PUT/DELETE` | `/courses`, `/lessons`, `/quizzes`, `/questions` | instructor, admin |
| `DELETE` | `/submissions`, `/progress` | admin |
| `*` | `/admin` | admin |
| fallback (all other authed requests incl. `GET`, `POST /submissions`, `POST /progress`) | any role |

Password hashing is done with `bcrypt` directly (`core/security.py`) and JWTs are
signed with HS256 using `JWT_SECRET` from the environment.

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