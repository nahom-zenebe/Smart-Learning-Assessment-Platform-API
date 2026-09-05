from datetime import datetime, timedelta
from typing import List, Optional

from db.mongodb import get_database

# A submission "passes" when its score (0-100) is >= this value.
PASS_SCORE = 70.0

# Score buckets (lower bounds) used in distributions.
DISTRIBUTION_BOUNDARIES = [0, 50, 70, 90, 101]
BUCKET_LABELS = {
    "0": "0-49",
    "50": "50-69",
    "70": "70-89",
    "90": "90-100",
}


class AnalyticsRepository:
    """Aggregation queries over the submission / progress collections."""

    @property
    def submissions(self):
        return get_database()["submissions"]

    @property
    def progress(self):
        return get_database()["progress"]

    @property
    def questions(self):
        return get_database()["questions"]

    @property
    def quizzes(self):
        return get_database()["quizzes"]

    @property
    def courses(self):
        return get_database()["courses"]

    @property
    def users(self):
        return get_database()["users"]

    # --- generic counts ------------------------------------------------

    async def count_documents(self, collection, query: Optional[dict] = None) -> int:
        return await collection.count_documents(query or {})

    # --- submissions ----------------------------------------------------

    async def submission_rows(
        self, query: Optional[dict] = None, limit: int = 10000
    ) -> List[dict]:
        cursor = (
            self.submissions.find(query or {}).sort("_id", -1).limit(limit)
        )
        return [dict(doc) for doc in await cursor.to_list(length=limit)]

    async def overall_score_summary(self, query: Optional[dict] = None) -> dict:
        """Count / avg / min / max / pass-count for a submission filter."""
        cursor = self.submissions.aggregate(
            [
                {"$match": query or {}},
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": 1},
                        "avg_score": {"$avg": "$score"},
                        "min_score": {"$min": "$score"},
                        "max_score": {"$max": "$score"},
                        "passes": {
                            "$sum": {
                                "$cond": [{"$gte": ["$score", PASS_SCORE]}, 1, 0]
                            }
                        },
                    }
                },
            ]
        )
        rows = await cursor.to_list(length=1)
        if not rows:
            return {
                "total": 0,
                "avg_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "passes": 0,
                "pass_rate": 0.0,
            }
        row = rows[0]
        total = row.get("total") or 0
        row["avg_score"] = round(row.get("avg_score") or 0, 2)
        row["min_score"] = round(row.get("min_score") or 0, 2)
        row["max_score"] = round(row.get("max_score") or 0, 2)
        row["pass_rate"] = round(row["passes"] / total * 100, 2) if total else 0.0
        return row

    async def quiz_score_summary(self, quiz_id: str) -> dict:
        return await self.overall_score_summary({"quiz_id": quiz_id})

    async def all_quiz_score_summaries(self, limit: int = 500) -> List[dict]:
        cursor = self.submissions.aggregate(
            [
                {
                    "$group": {
                        "_id": "$quiz_id",
                        "submissions": {"$sum": 1},
                        "avg_score": {"$avg": "$score"},
                        "min_score": {"$min": "$score"},
                        "max_score": {"$max": "$score"},
                        "passes": {
                            "$sum": {
                                "$cond": [{"$gte": ["$score", PASS_SCORE]}, 1, 0]
                            }
                        },
                    }
                },
                {"$sort": {"submissions": -1}},
                {"$limit": limit},
            ]
        )
        rows = await cursor.to_list(length=limit)
        result = []
        for row in rows:
            total = row.get("submissions") or 0
            result.append(
                {
                    "quiz_id": row["_id"],
                    "submissions": total,
                    "avg_score": round(row.get("avg_score") or 0, 2),
                    "min_score": round(row.get("min_score") or 0, 2),
                    "max_score": round(row.get("max_score") or 0, 2),
                    "pass_rate": (
                        round(row.get("passes", 0) / total * 100, 2)
                        if total
                        else 0.0
                    ),
                }
            )
        return result

    async def score_distribution(self, query: Optional[dict] = None) -> List[dict]:
        cursor = self.submissions.aggregate(
            [
                {"$match": query or {}},
                {
                    "$bucket": {
                        "groupBy": "$score",
                        "boundaries": DISTRIBUTION_BOUNDARIES,
                        "default": "90-100",
                        "output": {"count": {"$sum": 1}},
                    }
                },
            ]
        )
        rows = await cursor.to_list(length=10)
        return [
            {
                "bucket": BUCKET_LABELS.get(str(int(row["_id"])), str(row["_id"])),
                "count": row.get("count", 0),
            }
            for row in rows
        ]

    async def submissions_per_day(self, days: int = 30) -> List[dict]:
        cutoff = datetime.now().astimezone() - timedelta(days=days)
        cursor = self.submissions.aggregate(
            [
                {"$match": {"submitted_at": {"$gte": cutoff}}},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$submitted_at",
                            }
                        },
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
        )
        rows = await cursor.to_list(length=days)
        return [{"date": row["_id"], "count": row.get("count", 0)} for row in rows]

    # --- progress --------------------------------------------------------

    async def progress_rows(
        self, query: Optional[dict] = None, limit: int = 100000
    ) -> List[dict]:
        cursor = self.progress.find(query or {}).sort("_id", -1).limit(limit)
        return [dict(doc) for doc in await cursor.to_list(length=limit)]