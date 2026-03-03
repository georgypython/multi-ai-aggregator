from aiogram.fsm.state import State, StatesGroup


class AIFlow(StatesGroup):
    choosing_mode = State()
    choosing_model = State()
    chatting_llm = State()
    editing_llm_temperature = State()
    editing_llm_instructions = State()
