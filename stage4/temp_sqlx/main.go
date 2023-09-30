package main

import (
	"fmt"
	"github.com/jmoiron/sqlx"
	_ "github.com/mattn/go-sqlite3"
	"log"
	"math/rand"
	"strconv"
	"strings"
)

type Card struct {
	ID      int    `db:"id"`
	Number  string `db:"number"`
	PIN     string `db:"pin"`
	Balance int    `db:"balance"`
}

type BankingSystem struct {
	db *sqlx.DB
}

func (b *BankingSystem) generateLuhnChecksum(cardNumber string) string {
	digits := strings.Split(cardNumber, "")
	var checksum int
	for i, digit := range digits {
		d, err := strconv.Atoi(digit)
		if err != nil {
			log.Fatal(err)
		}
		if i%2 == 0 {
			d *= 2
			if d > 9 {
				d -= 9
			}
		}
		checksum += d
	}
	checkDigit := (10 - (checksum % 10)) % 10
	return strconv.Itoa(checkDigit)
}

func (b *BankingSystem) generateCardNumber() string {
	cardNumber := "400000" + fmt.Sprintf("%09d", rand.Intn(999999999))
	cardNumber += b.generateLuhnChecksum(cardNumber)
	return cardNumber
}

func (*BankingSystem) checkBalance(card *Card) {
	fmt.Println("Balance:", card.Balance)
}

func (b *BankingSystem) addIncome(card *Card) {
	fmt.Println("Enter income:")
	var income int
	fmt.Scanln(&income)

	if _, err := b.db.Exec(
		"UPDATE card SET balance = balance + ? WHERE number = ?", income, card.Number); err != nil {
		log.Fatal(err)
	}
	fmt.Println("Income was added!")
}

func (b *BankingSystem) transfer(card *Card) {
	fmt.Println("Enter card number:")
	var anotherCardNumber string
	fmt.Scanln(&anotherCardNumber)

	if card.Number == anotherCardNumber {
		fmt.Println("You can't transfer money to the same account!")
		return
	}

	if anotherCardNumber[len(anotherCardNumber)-1:] !=
		b.generateLuhnChecksum(anotherCardNumber[:len(anotherCardNumber)-1]) {
		fmt.Println("Probably you made a mistake in the card number. Please try again!")
		return
	}

	var anotherCard Card
	err := b.db.Get(&anotherCard, "SELECT * FROM card WHERE number = ?", anotherCardNumber)
	if err != nil {
		fmt.Println("Such a card does not exist.")
		return
	}

	fmt.Println("Enter how much money you want to transfer:")
	var amount int
	_, _ = fmt.Scanln(&amount)

	tx, err := b.db.Beginx()
	if err != nil {
		log.Fatal(err)
	}

	err = b.db.Get(card, "SELECT * FROM card WHERE number = ?", card.Number)
	if err != nil {
		err := tx.Rollback()
		if err != nil {
			log.Fatal(err)
		}
		log.Fatal(err)
	}

	if card.Balance < amount {
		fmt.Println("Not enough money!")
		err := tx.Rollback()
		if err != nil {
			log.Fatal(err)
		}
		return
	}

	_, err = tx.Exec("UPDATE card SET balance = balance - ? WHERE number = ?", amount, card.Number)
	if err != nil {
		err := tx.Rollback()
		if err != nil {
			log.Fatal(err)
		}
		log.Fatal(err)
	}

	_, err = tx.Exec("UPDATE card SET balance = balance + ? WHERE number = ?", amount, anotherCardNumber)
	if err != nil {
		err := tx.Rollback()
		if err != nil {
			log.Fatal(err)
		}
		log.Fatal(err)
	}

	err = tx.Commit()
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("Success!")
}

func (b *BankingSystem) createAccount() {
	card := Card{
		Number:  b.generateCardNumber(),
		PIN:     fmt.Sprintf("%04d", rand.Intn(10000)),
		Balance: 0,
	}
	_, err := b.db.Exec("INSERT INTO card (number, pin, balance) VALUES (?, ?, ?)",
		card.Number, card.PIN, card.Balance)

	if err != nil {
		fmt.Println("Failed to create account!")
		return
	}

	fmt.Println("Your card has been created")
	fmt.Println("Your card number:")
	fmt.Println(card.Number)
	fmt.Println("Your card PIN:")
	fmt.Println(card.PIN)
}

func (b *BankingSystem) closeAccount(card *Card) {
	if _, err := b.db.Exec("DELETE FROM card WHERE number = ? AND pin = ?", card.Number, card.PIN); err != nil {
		log.Fatal(err)
	}
	fmt.Println("The account has been closed!")
}

func (b *BankingSystem) login() {
	fmt.Println("Enter your card number:")
	var number string
	fmt.Scanln(&number)

	fmt.Println("Enter your PIN:")
	var pin string
	fmt.Scanln(&pin)

	var card Card
	err := b.db.Get(&card, "SELECT * FROM card WHERE number = ? AND pin = ?", number, pin)
	if err != nil {
		fmt.Println("Wrong card number or PIN!")
		return
	}
	fmt.Println("You have successfully logged in!")
	b.accountOperations(&card)
}

func (b *BankingSystem) accountOperations(card *Card) {
	for {
		fmt.Println("1. Balance\n2. Add income\n3. Do transfer\n4. Close account\n5. Log out\n0. Exit")
		var innerChoice int
		fmt.Scanln(&innerChoice)

		switch innerChoice {
		case 1:
			b.checkBalance(card)
		case 2:
			b.addIncome(card)
		case 3:
			b.transfer(card)
		case 4:
			b.closeAccount(card)
			return
		case 5:
			fmt.Println("You have successfully logged out!")
			return
		case 0:
			return
		default:
			fmt.Println("Wrong option!")
		}
	}
}

func (b *BankingSystem) createCardTable() {
	if _, err := b.db.Exec(`CREATE TABLE IF NOT EXISTS card (
	id INTEGER PRIMARY KEY,
	number TEXT,
	pin TEXT,
	balance INTEGER DEFAULT 0
	)`); err != nil {
		log.Fatal(err)
	}
}

func (b *BankingSystem) start() {
	b.createCardTable()

	for {
		fmt.Println("1. Create an account\n2. Log into account\n0. Exit")
		var choice int
		fmt.Scanln(&choice)

		switch choice {
		case 1:
			b.createAccount()
		case 2:
			b.login()
		case 0:
			return
		default:
			fmt.Println("Wrong option!")
		}
	}
}

func main() {
	db, err := sqlx.Connect("sqlite3", "card.s3db")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	bankingSystem := &BankingSystem{db: db}
	bankingSystem.start()
}
