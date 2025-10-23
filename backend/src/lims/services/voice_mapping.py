"""Voice mapping service for extracting patient data from voice transcripts."""

import re
from typing import Any


class VoiceMapping:
    """Service for mapping voice transcripts to patient fields."""

    # Keywords for field extraction
    NAME_KEYWORDS = ["name", "naam", "patient name", "مریض کا نام"]
    AGE_KEYWORDS = ["age", "umr", "عمر", "years old", "سال"]
    GENDER_KEYWORDS = {
        "male": ["male", "mard", "مرد", "boy", "man"],
        "female": ["female", "aurat", "عورت", "girl", "woman", "lady"],
        "other": ["other", "doosra", "دوسرا"],
    }
    PHONE_KEYWORDS = ["phone", "contact", "number", "نمبر", "فون"]
    TESTS_KEYWORDS = ["test", "tests", "ٹیسٹ", "investigation"]

    @staticmethod
    def extract_name(transcript: str) -> tuple[str | None, float]:
        """Extract name from transcript with confidence score."""
        transcript_lower = transcript.lower()

        # Look for patterns like "name is X" or "patient name X"
        for keyword in VoiceMapping.NAME_KEYWORDS:
            if keyword in transcript_lower:
                # Try to extract name after the keyword
                pattern = rf"{keyword}\s+(?:is\s+)?([A-Za-z\s]+?)(?:\s+(?:age|umr|عمر|phone|contact|test|$))"
                match = re.search(pattern, transcript, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    if len(name) > 1:  # Valid name
                        return name, 0.95

        # Try to extract capitalized words (likely names) at the start
        words = transcript.split()
        if len(words) >= 2:
            potential_name = []
            for word in words[:4]:  # Check first 4 words
                if word[0].isupper() and word.isalpha():
                    potential_name.append(word)
                else:
                    break
            if len(potential_name) >= 2:
                return " ".join(potential_name), 0.70

        return None, 0.0

    @staticmethod
    def extract_age(transcript: str) -> tuple[int | None, float]:
        """Extract age from transcript with confidence score."""
        transcript.lower()

        # Look for patterns like "age 35", "35 years old", "umr 40"
        patterns = [
            r"(?:age|umr|عمر)\s+(?:is\s+)?(\d{1,3})",
            r"(\d{1,3})\s+(?:years?\s+old|سال)",
            r"(?:aged\s+)?(\d{1,3})\s+(?:year|yr)",
        ]

        for pattern in patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 0 <= age <= 150:  # Valid age range
                    return age, 0.95

        # Look for standalone numbers that could be age
        numbers = re.findall(r"\b(\d{1,3})\b", transcript)
        for num in numbers:
            age = int(num)
            if 1 <= age <= 120:  # Reasonable age range
                return age, 0.60

        return None, 0.0

    @staticmethod
    def extract_gender(transcript: str) -> tuple[str | None, float]:
        """Extract gender from transcript with confidence score."""
        transcript_lower = transcript.lower()

        # Check in specific order to avoid false matches (e.g., "woman" contains "man")
        # Check female keywords first as they're more specific
        for keyword in VoiceMapping.GENDER_KEYWORDS["female"]:
            if keyword in transcript_lower:
                confidence = 0.95 if len(keyword) > 3 else 0.85
                return "Female", confidence

        # Then check male keywords
        for keyword in VoiceMapping.GENDER_KEYWORDS["male"]:
            if keyword in transcript_lower:
                confidence = 0.95 if len(keyword) > 3 else 0.85
                return "Male", confidence

        # Finally check other
        for keyword in VoiceMapping.GENDER_KEYWORDS["other"]:
            if keyword in transcript_lower:
                confidence = 0.95 if len(keyword) > 3 else 0.85
                return "Other", confidence

        return None, 0.0

    @staticmethod
    def extract_contact(transcript: str) -> tuple[str | None, float]:
        """Extract phone number from transcript with confidence score."""
        # Look for phone number patterns
        patterns = [
            r"(?:phone|contact|number|نمبر|فون)\s*(?:is\s*)?([0-9\-\+\(\)\s]{7,15})",
            r"([0-9]{3}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})",  # US format
            r"(\+?[0-9]{10,15})",  # International
        ]

        for pattern in patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                phone = match.group(1).strip()
                # Clean up phone number
                phone = re.sub(r"[^\d\+\-]", "", phone)
                if len(phone) >= 7:
                    return phone, 0.90

        return None, 0.0

    @staticmethod
    def extract_tests(transcript: str) -> tuple[str | None, float]:
        """Extract test names from transcript with confidence score."""
        transcript_lower = transcript.lower()

        # Common test names
        common_tests = [
            "cbc",
            "complete blood count",
            "glucose",
            "hba1c",
            "lipid profile",
            "liver function",
            "kidney function",
            "urine",
            "stool",
            "x-ray",
            "ultrasound",
            "ecg",
        ]

        found_tests = []
        for test in common_tests:
            if test in transcript_lower:
                found_tests.append(test)

        if found_tests:
            return ", ".join(found_tests), 0.85

        # Look for generic test mention
        for keyword in VoiceMapping.TESTS_KEYWORDS:
            if keyword in transcript_lower:
                # Extract words after "test" keyword
                pattern = rf"{keyword}\s+(?:for\s+)?([A-Za-z\s,]+?)(?:\s+(?:age|phone|$))"
                match = re.search(pattern, transcript, re.IGNORECASE)
                if match:
                    tests = match.group(1).strip()
                    return tests, 0.70

        return None, 0.0

    @classmethod
    def map_transcript(cls, transcript: str) -> dict[str, Any]:
        """
        Map a voice transcript to patient fields with confidence scores.

        Returns a dictionary with:
        - fields: Dict of extracted field values
        - confidences: Dict of confidence scores for each field
        - overall_confidence: Average confidence score
        """
        name, name_conf = cls.extract_name(transcript)
        age, age_conf = cls.extract_age(transcript)
        gender, gender_conf = cls.extract_gender(transcript)
        contact, contact_conf = cls.extract_contact(transcript)
        tests, tests_conf = cls.extract_tests(transcript)

        fields = {}
        confidences = {}

        if name:
            fields["name"] = name
            confidences["name"] = name_conf

        if age:
            fields["age"] = age
            confidences["age"] = age_conf

        if gender:
            fields["gender"] = gender
            confidences["gender"] = gender_conf

        if contact:
            fields["contact"] = contact
            confidences["contact"] = contact_conf

        if tests:
            fields["tests"] = tests
            confidences["tests"] = tests_conf

        # Calculate overall confidence
        if confidences:
            overall_confidence = sum(confidences.values()) / len(confidences)
        else:
            overall_confidence = 0.0

        return {
            "fields": fields,
            "confidences": confidences,
            "overall_confidence": overall_confidence,
        }
