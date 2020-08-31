from robots.app import MultiBattleApp
from robots.battle import MultiBattle
from robots.bots import MyFirstRobot, RandomRobot

app = MultiBattleApp((1200, 800), battle=MultiBattle(size=(600, 400), robots=[
    MyFirstRobot.MyFirstRobot,
    RandomRobot.RandomRobot
], num_battles=4), rows=2)
app.run()
