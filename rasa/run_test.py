from rasa.core.agent import Agent
import asyncio

if __name__ == '__main__':
    model_path = 'models/moodbot_all.tar.gz'
    #serve_application(model_path=model_path, channel="rest")
    agent = Agent.load(model_path=model_path)
    # await agent.handle_text("hello")
    loop = asyncio.get_event_loop()
    sent = loop.run_until_complete(agent.handle_text(text_message="I feel so bad"))
    print(sent)