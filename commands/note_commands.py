class NoteCommands:
    """
    Handles project notebook commands.
    """

    def handle(self, brain, message):

        lower = message.lower().rstrip("?")

        # ----------------------------
        # Add Note
        # ----------------------------

        if lower.startswith("note "):

            note = message[5:].strip()

            if not note:

                return "Aether: Please provide a note."

            project = brain.cortex.get_current_project()

            if project is None:

                return (
                    "Aether: No active project. "
                    "Switch to a project first."
                )

            if brain.cortex.add_note(note):

                return (
                    f'Aether: Note saved to "{project.name}".'
                )

            return "Aether: I couldn't save that note."

        # ----------------------------
        # Show Notes
        # ----------------------------

        if lower in (
            "show notes",
            "list notes",
            "what are my notes",
            "what notes do i have"
        ):

            project = brain.cortex.get_current_project()

            if project is None:

                return "Aether: No active project."

            notes = brain.cortex.get_notes()

            if not notes:

                return (
                    f'Aether: No notes for "{project.name}".'
                )

            output = (
                f'Aether: Notes for "{project.name}":\n\n'
            )

            for index, note in enumerate(notes, start=1):

                output += f"{index}. {note}\n"

            return output

        return None