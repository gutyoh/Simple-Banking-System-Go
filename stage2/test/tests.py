import random
import re

from hstest import dynamic_test, StageTest, CheckResult, TestedProgram


class SimpleBankSystemTest(StageTest):
    card_number_pattern = re.compile(r'^400000\d{10}$', re.MULTILINE)
    pin_pattern = re.compile(r'^\d{4}$', re.MULTILINE)

    @dynamic_test(time_limit=60000)
    def test1_check_card_credentials(self):
        program = TestedProgram()
        program.start()

        output = program.execute('1')

        card_number_matcher = self.card_number_pattern.search(output)

        if not card_number_matcher:
            return CheckResult.wrong(
                'You are printing the card number incorrectly. '
                'The card number should look like in the example: 400000DDDDDDDDDD, '
                'where D is a digit.')

        pin_matcher = self.pin_pattern.search(output)

        if not pin_matcher:
            return CheckResult.wrong(
                'You are printing the card PIN incorrectly. '
                'The PIN should look like in the example: DDDD, where D is a digit.')

        correct_card_number = card_number_matcher.group()

        output = program.execute('1')
        card_number_matcher = self.card_number_pattern.search(output)

        if not card_number_matcher:
            return CheckResult.wrong(
                'You are printing the card number incorrectly. '
                'The card number should look like in the example: 400000DDDDDDDDDD, '
                'where D is a digit.')

        pin_matcher = self.pin_pattern.search(output)

        if not pin_matcher:
            return CheckResult.wrong(
                'You are printing the card PIN incorrectly. '
                'The PIN should look like in the example: DDDD, where D is a digit.')

        another_card_number = card_number_matcher.group()

        if another_card_number == correct_card_number:
            return CheckResult.wrong('Your program generates two identical card numbers!')

        program.execute('0')

        return CheckResult.correct()

    @dynamic_test(time_limit=60000)
    def test2_check_log_in_and_log_out(self):
        program = TestedProgram()
        program.start()

        output = program.execute('1')

        card_number_matcher = self.card_number_pattern.search(output)

        if not card_number_matcher:
            return CheckResult.wrong(
                'You are printing the card number incorrectly. '
                'The card number should look like in the example: 400000DDDDDDDDDD, '
                'where D is a digit.')

        pin_matcher = self.pin_pattern.search(output)

        if not pin_matcher:
            return CheckResult.wrong(
                'You are printing the card PIN incorrectly. '
                'The PIN should look like in the example: DDDD, where D is a digit.')
        correct_pin = pin_matcher.group().strip()
        correct_card_number = card_number_matcher.group()

        program.execute('2')
        output = program.execute('{}\n{}'.format(correct_card_number, correct_pin))

        if 'successfully' not in output.lower():
            return CheckResult.wrong(
                'The user should be signed in after entering the correct card information.')

        output = program.execute('2')

        if 'create' not in output.lower():
            return CheckResult.wrong(
                'The user should be logged out after choosing \'Log out\' option.\n'
                'And you should print the menu with \'Create an account\' option.')

        program.execute('0')

        return CheckResult.correct()

    @dynamic_test(time_limit=60000)
    def test3_check_log_in_with_wrong_pin(self):
        program = TestedProgram()
        program.start()

        output = program.execute('1')

        card_number_matcher = self.card_number_pattern.search(output)
        pin_matcher = self.pin_pattern.search(output)

        if not card_number_matcher or not pin_matcher:
            return CheckResult.wrong('You should output card number and PIN like in example!')

        correct_card_number = card_number_matcher.group()
        correct_pin = pin_matcher.group()

        random.seed()

        incorrect_pin = correct_pin

        while correct_pin == incorrect_pin:
            incorrect_pin = str(1000 + random.randint(0, 8999))

        program.execute('2')
        output = program.execute('{}\n{}'.format(correct_card_number, incorrect_pin))

        if 'successfully' in output.lower():
            return CheckResult.wrong(
                'The user should not be signed in after entering incorrect card information.')

        program.execute('0')

        return CheckResult.correct()

    @dynamic_test(time_limit=60000)
    def test4_check_log_in_to_not_existing_account(self):
        program = TestedProgram()
        program.start()

        output = program.execute('1')

        card_number_matcher = self.card_number_pattern.search(output)
        pin_matcher = self.pin_pattern.search(output)

        if not card_number_matcher or not pin_matcher:
            return CheckResult.wrong('You should output card number and PIN like in example')

        correct_card_number = card_number_matcher.group()

        random.seed()

        correct_pin = pin_matcher.group().strip()
        incorrect_card_number = correct_card_number

        while correct_card_number == incorrect_card_number:
            incorrect_card_number = '400000' + str(100000000 + random.randint(0, 800000000))

        program.execute('2')
        output = program.execute('{}\n{}'.format(incorrect_card_number, correct_pin))

        if 'successfully' in output.lower():
            return CheckResult.wrong(
                'The user should not be signed in after entering the information of a non-existing card.')

        return CheckResult.correct()

    @dynamic_test(time_limit=60000)
    def test5_check_balance(self):
        program = TestedProgram()
        program.start()

        output = program.execute('1')

        card_number_matcher = self.card_number_pattern.search(output)
        pin_matcher = self.pin_pattern.search(output)

        if not card_number_matcher or not pin_matcher:
            return CheckResult.wrong('You should output card number and PIN like in example')

        correct_pin = pin_matcher.group().strip()
        correct_card_number = card_number_matcher.group()

        program.execute('2')
        program.execute('{}\n{}'.format(correct_card_number, correct_pin))
        output = program.execute('1')

        if '0' not in output:
            return CheckResult.wrong('Expected balance: 0')

        program.execute('0')

        return CheckResult.correct()

    @dynamic_test(time_limit=60000)
    def test6_check_luhn_algorithm(self):
        program = TestedProgram()
        program.start()

        output = program.execute("1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1")

        card_number_matcher = self.card_number_pattern.findall(output)

        is_some_card_found = False
        found_cards = 0

        for card_number in card_number_matcher:
            found_cards += 1

            if not is_some_card_found:
                is_some_card_found = True

            if not self.check_luhn_algorithm(card_number):
                return CheckResult.wrong(f"The card number {card_number} doesn't pass the Luhn algorithm.")

        if not is_some_card_found:
            return CheckResult.wrong("You should output card number and PIN like in example")

        if found_cards != 20:
            return CheckResult.wrong(f"Tried to generate 20 cards, but found {found_cards}")

        return CheckResult.correct()

    @staticmethod
    def check_luhn_algorithm(number):
        luhn = [int(char) for char in str(number)]
        for i, num in enumerate(luhn):
            if (i + 1) % 2 == 0:
                continue
            temp = num * 2
            luhn[i] = temp if temp < 10 else temp - 9
        return sum(luhn) % 10 == 0


if __name__ == '__main__':
    SimpleBankSystemTest().run_tests()
