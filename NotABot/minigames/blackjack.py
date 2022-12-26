from NotABot.common import bot, log, cfg, general_utils
import discord
from secrets import randbelow
from itertools import product
from typing import List, Tuple

cards = list(product(['2','3','4','5','6','7','8','9','10','J','Q','K','A'], ['\u2660', '\u2665', '\u2666', '\u2663']))

# I'm not using a database for the active games. There is simply no need.
temp_memory = {}

# Blackjack test.
class BlackjackView(discord.ui.View):
    # This is our blackjack view. It isn't really a view in terms of MVC but it handles both the display and the player controls.

    async def retrieve_game_data(self, ctx: discord.ApplicationContext):
        # Look for the author's game and determine if they are responding to the correct message.
        try:
            msg_id = temp_memory[ctx.author.mention]["msg_id"]
            bj_model = temp_memory[ctx.author.mention]["model"]
            # print(msg_id, ctx.message.id)
            if msg_id != ctx.message.id:
                await ctx.respond("Hey, go open your own game >:(.", ephemeral = True)
                return
        except KeyError:
            await ctx.respond("Oops, I can't find your game.", ephemeral = True)
            return
        return bj_model

    async def refresh_display(self, ctx: discord.ApplicationContext, bj_model, game_ended: int):
        _, _, bj_embed = construct_blackjack_embed(self, bj_model, game_ended)
        await ctx.message.edit(embed = bj_embed, view = self if not game_ended else None)

    def cleanup(self, author: str):
        temp_memory.pop(author)

    # "Hit" button
    @discord.ui.button(label = "Hit", style = discord.ButtonStyle.primary)
    async def hit_button_callback(self, button, interaction):
        ctx = await bot.get_application_context(interaction)
        bj_model = await self.retrieve_game_data(ctx)
        game_ended = await bj_model.player_hit(ctx)
        await self.refresh_display(ctx, bj_model, game_ended)
        if game_ended:
            self.cleanup(ctx.author.mention)
        await ctx.response.defer()

    # "Stand" button
    @discord.ui.button(label = "Stand", style = discord.ButtonStyle.primary)
    async def stand_button_callback(self, button, interaction):
        ctx = await bot.get_application_context(interaction)
        bj_model = await self.retrieve_game_data(ctx)
        game_ended = await bj_model.player_stand(ctx)
        await self.refresh_display(ctx, bj_model, game_ended)
        if game_ended:
            self.cleanup(ctx.author.mention)
        await ctx.response.defer()

    # "Fold" button
    @discord.ui.button(label = "Fold", style = discord.ButtonStyle.red)
    async def fold_button_callback(self, button, interaction):
        ctx = await bot.get_application_context(interaction)
        bj_model = await self.retrieve_game_data(ctx)
        game_ended = await bj_model.player_fold(ctx)
        await self.refresh_display(ctx, bj_model, game_ended)
        if game_ended:
            self.cleanup(ctx.author.mention)
        await ctx.response.defer()

    def __init__(self):
        super().__init__(timeout = None)

