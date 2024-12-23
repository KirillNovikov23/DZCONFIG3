import re
import sys
import toml

# Регулярные выражения для синтаксиса
CONST_DECLARATION = re.compile(r"^([a-zA-Z][a-zA-Z0-9]*)\s*<-\s*(\d+|\{.*\})$")
DICT_BEGIN = re.compile(r"^begin\s*;?\s*$")
DICT_END = re.compile(r"^end\s*;?\s*$")
ENTRY_PATTERN = re.compile(r"^([a-zA-Z][a-zA-Z0-9]*)\s*:=\s*(\d+|[a-zA-Z][a-zA-Z0-9]*)\s*;?\s*$")
CONST_USE = re.compile(r"^\^\((.*?)\)")

# Глобальный словарь констант
constants = {}


def evaluate_constant(name: str):
    """Получить значение константы или сообщить об ошибке."""
    if name in constants:
        return constants[name]
    raise ValueError(f"Константа '{name}' не определена")


def parse_input(input_text: str) -> dict:
    """Разбирает входной текст и преобразует его в словарь TOML."""
    toml_data = {}
    lines = [line.strip() for line in input_text.splitlines() if line.strip()]
    stack = []  # Стек для вложенных словарей
    current_dict = toml_data

    for line in lines:
        # Удаляем точку с запятой в конце строки
        line = line.rstrip(';').strip()
        # Объявление констант
        if match := CONST_DECLARATION.match(line):
            name, value = match.groups()
            constants[name] = int(value)
        # Использование констант
        elif match := CONST_USE.match(line):
            name = match.group(1)
            value = evaluate_constant(name)
            current_dict[name] = value
        # Начало словаря
        elif DICT_BEGIN.match(line):
            new_dict = {}
            stack.append(current_dict)
            if 'nested' not in current_dict:
                current_dict['nested'] = []
            current_dict['nested'].append(new_dict)
            current_dict = new_dict
        # Конец словаря
        elif DICT_END.match(line):
            if not stack:
                raise SyntaxError("Несоответствующие 'end'")
            current_dict = stack.pop()
        # Ввод значений
        elif match := ENTRY_PATTERN.match(line):
            name, value = match.groups()
            if value in constants:
                value = constants[value]  # Использование значения константы
            else:
                value = int(value) if value.isdigit() else value
            current_dict[name] = value
        else:
            print(f"Отладка: Строка побайтово -> {repr(line)}", file=sys.stderr)
            raise SyntaxError(f"Синтаксическая ошибка: {line}")

    if stack:
        raise SyntaxError("Несоответствующие 'begin' и 'end'")

    return toml_data


def main():
    """Основная функция для чтения ввода и записи в TOML файл."""
    if len(sys.argv) != 2:
        print("Использование: python script.py <output_file>", file=sys.stderr)
        sys.exit(1)

    output_file = sys.argv[1]
    input_text = sys.stdin.read()
    input_text = input_text.lstrip('\ufeff')  # Удаляем BOM, если он есть

    try:
        toml_data = parse_input(input_text)
        print(f"Отладка: Содержимое TOML перед записью -> {toml_data}", file=sys.stderr)
        if not toml_data:
            raise ValueError("Ошибка: TOML-данные пусты после обработки.")
        with open(output_file, 'w') as f:
            toml.dump(toml_data, f)
        print(f"TOML файл успешно создан: {output_file}")
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()