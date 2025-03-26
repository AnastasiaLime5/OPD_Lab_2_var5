from aiogram import Bot, Dispatcher, types, F  # F - для фильтров сообщений
from aiogram.filters import Command  # Для обработки команд ( /start)
from aiogram.fsm.context import FSMContext  # Для работы с машиной состояний
from aiogram.fsm.state import State, StatesGroup  # Создание состояний
from aiogram.fsm.storage.memory import MemoryStorage  # Хранение состояний в памяти
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton  # Для создания клавиатуры

# База данных родителей и их детей (временное хранилище)
# Ключ - chat_id родителя, значение - данные об ученике
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

valid_codes = ["2025", "class11A"] # Коды доступа

bot = Bot(token="7635891167:AAHGxAdbFhwP9YfkQY8KjnGujMlJ2M1p7gI") # Бот с токеном
storage = MemoryStorage() # Хранилище состояний в оперативной памяти
dp = Dispatcher(storage=storage) # Создание диспетчера для обработки сообщений

# Класс для определения состояний бота (FSM - Finite State Machine)
class AuthStates(StatesGroup):
    waiting_for_code = State()  # Ожидание ввода кода доступа
    waiting_for_name = State()  # Ожидание ввода имени ученика

# Функция показа главного меню
async def show_main_menu(message: types.Message):
    menu = ReplyKeyboardMarkup(   # Создание клавиатуры с двумя кнопками
        keyboard=[
            [KeyboardButton(text="Успеваемость"), KeyboardButton(text="Начать")]
        ],
        resize_keyboard=True  # Автоматическое изменение размера кнопок
    )
    await message.answer("Выберите действие:", reply_markup=menu)

# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()  # Очистка текущего состояния
    if str(message.chat.id) in parents_db:  # Проверка, зарегистрирован ли уже пользователь
        await message.answer(f"Добро пожаловать, {parents_db[str(message.chat.id)]['child_name']}!")
    else:
        await message.answer("Добро пожаловать в бот для родителей!")
    await show_main_menu(message)  # Показ главного меню

# Обработчик кнопки "Начать"
@dp.message(F.text == "Начать")
async def restart(message: types.Message, state: FSMContext):
    await state.clear()  # Очистка состояния
    if str(message.chat.id) in parents_db: # Удаление данных пользователя, если они есть
        del parents_db[str(message.chat.id)]
    await message.answer("Введите код доступа:")
    await state.set_state(AuthStates.waiting_for_code)  # Установка состояния ожидания кода

# Обработчик состояния ожидания кода
@dp.message(AuthStates.waiting_for_code)
async def check_code(message: types.Message, state: FSMContext):
    if message.text not in valid_codes:  # Проверка валидности кода
        await message.answer("Неверный код. Введите еще раз.")
        return  # Выход, если код неверный

    await message.answer("Код принят. Введите имя и фамилию ученика:")
    await state.set_state(AuthStates.waiting_for_name)  # Переход к ожиданию имени

# Обработчик состояния ожидания имени ученика
@dp.message(AuthStates.waiting_for_name)
async def check_student(message: types.Message, state: FSMContext):
    student_name = message.text.strip()  # Удаление лишних пробелов
    found_student = None
    for data in parents_db.values(): # Поиск ученика в базе данных
        if student_name.lower() == data['child_name'].lower():
            found_student = data
            break

    if not found_student:
        await message.answer("Ученик не найден. Проверьте данные и попробуйте снова.")
        return

    # Сохранение данных ученика для текущего чата
    parents_db[str(message.chat.id)] = found_student.copy()
    await message.answer(f"Ученик {found_student['child_name']} найден.")
    await show_main_menu(message)  # Показ главного меню
    await state.clear()  # Очистка состояния

# Обработчик кнопки "Успеваемость"
@dp.message(F.text == "Успеваемость")
async def show_grades(message: types.Message):
    if str(message.chat.id) not in parents_db: # Проверка авторизации пользователя
        await message.answer("Сначала авторизуйтесь (нажмите 'Начать')")
        return

    student = parents_db[str(message.chat.id)]
    response = f"Успеваемость ученика {student['child_name']}:\n\n"

    # Формирование строки с оценками по предметам
    for subject, grades in student['grades'].items():
        response += f"{subject}: {', '.join(map(str, grades))}\n"

    await message.answer(response)  # Отправка успеваемости

# Запуск бота
if __name__ == "__main__":
    dp.run_polling(bot)  # Запуск бота в режиме polling