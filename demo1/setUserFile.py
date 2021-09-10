# Ask repeatedly until the user answers 'y' or 'n'.
while True:
    answer = input("Have you been here before? (y/n) ")
    if answer == 'Y' or answer == 'y':
        been_here_before = True
        break
    elif answer == 'N' or answer == 'n':
        been_here_before = False
        break
    else:
        print("Enter 'y' or 'n'.")

if been_here_before:
    # Read username and password from a file.
    with open('userinfo.txt', 'r') as f:
        username = f.readline().rstrip('\n')
        password = f.readline().rstrip('\n')

    if input("Username: ") != username:
        print("Wrong username!")
    elif input("Password: ") != password:
        print("Wrong password!")
    else:
        print("Correct username and password, welcome!")

else:
    # Write username and password to a file.
    username = input("Username: ")
    password = input("Password: ")
    with open('userinfo.txt', 'w') as f:
        print(username, file=f)
        print(password, file=f)

    print("Done! Now run this program again and select 'y'.")