class BlackjackModel():
    # This is our model class for the blackjack game.
    # https://estopoker.com/rules/blackjack says that the player is to make all their moves first.
    # Also, that the dealer is supposed to stop once they hit 17.

    # We will indicate a player loss via -1 and a player win via 1.
    async def player_hit(self, ctx: discord.ApplicationContext):
        if not self.player_turn: return False
        self.deal(self.player_hand)
        # After a player hits, the game only ends when the player busts.
        if self.hand_status(self.player_hand) == "bust":
            return -1
        elif self.hand_status(self.player_hand) == "blackjack":
            return 1
        else:
            return 0
    
    async def player_stand(self, ctx: discord.ApplicationContext):
        if not self.player_turn: return 0
        self.player_turn = 0
        while self.sum_in_hand(self.dealer_hand) < 17:
            self.deal(self.dealer_hand)
        # After a player stands, the game ends.
        if ((self.hand_status(self.player_hand) != "bust" and self.hand_status(self.dealer_hand) == "bust") 
            or self.sum_in_hand(self.player_hand) > self.sum_in_hand(self.dealer_hand)):
            return 1 # Player Win
        elif self.sum_in_hand(self.player_hand) == self.sum_in_hand(self.dealer_hand):
            return 2 # Draw
        else:
            return -1 # Player loses


    async def player_fold(self, ctx: discord.ApplicationContext):
        if not self.player_turn: return 0
        # After a player folds, the game (obviously) ends.
        return -1

    def sum_in_hand(self, hand: List[Tuple[str, str]]):
        hand_sum = 0
        a_counter = 0
        for card, _ in hand:
            try:
                hand_sum += int(card)
            except ValueError:
                if card in ['J', 'Q', 'K']:
                    hand_sum += 10
                elif card == 'A':
                    a_counter += 1
        for i in range(a_counter):
            hand_sum += 11 if hand_sum < 11 else 1
        return hand_sum

    def hand_status(self, hand: List[Tuple[str, str]]):
        hand_sum = self.sum_in_hand(hand)
        if hand_sum > 21:
            return "bust"
        elif hand_sum == 21:
            return "blackjack"
        else:
            return "nothing"

    def rep_hand(self, hand: str, full: bool = False):
        if hand == "Player":
            # It would be really funny if the player couldn't see their own hand fully.
            return self.display_hand(self.player_hand, True)
        elif hand == "Dealer":
            return self.display_hand(self.dealer_hand, full)
        else:
            raise Exception

    def display_hand(self, hand: List[Tuple[str, str]], full: bool):
        try:
            card = hand[0][0]
            suit = hand[0][1]
            display = f"{card}{suit}" + (" " if len(hand) > 1 else "")
            for i in range(1, len(hand)):
                card = hand[i][0]
                suit = hand[i][1]
                display += f"{card}{suit}" if full else "?" 
                display += ("  " if i < len(hand[1:]) - 1 else "")
        except:
            display = "No cards!"
        
        return display
            

    def deal(self, recipient: List[str]):
        to_be_dealt = cards[randbelow(len(cards))]
        recipient.append(to_be_dealt)

    def start_game(self):
        self.player_hand = []
        self.dealer_hand = []
        for _ in range(2):
            self.deal(self.player_hand)
            self.deal(self.dealer_hand)

    def __init__(self):
        self.player_hand = []
        self.player_turn = True
        self.dealer_hand = []

def construct_blackjack_embed(bj_view: BlackjackView = None, bj_model: BlackjackModel = None, game_state: int = 0):
    if bj_view is None:
        # We wish to initialise a new game.
        bj_view = BlackjackView()

    if bj_model is None:
        bj_model = BlackjackModel()
        bj_model.start_game()
        # Check for auto blackjack.
        if bj_model.sum_in_hand(bj_model.player_hand) == 21:
            game_state = 1

    title = "Blackjack"
    if game_state == 0 or game_state == 2:
        color = cfg.BLACKJACK_CFG["embed_color"]
        if game_state:
            title += " (Draw!)"
    elif game_state == 1:
        color = cfg.BLACKJACK_CFG["win_color"]
        title += " (Win!)"
    elif game_state == -1:
        color = cfg.BLACKJACK_CFG["lose_color"]
        title += " (Lose...)"

    bj_embed = discord.Embed(
                            color = color,
                            title = title
                            )
    bj_embed.add_field(name = f"Dealer's Hand (Total points: {bj_model.sum_in_hand(bj_model.dealer_hand) if game_state else '?'})", value = bj_model.rep_hand("Dealer", game_state), inline = False)
    bj_embed.add_field(name = f"Your Hand (Total points: {bj_model.sum_in_hand(bj_model.player_hand)})", value = bj_model.rep_hand("Player", game_state), inline = False)
    
    if game_state == 1:
        bj_view = None
    
    return bj_model, bj_view, bj_embed

@bot.command(aliases=['bj'])
async def blackjack(ctx: discord.ApplicationContext):
    # For simplicity's sake we will offer infinite blackjack.
    if ctx.author.mention in temp_memory.keys():
        await ctx.send_response("I don't have enough dealers to allow you to play multiple games at once, sorry (not sorry!)", ephemeral = True)
    else:
        bj_model, bj_view, bj_embed = construct_blackjack_embed()
        bj_msg = await ctx.channel.send(embed = bj_embed, view = bj_view)
        # Create an entry tagged to the invoker containing all information necessary.
        temp_memory[ctx.author.mention] = {"msg_id": bj_msg.id, "model": bj_model}
        await ctx.respond("Setting up your game...", ephemeral = True, delete_after = 1)