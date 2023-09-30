package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
)

func main() {
	definition := regexp.MustCompile(`^[a-z]+_to_[a-z]+$`)
	constant := regexp.MustCompile(`^-?[0-9]+(\.[0-9]+)?$`)

	scanner := bufio.NewScanner(os.Stdin)
	fmt.Println("Enter a definition:")
	text := scanner.Text()

	input := strings.Fields(strings.TrimSpace(text))

	if len(input) == 2 && definition.MatchString(input[0]) && constant.MatchString(input[1]) {
		fmt.Println("The definition is correct!")
	} else {
		fmt.Println("The definition is incorrect!")
	}
}
