from __future__ import annotations
import asyncio
import random
import datetime
from itertools import chain, groupby
import numpy as np
from utils.errors import AnotherGame
from utils.useful import make_async
from typing import Union
from PIL import Image, ImageDraw, ImageFont
from utils.errors import Connect4ColumnFull


class GlobalPlayers:
    __slots__ = ("games",)

    def __init__(self):
        # Author will have the Game object
        # While the player will point to the author's id
        self.games = {}

    def get_player(self, player_id):
        if player_id in self.games:
            game = self.games[player_id]
            if isinstance(game, int):
                return self.games[game]
            else:
                return game

    def add(self, ctx, players_id, game):
        if ctx.author.id in self.games:
            raise AnotherGame(ctx.author.id)  # if coded correctly, this isn't possible to hit
        new_game = Game(ctx, players_id, game, False)
        self.games.update({ctx.author.id: new_game})
        for player_id in players_id:
            if player_id in self.games:
                raise AnotherGame(player_id)
            self.games.update({player_id: ctx.author.id})
        return new_game

    def remove(self, game: Union[Game, int]):
        if isinstance(game, int):
            # if int, it must be an author id
            game = self.games.pop(game)
            for player_id in game.players_id:
                self.games.pop(player_id, None)
        else:
            self.games.pop(game.author_id)
            for player_id in game.players_id:
                self.games.pop(player_id, None)

    def __len__(self):
        return len(self.games)


class Game:
    __slots__ = ("ctx", "created_at", "author_id", "players_id", "game", "status")

    def __init__(self, ctx, players_id: list, game: str, status: bool):
        self.ctx = ctx
        self.created_at = datetime.datetime.utcnow()
        self.author_id = ctx.author.id
        self.players_id = players_id
        self.game = game
        self.status = status

    @property
    def author(self):
        return self.ctx.bot.get_user(self.author_id)

    @property
    def players(self):
        return [self.ctx.bot.get_user(player_id) for player_id in self.players_id]

    def __contains__(self, player):
        auth, players = (self.author_id, self.players_id) if isinstance(player, int) else (self.author, self.players)
        return player in players or player == auth

    def __str__(self):
        return self.game

    class Connect4:
        __slots__ = ("players", "turn", "cols", "rows", "win", "NONE", "board", "new", "FOLDER", "CHANGE",
                     "previous_image", "first_time")

        def __init__(self, players, start=None, cols=7, rows=6, win_requirements=4):
            if 2 < len(players) < 0:
                raise Exception("Higher/Lower than 2 players.")

            self.players = players
            self.turn = random.randint(1, 2)
            self.cols = cols
            self.rows = rows
            self.win = win_requirements
            self.NONE = 0
            self.CHANGE = 2 ^ 1
            self.board = [[self.NONE] * rows for _ in range(cols)]
            self.new = (-1, -1)
            self.FOLDER = "resources/connect_4"
            self.previous_image = None
            self.first_time = True

        def check_draw(self):
            return all(col[0] != self.NONE for col in self.board)

        def insert(self, column, color):
            """Insert the player color in the given column."""
            col = self.board[column]
            final_cell = 0
            if col[final_cell] != self.NONE:
                raise Connect4ColumnFull(self.players[color], column)

            row = col.index(self.NONE)
            col[row] = color
            self.new = (column, row)
            if self.check_draw():
                return "draw"
            if self.check_for_win():
                return "win"
            self.change_turn()


        def check_for_win(self):
            """Check the current board for a winner."""
            return self.get_winner()

        def get_winner(self):
            """Get the winner on the current board.
               Win algorithm was made by Patrick Westerhoff, I really like how short he made this.
            """
            lines = (
                self.board,  # columns
                zip(*self.board),  # rows
                self.diagonals_positive(self.board, self.cols, self.rows),  # positive diagonals
                self.diagonals_negative(self.board, self.cols, self.rows)  # negative diagonals
            )

            for line in chain(*lines):
                for color, group in groupby(line):
                    if color != self.NONE and len(list(group)) >= self.win:
                        return color

        async def first_time_render(self):
            with Image.open(f"{self.FOLDER}/connect4_board.png") as image_board:
                # draw the player text above
                TEXT_POSITION = ((177, 54), (515, 54))
                for players, pos in zip(self.players, TEXT_POSITION):
                    player_text = await render_text(self.players.display_name, (307, 89), 50, (255, 255, 255))
                    image_board.paste(player_text, pos, mask=player_text)
            self.first_time = False
            return image_board

        async def render_board(self):
            """Renders the board, putting everything in place including text, players and the board itself"""
            image_board = self.previous_image
            if self.first_time:
                image_board = await self.first_time_render()
            # Actually draws the player's positions
            player_dot = tuple(f"player_{x + 1}.png" for x in range(2))
            FIRST_POSITION = 120
            INITIAL_X = 92
            INITIAL_Y = 236
            MARGIN = 3
            offset_x, offset_y = tuple(FIRST_POSITION * x for x in self.new)
            x, y = self.new
            pos = self.board[x][y] - 1
            player_resources = player_dot[pos]
            with Image.open(f"{self.FOLDER}/{player_resources}") as image:
                stroke_image = await render_stroke_image(image)
                image_board.paste(stroke_image, ((INITIAL_X + offset_x) - MARGIN, (INITIAL_Y + offset_y) - MARGIN),
                                  mask=stroke_image)
                image_board.paste(image, (INITIAL_X + offset_x, INITIAL_Y + offset_y),
                                  mask=image)

            self.previous_image = image_board
            return image_board

        def diagonals_positive(self, matrix, cols, rows):
            """Get positive diagonals, going from bottom-left to top-right."""
            for di in ([(j, i - j) for j in range(cols)] for i in range(cols + rows - 1)):
                yield [matrix[i][j] for i, j in di if 0 <= i < cols and 0 <= j < rows]

        def diagonals_negative(self, matrix, cols, rows):
            """Get negative diagonals, going from top-left to bottom-right."""
            for di in ([(j, i - cols + j + 1) for j in range(cols)] for i in range(cols + rows - 1)):
                yield [matrix[i][j] for i, j in di if 0 <= i < cols and 0 <= j < rows]

        def change_turn(self):
            self.turn ^= self.CHANGE
            return self.turn


