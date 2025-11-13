from browser_use import Agent, ChatOpenAI, Browser

linux_path = "/usr/bin/google-chrome"

browser = Browser(
    executable_path=linux_path,
    headless=False,
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

