from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Инициализация базы данных
parents_db = {
    'parent1_chat_id': {'child_name': 'Анастасия Назарова',
                        'grades': {'Математика': [5, 4, 5], 'Русский': [4, 5, 4], 'География': [5, 5, 4],
                                   'Литература': [5, 5, 5], 'Физика': [5, 5, 4]}},
    'parent2_chat_id': {'child_name': 'Алина Зданникова',
                        'grades': {'Математика': [5, 4, 5], 'Русский': [5, 5, 4], 'География': [5, 5, 5],
                                   'Литература': [3, 4, 5], 'Физика': [4, 4, 5]}},
    'parent3_chat_id': {'child_name': 'Анна Гергерт',
                        'grades': {'Математика': [3, 4, 5], 'Русский': [5, 5, 4], 'География': [5, 5, 5],
                                   'Литература': [5, 5, 4], 'Физика': [4, 5, 5]}},
    'parent4_chat_id': {'child_name': 'Динара Жакина',
                        'grades': {'Математика': [4, 4, 4], 'Русский': [5, 5, 4], 'География': [5, 4, 5],
                                   'Литература': [5, 5, 4], 'Физика': [4, 4, 5]}},
    'parent5_chat_id': {'child_name': 'Альбина Наурзбаева',
                        'grades': {'Математика': [4, 4, 5], 'Русский': [5, 5, 4], 'География': [4, 5, 5],
                                   'Литература': [5, 5, 4], 'Физика': [4, 4, 3]}},
}

valid_codes = ["2025", "class11A"]

bot = Bot(token="7635891167:AAHGxAdbFhwP9YfkQY8KjnGujMlJ2M1p7gI")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class AuthStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_name = State()

async def show_main_menu(message: types.Message):
    menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Успеваемость"), KeyboardButton(text="Начать")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите действие:", reply_markup=menu)

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    if str(message.chat.id) in parents_db:
        await message.answer(f"Добро пожаловать, {parents_db[str(message.chat.id)]['child_name']}!")
    else:
        await message.answer("Добро пожаловать в бот для родителей!")
    await show_main_menu(message)

@dp.message(F.text == "Начать заново")
async def restart(message: types.Message, state: FSMContext):
    await state.clear()
    if str(message.chat.id) in parents_db:
        del parents_db[str(message.chat.id)]
    await message.answer("Введите код доступа:")
    await state.set_state(AuthStates.waiting_for_code)

@dp.message(AuthStates.waiting_for_code)
async def check_code(message: types.Message, state: FSMContext):
    if message.text not in valid_codes:
        await message.answer("Неверный код. Введите еще раз.")
        return

    await message.answer("Код принят. Введите имя и фамилию ученика:")
    await state.set_state(AuthStates.waiting_for_name)

@dp.message(AuthStates.waiting_for_name)
async def check_student(message: types.Message, state: FSMContext):
    student_name = message.text.strip()
    found_student = None

    for data in parents_db.values():
        if student_name.lower() == data['child_name'].lower():
            found_student = data
            break

    if not found_student:
        await message.answer("Ученик не найден. Проверьте данные и попробуйте снова.")
        return

    parents_db[str(message.chat.id)] = found_student.copy()
    await message.answer(f"Ученик {found_student['child_name']} найден.")
    await show_main_menu(message)
    await state.clear()

@dp.message(F.text == "Успеваемость")
async def show_grades(message: types.Message):
    if str(message.chat.id) not in parents_db:
        await message.answer("Сначала авторизуйтесь (нажмите 'Начать')")
        return

    student = parents_db[str(message.chat.id)]
    response = f"Успеваемость ученика {student['child_name']}:\n\n"

    for subject, grades in student['grades'].items():
        response += f"{subject}: {', '.join(map(str, grades))}\n"

    await message.answer(response)

if __name__ == "__main__":
    dp.run_polling(bot)