package main

import (
	"fmt"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"log"
	"math/rand"
)

// DatabaseName is the name of the database file
const DatabaseName = "card.s3db"

// Main menu options
const (
	MainMenuCreateAccount = "1. Create an account"
	MainMenuLogin         = "2. Log into account"
	MenuExit              = "0. Exit"
)

// Account operations options
const (
	AccountOperationsBalance = "1. Balance"
	AccountOperationsLogout  = "2. Log out"
)

// Banking system prompts
const (
	CardNumberPrompt = "Enter your card number:"
	PINPrompt        = "Enter your PIN:"
)

// Banking system messages
const (
	WrongCredentialsMsg = "Wrong card number or PIN"
	WrongOptionMsg      = "Wrong option!"
	LoggedInMsg         = "You have successfully logged in!"
	LoggedOutMsg        = "You have successfully logged out!"
	GoodbyeMsg          = "Bye!"
	CardCreatedMsg      = "Your card has been created"
	CardNumberMsg       = "Your card number:\n%s\n"
	CardPINMsg          = "Your card PIN:\n%s\n\n"
	BalanceMsg          = "Balance: %d"
)

func luhnAlgorithm(number string) bool {
	sum := 0

	for i, char := range number {
		digit := int(char - '0')

		if (len(number)-i)%2 == 0 {
			digit *= 2
			if digit > 9 {
				digit -= 9
			}
		}

		sum += digit
	}

	return sum%10 == 0
}

func generateLuhnChecksum(number string) int {
	checksum := 0

	for i := 0; i <= 9; i++ {
		if luhnAlgorithm(number + fmt.Sprintf("%d", i)) {
			checksum = i
			break
		}
	}

	return checksum
}

type Card struct {
	// gorm.Model
	ID      uint   `gorm:"primaryKey"`
	Number  string `gorm:"unique;not null"`
	PIN     string
	Balance int `gorm:"default:0"`
}

func (Card) TableName() string {
	return "card"
}

type BankingSystem struct {
	db *gorm.DB
}

func (bs *BankingSystem) MainMenu() {
	for {
		fmt.Println(MainMenuCreateAccount)
		fmt.Println(MainMenuLogin)
		fmt.Println(MenuExit)

		var choice int
		fmt.Scanln(&choice)

		switch choice {
		case 1:
			bs.CreateAccount()
		case 2:
			bs.Login()
		case 0:
			fmt.Println("\n" + GoodbyeMsg)
			return
		default:
			fmt.Println(WrongOptionMsg)
		}
	}
}

func (bs *BankingSystem) CreateAccount() {
	cardNumber, pin := bs.GenerateCardAndPIN()
	card := Card{Number: cardNumber, PIN: pin}
	result := bs.db.Create(&card)
	if result.Error != nil {
		fmt.Printf("cannot create card: %v\n", result.Error)
		return
	}

	fmt.Println("\n" + CardCreatedMsg)
	fmt.Printf(CardNumberMsg, cardNumber)
	fmt.Printf(CardPINMsg, pin)
}

func (bs *BankingSystem) GenerateCardAndPIN() (string, string) {
	cardBase := "400000" + fmt.Sprintf("%09d", rand.Intn(1000000000))
	checksum := generateLuhnChecksum(cardBase)
	cardNumber := cardBase + fmt.Sprintf("%d", checksum)
	pin := fmt.Sprintf("%04d", rand.Intn(10000))
	return cardNumber, pin
}

func (bs *BankingSystem) Login() {
	fmt.Println("\n" + CardNumberPrompt)
	var cardNumber string
	fmt.Scanln(&cardNumber)

	fmt.Println(PINPrompt)
	var pin string
	fmt.Scanln(&pin)

	var card Card
	result := bs.db.Where("number = ? AND pin = ?", cardNumber, pin).First(&card)
	if result.Error != nil {
		fmt.Println("\n" + WrongCredentialsMsg)
		return
	}

	fmt.Println("\n" + LoggedInMsg)
	bs.AccountOperationsMenu()
}

func (bs *BankingSystem) AccountOperationsMenu() {
	for {
		fmt.Println("\n" + AccountOperationsBalance)
		fmt.Println(AccountOperationsLogout)
		fmt.Println(MenuExit)

		var choice int
		fmt.Scanln(&choice)

		switch choice {
		case 1:
			fmt.Printf("\n"+BalanceMsg+"\n", 0)
		case 2:
			fmt.Println("\n" + LoggedOutMsg)
			return
		case 0:
			return
		default:
			fmt.Println(WrongOptionMsg)
		}
	}
}

func NewBankingSystem(db *gorm.DB) (*BankingSystem, error) {
	if !db.Migrator().HasTable(&Card{}) {
		err := db.Migrator().CreateTable(&Card{})
		if err != nil {
			return nil, fmt.Errorf("failed to create cards table: %w", err)
		}
	}

	return &BankingSystem{
		db: db,
	}, nil
}

func main() {
	db, err := gorm.Open(sqlite.Open(DatabaseName), &gorm.Config{})
	if err != nil {
		log.Fatalf("failed to open %s: %v", DatabaseName, err)
	}

	bs, err := NewBankingSystem(db)
	if err != nil {
		log.Fatalf("failed to initialize the application: %v", err)
	}

	bs.MainMenu()
}
