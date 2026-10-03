import numpy as np
from typing import Dict, List, Any, Optional

class BreedMatcherEngine:
    """
    Encapsulates the fuzzy matching, dealbreaker filtration, and weighted 
    aggregation algorithms using strictly atomic methods and separated variable definitions.
    """
    
    def __init__(self, user_preferences: Dict[str, Any], breeds_data: List[Dict[str, Any]]) -> None:
        user_preferences_argument: Dict[str, Any]
        breeds_data_argument: List[Dict[str, Any]]

        user_preferences_argument = user_preferences
        breeds_data_argument = breeds_data

        self._user_preferences = user_preferences_argument
        self._breeds_data = breeds_data_argument

    def _is_ordinal_trait_violating_dealbreaker(self, breed_value: int, configuration: Dict[str, Any]) -> bool:
        """Atomic check: Verifies if a single ordinal trait value violates its dealbreaker status."""
        is_dealbreaker: bool
        user_minimum: int
        user_maximum: int
        is_within_range: bool
        is_violating_range: bool

        is_dealbreaker = configuration.get("dealbreaker", False)
        if not is_dealbreaker:
            return False

        user_minimum, user_maximum = configuration["range"]
        is_within_range = (user_minimum <= breed_value <= user_maximum)
        is_violating_range = not is_within_range
        return is_violating_range

    def _is_binary_trait_violating_dealbreaker(self, breed_attributes: Dict[str, Any]) -> bool:
        """Atomic check: Verifies if a breed violates the binary hypoallergenic dealbreaker choice."""
        binary_configuration: Dict[str, Any]
        hypoallergenic_choice: str
        breed_is_hypoallergenic: bool
        wants_hypoallergenic: bool
        violates_positive_hypoallergenic: bool
        wants_no_hypoallergenic: bool
        violates_negative_hypoallergenic: bool

        binary_configuration = self._user_preferences.get("binary", {})
        hypoallergenic_choice = binary_configuration.get("hypoallergenic", "Doesn't Matter")
        breed_is_hypoallergenic = breed_attributes.get("hypoallergenic", False)
        
        wants_hypoallergenic = (hypoallergenic_choice == "Must Be Hypoallergenic")
        violates_positive_hypoallergenic = (wants_hypoallergenic and not breed_is_hypoallergenic)
        if violates_positive_hypoallergenic:
            return True

        wants_no_hypoallergenic = (hypoallergenic_choice == "Must NOT Be Hypoallergenic")
        violates_negative_hypoallergenic = (wants_no_hypoallergenic and breed_is_hypoallergenic)
        if violates_negative_hypoallergenic:
            return True

        return False

    def _passes_dealbreakers(self, breed: Dict[str, Any]) -> bool:
        """Atomic orchestrator: Evaluates all dealbreaker conditions for a single breed."""
        breed_attributes: Dict[str, Any]
        traits_configuration: Dict[str, Any]
        breed_traits_mapping: Dict[str, int]
        is_binary_violating: bool
        trait_key: str
        configuration: Dict[str, Any]
        breed_value: int
        is_ordinal_violating: bool

        breed_attributes = breed.get("attributes", {})
        traits_configuration = self._user_preferences.get("traits", {})
        breed_traits_mapping = breed_attributes.get("traits", {})

        is_binary_violating = self._is_binary_trait_violating_dealbreaker(breed_attributes)
        if is_binary_violating:
            return False

        for trait_key, configuration in traits_configuration.items():
            breed_value = breed_traits_mapping.get(trait_key, 3)
            is_ordinal_violating = self._is_ordinal_trait_violating_dealbreaker(breed_value, configuration)
            if is_ordinal_violating:
                return False

        return True

    def _calculate_single_trait_utility(self, breed_value: int, configuration: Dict[str, Any]) -> Optional[float]:
        """Atomic calculation: Computes fuzzy utility for one single ordinal trait."""
        user_minimum: int
        user_maximum: int
        is_indifferent: bool
        is_strict: bool
        is_within_core_zone: bool
        distance_from_minimum: int
        distance_from_maximum: int
        minimum_distance: int
        decayed_utility: float
        bounded_utility: float

        user_minimum, user_maximum = configuration["range"]
        is_indifferent = (user_minimum == 1 and user_maximum == 5)
        if is_indifferent:
            return None

        is_strict = configuration.get("strict", False)
        is_within_core_zone = (user_minimum <= breed_value <= user_maximum)
        if is_within_core_zone:
            return 1.0

        if is_strict:
            return 0.0

        distance_from_minimum = abs(breed_value - user_minimum)
        distance_from_maximum = abs(breed_value - user_maximum)
        minimum_distance = min(distance_from_minimum, distance_from_maximum)
        decayed_utility = 1.0 - (minimum_distance * 0.35)
        bounded_utility = max(0.0, decayed_utility)
        return bounded_utility

    def _calculate_weight_utility(self, breed_attributes: Dict[str, Any]) -> float:
        """Atomic calculation: Computes fuzzy utility strictly for breed weight."""
        default_weight_range: Dict[str, float]
        male_weight_range: Dict[str, float]
        weight_minimum_limit: float
        weight_maximum_limit: float
        breed_weight_midpoint: float
        continuous_configuration: Dict[str, Any]
        user_weight_tuple: tuple
        user_weight_minimum: float
        user_weight_maximum: float
        is_weight_in_range: bool
        weight_distance_from_minimum: float
        weight_distance_from_maximum: float
        minimum_weight_distance: float
        decayed_weight_utility: float
        weight_utility: float

        default_weight_range = {"min": 10.0, "max": 25.0}
        male_weight_range = breed_attributes.get("male_weight", default_weight_range)
        weight_minimum_limit = male_weight_range.get("min", 10.0)
        weight_maximum_limit = male_weight_range.get("max", 25.0)
        breed_weight_midpoint = (weight_minimum_limit + weight_maximum_limit) / 2.0
        
        continuous_configuration = self._user_preferences.get("continuous", {})
        user_weight_tuple = continuous_configuration.get("weight_kg", (2.0, 80.0))
        user_weight_minimum, user_weight_maximum = user_weight_tuple

        is_weight_in_range = (user_weight_minimum <= breed_weight_midpoint <= user_weight_maximum)
        if is_weight_in_range:
            return 1.0

        weight_distance_from_minimum = abs(breed_weight_midpoint - user_weight_minimum)
        weight_distance_from_maximum = abs(breed_weight_midpoint - user_weight_maximum)
        minimum_weight_distance = min(weight_distance_from_minimum, weight_distance_from_maximum)
        decayed_weight_utility = 1.0 - (minimum_weight_distance / 20.0)
        weight_utility = max(0.0, decayed_weight_utility)
        return weight_utility

    def _calculate_exercise_utility(self, breed_attributes: Dict[str, Any]) -> float:
        """Atomic calculation: Computes fuzzy utility strictly for daily exercise minutes."""
        breed_traits_mapping: Dict[str, Any]
        breed_exercise_minutes: int
        continuous_configuration: Dict[str, Any]
        user_exercise_tuple: tuple
        user_exercise_minimum: int
        user_exercise_maximum: int
        is_exercise_in_range: bool
        exercise_distance_from_minimum: float
        exercise_distance_from_maximum: float
        minimum_exercise_distance: float
        decayed_exercise_utility: float
        exercise_utility: float

        breed_traits_mapping = breed_attributes.get("traits", {})
        breed_exercise_minutes = breed_traits_mapping.get("exercise_minutes", 60)
        
        continuous_configuration = self._user_preferences.get("continuous", {})
        user_exercise_tuple = continuous_configuration.get("exercise_minutes", (10, 180))
        user_exercise_minimum, user_exercise_maximum = user_exercise_tuple

        is_exercise_in_range = (user_exercise_minimum <= breed_exercise_minutes <= user_exercise_maximum)
        if is_exercise_in_range:
            return 1.0

        exercise_distance_from_minimum = abs(breed_exercise_minutes - user_exercise_minimum)
        exercise_distance_from_maximum = abs(breed_exercise_minutes - user_exercise_maximum)
        minimum_exercise_distance = min(exercise_distance_from_minimum, exercise_distance_from_maximum)
        decayed_exercise_utility = 1.0 - (minimum_exercise_distance / 60.0)
        exercise_utility = max(0.0, decayed_exercise_utility)
        return exercise_utility

    def _calculate_tag_utility(self, breed_temperaments: List[str]) -> float:
        """Atomic calculation: Computes set-overlap similarity ratio for temperament keywords."""
        temperament_tags_configuration: List[str]
        has_no_tags: bool
        normalized_breed_temperaments: List[str]
        matching_tags_count: int
        similarity_ratio: float

        temperament_tags_configuration = self._user_preferences.get("tags", {}).get("temperament", [])
        has_no_tags = (not temperament_tags_configuration or not breed_temperaments)
        if has_no_tags:
            return 0.0

        normalized_breed_temperaments = [temperament.lower() for temperament in breed_temperaments]
        matching_tags_count = sum(
            1 for tag in temperament_tags_configuration if tag.lower() in normalized_breed_temperaments
        )
        similarity_ratio = float(matching_tags_count / len(temperament_tags_configuration))
        return similarity_ratio

    def run(self) -> List[Dict[str, Any]]:
        """Public orchestrator method: Filters, scores, and sorts all breeds."""
        scored_breeds: List[Dict[str, Any]]
        breed: Dict[str, Any]
        breed_attributes: Dict[str, Any]
        passes_filter: bool
        traits_configuration: Dict[str, Any]
        breed_traits_mapping: Dict[str, int]
        ordinal_utilities: List[float]
        trait_key: str
        configuration: Dict[str, Any]
        breed_value: int
        trait_utility: Optional[float]
        mean_ordinal_score: float
        weight_score: float
        exercise_score: float
        mean_continuous_score: float
        tag_score: float
        base_score: float
        weighted_score: float
        match_percentage: float
        breed_id: str
        breed_name: str
        breed_description: str
        scored_breed_record: Dict[str, Any]

        scored_breeds = []

        for breed in self._breeds_data:
            breed_attributes = breed.get("attributes", {})
            
            # Step 1: Pre-pass dealbreaker check
            passes_filter = self._passes_dealbreakers(breed)
            if not passes_filter:
                continue

            # Step 2: Compute individual ordinal utilities atomically
            traits_configuration = self._user_preferences.get("traits", {})
            breed_traits_mapping = breed_attributes.get("traits", {})
            ordinal_utilities = []

            for trait_key, configuration in traits_configuration.items():
                breed_value = breed_traits_mapping.get(trait_key, 3)
                trait_utility = self._calculate_single_trait_utility(breed_value, configuration)
                if trait_utility is not None:
                    ordinal_utilities.append(trait_utility)

            mean_ordinal_score = float(np.mean(ordinal_utilities)) if ordinal_utilities else 1.0

            # Step 3: Compute continuous utilities atomically
            weight_score = self._calculate_weight_utility(breed_attributes)
            exercise_score = self._calculate_exercise_utility(breed_attributes)
            mean_continuous_score = float(np.mean([weight_score, exercise_score]))

            # Step 4: Compute tag similarity utility atomically
            tag_score = self._calculate_tag_utility(breed_attributes.get("temperament", []))

            # Step 5: Weighted aggregation and final score calculation
            base_score = (mean_ordinal_score + mean_continuous_score) / 2.0
            weighted_score = (base_score * 0.8) + (tag_score * 0.2)
            match_percentage = round(weighted_score * 100, 1)

            breed_id = breed.get("id", "")
            breed_name = breed_attributes.get("name", "Unknown Breed")
            breed_description = breed_attributes.get("description", "")

            scored_breed_record = {
                "id": breed_id,
                "name": breed_name,
                "description": breed_description,
                "match_score": match_percentage,
                "attributes": breed_attributes
            }
            
            scored_breeds.append(scored_breed_record)

        # Sort results from highest match percentage to lowest
        scored_breeds.sort(key=lambda record: record["match_score"], reverse=True)
        return scored_breeds