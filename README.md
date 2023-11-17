# zuki-helpers

Here's a list of bots, both operational and unoperational, which are part of the zukijourney ecosystem. These are all open-source via the GPLv3 License! :)

# zuki.time

Time management bot for roleplay servers. Allows progression of in-character time.

## Commands

- `/settime [Time per IRL day] [monthly/yearly rate] [start day] [month] [year]`: Set up the time settings for the server. Time must be in format like `12y` or `3 months`. After setup, you must use `/toggletime` to start progression.

- `/timeinfo`: Get the current time settings.

- `/endtime`: Reset the time settings.

- `/setchannel [channel]`: Set the channel for time updates.

- `/setvoice [channel]`: Set the voice channel for time updates.

- `/remove [channel/role]`: Remove configured channel, voice channel, or ping role.

- `/gettime`: Get the current in-character time.

- `/timeuntil [DD/MM/YYYY]`: Calculate when a given date will be reached.

- `/toggletime`: Pause/unpause time progression.

- `/help`: Show help embed.

- `/report [message]`: Report an issue to the developer.

# zuki.starboard

Starboard bot to showcase highly starred/reacted messages.

## Commands

- `/board [channel]`: Set the starboard channel.

- `/watch [channel]`: Add a channel to watch for stars.

- `/delwatch [channel]`: Remove a watched channel.

- `/minstar [number]`: Set minimum stars for starboard. Default is 2.

- `/autoreact`: Toggle bot's auto reactions on messages.

- `/help`: Show help message.

# zuki.count

Counting game bot. Users take turns incrementing/decrementing numbers.

## Commands

- `/setup [channel] [forward/backward]`: Set up counting in a channel.

# zuki.status

Status bot for monitoring uptime of other bots. Owner-only.

## Commands

- `/stats [bot]`: Get uptime stats for a bot.

  Here is documentation for the inactive bots:

## Inactive Bots

### prez.py Bot

A simple bot to compare US state populations.

**Commands:**

- `!compare_population [state1] [state2]`: Compare the populations of two US states.

### AI Chat Bot

A bot that uses the OpenAI API to have conversations.

**Commands:**

- `/ask [question]`: Ask the AI a question.

### Disboard Bumper Bot

A selfbot that does the funny thing for disboard. **Obviously, only an educational purposes example.**

**Commands:**

- `$start`: Start ping loop in current channel.
- `$stop`: Stop ping loop in current channel.
- `$inv [url]`: Join/bump server via invite URL.

# Essential Links, Credits, and the other bots!
For more bots, check out the [zukijourney-bots repository](https://github.com/zukixa/zukijourney-bots), the [zuki-risk repository](https://github.com/zukixa/zuki-risk), the [zuki-trivia repositiory](https://github.com/zukixa/zuki-trivia), or simply invite one of the talked-about bots involved below!
- [zuki.gm](https://discord.com/api/oauth2/authorize?client_id=1055209868899913788&permissions=8&scope=bot%20applications.commands)
- [zuki.time](https://discord.com/api/oauth2/authorize?client_id=1101035453710348339&permissions=19218435669072&scope=bot%20applications.commands)
- [zuki.count](https://discord.com/api/oauth2/authorize?client_id=1102325506294153348&permissions=1479750581360&scope=bot%20applications.commands)
- [zuki.risk](https://discord.com/api/oauth2/authorize?client_id=1054742546343010376&permissions=19218569878737&scope=applications.commands%20bot)
- [zuki.trivia](https://discord.com/api/oauth2/authorize?client_id=1070246268443557968&permissions=1625846840385&scope=applications.commands%20bot)
- [zuki.star](https://discord.com/api/oauth2/authorize?client_id=1116909665738051754&permissions=10318726429921&scope=bot%20applications.commands)

For the support server, or get into contact with me -- join the support server! [Over here...](discord.gg/pjcGtjc9BY)

