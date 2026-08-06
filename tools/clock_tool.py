from datetime import datetime


class ClockTool:

    def get_time(self):

        now = datetime.now()

        return now.strftime("%I:%M %p")