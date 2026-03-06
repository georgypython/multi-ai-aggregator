from aiogram.fsm.state import State, StatesGroup


class AIFlow(StatesGroup):
    choosing_mode = State()
    choosing_model = State()
    choosing_image_size = State()
    choosing_image_quality = State()
    waiting_image_prompt = State()
    chatting_llm = State()
    editing_llm_temperature = State()
    editing_llm_instructions = State()
