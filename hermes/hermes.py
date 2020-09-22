#!/usr/bin/env python

__usage__ = "hermes.py config_json_file"

from .plot import plot_and_save

import discord
import discord.ext.commands

import os, json, sys, string, random, datetime, re

class HermesPoll:
    """
    Class for actually managing vote counting, plotting, etc.

    expects a command string that looks something like:
    $start question|answer1|answer2... (up to 6 answers)

    Bad votes are silently ignored.
    """

    def __init__(self,
                 poll_master,
                 cmd_string="",
                 separator="|",
                 shuffle_order=True,
                 auto_add_confused=True):
        """
        poll_master: user who started and thus controls poll
        cmd_string: command passed to start the poll
        separator: separator separating questions and prompts.
        shuffle_order: (bool) shuffle the order of the answers
        auto_add_confused: (bool) add "I'm confused!" option at the end
        """

        self._poll_master = poll_master
        self._cmd_string = cmd_string
        self._separator = separator

        # Parse command fiels
        fields = self._cmd_string.split(self._separator)
        if len(fields) < 3 or len(fields) > 7:
            err = "command should look like: question|answer1|answer2|...  (up to 6 answers)"
            raise ValueError(err)

        # Get the poll prompt
        self._prompt = " ".join(fields[0].split(" ")[1:]).strip()

        # Get the answers
        self._answers = fields[1:]

        # Shuffle the list of answers, recording the position of the correct
        # answer.
        correct_answer = self._answers[0]
        if shuffle_order:
            random.shuffle(self._answers)
        self._correct_answer_position = [i for i in range(len(self._answers))
                                         if self._answers[i] == correct_answer][0]

        # Add "I'm confused!" as the last option
        if auto_add_confused:
            self._answers.append("I'm confused!")

        # Map the possible answers to possible votes (A-G)
        self._vote_to_value = {}
        for i, a in enumerate(self._answers):
            self._vote_to_value[string.ascii_uppercase[i]] = a.strip()

        # Dictionary to hold vote counts
        self._counts = {}

    @property
    def prompt(self):
        """
        Poll prompt.
        """
        return self._prompt

    @property
    def vote_to_value(self):
        """
        map from poll options (A,B,C, etc.) to string values.
        """
        return self._vote_to_value

    @property
    def poll_master(self):
        """
        User who started and thus controls poll.
        """
        return self._poll_master

    def update_counts(self,user,vote):
        """
        Update the vote count.

        user: user name
        vote: vote (A, B, C, D, etc.)
        """

        # Update the vote.  User is used as key so each user gets a single vote.
        # If the user votes again, their vote is simply replaced with the new
        # vote.
        self._counts[user] = vote

    def get_results(self):
        """
        Get poll results as a dictionary keying A,B,C etc. to number of times
        seen.
        """

        # Votes that were seen (A, B, C, etc.)
        all_votes = list(self._counts.values())

        # Create out_dict, keying possible vote values to number of times
        # they were seen.
        out_dict = {}
        for v in self._vote_to_value.keys():
            value = self._vote_to_value[v]
            out_dict[value] = sum(vote == v for vote in all_votes)

        return out_dict

    def generate_plot(self):
        """
        Generate a pretty plot of the results.
        """

        count_dict = self.get_results()
        title = self.prompt

        time_stamp = str(datetime.datetime.now())
        title_stamp = re.sub("[_ ]","-",self._prompt)
        file_root = f"{time_stamp}-{title_stamp[:20]}"

        plot_and_save(count_dict,title,file_root)

        # Return the name of the file.

        return f"{file_root}.png"


def load_config(config_file="config.json"):
    """
    Load configration information from a .json file.

    In the future:
    The DISCORD_TOKEN should be read from an environment variable and the
    channel ids should be pulled down from webhooks.
    """

    conf = json.load(open(config_file))

    token = conf["DISCORD_TOKEN"]
    master_channel = conf["MASTER_CHANNEL"]
    poll_channel = conf["POLL_CHANNEL"]

    return token, master_channel, poll_channel


