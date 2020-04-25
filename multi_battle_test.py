from robots.app import App
from robots.battle import MultiBattle
from robots.bots import MyFirstRobot, RandomRobot

app = App((1200, 800))
app.battle = MultiBattle(app, (600,400), [
    MyFirstRobot.MyFirstRobot,
    RandomRobot.RandomRobot
], 16)
app.on_execute()
