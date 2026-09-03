print ("Welcome to the mini personality quiz!")
while True:
    color = input ("What's your favorite color? (red, blue, green)")
    animal = input ("Pick an animal: (cat, dog, bird)")

    score = 0

    if color.lower() == "red":
        score += 2
    elif color.lower() == "blue":
        score += 1
    elif color.lower() == "green":
        score += 1

    if animal.lower() == "dog":
        score += 2
    elif animal.lower() == "cat":
        score += 1
    elif animal.lower() == "bird":
        score += 1

    if score >= 4:
        print("You're bold and energetic - a real go-getter!")
    elif score == 3:
        print("Calm but decisive. Balanced vibes.")
    else:
        print("Thoughtful and curious - you notice the little things.") 
        
    again = input("Wanna play again? (yes/no)").lower ()
    if again != "yes":
        print("Alright, thanks for playing!")
        break  