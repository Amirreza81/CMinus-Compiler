from enum import Enum


class RelativeOperation(Enum):
    ADD = 'ADD'
    LT = 'LT'
    ASSIGN = 'ASSIGN'
    MULT = 'MULT'
    SUB = 'SUB'
    EQ = 'EQ'
    JPF = 'JPF'
    JP = 'JP'
    PRINT = 'PRINT'


class CodeGenerator:
    def __init__(self):
        self.current_scope = 0
        self.return_stack = list()
        self.index = 0
        self.temp_address = 500
        self.symbol_table = dict()
        self.SS = list()
        self.PB = dict()
        self.break_stack = list()
        self.variable_size = 4

        self.semantic_errors = []
        self.symbol_table.update(
            {'KEYWORDs': ['if', 'else', 'void', 'int', 'while', 'break', 'return'],
             'IDs': []})
        self.operations_dict = {'+': RelativeOperation.ADD.value,
                                '-': RelativeOperation.SUB.value,
                                '<': RelativeOperation.LT.value,
                                '==': RelativeOperation.EQ.value}

    def find_address(self, token_string):
        if token_string == 'output':
            return 'output'
        for record in self.symbol_table['IDs'][::-1]:
            line_number = record[0]
            type_token = record[1]
            lexeme = record[2]
            if token_string == line_number:
                return lexeme

    def call_routine(self, name, lookahead):
        function_name = name[1:]
        self.__getattribute__(function_name)(lookahead)

    def insert_code(self, relop, opr1, opr2='', dist=''):
        i = self.index
        self.PB[i] = f'({relop}, {opr1}, {opr2}, {dist})'
        self.index += 1

    def get_temp(self, count=1):
        address = str(self.temp_address)
        for i in range(count):
            self.insert_code(RelativeOperation.ASSIGN.value, '#0', str(self.temp_address))
            self.temp_address += self.variable_size
        return address

    def add_variable_to_ss(self, lookahead):
        top = self.SS.pop()
        address = self.get_temp()
        scope = self.current_scope
        self.symbol_table['IDs'].append((top, 'int', address, scope))

    def create_array(self, lookahead):
        array_size = int(self.SS.pop()[1:])
        array_id = self.SS.pop()
        address = self.get_temp()
        array_space = self.get_temp(array_size)
        self.insert_code(RelativeOperation.ASSIGN.value, f'#{array_space}', address)
        self.symbol_table['IDs'].append((array_id, 'int*', address, self.current_scope))

    def pid(self, lookahead):
        self.SS.append(lookahead[2])
        print("++++++++++++++++++++1")
        print(self.SS)
        print("++++++++++++++++++++")

    def pid_addr(self, lookahead):
        print("++++++++++++++++++++lookahead")
        print(lookahead)
        print("++++++++++++++++++++")
        self.SS.append(CodeGenerator.find_address(self, lookahead[2]))
        print("++++++++++++++++++++2")
        print(self.SS)
        print("++++++++++++++++++++")

    def push_number(self, lookahead):
        self.SS.append(f'#{lookahead[2]}')
        print("++++++++++++++++++++3")
        print(self.SS)
        print("++++++++++++++++++++")

    def popr(self, lookahead):
        self.SS.append(lookahead[2])
        print("++++++++++++++++++++4")
        print(self.SS)
        print("++++++++++++++++++++")

    def save_operation(self, lookahead):
        operand_2 = self.SS.pop()
        operator = self.SS.pop()
        operand_1 = self.SS.pop()

        address = self.get_temp()
        opr = self.operations_dict[operator]
        self.insert_code(opr, operand_1, operand_2, address)

        self.SS.append(address)
        print("++++++++++++++++++++5")
        print(self.SS)
        print("++++++++++++++++++++")

    def assign_operation(self, lookahead):
        opr1 = self.SS[-1]
        opr2 = self.SS[-2]
        self.insert_code(RelativeOperation.ASSIGN.value, opr1, opr2)
        self.SS.pop()

    def mult(self, lookahead):
        opr1 = self.SS[-1]
        opr2 = self.SS[-2]
        result_address = self.get_temp()
        self.insert_code(RelativeOperation.MULT.value, opr1, opr2, result_address)
        self.SS.pop()
        self.SS.pop()
        self.SS.append(result_address)
        print("++++++++++++++++++++6")
        print(self.SS)
        print("++++++++++++++++++++")

    def define_array_argument(self, lookahead):
        top = self.symbol_table['IDs'][-1]
        del self.symbol_table['IDs'][-1]
        self.symbol_table['IDs'].append((top[0], 'int*', top[2], top[3]))

    def handling_indexes_of_arrays(self, lookahead):
        idx = self.SS.pop()
        array_address = self.SS.pop()
        temp = self.get_temp()
        result = self.get_temp()
        self.insert_code(RelativeOperation.MULT.value, '#4', idx, temp)
        self.insert_code(RelativeOperation.ASSIGN.value, f'{array_address}', result)
        self.insert_code(RelativeOperation.ADD.value, result, temp, result)
        self.SS.append(f'@{result}')
        print("++++++++++++++++++++7")
        print(self.SS)
        print("++++++++++++++++++++")

    def output_function(self, lookahead):
        if self.SS[-2] == 'output':
            self.insert_code(RelativeOperation.PRINT.value, self.SS.pop())

    def save(self, lookahead):
        self.SS.append(self.index)
        print("++++++++++++++++++++8")
        print(self.SS)
        print("++++++++++++++++++++")
        self.index += 1

    def label(self, lookahead):
        self.SS.append(self.index)
        print("++++++++++++++++++++9")
        print(self.SS)
        print("++++++++++++++++++++")

    def jpf_save(self, lookahead):
        dest = self.SS.pop()
        src = self.SS.pop()
        self.PB[dest] = f'(JPF, {src}, {self.index + 1}, )'
        self.SS.append(self.index)
        print("++++++++++++++++++++10")
        print(self.SS)
        print("++++++++++++++++++++")
        self.index += 1

    def jump(self, lookahead):
        dest = int(self.SS.pop())
        self.PB[dest] = f'(JP, {self.index}, , )'

    def handle_jumps_in_while_loop(self, lookahead):
        self.PB[int(self.SS[-1])] = f'(JPF, {self.SS[-2]}, {self.index + 1}, )'
        self.PB[self.index] = f'(JP, {self.SS[-3]}, , )'
        self.index += 1
        self.SS.pop(), self.SS.pop(), self.SS.pop()

    def negative(self, lookahead):
        result = self.get_temp()
        factor_value = self.SS.pop()
        self.insert_code(RelativeOperation.SUB.value, '#0', factor_value, result)
        self.SS.append(result)
        print("++++++++++++++++++++11")
        print(self.SS)
        print("++++++++++++++++++++")

    def pop_trash_data(self, lookahead):
        self.SS.pop()

    def end_of_loop_with_break(self, lookahead):
        self.break_stack.append(self.index)
        self.index += 1

    def new_break(self, lookahead):
        self.break_stack.append('>>>')

    def back_to_scope_with_end_break(self, lookahead):
        latest_block = len(self.break_stack) - self.break_stack[::-1].index('>>>') - 1
        for item in self.break_stack[latest_block + 1:]:
            self.PB[item] = f'(JP, {self.index}, , )'
        self.break_stack = self.break_stack[:latest_block]

    # Function call and return
    def end_of_a_function(self, lookahead):
        self.SS.pop()
        self.SS.pop()
        self.SS.pop()
        for st in self.symbol_table['IDs'][::-1]:
            if st[1] == 'function':
                if st[0] == 'main':
                    top = self.SS.pop()
                    self.PB[top] = f'(ASSIGN, #0, {self.get_temp()}, )'
                    return
                break
            else:
                continue
        top = self.SS.pop()
        self.PB[top] = f'(JP, {self.index}, , )'

    def call_function(self, lookahead):
        if self.SS[-1] != 'output':
            elements = []
            print("++++++++++++++++++++15")
            print(self.SS)
            print("++++++++++++++++++++")
            collections = []
            for top in self.SS[::-1]:
                if isinstance(top, list):
                    collections = top
                    break
                elements = [top] + elements
            print("**********************")
            print(collections)
            print("**********************")
            # assign each element
            for variable, element in zip(collections[1], elements):
                self.insert_code(RelativeOperation.ASSIGN.value, element, variable[2])
                self.SS.pop()  # pop each element
            for i in range(len(elements) - len(collections[1])):
                self.SS.pop()
            self.SS.pop()
            self.insert_code(RelativeOperation.ASSIGN.value, f'#{self.index + 2}', collections[2])
            # jump
            self.insert_code(RelativeOperation.JP.value, collections[-1])
            # save result to temp
            result = self.get_temp()
            print("++++++++++++++++++++16")
            self.insert_code(RelativeOperation.ASSIGN.value, collections[0], result)
            print(self.SS)
            print("++++++++++++++++++++")
            self.SS.append(result)


    def define_params(self, lookahead):
        top = self.SS.pop()
        self.SS.append(self.index)
        print("++++++++++++++++++++17")
        print(self.SS)
        print("++++++++++++++++++++")
        self.index += 1
        print("++++++++++++++++++++18")
        print(self.SS)
        print("++++++++++++++++++++")
        self.SS.append(top)
        self.symbol_table['IDs'].append('>>')

    def pindex(self, lookahead):
        self.SS.append(f'#{self.index}')
        print("++++++++++++++++++++19")
        print(self.SS)
        print("++++++++++++++++++++")

    def start_function(self, lookahead):
        func_id = self.SS[-1]
        return_address = self.get_temp()
        current_index = self.index
        return_value = self.get_temp()
        self.SS.append(return_value)
        self.SS.append(return_address)
        print("++++++++++++++++++++20")
        print(self.SS)
        print("++++++++++++++++++++")
        args_start_index = self.symbol_table['IDs'].index('>>')
        func_args = self.symbol_table['IDs'][args_start_index + 1:]
        self.symbol_table['IDs'].pop(args_start_index)
        self.symbol_table['IDs'] \
            .append((func_id, 'function', [return_value, func_args, return_address, current_index], self.current_scope))

    # Manage returns
    def find_return(self, lookahead):
        self.return_stack.append('>>>')

    def save_point_of_return(self, lookahead):
        self.return_stack.append((self.index, self.SS[-1]))
        self.SS.pop()
        self.index += 2

    def return_to_main(self, lookahead):
        if self.SS[-3] != 'main':
            return_address = self.SS[-1]
            self.insert_code(RelativeOperation.JP.value, f'@{return_address}')

    def close_return(self, lookahead):
        latest_func = len(self.return_stack) - 1
        latest_func = latest_func - self.return_stack[::-1].index('>>>')
        return_value = self.SS[-2]
        return_address = self.SS[-1]
        for rs in self.return_stack[latest_func + 1:]:
            index = rs[0]
            self.PB[index] = f'(ASSIGN, {rs[1]}, {return_value}, )'
            self.PB[index + 1] = f'(JP, @{return_address}, , )'
        self.return_stack = self.return_stack[:latest_func]

    def go_to_next_scope(self, lookahead):
        self.current_scope += 1

    def back_to_previous_scope(self, lookahead):
        for record in self.symbol_table['IDs'][::-1]:
            if record[3] == self.current_scope:
                del self.symbol_table['IDs'][-1]
        self.current_scope -= 1
