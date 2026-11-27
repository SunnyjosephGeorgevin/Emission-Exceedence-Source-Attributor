
import re


class InterpretationValidator:

    UNSUPPORTED_UNIT_PATTERNS = [
        r"\bμg/m³\b",
        r"\bµg/m³\b",
        r"\bmg/m³\b",
        r"\bppm\b",
        r"\bm/s\b",
        r"\bmeters per second\b",
    ]

    UNSAFE_RECOMMENDATION_PATTERNS = [
        r"\brecommend(?:s|ed|ing)?\s+(?:to\s+)?enforce\b",
        r"\brecommend(?:s|ed|ing)?\s+(?:to\s+)?prosecut\w*\b",
        r"\brecommend(?:s|ed|ing)?\s+(?:to\s+)?penali[sz]\w*\b",
        r"\brecommend(?:s|ed|ing)?\s+(?:to\s+)?fine\b",
        r"\bshould be prosecuted\b",
        r"\bshould be fined\b",
        r"\bimmediate enforcement action\b",
        r"\bconfirmed permit violation\b",
        r"\bhas violated environmental regulations\b",
        r"\bis violating environmental regulations\b",
    ]

    @staticmethod
    def _number_present(value, text):
        """Match equivalent numeric representations such as 180 and 180.0."""
        try:
            target = float(value)
        except (TypeError, ValueError):
            return str(value).lower() in text.lower()

        numbers = re.findall(
            r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?",
            text,
        )

        return any(float(number) == target for number in numbers)

    @staticmethod
    def _alignment_claims(sentence):
        """Identify positive and negative alignment claims."""

        negative = bool(
            re.search(
                r"\bnot\s+(?:directionally\s+)?aligned\b"
                r"|\bno alignment\b"
                r"|\bunaligned\b"
                r"|\b(?:directionally\s+)?aligned\b"
                r"[^.!?\n]{0,80}\b(?:false|no|0)\b",
                sentence,
            )
        )

        positive = bool(
            re.search(
                r"\b(?:directionally\s+)?aligned\s*[:=]\s*(?:true|yes|1)\b"
                r"|\b(?:is|are|was|were)\s+(?:directionally\s+)?aligned\b"
                r"|\b(?:directionally\s+)?aligned\s+with\b",
                sentence,
            )
        )

        # Explicit negative wording takes precedence over the word "aligned".
        if negative:
            positive = False

        return positive, negative

    def validate(self, interpretation, investigation_result):

        errors = []
        warnings = []
        checks = []

        text_parts = [
            interpretation.get("ambient_analysis", ""),
            interpretation.get("wind_analysis", ""),
            interpretation.get("facility_analysis", ""),
            *interpretation.get("limitations", []),
            *interpretation.get("recommendations", []),
        ]

        text = " ".join(str(part) for part in text_parts)
        text_lower = text.lower()

        # Check 1: Unsupported measurement units.
        for pattern in self.UNSUPPORTED_UNIT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                errors.append(
                    f"Unsupported measurement unit detected: {pattern}"
                )

        checks.append("unsupported_units")

        # Check 2: Ambient measurements and thresholds.
        exceedances = (
            investigation_result
            .get("exceedance_result", {})
            .get("exceedances", [])
        )

        for item in exceedances:
            measured_value = item["measured_value"]
            threshold = item["threshold"]

            if not self._number_present(measured_value, text):
                errors.append(
                    f"Measured value {measured_value} is missing."
                )

            if not self._number_present(threshold, text):
                errors.append(
                    f"Threshold {threshold} is missing."
                )

        checks.append("ambient_measurements")

        # Check 3: Facility identity.
        candidates = investigation_result.get(
            "screened_candidates", []
        )

        for candidate in candidates:
            facility_name = candidate.get("facility_name")
            facility_id = candidate.get("facility_id")

            identity_found = (
                bool(
                    facility_name
                    and facility_name.lower() in text_lower
                )
                or bool(
                    facility_id
                    and facility_id.lower() in text_lower
                )
            )

            if not identity_found:
                warnings.append(
                    f"Facility {facility_name or facility_id} "
                    "was not mentioned in the interpretation."
                )

        checks.append("facility_identity")

        # Check 4: Wind alignment consistency.
        sentences = re.split(
            r"(?<=[.!?])\s+|\n",
            text_lower,
        )

        for candidate in candidates:
            facility_name = candidate.get("facility_name", "")
            facility_id = candidate.get("facility_id", "")
            alignment = candidate.get(
                "is_directionally_aligned"
            )

            for sentence in sentences:

                mentions_facility = (
                    bool(
                        facility_name
                        and facility_name.lower() in sentence
                    )
                    or bool(
                        facility_id
                        and facility_id.lower() in sentence
                    )
                )

                if not mentions_facility or alignment is None:
                    continue

                says_aligned, says_not_aligned = (
                    self._alignment_claims(sentence)
                )

                if alignment is False and says_aligned:
                    errors.append(
                        f"Contradictory wind-alignment claim for "
                        f"{facility_name or facility_id}."
                    )

                elif alignment is True and says_not_aligned:
                    errors.append(
                        f"Contradictory wind-alignment claim for "
                        f"{facility_name or facility_id}."
                    )

        checks.append("wind_alignment_consistency")

        # Check 5: Unsafe regulatory recommendations.
        recommendation_text = " ".join(
            str(item)
            for item in interpretation.get("recommendations", [])
        )

        for pattern in self.UNSAFE_RECOMMENDATION_PATTERNS:
            if re.search(
                pattern,
                recommendation_text,
                re.IGNORECASE,
            ):
                errors.append(
                    "Unsupported regulatory action recommendation "
                    f"detected: {pattern}"
                )

        checks.append("recommendation_safety")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "checks_performed": checks,
        }
