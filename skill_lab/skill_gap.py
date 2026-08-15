class SkillGap:
    """
    Represents a capability that Aether does not currently have.
    """

    def __init__(
        self,
        request,
        capability,
        status="unresolved",
        resolution=None,
        created_at=None
    ):

        self.request = request
        self.capability = capability
        self.status = status
        self.resolution = resolution
        self.created_at = created_at

    def to_dict(self):
        """
        Convert the SkillGap into a JSON-compatible dictionary.
        """

        return {
            "request": self.request,
            "capability": self.capability,
            "status": self.status,
            "resolution": self.resolution,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        """
        Rebuild a SkillGap from saved data.
        """

        return cls(
            request=data.get(
                "request",
                ""
            ),
            capability=data.get(
                "capability",
                ""
            ),
            status=data.get(
                "status",
                "unresolved"
            ),
            resolution=data.get(
                "resolution"
            ),
            created_at=data.get(
                "created_at"
            )
        )