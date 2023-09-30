package main

import (
	"fmt"
	"github.com/jmoiron/sqlx"
	_ "github.com/mattn/go-sqlite3"
	"log"
	"math/rand"
	"strconv"
	"strings"
	"time"
)

type Card struct {
	ID      int    `db:"id"`
	Number  string `db:"number"`
	PIN     string `db:"pin"`
	Balance int    `db:"balance"`
}

type BankingService struct {
	db *sqlx.DB
}

func (b *BankingService) generateLuhnChecksum(cardNumber string) string {
	digits := strings.Split(cardNumber, "")
	var checksum int
	for i, digit := range digits {
		d, _ := strconv.Atoi(digit)
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

func (b *BankingService) generateCardNumber() string {
	cardNumber := "400000" + fmt.Sprintf("%09d", rand.Intn(999999999))
	cardNumber += b.generateLuhnChecksum(cardNumber)
	return cardNumber
}

func (b *BankingService) initialize() {
	_, _ = b.db.Exec(`CREATE TABLE IF NOT EXISTS card (
    id INTEGER PRIMARY KEY,
    number TEXT,
    pin TEXT,
    balance INTEGER DEFAULT 0
    )`)
}

func (b *BankingService) run() {
	b.initialize()

	for {
		fmt.Println("1. Create an account\n2. Log into account\n0. Exit")
		var choice int
		_, _ = fmt.Scan(&choice)

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

func (b *BankingService) createAccount() {
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

func (b *BankingService) login() {
	fmt.Println("Enter your card number:")
	var number string
	_, _ = fmt.Scan(&number)

	fmt.Println("Enter your PIN:")
	var pin string
	_, _ = fmt.Scan(&pin)

	var card Card
	err := b.db.Get(&card, "SELECT * FROM card WHERE number = ? AND pin = ?", number, pin)

	if err != nil {
		fmt.Println("Wrong card number or PIN!")
		return
	}

	fmt.Println("You have successfully logged in!")
	b.accountOperations(&card)
}

func (b *BankingService) accountOperations(card *Card) {
	for {
		fmt.Println("1. Balance\n2. Add income\n3. Do transfer\n4. Close account\n5. Log out\n0. Exit")
		var innerChoice int
		_, _ = fmt.Scan(&innerChoice)

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

func (b *BankingService) checkBalance(card *Card) {
	fmt.Println("Balance:", card.Balance)
}

func (b *BankingService) addIncome(card *Card) {
	fmt.Println("Enter income:")
	var income int
	_, _ = fmt.Scan(&income)
	_, _ = b.db.Exec("UPDATE card SET balance = balance + ? WHERE number = ?", income, card.Number)
	fmt.Println("Income was added!")
}

func (b *BankingService) transfer(card *Card) {
	fmt.Println("Enter card number:")
	var anotherCardNumber string
	_, _ = fmt.Scan(&anotherCardNumber)
	if card.Number == anotherCardNumber {
		fmt.Println("You can't transfer money to the same account!")
		return
	}

	if anotherCardNumber[len(anotherCardNumber)-1:] != b.generateLuhnChecksum(anotherCardNumber[:len(anotherCardNumber)-1]) {
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
	_, _ = fmt.Scan(&amount)

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

func (b *BankingService) closeAccount(card *Card) {
	_, _ = b.db.Exec("DELETE FROM card WHERE number = ? AND pin = ?", card.Number, card.PIN)
	fmt.Println("The account has been closed!")
}

func main() {
	rand.New(rand.NewSource(time.Now().UnixNano()))
	db, _ := sqlx.Connect("sqlite3", "card.s3db")
	defer db.Close()
	service := &BankingService{db: db}
	service.run()
}
