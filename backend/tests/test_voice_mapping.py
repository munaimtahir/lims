"""Tests for voice mapping service."""

from lims.services.voice_mapping import VoiceMapping


class TestVoiceMapping:
    """Test voice mapping functionality."""

    def test_extract_name_english(self):
        """Test name extraction from English transcript."""
        transcript = "Patient name is John Doe age 35"
        name, confidence = VoiceMapping.extract_name(transcript)
        assert name == "John Doe"
        assert confidence >= 0.9

    def test_extract_name_urdu(self):
        """Test name extraction with Urdu keywords."""
        transcript = "naam Ahmed Khan age 40"
        name, confidence = VoiceMapping.extract_name(transcript)
        assert name == "Ahmed Khan"
        assert confidence >= 0.9

    def test_extract_age_standard(self):
        """Test age extraction standard format."""
        transcript = "Patient age is 45 years"
        age, confidence = VoiceMapping.extract_age(transcript)
        assert age == 45
        assert confidence >= 0.9

    def test_extract_age_years_old(self):
        """Test age extraction with 'years old' format."""
        transcript = "Patient is 28 years old"
        age, confidence = VoiceMapping.extract_age(transcript)
        assert age == 28
        assert confidence >= 0.9

    def test_extract_gender_male(self):
        """Test gender extraction - male."""
        transcript = "Patient gender male age 30"
        gender, confidence = VoiceMapping.extract_gender(transcript)
        assert gender == "Male"
        assert confidence >= 0.85

    def test_extract_gender_female(self):
        """Test gender extraction - female."""
        transcript = "Patient is a woman aged 35"
        gender, confidence = VoiceMapping.extract_gender(transcript)
        assert gender == "Female"
        assert confidence >= 0.85

    def test_extract_contact_standard(self):
        """Test phone number extraction."""
        transcript = "Contact number is 555-1234"
        contact, confidence = VoiceMapping.extract_contact(transcript)
        assert "555" in contact and "1234" in contact
        assert confidence >= 0.9

    def test_extract_tests(self):
        """Test extraction of test names."""
        transcript = "Patient needs CBC and glucose tests"
        tests, confidence = VoiceMapping.extract_tests(transcript)
        assert "cbc" in tests.lower()
        assert confidence >= 0.7

    def test_map_complete_transcript_high_confidence(self):
        """Test complete mapping with high confidence."""
        transcript = "Patient name is Sarah Johnson age 42 female contact 555-9876 test CBC"
        result = VoiceMapping.map_transcript(transcript)

        assert "name" in result["fields"]
        assert "age" in result["fields"]
        assert "gender" in result["fields"]
        assert "contact" in result["fields"]
        assert result["overall_confidence"] >= 0.85

    def test_map_incomplete_transcript(self):
        """Test mapping with incomplete information."""
        transcript = "Patient name is Bob age something"
        result = VoiceMapping.map_transcript(transcript)

        assert "name" in result["fields"]
        assert result["fields"]["name"] == "Bob"
        # Age should not be extracted (invalid)
        assert "age" not in result["fields"] or result["fields"]["age"] is None

    def test_map_mixed_language(self):
        """Test mapping with mixed English/Urdu."""
        transcript = "naam Ali Hassan umr 50 male phone 555-4321"
        result = VoiceMapping.map_transcript(transcript)

        assert "name" in result["fields"]
        assert "age" in result["fields"]
        assert result["fields"]["age"] == 50
        assert "gender" in result["fields"]

    def test_confidence_thresholds(self):
        """Test confidence scoring thresholds."""
        # High confidence transcript
        high_conf = "Patient name is John Smith age 35 male"
        result_high = VoiceMapping.map_transcript(high_conf)
        assert result_high["overall_confidence"] >= 0.9

        # Medium confidence (some ambiguity)
        med_conf = "John Smith 35"
        result_med = VoiceMapping.map_transcript(med_conf)
        assert 0.6 <= result_med["overall_confidence"] < 0.9

        # Low confidence (very ambiguous)
        low_conf = "Maybe some patient"
        result_low = VoiceMapping.map_transcript(low_conf)
        assert result_low["overall_confidence"] < 0.6

    def test_sample_phrases(self):
        """Test 10 sample phrases as per Stage B requirements."""
        sample_phrases = [
            "Patient name is Maria Garcia age 29 female phone 555-1111",
            "naam Muhammad Ali umr 45 mard contact 555-2222",
            "John Doe 35 years old male test CBC",
            "Patient Sarah aged 28 woman phone 555-3333 glucose test",
            "naam Fatima Khan umr 32 aurat",
            "Patient name David Lee age 50 male contact 555-4444 test lipid profile",
            "Ahmed Hassan 40 years mard phone 555-5555",
            "Patient is Jane Smith age 38 female CBC and liver function",
            "naam Ayesha Malik umr 25 lady contact 555-6666",
            "Patient Robert Brown aged 55 man test kidney function",
        ]

        for phrase in sample_phrases:
            result = VoiceMapping.map_transcript(phrase)
            # Each phrase should extract at least name
            assert "name" in result["fields"] or "age" in result["fields"]
            # Overall confidence should be reasonable
            assert result["overall_confidence"] > 0.0
