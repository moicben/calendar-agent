import os
from browser_use import Agent, ChatOpenAI, Browser
from dotenv import load_dotenv

load_dotenv()

linux_path = "/usr/bin/google-chrome"

browser_args = [
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-networking",
    "--disable-sync",
    "--new-window",
    "--remote-debugging-address=127.0.0.1",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-gpu",
]

browser = Browser(
    executable_path=linux_path,
    headless=False,
    args=browser_args,
)

task = "Va sur https://www.google.com et cherche 'browser-use'"

agent = Agent(
    task=task,
    llm=ChatOpenAI(model="gpt-4o-mini"),
    browser=browser,
)

result = agent.run_sync(max_steps=5)
print(result)

browser.close()

