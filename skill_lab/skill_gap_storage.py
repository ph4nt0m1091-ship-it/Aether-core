import json
from pathlib import Path

from skill_lab.skill_gap import SkillGap


class SkillGapStorage:
    """
    Handles persistent storage for Aether's Skill Gaps.
    """

    def __init__(self, path="storage/skill_gaps.json"):

        self.path = Path(path)

    # ---------------------------------
    # LOAD
    # ---------------------------------

    def load(self):
        """
        Load all saved Skill Gaps and remove
        duplicate unresolved capabilities.
        """

        if not self.path.exists():

            return []

        try:

            with self.path.open(
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

        except (
            json.JSONDecodeError,
            OSError
        ):

            return []

        if not isinstance(data, list):

            return []

        gaps = [
            SkillGap.from_dict(item)
            for item in data
            if isinstance(item, dict)
        ]

        # ----------------------------
        # Remove duplicate unresolved gaps
        # ----------------------------

        cleaned = []
        unresolved_capabilities = set()

        for gap in gaps:

            if gap.status == "unresolved":

                if gap.capability in unresolved_capabilities:

                    continue

                unresolved_capabilities.add(
                    gap.capability
                )

            cleaned.append(gap)

        # ----------------------------
        # Persist cleanup if needed
        # ----------------------------

        if len(cleaned) != len(gaps):

            self.save(cleaned)

        return cleaned

    # ---------------------------------
    # SAVE
    # ---------------------------------

    def save(self, gaps):
        """
        Save all Skill Gaps.
        """

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        data = [
            gap.to_dict()
            for gap in gaps
        ]

        with self.path.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

    # ---------------------------------
    # ADD
    # ---------------------------------

    def add(self, gap):
        """
        Add a Skill Gap unless an unresolved
        gap for the same capability already exists.

        Returns the existing gap when a duplicate
        is detected.
        """

        gaps = self.load()

        # ----------------------------
        # Check for unresolved duplicate
        # ----------------------------

        for existing_gap in gaps:

            if (
                existing_gap.capability
                == gap.capability
                and existing_gap.status
                == "unresolved"
            ):

                return existing_gap

        # ----------------------------
        # Add new gap
        # ----------------------------

        gaps.append(gap)

        self.save(gaps)

        return gap

    # ---------------------------------
    # RESOLVE
    # ---------------------------------

    def resolve(self, capability, resolution):
        """
        Mark an unresolved Skill Gap as resolved.

        Returns the resolved Skill Gap when found.
        Returns None when no matching unresolved
        capability exists.
        """

        gaps = self.load()

        for gap in gaps:

            if (
                gap.capability == capability
                and gap.status == "unresolved"
            ):

                gap.status = "resolved"
                gap.resolution = resolution

                self.save(gaps)

                return gap

        return None

    # ---------------------------------
    # GET ALL
    # ---------------------------------

    def get_all(self):
        """
        Return every saved Skill Gap.
        """

        return self.load()