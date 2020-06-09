from robots.app import App

app = App((600, 400))
app.set_sim_rate(1)
app.on_execute()
