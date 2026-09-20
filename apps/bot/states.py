from aiogram.fsm.state import State,StatesGroup

class LoginStates(StatesGroup):
    first_name = State()
    last_name = State()
    phone_number = State()
    username = State()
    password = State()