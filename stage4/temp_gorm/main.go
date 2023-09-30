package main

import (
	"fmt"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"log"
	"math/rand"
	"strconv"
	"strings"
)

type Card struct {
	ID      int `gorm:"primaryKey"`
	Number  string
	PIN     string
	Balance int
}

func (Card) TableName() string {
	return "card"
}

type BankingSystem struct {
	db *gorm.DB
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
	cardNumber := "400000" + fmt.Sprintf("%09d", rand.Intn(1000000000))
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

	b.db.Model(&card).Update("balance", gorm.Expr("balance + ?", income))
	b.db.Where("number = ? AND pin = ?", card.Number, card.PIN).First(&card)

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
	result := b.db.Where("number = ?", anotherCardNumber).First(&anotherCard)
	if result.Error != nil {
		fmt.Println("Such a card does not exist.")
		return
	}

	fmt.Println("Enter how much money you want to transfer:")
	var amount int
	fmt.Scanln(&amount)

	if card.Balance < amount {
		fmt.Println("Not enough money!")
		return
	}

	err := b.db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Model(&card).Update("balance", gorm.Expr("balance - ?", amount)).Error; err != nil {
			return err
		}
		if err := tx.Model(&anotherCard).Update("balance", gorm.Expr("balance + ?", amount)).Error; err != nil {
			return err
		}
		tx.Where("number = ? AND pin = ?", card.Number, card.PIN).First(&card)
		fmt.Println("Success!")
		return nil
	})
	if err != nil {
		log.Fatal(err)
	}
}

func (b *BankingSystem) createAccount() {
	card := Card{
		Number:  b.generateCardNumber(),
		PIN:     fmt.Sprintf("%04d", rand.Intn(10000)),
		Balance: 0,
	}

	result := b.db.Create(&card)
	if result.Error != nil {
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
	result := b.db.Delete(&card)
	if result.Error != nil {
		log.Fatal(result.Error)
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
	result := b.db.Where("number = ? AND pin = ?", number, pin).First(&card)

	if result.Error != nil {
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

func (b *BankingSystem) start() {
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
	db, err := gorm.Open(sqlite.Open("card.s3db"), &gorm.Config{})
	if err != nil {
		log.Fatal(err)
	}

	err = db.AutoMigrate(&Card{})
	if err != nil {
		log.Fatal(err)
	}

	bankingSystem := &BankingSystem{db: db}
	bankingSystem.start()
}
