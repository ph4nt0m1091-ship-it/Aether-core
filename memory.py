import json
import os
import re
from copy import deepcopy


class Memory:
    """
    Structured long-term memory for Aether.

    Memory v2 keeps durable user information separate from
    short-term conversation context and automatically migrates
    the original v1 memory.json shape without losing data.
    """

    SCHEMA_VERSION = 2

    def __init__(self):

        self.filename = "data/memory.json"

        self.data = self._default_data()

        self.load()

    # -------------------------
    # DEFAULT STRUCTURE
    # -------------------------

    def _default_data(self):

        return {
            "version": self.SCHEMA_VERSION,
            "identity": {
                "name": None
            },
            "preferences": {
                "favorite_color": None,
                "likes": [],
                "facts": {}
            },
            "people_and_pets": {
                "dog_name": None
            },
            "projects": {},
            "goals": [],
            "notes": []
        }

    # -------------------------
    # LOAD / MIGRATE
    # -------------------------

    def load(self):

        if not os.path.exists(self.filename):

            self.save()
            return

        try:

            with open(
                self.filename,
                "r",
                encoding="utf-8"
            ) as file:

                loaded = json.load(file)

        except (
            OSError,
            json.JSONDecodeError
        ):

            return

        if not isinstance(
            loaded,
            dict
        ):

            return

        if loaded.get(
            "version"
        ) == self.SCHEMA_VERSION:

            self.data = (
                self._merge_defaults(
                    loaded
                )
            )

            return

        self.data = (
            self._migrate_v1(
                loaded
            )
        )

        self.save()

    def _migrate_v1(
        self,
        old_data
    ):

        migrated = (
            self._default_data()
        )

        migrated[
            "identity"
        ][
            "name"
        ] = old_data.get(
            "name"
        )

        migrated[
            "preferences"
        ][
            "favorite_color"
        ] = old_data.get(
            "favorite_color"
        )

        migrated[
            "people_and_pets"
        ][
            "dog_name"
        ] = old_data.get(
            "dog_name"
        )

        old_likes = old_data.get(
            "likes",
            []
        )

        if isinstance(
            old_likes,
            list
        ):

            migrated[
                "preferences"
            ][
                "likes"
            ] = [
                str(
                    item
                )
                for item in old_likes
                if str(
                    item
                ).strip()
            ]

        return migrated

    def _merge_defaults(
        self,
        loaded
    ):

        merged = (
            deepcopy(
                self._default_data()
            )
        )

        for key, value in loaded.items():

            if (
                key in merged
                and isinstance(
                    merged[
                        key
                    ],
                    dict
                )
                and isinstance(
                    value,
                    dict
                )
            ):

                merged[
                    key
                ].update(
                    value
                )

            else:

                merged[
                    key
                ] = value

        merged[
            "version"
        ] = self.SCHEMA_VERSION

        return merged

    # -------------------------
    # SAVE
    # -------------------------

    def save(self):

        folder = os.path.dirname(
            self.filename
        )

        if folder:

            os.makedirs(
                folder,
                exist_ok=True
            )

        with open(
            self.filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.data,
                file,
                indent=4,
                ensure_ascii=False
            )

    # -------------------------
    # REMEMBER / FORGET ROUTER
    # -------------------------

    def remember(
        self,
        text
    ):
        """
        Parse explicit durable-memory statements.

        Returns None when the message is not a memory write.
        Otherwise returns a small result dictionary that main.py
        can use to acknowledge the action without sending it to AI.
        """

        original = str(
            text or ""
        ).strip()

        if not original:

            return None

        lower = original.lower()

        if lower.startswith(
            "remember that "
        ):

            statement = original[
                len(
                    "remember that "
                ):
            ].strip()

            return (
                self._remember_statement(
                    statement
                )
            )

        if lower.startswith(
            "remember "
        ):

            statement = original[
                len(
                    "remember "
                ):
            ].strip()

            if statement:

                return (
                    self._remember_statement(
                        statement
                    )
                )

        if lower.startswith(
            "forget "
        ):

            target = original[
                len(
                    "forget "
                ):
            ].strip()

            return (
                self.forget(
                    target
                )
            )

        # Backward-compatible natural statements.
        legacy_prefixes = (
            "my name is ",
            "my favorite color is ",
            "my dog's name is ",
            "my dog is named ",
            "i like ",
            "i prefer "
        )

        if lower.startswith(
            legacy_prefixes
        ):

            return (
                self._remember_statement(
                    original
                )
            )

        return None

    def _remember_statement(
        self,
        statement
    ):

        statement = str(
            statement or ""
        ).strip().strip(
            " ."
        )

        if not statement:

            return {
                "success": False,
                "response": (
                    "Aether: Tell me what you want me to remember."
                )
            }

        lower = statement.lower()

        # -------------------------
        # IDENTITY
        # -------------------------

        if lower.startswith(
            "my name is "
        ):

            value = statement[
                len(
                    "my name is "
                ):
            ].strip(
                " ."
            )

            if not value:

                return (
                    self._missing_value(
                        "name"
                    )
                )

            self.data[
                "identity"
            ][
                "name"
            ] = value

            self.save()

            return (
                self._saved(
                    "name",
                    value
                )
            )

        # -------------------------
        # FAVORITE COLOR
        # -------------------------

        if lower.startswith(
            "my favorite color is "
        ):

            value = statement[
                len(
                    "my favorite color is "
                ):
            ].strip(
                " ."
            )

            if not value:

                return (
                    self._missing_value(
                        "favorite color"
                    )
                )

            self.data[
                "preferences"
            ][
                "favorite_color"
            ] = value

            self.save()

            return (
                self._saved(
                    "favorite color",
                    value
                )
            )

        # -------------------------
        # DOG NAME
        # -------------------------

        dog_prefixes = (
            "my dog's name is ",
            "my dog is named "
        )

        for prefix in dog_prefixes:

            if lower.startswith(
                prefix
            ):

                value = statement[
                    len(
                        prefix
                    ):
                ].strip(
                    " ."
                )

                if not value:

                    return (
                        self._missing_value(
                            "dog name"
                        )
                    )

                self.data[
                    "people_and_pets"
                ][
                    "dog_name"
                ] = value

                self.save()

                return (
                    self._saved(
                        "dog name",
                        value
                    )
                )

        # -------------------------
        # LIKES
        # -------------------------

        if lower.startswith(
            "i like "
        ):

            value = statement[
                len(
                    "i like "
                ):
            ].strip(
                " ."
            )

            if not value:

                return (
                    self._missing_value(
                        "like"
                    )
                )

            likes = self.data[
                "preferences"
            ][
                "likes"
            ]

            if value.lower() not in [
                item.lower()
                for item in likes
            ]:

                likes.append(
                    value
                )

                self.save()

            return {
                "success": True,
                "response": (
                    f"Aether: I'll remember that you like {value}."
                )
            }

        # -------------------------
        # PREFERENCES
        # -------------------------

        if lower.startswith(
            "i prefer "
        ):

            value = statement[
                len(
                    "i prefer "
                ):
            ].strip(
                " ."
            )

            if not value:

                return (
                    self._missing_value(
                        "preference"
                    )
                )

            return (
                self._set_fact(
                    "preference",
                    value,
                    response=(
                        f"Aether: I'll remember that you prefer {value}."
                    )
                )
            )

        # -------------------------
        # MAIN PROJECT
        # -------------------------

        project_match = re.match(
            r"^(.+?)\s+is\s+my\s+main\s+project$",
            statement,
            flags=re.IGNORECASE
        )

        if project_match:

            project_name = (
                project_match
                .group(
                    1
                )
                .strip()
            )

            self.data[
                "projects"
            ][
                "main"
            ] = project_name

            self.save()

            return {
                "success": True,
                "response": (
                    f"Aether: I'll remember that "
                    f"{project_name} is your main project."
                )
            }

        # -------------------------
        # FAVORITE / GENERAL FACT
        # -------------------------

        fact_match = re.match(
            r"^my\s+(.+?)\s+is\s+(.+)$",
            statement,
            flags=re.IGNORECASE
        )

        if fact_match:

            raw_key = (
                fact_match
                .group(
                    1
                )
                .strip()
            )

            value = (
                fact_match
                .group(
                    2
                )
                .strip(
                    " ."
                )
            )

            key = (
                self._normalize_key(
                    raw_key
                )
            )

            return (
                self._set_fact(
                    key,
                    value,
                    response=(
                        f"Aether: I'll remember your "
                        f"{raw_key} is {value}."
                    )
                )
            )

        # -------------------------
        # GENERAL NOTE
        # -------------------------

        notes = self.data[
            "notes"
        ]

        if statement.lower() not in [
            note.lower()
            for note in notes
        ]:

            notes.append(
                statement
            )

            self.save()

        return {
            "success": True,
            "response": (
                "Aether: I'll remember that."
            )
        }

    # -------------------------
    # FORGET
    # -------------------------

    def forget(
        self,
        target
    ):

        target = str(
            target or ""
        ).strip().strip(
            " .?"
        )

        if not target:

            return {
                "success": False,
                "response": (
                    "Aether: Tell me exactly what you want me to forget."
                )
            }

        lower = target.lower()

        aliases = {
            "my name": (
                "identity",
                "name"
            ),
            "name": (
                "identity",
                "name"
            ),
            "my favorite color": (
                "preferences",
                "favorite_color"
            ),
            "favorite color": (
                "preferences",
                "favorite_color"
            ),
            "my dog's name": (
                "people_and_pets",
                "dog_name"
            ),
            "my dog name": (
                "people_and_pets",
                "dog_name"
            ),
            "dog name": (
                "people_and_pets",
                "dog_name"
            ),
            "my main project": (
                "projects",
                "main"
            ),
            "main project": (
                "projects",
                "main"
            )
        }

        if lower in aliases:

            section, key = aliases[
                lower
            ]

            value = self.data.get(
                section,
                {}
            ).get(
                key
            )

            if value is None:

                return {
                    "success": False,
                    "response": (
                        f"Aether: I don't have {target} stored."
                    )
                }

            self.data[
                section
            ][
                key
            ] = None

            self.save()

            return {
                "success": True,
                "response": (
                    f"Aether: I forgot {target}."
                )
            }

        if lower.startswith(
            "that i like "
        ):

            value = target[
                len(
                    "that i like "
                ):
            ].strip()

            return (
                self._forget_like(
                    value
                )
            )

        if lower.startswith(
            "i like "
        ):

            value = target[
                len(
                    "i like "
                ):
            ].strip()

            return (
                self._forget_like(
                    value
                )
            )

        fact_key = lower

        if fact_key.startswith(
            "my "
        ):

            fact_key = fact_key[
                3:
            ]

        fact_key = (
            self._normalize_key(
                fact_key
            )
        )

        facts = self.data[
            "preferences"
        ][
            "facts"
        ]

        matched_key = None

        for stored_key in facts:

            if (
                self._normalize_key(
                    stored_key
                )
                == fact_key
            ):

                matched_key = stored_key
                break

        if matched_key is not None:

            del facts[
                matched_key
            ]

            self.save()

            display = matched_key.replace(
                "_",
                " "
            )

            return {
                "success": True,
                "response": (
                    f"Aether: I forgot your {display}."
                )
            }

        for index, note in enumerate(
            list(
                self.data[
                    "notes"
                ]
            )
        ):

            if note.lower() == lower:

                del self.data[
                    "notes"
                ][
                    index
                ]

                self.save()

                return {
                    "success": True,
                    "response": (
                        "Aether: I forgot that note."
                    )
                }

        return {
            "success": False,
            "response": (
                f"Aether: I couldn't find anything stored for {target}."
            )
        }

    def _forget_like(
        self,
        value
    ):

        likes = self.data[
            "preferences"
        ][
            "likes"
        ]

        for index, item in enumerate(
            list(
                likes
            )
        ):

            if (
                item.lower()
                == value.lower()
            ):

                del likes[
                    index
                ]

                self.save()

                return {
                    "success": True,
                    "response": (
                        f"Aether: I forgot that you like {item}."
                    )
                }

        return {
            "success": False,
            "response": (
                f"Aether: I don't have {value} in your likes."
            )
        }

    # -------------------------
    # LOOKUP
    # -------------------------

    def get_fact(
        self,
        key
    ):

        key = (
            self._normalize_key(
                key
            )
        )

        special = {
            "name": self.get_name(),
            "favorite_color": (
                self.get_favorite_color()
            ),
            "dog_name": (
                self.get_dog_name()
            ),
            "main_project": (
                self.get_main_project()
            )
        }

        if (
            key in special
            and special[
                key
            ] is not None
        ):

            return special[
                key
            ]

        facts = self.data[
            "preferences"
        ][
            "facts"
        ]

        for stored_key, value in facts.items():

            if (
                self._normalize_key(
                    stored_key
                )
                == key
            ):

                return value

        return None

    def summary_lines(
        self
    ):

        lines = []

        name = self.get_name()

        if name:

            lines.append(
                f"Name: {name}"
            )

        color = (
            self.get_favorite_color()
        )

        if color:

            lines.append(
                f"Favorite color: {color}"
            )

        dog = self.get_dog_name()

        if dog:

            lines.append(
                f"Dog's name: {dog}"
            )

        likes = self.get_likes()

        if likes:

            lines.append(
                "Likes: "
                + ", ".join(
                    likes
                )
            )

        main_project = (
            self.get_main_project()
        )

        if main_project:

            lines.append(
                f"Main project: {main_project}"
            )

        facts = self.data[
            "preferences"
        ][
            "facts"
        ]

        for key, value in facts.items():

            display = key.replace(
                "_",
                " "
            )

            lines.append(
                f"{display.title()}: {value}"
            )

        notes = self.data.get(
            "notes",
            []
        )

        for note in notes:

            lines.append(
                f"Note: {note}"
            )

        return lines

    # -------------------------
    # HELPERS
    # -------------------------

    def _normalize_key(
        self,
        key
    ):

        key = str(
            key or ""
        ).strip().lower()

        key = re.sub(
            r"[^a-z0-9]+",
            "_",
            key
        )

        return key.strip(
            "_"
        )

    def _set_fact(
        self,
        key,
        value,
        response
    ):

        key = (
            self._normalize_key(
                key
            )
        )

        value = str(
            value or ""
        ).strip(
            " ."
        )

        if not key or not value:

            return {
                "success": False,
                "response": (
                    "Aether: I couldn't determine "
                    "what should be remembered."
                )
            }

        self.data[
            "preferences"
        ][
            "facts"
        ][
            key
        ] = value

        self.save()

        return {
            "success": True,
            "response": response
        }

    def _saved(
        self,
        label,
        value
    ):

        return {
            "success": True,
            "response": (
                f"Aether: I'll remember your "
                f"{label} is {value}."
            )
        }

    def _missing_value(
        self,
        label
    ):

        return {
            "success": False,
            "response": (
                f"Aether: I couldn't determine "
                f"the {label} to remember."
            )
        }

    # -------------------------
    # BACKWARD-COMPATIBLE GETTERS
    # -------------------------

    def get_name(self):

        return self.data.get(
            "identity",
            {}
        ).get(
            "name"
        )

    def get_favorite_color(self):

        return self.data.get(
            "preferences",
            {}
        ).get(
            "favorite_color"
        )

    def get_dog_name(self):

        return self.data.get(
            "people_and_pets",
            {}
        ).get(
            "dog_name"
        )

    def get_likes(self):

        return self.data.get(
            "preferences",
            {}
        ).get(
            "likes",
            []
        )

    def get_main_project(self):

        return self.data.get(
            "projects",
            {}
        ).get(
            "main"
        )
