import os
import random
import re
import shutil
import sqlite3

from hstest import dynamic_test, StageTest, CheckResult, TestedProgram


class SimpleBankSystemTest(StageTest):
    database_file_name = 'card.s3db'
    temp_database_file_name = 'tempDatabase.s3db'
    args = ['-fileName', database_file_name]
    table_name = 'cards'
    correct_data = {}

    card_number_pattern = re.compile(r'^400000\d{10}$', re.MULTILINE)
    pin_pattern = re.compile(r'^\d{4}$', re.MULTILINE)

    connection = None

    @dynamic_test(time_limit=60000)
    def test1_check_database_file(self):
        program = TestedProgram()
        program.start(*self.args)

        self.stop_and_check_if_user_program_was_stopped(program)

        if not os.path.exists(self.database_file_name):
            return CheckResult.wrong(
                "You should create a database file named " + self.database_file_name + ". "
                                                                                       "The file name should be taken from the command line arguments.\n"
                                                                                       "The database file shouldn't be deleted after stopping the program!"
            )

        return CheckResult.correct()

    @dynamic_test(time_limit=60000)
    def test2_check_connection(self):
        program = TestedProgram()
        program.start(*self.args)

        self.stop_and_check_if_user_program_was_stopped(program)

        self.get_connection()
        self.close_connection()

        return CheckResult.correct()

    @dynamic_test(time_limit=60000)
    def test3_check_if_table_exists(self):
        program = TestedProgram()
        program.start(*self.args)

        self.stop_and_check_if_user_program_was_stopped(program)

        try:
            cursor = self.get_connection().cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type ='table' AND name NOT LIKE 'sqlite_%';")
            table_names = [table_name[0] for table_name in cursor.fetchall()]

            if self.table_name in table_names:
                self.close_connection()
                return CheckResult.correct()
        except sqlite3.Error:
            self.close_connection()
            raise Exception("Can't execute a query in your database! Make sure that your database isn't broken "
                            "and you close your connection at the end of the program!")

        self.close_connection()
        return CheckResult.wrong("Your database doesn't have a table named " + self.table_name + "!\n"
                                                                                                 "Found tables: " + ", ".join(
            table_names))

    @dynamic_test(time_limit=60000)
    def test4_check_columns(self):
        program = TestedProgram()
        program.start(*self.args)

        self.stop_and_check_if_user_program_was_stopped(program)

        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(" + self.table_name + ");")
            columns = {column['name'].lower(): column['type'].upper() for column in cursor.fetchall()}

            correct_columns = [
                ["id", "INTEGER", "INT"],
                ["number", "TEXT", "VARCHAR"],
                ["pin", "TEXT", "VARCHAR"],
                ["balance", "INTEGER", "INT"]]

            for correct_column in correct_columns:
                error_message = "Can't find '" + correct_column[0] + "' column with '" + correct_column[
                    1] + "' type.\n" + "Your table should have columns described in " + "the stage instructions."
                if correct_column[0] not in columns:
                    return CheckResult.wrong(error_message)
                elif correct_column[1] not in columns[correct_column[0]] and correct_column[2] not in \
                        columns[correct_column[0]]:
                    return CheckResult.wrong(error_message)
        except sqlite3.Error:
            raise Exception("Can't connect to the database!")

        self.close_connection()
        return CheckResult.correct()

    @dynamic_test
    def test5_check_adding_rows_to_the_table(self):
        self.delete_all_rows()

        program = TestedProgram()
        program.start(*self.args)

        output = program.execute("1")

        if not self.get_data(output):
            return CheckResult.wrong("You should output card number and PIN like in example\n" +
                                     "Or it doesn't pass the Luhn algorithm")

        output = program.execute("1")

        if not self.get_data(output):
            return CheckResult.wrong("You should output card number and PIN like in example\n" +
                                     "Or it doesn't pass the Luhn algorithm")

        output = program.execute("1")

        if not self.get_data(output):
            return CheckResult.wrong("You should output card number and PIN like in example\n" +
                                     "Or it doesn't pass the Luhn algorithm")

        output = program.execute("1")

        if not self.get_data(output):
            return CheckResult.wrong("You should output card number and PIN like in example\n" +
                                     "Or it doesn't pass the Luhn algorithm")

        output = program.execute("1")

        if not self.get_data(output):
            return CheckResult.wrong("You should output card number and PIN like in example\n" +
                                     "Or it doesn't pass the Luhn algorithm")

        self.stop_and_check_if_user_program_was_stopped(program)

        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name};")
            user_data = {}

            rows = cursor.fetchall()
            for row in rows:
                # print(row['number'])
                if row['number'] is None:
                    return CheckResult.wrong("The card number shouldn't be null in the database!")
                if row['balance'] != 0:
                    return CheckResult.wrong("Default balance value should be 0 in the database!")
                if row['pin'] is None:
                    return CheckResult.wrong("The PIN shouldn't be null in the database!")
                user_data[row['number']] = row['pin']

            for card_number, pin in self.correct_data.items():
                if card_number not in user_data:
                    return CheckResult.wrong("Your database doesn't save newly created cards.")
                elif user_data[card_number] != pin:
                    return CheckResult.wrong(f"Correct PIN for card number {card_number} should be {pin}")

        except sqlite3.Error:
            return CheckResult.wrong("Can't connect the database!")

        self.close_connection()
        return CheckResult.correct()

    @dynamic_test(time_limit=60000)
    def test6_check_log_in(self):
        program = TestedProgram()
        program.start(*self.args)

        output = program.execute("1")

        card_number_matcher = self.card_number_pattern.search(output)

        if not card_number_matcher:
            return CheckResult.wrong("You are printing the card number " +
                                     "incorrectly. The card number should look like in the example:" +
                                     " 400000DDDDDDDDDD, where D is a digit.")

        pin_matcher = self.pin_pattern.search(output)

        if not pin_matcher:
            return CheckResult.wrong("You are printing the card PIN " +
                                     "incorrectly. The PIN should look like in the example: DDDD, where D is a digit.")

        correct_pin = pin_matcher.group().strip()
        correct_card_number = card_number_matcher.group()

        program.execute("2")
        output = program.execute(correct_card_number + "\n" + correct_pin)

        if "successfully" not in output.lower():
            return CheckResult.wrong("The user should be signed in after" +
                                     " entering the correct card information.")

        self.stop_and_check_if_user_program_was_stopped(program)

        return CheckResult.correct()

    @dynamic_test(time_limit=60000)
    def test7_check_log_in_with_wrong_pin(self):
        program = TestedProgram()
        program.start(*self.args)

        output = program.execute("1")

        card_number_matcher = self.card_number_pattern.search(output)
        pin_matcher = self.pin_pattern.search(output)

        if not card_number_matcher or not pin_matcher:
            return CheckResult.wrong("You should output card number and PIN like in example")

        correct_card_number = card_number_matcher.group()
        correct_pin = pin_matcher.group()

        incorrect_pin = correct_pin

        while correct_pin == incorrect_pin:
            incorrect_pin = str(1000 + random.randint(0, 8999))

        program.execute("2")
        output = program.execute(correct_card_number + "\n" + incorrect_pin)

        if "successfully" in output.lower():
            return CheckResult.wrong("The user should not be signed in" +
                                     " after entering incorrect card information.")

        self.stop_and_check_if_user_program_was_stopped(program)
        return CheckResult.correct()

    @dynamic_test(time_limit=60000)
    def test8_check_log_in_to_not_existing_account(self):
        program = TestedProgram()
        program.start(*self.args)

        output = program.execute("1")

        card_number_matcher = self.card_number_pattern.search(output)
        pin_matcher = self.pin_pattern.search(output)

        if not card_number_matcher or not pin_matcher:
            return CheckResult.wrong("You should output card number and PIN like in example")

        correct_card_number = card_number_matcher.group()

        random.seed()

        correct_pin = pin_matcher.group().strip()
        incorrect_card_number = correct_card_number

        while correct_card_number == incorrect_card_number:
            incorrect_card_number = '400000' + str(100000000 + random.randint(0, 800000000))

        program.execute("2")
        output = program.execute(incorrect_card_number + "\n" + correct_pin)

        if "successfully" in output.lower():
            return CheckResult.wrong("The user should not be signed in" +
                                     " after entering incorrect card information.")

        self.stop_and_check_if_user_program_was_stopped(program)
        return CheckResult.correct()

    @dynamic_test(time_limit=60000)
    def test9_check_balance(self):
        program = TestedProgram()
        program.start(*self.args)

        output = program.execute("1")

        card_number_matcher = self.card_number_pattern.search(output)
        pin_matcher = self.pin_pattern.search(output)

        if not card_number_matcher or not pin_matcher:
            return CheckResult.wrong("You should output card number and PIN like in example")

        correct_pin = pin_matcher.group().strip()
        correct_card_number = card_number_matcher.group()

        program.execute("2")
        program.execute(correct_card_number + "\n" + correct_pin)

        output = program.execute("1")

        if "0" not in output:
            return CheckResult.wrong("Expected balance: 0")

        self.stop_and_check_if_user_program_was_stopped(program)
        return CheckResult.correct()

    @staticmethod
    def get_connection():
        if SimpleBankSystemTest.connection is None:
            SimpleBankSystemTest.connection = sqlite3.connect(SimpleBankSystemTest.database_file_name)
        return SimpleBankSystemTest.connection

    @staticmethod
    def close_connection():
        if SimpleBankSystemTest.connection is not None:
            SimpleBankSystemTest.connection.close()
            SimpleBankSystemTest.connection = None

    @staticmethod
    def create_temp_database():
        SimpleBankSystemTest.close_connection()

        if os.path.exists(SimpleBankSystemTest.database_file_name):
            if os.path.exists(SimpleBankSystemTest.temp_database_file_name):
                os.remove(SimpleBankSystemTest.temp_database_file_name)
            shutil.move(SimpleBankSystemTest.database_file_name, SimpleBankSystemTest.temp_database_file_name)

    @staticmethod
    def delete_temp_database():
        SimpleBankSystemTest.close_connection()

        if os.path.exists(SimpleBankSystemTest.temp_database_file_name):
            if os.path.exists(SimpleBankSystemTest.database_file_name):
                os.remove(SimpleBankSystemTest.database_file_name)
            shutil.move(SimpleBankSystemTest.temp_database_file_name, SimpleBankSystemTest.database_file_name)

    def get_data(self, out):
        card_number_matcher = self.card_number_pattern.search(out)
        pin_matcher = self.pin_pattern.search(out)

        if not card_number_matcher or not pin_matcher:
            return False

        number = card_number_matcher.group()
        PIN = pin_matcher.group()

        if not self.check_luhn_algorithm(number):
            return False

        self.correct_data[number] = PIN

        return True

    @staticmethod
    def check_luhn_algorithm(card_number):
        result = 0
        for i in range(len(card_number)):
            digit = int(card_number[i])
            if i % 2 == 0:
                double_digit = digit * 2 if digit * 2 <= 9 else digit * 2 - 9
                result += double_digit
                continue
            result += digit
        return result % 10 == 0

    def delete_all_rows(self):
        try:
            cursor = self.get_connection().cursor()
            cursor.execute(f"DELETE FROM {self.table_name};")
            self.close_connection()
        except sqlite3.Error:
            raise Exception("Can't execute a query in your database! Make sure that your database isn't broken "
                            "and you close your connection at the end of the program!")

    @staticmethod
    def stop_and_check_if_user_program_was_stopped(program):
        program.execute("0")
        if not program.is_finished():
            raise Exception("After choosing 'Exit' item you should stop your program and close database connection!")


if __name__ == '__main__':
    SimpleBankSystemTest().run_tests()
