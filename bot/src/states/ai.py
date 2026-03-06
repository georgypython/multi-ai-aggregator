from aiogram.fsm.state import State, StatesGroup


class AIFlow(StatesGroup):
    choosing_mode = State()
    choosing_model = State()
    choosing_image_size = State()
    choosing_image_quality = State()
    waiting_image_prompt = State()
    choosing_video_duration = State()
    choosing_video_size = State()
    waiting_video_prompt = State()
    chatting_llm = State()
    editing_llm_temperature = State()
    editing_llm_instructions = State()
