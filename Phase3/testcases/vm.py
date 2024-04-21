import sys
import re

COMMAND_PATTERN = re.compile(
    r'\d+\s+\(\s*(?P<command>[A-Z]+)(?P<params>(\s*,\s*[#@]?[-+]?\d*)+)\s*\)')


class Context:
    def __init__(self, output_file, error_file):
        self.memory = dict()
        self.pc = 0
        self.output_file = output_file
        self.error_file = error_file


def run(instructions: list[str], output_file, error_file):
    context = Context(output_file, error_file)
    instructions = [inst for inst in instructions if not inst.isspace()]
    while context.pc < len(instructions):
        try:
            instruction = instructions[context.pc]
            __execute(instruction, context)
        except:
            print(context.memory, file=sys.stderr)
            raise


def __execute(instruction: str, context: Context):
    print('--->  PC =', context.pc,
          'command :', instruction,
          end='',
          file=context.error_file)

    def resolve(param: str):
        if param.casefold() == 'true':
            return 1
        elif param.casefold() == 'false':
            return 0

        value = int(param) if param[0].isdigit() else int(param[1:])

        if param.startswith('#'):
            return value
        elif param.startswith('@'):
            return read_memory(read_memory(value))
        else:
            return read_memory(value)

    def resolve_dest(param: str):
        value = int(param) if param[0].isdigit() else int(param[1:])

        if param.startswith('#'):
            return value
        elif param.startswith('@'):
            return read_memory(value)
        else:
            return value

    def read_memory(address: int):
        value = memory.get(address, None)
        if value is None:
            raise Exception('Invalid access to memory', address)

        return value

    def set_memory(param: str, value: int):
        address = resolve_dest(param)
        memory[address] = value
        print(f'--->  memory[{address}] =', value, file=context.error_file)

    memory = context.memory
    context.pc += 1

    match = re.match(COMMAND_PATTERN, instruction)
    if not match:
        raise Exception('Invalid Command', instruction)

    command = match['command'].upper()
    params = [s.strip() for s in match['params'].split(',')[1:]]
    # Only for consistency with legacy tester
    params = [p for p in params if p and not p.isspace()]

    def run_triple_address(operation):
        set_memory(params[2],
                   operation(resolve(params[0]), resolve(params[1])))

    if command == 'ADD':
        run_triple_address(lambda x0, x1: x0 + x1)

    elif command == 'AND':
        run_triple_address(lambda x0, x1: x0 & x1)

    elif command == 'ASSIGN':
        # Only because of consistency with the legacy tester
        if resolve_dest(params[1]) not in memory:
            memory[resolve_dest(params[1])] = 0
        set_memory(params[1], resolve(params[0]))

    elif command == 'EQ':
        run_triple_address(lambda x0, x1: int(x0 == x1))

    elif command == 'JPF':
        if not resolve(params[0]):
            context.pc = resolve_dest(params[1])

    elif command == 'JP':
        context.pc = resolve_dest(params[0])

    elif command == 'LT':
        run_triple_address(lambda x0, x1: int(x0 < x1))

    elif command == 'MULT':
        run_triple_address(lambda x0, x1: x0 * x1)

    elif command == 'DIV':
        run_triple_address(lambda x0, x1: x0 // x1)

    elif command == 'NOT':
        set_memory(params[1], not resolve(params[0]))

    elif command == 'PRINT':
        print('PRINT', resolve(params[0]),
              sep='    ', file=context.output_file)

    elif command == 'SUB':
        run_triple_address(lambda x0, x1: x0 - x1)

    else:
        raise Exception('Invalid Command', command)

if __name__ == "__main__":
    run(sys.stdin.readlines(), sys.stdout, sys.stderr)
