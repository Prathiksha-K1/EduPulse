"""
Knowledge Tracing & Adaptive Level Estimator
-------------------------------------------
This module exposes a clean interface `estimate_level(history)`
currently driven by an Elo-based cognitive mastery algorithm.
Designed so that any deep learning model (e.g., DKT / Saint+ trained on Kaggle)
can be swapped in seamlessly.
"""

from typing import List, Dict, Any

class KnowledgeTracingEstimator:
    def __init__(self, base_rating: float = 1200.0, k_factor: float = 32.0):
        self.base_rating = base_rating
        self.k_factor = k_factor

    def compute_expected_score(self, student_rating: float, item_difficulty: float) -> float:
        """Standard logistic expectation function from Item Response Theory (IRT) & Elo."""
        return 1.0 / (1.0 + 10.0 ** ((item_difficulty - student_rating) / 400.0))

    def update_rating(self, current_rating: float, actual_score: float, item_difficulty: float = 1200.0) -> float:
        expected = self.compute_expected_score(current_rating, item_difficulty)
        return current_rating + self.k_factor * (actual_score - expected)

    def estimate_level(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Public model hook.
        
        Args:
            history: List of interaction dictionaries containing:
                     - 'score': number of correct answers
                     - 'total': total questions
                     - 'percentage': percentage score (0-100)
                     - 'time_taken': seconds
                     - 'topic': subject/topic name

        Returns:
            Dict containing level ('Beginner', 'Intermediate', 'Advanced'),
            elo_rating, mastery_percentage, and adaptive recommendation.
        """
        if not history:
            return {
                "level": "Beginner",
                "elo_rating": self.base_rating,
                "mastery_percentage": 40.0,
                "recommendation": "Start with foundational concepts and core definitions."
            }

        rating = self.base_rating
        total_questions = 0
        total_correct = 0

        for record in history:
            score = record.get("score", 0)
            total = record.get("total", 5)
            total_questions += total
            total_correct += score

            # Normalize outcome to [0, 1]
            outcome = score / max(total, 1)
            # Higher difficulty for consecutive high scores
            item_difficulty = 1100.0 + (outcome * 200.0)
            rating = self.update_rating(rating, outcome, item_difficulty)

        accuracy = (total_correct / max(total_questions, 1)) * 100.0

        if rating >= 1350 or accuracy >= 80:
            level = "Advanced"
            rec = "Ready for high-order application questions and board exam challenge sets."
        elif rating >= 1150 or accuracy >= 50:
            level = "Intermediate"
            rec = "Good conceptual grasp! Focus on numerical practice and multi-step derivations."
        else:
            level = "Beginner"
            rec = "Strengthen basic definitions and follow along with the audio lecture summaries."

        return {
            "level": level,
            "elo_rating": round(rating, 1),
            "mastery_percentage": min(round(accuracy, 1), 100.0),
            "recommendation": rec
        }

# Global instance for easy import
estimator = KnowledgeTracingEstimator()

def estimate_level(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Clean pluggable entry point."""
    return estimator.estimate_level(history)
