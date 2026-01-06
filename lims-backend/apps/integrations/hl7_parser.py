"""
HL7 message parser for analyzer integration.
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class HL7Parser:
    """
    Parser for HL7 messages from laboratory analyzers.
    
    Supports basic HL7 v2.x message parsing for ORU^R01 (Observation Result) messages.
    """
    
    def __init__(self, message: str):
        """
        Initialize parser with HL7 message.
        
        Args:
            message (str): Raw HL7 message string
        """
        self.message = message
        self.segments = self._parse_segments()
    
    def _parse_segments(self) -> List[List[str]]:
        """
        Parse HL7 message into segments.
        
        Returns:
            List of segments, each segment is a list of fields
        """
        # Split by segment separator (usually \r or \n)
        segment_lines = re.split(r'[\r\n]+', self.message.strip())
        
        segments = []
        for line in segment_lines:
            if not line:
                continue
            
            # Split by field separator (usually |)
            fields = line.split('|')
            segments.append(fields)
        
        return segments
    
    def get_segment(self, segment_type: str) -> Optional[List[str]]:
        """
        Get first segment of specified type.
        
        Args:
            segment_type (str): Segment type (e.g., 'MSH', 'PID', 'OBR', 'OBX')
        
        Returns:
            List of fields or None if not found
        """
        for segment in self.segments:
            if segment and segment[0] == segment_type:
                return segment
        return None
    
    def get_all_segments(self, segment_type: str) -> List[List[str]]:
        """
        Get all segments of specified type.
        
        Args:
            segment_type (str): Segment type
        
        Returns:
            List of segments
        """
        return [seg for seg in self.segments if seg and seg[0] == segment_type]
    
    def parse_patient_info(self) -> Dict:
        """
        Parse patient information from PID segment.
        
        Returns:
            Dictionary with patient information
        """
        pid = self.get_segment('PID')
        if not pid or len(pid) < 4:
            return {}
        
        # PID.3 = Patient ID (External ID)
        # PID.5 = Patient Name (Family^Given^Middle^Suffix^Prefix)
        # PID.7 = Date/Time of Birth
        # PID.8 = Administrative Sex
        
        patient_id = pid[3].split('^')[0] if len(pid) > 3 else ""
        name_parts = pid[5].split('^') if len(pid) > 5 else []
        dob = pid[7] if len(pid) > 7 else ""
        gender = pid[8] if len(pid) > 8 else ""
        
        return {
            "patient_id": patient_id,
            "last_name": name_parts[0] if len(name_parts) > 0 else "",
            "first_name": name_parts[1] if len(name_parts) > 1 else "",
            "date_of_birth": dob,
            "gender": gender,
        }
    
    def parse_order_info(self) -> Dict:
        """
        Parse order information from OBR segment.
        
        Returns:
            Dictionary with order information
        """
        obr = self.get_segment('OBR')
        if not obr or len(obr) < 4:
            return {}
        
        # OBR.2 = Placer Order Number
        # OBR.3 = Filler Order Number
        # OBR.4 = Universal Service Identifier (Test Code)
        
        placer_order = obr[2].split('^')[0] if len(obr) > 2 else ""
        filler_order = obr[3].split('^')[0] if len(obr) > 3 else ""
        test_code = obr[4].split('^')[0] if len(obr) > 4 else ""
        
        return {
            "placer_order_number": placer_order,
            "filler_order_number": filler_order,
            "test_code": test_code,
        }
    
    def parse_results(self) -> List[Dict]:
        """
        Parse test results from OBX segments.
        
        Returns:
            List of result dictionaries
        """
        obx_segments = self.get_all_segments('OBX')
        results = []
        
        for obx in obx_segments:
            if len(obx) < 6:
                continue
            
            # OBX.2 = Value Type (NM, TX, etc.)
            # OBX.3 = Observation Identifier (Test Parameter)
            # OBX.5 = Observation Value
            # OBX.6 = Units
            # OBX.8 = Abnormal Flags
            
            value_type = obx[2] if len(obx) > 2 else ""
            param_id = obx[3].split('^')[0] if len(obx) > 3 else ""
            param_name = obx[3].split('^')[1] if len(obx) > 3 and '^' in obx[3] else param_id
            value = obx[5] if len(obx) > 5 else ""
            unit = obx[6] if len(obx) > 6 else ""
            flag = obx[8] if len(obx) > 8 else ""
            
            results.append({
                "value_type": value_type,
                "parameter_id": param_id,
                "parameter_name": param_name,
                "value": value,
                "unit": unit,
                "flag": flag,
            })
        
        return results
    
    def parse(self) -> Dict:
        """
        Parse complete HL7 message.
        
        Returns:
            Dictionary with parsed data including patient, order, and results
        """
        try:
            msh = self.get_segment('MSH')
            if not msh:
                logger.warning("Missing MSH segment, returning empty structure")
                return {
                    "message_type": "",
                    "patient": {},
                    "order": {},
                    "results": [],
                }
            
            message_type = msh[8] if len(msh) > 8 else ""
            
            return {
                "message_type": message_type,
                "patient": self.parse_patient_info(),
                "order": self.parse_order_info(),
                "results": self.parse_results(),
            }
        except Exception as e:
            logger.error(f"Error parsing HL7 message: {e}")
            # Return empty structure instead of raising
            return {
                "message_type": "",
                "patient": {},
                "order": {},
                "results": [],
            }


def parse_hl7_message(message: str) -> Dict:
    """
    Convenience function to parse HL7 message.
    
    Args:
        message (str): Raw HL7 message
    
    Returns:
        Dictionary with parsed data
    """
    parser = HL7Parser(message)
    return parser.parse()