def run_poll(config_file,command_prefix="$"):
    """
    Function that starts and holds aynchronous poll bot.

    config_file: json file with bot configuration options
    command_prefix: bot command prefix
    """

    # Read configuration
    token, master_channel, poll_channel = load_config(config_file)

    # Initialize bot (but do not start)
    bot = discord.ext.commands.Bot(command_prefix)
    bot.hpoll = None
    bot._master_channel_id = master_channel
    bot._poll_channel_id = poll_channel

    @bot.command()
    async def start(ctx):
        """
        Start a poll with $start.
        """

        # Check to see if a poll is already running
        if bot.hpoll is not None:
            err = "a poll is already running\n"
            raise RuntimeError(err)

        # Get the master channel (used to control the poll)
        bot._master_channel = bot.get_channel(bot._master_channel_id)
        if bot._master_channel is None:
            err = f"could not find master channel\n"
            raise RuntimeError(err)

        # Get the poll channel (used to administer the poll)
        bot._poll_channel = bot.get_channel(bot._poll_channel_id)
        if bot._poll_channel is None:
            err = f"could not find poll channel\n"
            raise RuntimeError(err)

        # Make sure this control message just came from the master channel
        if ctx.message.channel != bot._master_channel:
            err = f"bot cannot be controlled from {ctx.message.channel}\n"
            raise RuntimeError(err)

        # Whoever sent the message is now the poll master
        poll_master = ctx.message.author

        # Grab command content and use to initialize poll
        cmd = ctx.message.content
        bot.hpoll = HermesPoll(poll_master,cmd)

        # Construct a pretty prompt
        prompt = bot.hpoll.prompt
        vote_to_value = bot.hpoll.vote_to_value

        embed = discord.Embed(title=f"**{prompt}**",color=3447003)
        for v in vote_to_value.keys():
            embed.add_field(name=v, value=vote_to_value[v], inline=True)

        description = f"Choose the best answer.  Example: to select 'A', post "
        description += f"the message '{bot.command_prefix}A' on #{bot._poll_channel}. "
        description += "Your post will disappear as your vote is counted. You can "
        description += "vote many times, but only your last vote is counted."
        embed.set_footer(text=description)

        # Stick pretty poll prompt onot the poll channel
        await bot._poll_channel.send(embed=embed)

    @bot.command()
    async def close(ctx):
        """
        Close a poll.  Generates a graphical summary and releases the poll for
        another poll to be run.
        """

        # Make sure poll is running
        if not bot.hpoll:
            err = "poll has not been started\n"
            raise RuntimeError(err)

        # Make sure this command comes from the right person
        if ctx.message.author != bot.hpoll.poll_master:
            err = "you are not the one in charge of this poll\n"
            raise RuntimeError(err)

        # Make sure this command comes from the right channel
        if ctx.message.channel != bot._master_channel:
            err = f"bot cannot be controlled from {ctx.message.channel}\n"
            raise RuntimeError(err)

        # Create pretty plot
        png_file = bot.hpoll.generate_plot()

        # Post the pretty plot
        file = discord.File(f"./{png_file}", filename=png_file)
        embed = discord.Embed(description="poll result")
        embed.set_image(url=f"attachment://{png_file}")

        await bot._poll_channel.send(file=file, embed=embed)

        # Close poll
        bot.hpoll = None


    # I just hard-coded in commands for A-G responses.  I should
    # probably have used cogs or something, but...  Each call updates the
    # vote count and nukes the message that gave the vote.

    @bot.command()
    async def A(ctx):
        bot.hpoll.update_counts(ctx.message.author,"A")
        await bot._poll_channel.delete_messages([ctx.message])


    @bot.command()
    async def B(ctx):
        bot.hpoll.update_counts(ctx.message.author,"B")
        await bot._poll_channel.delete_messages([ctx.message])

    @bot.command()
    async def C(ctx):
        bot.hpoll.update_counts(ctx.message.author,"C")
        await bot._poll_channel.delete_messages([ctx.message])

    @bot.command()
    async def D(ctx):
        bot.hpoll.update_counts(ctx.message.author,"D")
        await bot._poll_channel.delete_messages([ctx.message])

    @bot.command()
    async def E(ctx):
        bot.hpoll.update_counts(ctx.message.author,"E")
        await bot._poll_channel.delete_messages([ctx.message])

    @bot.command()
    async def F(ctx):
        bot.hpoll.update_counts(ctx.message.author,"F")
        await bot._poll_channel.delete_messages([ctx.message])

    @bot.command()
    async def G(ctx):
        bot.hpoll.update_counts(ctx.message.author,"G")
        await bot._poll_channel.delete_messages([ctx.message])

    bot.run(token)


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    try:
        config_file = argv[0]
    except IndexError:
        err = f"Incorrect arugments.\n\nUsage:\n\n{__usage__}\n\n"
        raise ValueError(err)

    run_poll(config_file)

if __name__ == "__main__":
    main()
