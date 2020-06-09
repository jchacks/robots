from robots.app import App, Battle
from robots.bots import MyFirstRobot, RandomRobot

app = App((600, 400))
app.battle = Battle(app, (600,400), [
    MyFirstRobot.MyFirstRobot,
    RandomRobot.RandomRobot
])

app.set_sim_rate(10)
app.on_execute()