@make_async()
def render_text(text, w_h, textsize, color):
    W, H = w_h
    # creates a new Box image for the text to be drawn on with a transparency box.
    text_box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_box)
    # declares the font
    text_font = ImageFont.truetype('.fonts/BebasNeue-Bold.ttf', size=textsize)

    # This auto sizes the text into the border + 20 as margin
    # This works by checking if the textsize is outside the text_box box, if it is, it will decrement by 2 until it fits
    margin = 20
    width = 0
    while draw.textsize(text, font=ImageFont.truetype('.fonts/BebasNeue-Bold.ttf', size=textsize))[width] + margin > W:
        textsize -= 2
        text_font = ImageFont.truetype('.fonts/BebasNeue-Bold.ttf', size=textsize)

    # still getting the text size, but it's for real this time
    w, h = draw.textsize(text, font=text_font)
    # The actual text is getting drawn into the image with stroke and given color
    draw.text(((W - w) / 2, (H - h) / 2), text, fill=color, font=text_font, stroke_fill=(0, 0, 0),
              stroke_width=1)
    # text_box is resized into the desired size.
    text_box.resize((W, H), Image.ANTIALIAS)
    return text_box


@make_async()
def render_stroke_image(player_dot_ind, color=(0, 99, 178)):
    """Responsible for rendering the stroke of an image"""
    old_size = player_dot_ind.size
    new_size = (old_size[0] + 50, old_size[1] + 50)

    # creates a new image which is 50 pixel bigger in 2 direction
    new_stroke = Image.new("RGB", new_size, color=color)
    new_stroke = new_stroke.resize(new_size)
    new_stroke = np.array(new_stroke)

    # A new canvas to draw
    alpha = Image.new("L", new_size, color=0)
    # draw with "L"(black and white 8 bit) mode, with the with black
    drawn_image = ImageDraw.Draw(alpha)
    drawn_image.pieslice([0, 0, new_size[0], new_size[1]], 0, 360, fill=255)

    array_np = np.array(alpha)
    combined_array = np.dstack((new_stroke, array_np))

    stroke_image = Image.fromarray(combined_array)
    stroke_image.thumbnail((old_size[0] + 6, old_size[1] + 6), resample=Image.ANTIALIAS)
    return stroke_image