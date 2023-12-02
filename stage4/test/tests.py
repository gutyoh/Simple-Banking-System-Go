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
        try:
            os.remove(self.temp_database_file_name)
            os.remove(self.database_file_name)
        except FileNotFoundError:
            pass

        program = TestedProgram()
        program.start(*self.args)

        self.stop_and_check_if_user_program_was_stopped(program)

        file = os.path.exists(self.database_file_name)

        if not file:
            return CheckResult.wrong("You should create a database file named " + self.database_file_name + ". "
                                                                                                            "The file name should be taken from the command line arguments.\n"
                                                                                                            "The database file shouldn't be deleted after stopping the program!")

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

        table_names = []

        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type ='table' AND name NOT LIKE 'sqlite_%';")
            rows = cursor.fetchall()
            for row in rows:
                table_names.append(row['name'])
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

    #     @DynamicTest(timeLimit = 60000)
    #     CheckResult ttest10_checkAddIncome() {
    #
    #         deleteAllRows();
    #
    #         TestedProgram program = new TestedProgram();
    #         program.start(args);
    #
    #         String output = program.execute("1");
    #
    #         Matcher cardNumberMatcher = cardNumberPattern.matcher(output);
    #         Matcher pinMatcher = pinPattern.matcher(output);
    #
    #         if (!cardNumberMatcher.find() || !pinMatcher.find()) {
    #             return new CheckResult(false, "You should output card number and PIN like in example");
    #         }
    #
    #         String correctPin = pinMatcher.group().trim();
    #         String correctCardNumber = cardNumberMatcher.group();
    #
    #         program.execute("2");
    #         program.execute(correctCardNumber + "\n" + correctPin);
    #         program.execute("2\n10000");
    #         stopAndCheckIfUserProgramWasStopped(program);
    #
    #         int userBalance = getBalance(correctCardNumber);
    #         if (userBalance != 10000) {
    #             return CheckResult.wrong("Account balance int the database is wrong after adding income.\nExpected 10000");
    #         }
    #
    #         program = new TestedProgram();
    #         program.start(args);
    #
    #         program.execute("2");
    #         program.execute(correctCardNumber + "\n" + correctPin);
    #         program.execute("2\n15000");
    #         stopAndCheckIfUserProgramWasStopped(program);
    #
    #         userBalance = getBalance(correctCardNumber);
    #         if (userBalance != 25000) {
    #             return CheckResult.wrong("Account balance is wrong after adding income.\nExpected 25000");
    #         }
    #
    #         return CheckResult.correct();
    #     }

    dynamic_test(time_limit=60000)

    def test10_check_add_income(self):
        self.delete_all_rows()

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
        program.execute("2\n10000")
        self.stop_and_check_if_user_program_was_stopped(program)

        user_balance = self.get_balance(correct_card_number)
        if user_balance != 10000:
            return CheckResult.wrong("Account balance int the database is wrong after adding income.\nExpected 10000")

        program = TestedProgram()
        program.start(*self.args)

        program.execute("2")
        program.execute(correct_card_number + "\n" + correct_pin)
        program.execute("2\n15000")
        self.stop_and_check_if_user_program_was_stopped(program)

        user_balance = self.get_balance(correct_card_number)
        if user_balance != 25000:
            return CheckResult.wrong("Account balance is wrong after adding income.\nExpected 25000")

        return CheckResult.correct()

    #     @DynamicTest(timeLimit = 60000)
    #     CheckResult ttest11_checkTransfer() {
    #
    #         String incorrectCardNumber = "2000007269641764"; //Doesn't pass Luhn algorithm
    #         String notExistingCardNumber = "2000007269641768";
    #
    #         deleteAllRows();
    #
    #         TestedProgram program = new TestedProgram();
    #         program.start(args);
    #
    #         String output = program.execute("1");
    #
    #         Matcher cardNumberMatcher = cardNumberPattern.matcher(output);
    #
    #         if (!cardNumberMatcher.find()) {
    #             return new CheckResult(false, "Your program outputs card number " +
    #                     "wrong.\nCard number should look like 400000DDDDDDDDDD. Where D is some digit");
    #         }
    #
    #         String toTransferCardNumber = cardNumberMatcher.group();
    #
    #         output = program.execute("1");
    #
    #         cardNumberMatcher = cardNumberPattern.matcher(output);
    #         Matcher pinMatcher = pinPattern.matcher(output);
    #
    #         if (!cardNumberMatcher.find() || !pinMatcher.find()) {
    #             return new CheckResult(false, "You should output card number and PIN like in example");
    #         }
    #
    #         String correctPin = pinMatcher.group().trim();
    #         String correctCardNumber = cardNumberMatcher.group();
    #
    #         program.execute("2");
    #         program.execute(correctCardNumber + "\n" + correctPin);
    #         output = program.execute("3\n" + incorrectCardNumber);
    #
    #         if (!output.contains("mistake")) {
    #             return new CheckResult(false, "You should not allow to transfer " +
    #                     "to a card number that doesn't pass the Luhn algorithm.\n You should print " +
    #                     "'Probably you made mistake in the card number. Please try again!'");
    #         }
    #
    #         output = program.execute("3\n" + notExistingCardNumber);
    #
    #         if (!output.contains("exist")) {
    #             return new CheckResult(false, "You should not allow to transfer " +
    #                     "to a card number that does not exist.\nYou should print " +
    #                     "'Such a card does not exist.'");
    #         }
    #
    #         output = program.execute("3\n" + toTransferCardNumber + "\n100000");
    #         if (!output.toLowerCase().contains("not enough money")) {
    #             return new CheckResult(false, "You should not allow a transfer if " +
    #                     "there is not enough money in the account to complete it. You should print " +
    #                     "'Not enough money!'");
    #         }
    #
    #         program.execute("2\n20000\n3\n" + toTransferCardNumber + "\n10000");
    #
    #         stopAndCheckIfUserProgramWasStopped(program);
    #
    #         int correctBalanceForBothAccounts = 10000;
    #         int toTransferCardBalance = getBalance(toTransferCardNumber);
    #         int correctCardNumberBalance = getBalance(correctCardNumber);
    #
    #         if (toTransferCardBalance != correctBalanceForBothAccounts) {
    #             return new CheckResult(false, "Incorrect account balance of the card to which the transfer was made.");
    #         }
    #
    #         if (correctCardNumberBalance != correctBalanceForBothAccounts) {
    #             return new CheckResult(false, "Incorrect account balance of the card used to make the transfer.");
    #         }
    #
    #         return CheckResult.correct();
    #     }

    dynamic_test(time_limit=60000)

    def test11_check_transfer(self):
        incorrect_card_number = "2000007269641764"
        not_existing_card_number = "2000007269641768"

        self.delete_all_rows()

        program = TestedProgram()
        program.start(*self.args)

        output = program.execute("1")

        card_number_matcher = self.card_number_pattern.search(output)

        if not card_number_matcher:
            return CheckResult.wrong("Your program outputs card number " +
                                     "wrong.\nCard number should look like 400000DDDDDDDDDD. Where D is some digit")

        to_transfer_card_number = card_number_matcher.group()

        output = program.execute("1")

        card_number_matcher = self.card_number_pattern.search(output)
        pin_matcher = self.pin_pattern.search(output)

        if not card_number_matcher or not pin_matcher:
            return CheckResult.wrong("You should output card number and PIN like in example")

        correct_pin = pin_matcher.group().strip()
        correct_card_number = card_number_matcher.group()

        program.execute("2")
        program.execute(correct_card_number + "\n" + correct_pin)
        output = program.execute("3\n" + incorrect_card_number)

        if "mistake" not in output.lower():
            return CheckResult.wrong("You should not allow to transfer " +
                                     "to a card number that doesn't pass the Luhn algorithm.\n You should print " +
                                     "'Probably you made mistake in the card number. Please try again!'")

        output = program.execute("3\n" + not_existing_card_number)

        if "exist" not in output.lower():
            return CheckResult.wrong("You should not allow to transfer " +
                                     "to a card number that does not exist.\nYou should print " +
                                     "'Such a card does not exist.'")

        output = program.execute("3\n" + to_transfer_card_number + "\n100000")
        if "not enough money" not in output.lower():
            return CheckResult.wrong("You should not allow a transfer if " +
                                     "there is not enough money in the account to complete it. You should print " +
                                     "'Not enough money!'")

        program.execute("2\n20000\n3\n" + to_transfer_card_number + "\n10000")

        self.stop_and_check_if_user_program_was_stopped(program)

        correct_balance_for_both_accounts = 10000
        to_transfer_card_balance = self.get_balance(to_transfer_card_number)
        correct_card_number_balance = self.get_balance(correct_card_number)

        if to_transfer_card_balance != correct_balance_for_both_accounts:
            return CheckResult.wrong("Incorrect account balance of the card to which the transfer was made.")

        if correct_card_number_balance != correct_balance_for_both_accounts:
            return CheckResult.wrong("Incorrect account balance of the card used to make the transfer.")

        return CheckResult.correct()

    #     @DynamicTest(timeLimit = 60000)
    #     CheckResult ttest12_checkTransfer() {
    #
    #         deleteAllRows();
    #
    #         TestedProgram program = new TestedProgram();
    #         program.start(args);
    #
    #         String output = program.execute("1");
    #
    #         Matcher cardNumberMatcher = cardNumberPattern.matcher(output);
    #         Matcher pinMatcher = pinPattern.matcher(output);
    #
    #         if (!cardNumberMatcher.find() || !pinMatcher.find()) {
    #             return new CheckResult(false, "You should output card number and PIN like in example");
    #         }
    #
    #         String correctPin = pinMatcher.group().trim();
    #         String correctCardNumber = cardNumberMatcher.group();
    #
    #         program.execute("2\n" + correctCardNumber + "\n" + correctPin + "\n4");
    #
    #         stopAndCheckIfUserProgramWasStopped(program);
    #
    #         try {
    #             DatabaseMetaData dbm = getConnection().getMetaData();
    #             ResultSet tables = dbm.getColumns(null, null, tableName, "deleted_at");
    #             if (tables.next()) {
    #                 // The GORM `deleted_at` column exists, so use the query with the `deleted_at` condition
    #                 PreparedStatement statement = getConnection().prepareStatement("SELECT * FROM " + tableName + " where number = ? AND (deleted_at IS NULL OR deleted_at = '')");
    #                 statement.setString(1, correctCardNumber);
    #                 ResultSet resultSet = statement.executeQuery();
    #                 if (resultSet.next()) {
    #                     return new CheckResult(false, "After closing the account, the card should be deleted " +
    #                             "from the database.");
    #                 }
    #             } else {
    #                 // The GORM `deleted_at` column does NOT exist, so use a straightforward existence check
    #                 PreparedStatement statement = getConnection().prepareStatement("SELECT * FROM " + tableName + " where number = ?");
    #                 statement.setString(1, correctCardNumber);
    #                 ResultSet resultSet = statement.executeQuery();
    #                 if (resultSet.next()) {
    #                     return new CheckResult(false, "After closing the account, the card should be deleted " +
    #                             "from the database.");
    #                 }
    #             }
    #         } catch (SQLException e) {
    #             throw new WrongAnswer("Can't execute a query in your database! Make sure that your database isn't broken and you close your connection at the end of the program!");
    #         }
    #
    #         closeConnection();
    #         return CheckResult.correct();
    #     }

    @dynamic_test(time_limit=60000)
    def test12_check_transfer(self):
        self.delete_all_rows()

        program = TestedProgram()
        program.start(*self.args)

        output = program.execute("1")

        card_number_matcher = self.card_number_pattern.search(output)
        pin_matcher = self.pin_pattern.search(output)

        if not card_number_matcher or not pin_matcher:
            return CheckResult.wrong("You should output card number and PIN like in example")

        correct_pin = pin_matcher.group().strip()
        correct_card_number = card_number_matcher.group()

        program.execute("2\n" + correct_card_number + "\n" + correct_pin + "\n4")

        self.stop_and_check_if_user_program_was_stopped(program)

        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name});")
            columns = [column['name'].lower() for column in cursor.fetchall()]

            if 'deleted_at' in columns:
                # The GORM `deleted_at` column exists, so use the query with the `deleted_at` condition
                cursor.execute(
                    f"SELECT * FROM {self.table_name} where number = ? AND (deleted_at IS NULL OR deleted_at = '')",
                    (correct_card_number,))
            else:
                # The GORM `deleted_at` column does NOT exist, so use a straightforward existence check
                cursor.execute(f"SELECT * FROM {self.table_name} where number = ?",
                               (correct_card_number,))

            rows = cursor.fetchall()
            if rows:
                return CheckResult.wrong("After closing the account, the card should be deleted " +
                                         "from the database.")
        except sqlite3.Error:
            raise Exception("Can't execute a query in your database! Make sure that your database isn't broken "
                            "and you close your connection at the end of the program!")

        self.close_connection()
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

    @staticmethod
    def get_balance(card_number):
        try:
            conn = SimpleBankSystemTest.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {SimpleBankSystemTest.table_name} WHERE number = ?", (card_number,))
            row = cursor.fetchone()
            balance = row['balance']
            SimpleBankSystemTest.close_connection()
            return balance
        except sqlite3.Error:
            raise Exception("Can't execute a query in your database! Make sure that your database isn't broken "
                            "and you close your connection at the end of the program!")


if __name__ == '__main__':
    SimpleBankSystemTest().run_tests()
