from io import StringIO
import os
from subprocess import Popen, PIPE, TimeoutExpired
from threading import Thread
import evaluator
import shutil
import vm

INPUT_CODE_FILENAME = 'input.txt'
COMPILER_OUTPUT_FILENAME = 'output.txt'
PROGRAM_OUTPUT_FILENAME = 'expected.txt'
SEMANTIC_ERRORS_FILENAME = 'semantic_errors.txt'


def run_and_evaluate(test_name):
    __compile(test_name)

    if(os.path.exists(__get_path_for_test(test_name, PROGRAM_OUTPUT_FILENAME))):
        __run()
        expected_program_output, program_output = __read_expected_and_actual(
            test_name, PROGRAM_OUTPUT_FILENAME)
        score1 = evaluator.calc_program_output_score(
            expected_program_output, program_output)
        score2 = 0
        print("Generated Program Output:", program_output)
        print("Expected Program Output:", expected_program_output)
    else:
        expected_errors, errors = __read_expected_and_actual(
            test_name, SEMANTIC_ERRORS_FILENAME)
        score1 = 0
        score2 = evaluator.calc_semantic_errors_score(expected_errors, errors)

    print(test_name, '-->', score1, score2)
    return score1, score2


def __compile(test_name):
    shutil.copyfile(
        __get_path_for_test(test_name, INPUT_CODE_FILENAME),
        f'./{INPUT_CODE_FILENAME}')

    for file_name in [
            COMPILER_OUTPUT_FILENAME,
            PROGRAM_OUTPUT_FILENAME,
            # SEMANTIC_ERRORS_FILENAME
            ]:
        if os.path.exists(file_name):
            os.remove(file_name)

    compiler_process = Popen(
        ['./venv/bin/python', 'compiler.py'], stdout=PIPE, stderr=PIPE)
    try:
        out, err = compiler_process.communicate(5)
    except TimeoutExpired:
        compiler_process.kill()
        raise
    print('Compiler Standard Output:', out)
    print('Compiler Standard Error:', err)


def __run():
    with open(COMPILER_OUTPUT_FILENAME, 'r') as generated_codes, \
            open(PROGRAM_OUTPUT_FILENAME, 'w') as output, \
            open(os.devnull, 'w') as devnull:
        # StringIO() as devnull:
        # t = Thread(
        #     target=vm.run,
        #     args=(generated_codes.readlines(), output, devnull))
        # t.start()
        # t.join(10)
        # if t.is_alive():
        #     raise TimeoutError()

        vm_process = Popen(
            ['./venv/bin/python', 'test/vm.py'],
            stdin=generated_codes, stdout=output, stderr=PIPE)
        try:
            _, err = vm_process.communicate(10)
            if vm_process.returncode != 0:
                print("VM standard error:", err)
                raise Exception("Error in running the program")
        except TimeoutExpired:
            vm_process.kill()
            raise


def __read_expected_and_actual(test_name: str, filename: str):
    if not filename.endswith('.txt'):
        filename = f'{filename}.txt'

    def read(path):
        with open(file=path, mode='r') as f:
            return f.read()

    expected = read(__get_path_for_test(test_name, filename))
    actual = read(filename)

    return expected, actual


def __get_path_for_test(test_name: str, filename: str):
    return os.path.join('test/testcases', test_name, filename)
