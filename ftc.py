import datetime
import re, json

class FictionalTimeController:
    TIME_CONVERSION_FACTORS = {
        'daily': lambda day, month, year: day,
        'monthly': lambda day, month, year: month,
        'yearly': lambda day, month, year: year,
    }

    def __init__(self, start_date, speed, notify_interval, guild_id, channel = None, role_id=None, voice = None, og_speed=None):
        self.start_date = start_date
        self.speed = self.calculate_secpermin(self.calculate_speed(speed)) if not og_speed else og_speed
        self.notify_interval = notify_interval.lower()
        self.role_id = role_id
        self.start_time = datetime.datetime.now()
        self.isRunning = False
        self.last_fictional_time = start_date
        self.monthsperday = self.calculate_speed(speed) if not og_speed else self.calculate_speed(og_speed)
        self.channel_id = channel
        self.voice_channel_id = voice
        self.guild_id = guild_id

    def calculate_speed(self, speed_str):
        if type(speed_str) != str:
            return speed_str
        match = re.findall(r"(\d+(?:\.\d+)?)(\D+)", speed_str)
        if match:
            num, unit = match[0]
            num = float(num)
            if "y" in unit:
                return num * 12  # Assuming speed is in years, converted to months
            else:
                return num
        else:
            raise ValueError("Invalid speed format.")

    def calculate_secpermin(self, speedTime):
        return float(speedTime * 1826.2125)  # Using the provided magic constant for conversion

    def current_fictional_time(self):
        try:
            if not self.isRunning:
                return self.last_fictional_time
            else:
                # Calculate the elapsed real-life time in seconds
                elapsed_real_seconds = (datetime.datetime.now() - self.start_time).total_seconds()
                
                # Convert the elapsed real-life seconds to minutes, as self.speed is based on per-minute calculations
                elapsed_real_minutes = elapsed_real_seconds / 60
                
                # Calculate the equivalent elapsed fictional seconds using the speed factor
                elapsed_fictional_seconds = elapsed_real_minutes * self.speed
                
                # Determine the current fictional time by adding the elapsed fictional seconds to the start date
                current_fictional_time = self.start_date + datetime.timedelta(seconds=elapsed_fictional_seconds)
                
                return current_fictional_time
        except:
            raise Exception("Your time is way too large. The bot is unable to continue.")

    # Method for calculating fictional time with added real-life hours
    def fictional_time_with_added_hours(self, hours):
        # Convert hours to minutes (since self.speed is in terms of real-life minutes)
        real_minutes_added = hours * 60
        
        # Calculate fictional seconds from those minutes, using the speed factor
        elapsed_fictional_seconds = real_minutes_added * self.speed
        
        # Calculate the future fictional time considering the added fictional seconds
        simulated_fictional_time = self.start_date + datetime.timedelta(seconds=elapsed_fictional_seconds)
        
        return simulated_fictional_time


def save_ftcs_state(ftcs, filename="/home/kira/k_zuki.helpers/new_time.json"):
    ftcs_state = {}
    for guild_id, ftc in ftcs.items():
        # Serialize FTC instance to a dict, adding channel_id and voice_channel_id
        ftc_state = {
            'start_date': ftc.start_date.strftime('%Y-%m-%d %H:%M:%S'),
            'speed': ftc.speed,
            'notify_interval': ftc.notify_interval,
            'guild_id': ftc.guild_id,
            'role_id': ftc.role_id,
            'start_time': ftc.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'isRunning': ftc.isRunning,
            'last_fictional_time': ftc.last_fictional_time.strftime('%Y-%m-%d %H:%M:%S'),
            'monthsperday': ftc.monthsperday,
            'channel_id': ftc.channel_id,
            'voice_channel_id': ftc.voice_channel_id,
        }
        ftcs_state[guild_id] = ftc_state

    # Write to file
    with open(filename, 'w') as file:
        json.dump(ftcs_state, file, indent=4)

def correct_datetime_format(dt_str):
    # Split the datetime string into date and time parts
    date_part, time_part = dt_str.split(" ")
    # Further split the date and time parts into their components
    date_components = date_part.split("-")
    time_components = time_part.split(":")
    
    # Correct the year to ensure it is always four digits
    date_components[0] = date_components[0].rjust(4, '0')  # Pad the year on the left with zeros
    
    # The month, day, hour, minute, and second should remain two digits, so apply zfill(2) to them
    corrected_date_components = [date_components[0]] + [component.zfill(2) for component in date_components[1:]]
    corrected_time_components = [component.zfill(2) for component in time_components]
    
    # Re-assemble the corrected date and time parts
    corrected_date_part = "-".join(corrected_date_components)
    corrected_time_part = ":".join(corrected_time_components)
    
    # Return the corrected datetime string
    return corrected_date_part + " " + corrected_time_part

def prep_json(filename="/home/kira/k_zuki.helpers/new_time.json"):
    with open(filename, 'r') as file:
        data = json.load(file)

    # Iterate through each item, correcting the specified fields
    for guild_id, ftc_data in data.items():
        if 'start_date' in ftc_data:
            ftc_data['start_date'] = correct_datetime_format(ftc_data['start_date'])
        if 'start_time' in ftc_data:
            ftc_data['start_time'] = correct_datetime_format(ftc_data['start_time'])
        if 'last_fictional_time' in ftc_data:
            ftc_data['last_fictional_time'] = correct_datetime_format(ftc_data['last_fictional_time'])

    # Write the corrected data back to the file
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

        
def load_ftcs_state(filename="/home/kira/k_zuki.helpers/new_time.json"):
    prep_json()
    with open(filename, 'r') as file:
        data = json.load(file)

    ftcs = {}
    for guild_id, ftc_data in data.items():
        # Convert string dates back to datetime objects
        ftc_data['start_date'] = datetime.datetime.strptime(ftc_data['start_date'], '%Y-%m-%d %H:%M:%S')
        ftc_data['start_time'] = datetime.datetime.strptime(ftc_data['start_time'], '%Y-%m-%d %H:%M:%S')
        ftc_data['last_fictional_time'] = datetime.datetime.strptime(ftc_data['last_fictional_time'], '%Y-%m-%d %H:%M:%S')

        # Rebuild the FTC instance, now including channel_id and voice_channel_id
        ftc = FictionalTimeController(
            start_date=ftc_data['start_date'],
            speed=ftc_data['speed'],  # Use monthsperday as the speed value needs to be recalculated inside the constructor
            notify_interval=ftc_data['notify_interval'],
            guild_id=ftc_data['guild_id'],
            channel=ftc_data.get('channel_id'),
            role_id=ftc_data.get('role_id'),
            voice=ftc_data.get('voice_channel_id'),
            og_speed=ftc_data['speed']
        )
        # Manually restore attributes that are not set via the constructor
        ftc.start_time = ftc_data['start_time']
        ftc.isRunning = ftc_data['isRunning']
        ftc.last_fictional_time = ftc_data['last_fictional_time']
        ftc.monthsperday = ftc_data['monthsperday']

        ftcs[guild_id] = ftc

    return ftcs