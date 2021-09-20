# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
import time
from time import sleep

# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game
j = 0 # number of guesses
start_sec = 0 # time when btn_submit was pressed down
guess_num = 0 # The current number being guessed by the user
value = 1
# DEFINE THE PINS USED HERE
LED_value = [11, 13, 15]
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
buzzer = 33
p_l = None
p_b = None  
play = "Start"
eeprom = ES2EEPROMUtils.ES2EEPROM()
eeprom.clear(2048)
eeprom.populate_mock_scores()

# Print the game banner
def welcome():
    os.system('clear')
    print("  _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")


# Print the game menu
def menu():
    global end_of_game
    global value
    global j 
    global p_l
    global p_b
    global play
  
    end_of_game=False
    
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        play="Scores"
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
    elif option == "P":
        os.system('clear')
        play="Begin"
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        value = generate_number()
        while not end_of_game:
            pass
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")


def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    print("There are {} scores. Here are the top 3!".format(count))
    # print out the scores in the required format
    raw_data.sort(key=lambda x: x[1])
    top_three = 0
    while (top_three<3):
         print("{} - {} took {} guesses".format(top_three+1, raw_data[top_three][0], raw_data[top_three][1]))
         top_three+=1
   


# Setup Pins
def setup():
    global p_l
    global p_b
    # Setup board mode
    GPIO.setmode(GPIO.BOARD)
    
    GPIO.setup(LED_value, GPIO.OUT)
    GPIO.output(LED_value, False)
    # Setup regular GPIO
    GPIO.setup(LED_accuracy,GPIO.OUT)
    GPIO.setup(buzzer,GPIO.OUT)
    
   # GPIO.setup(volt,GPIO.OUT)
   # GPIO.setup(32,GPIO.OUT)
   # GPIO.output(12, 0)
    
    # Setup PWM channels
    
    p_b= GPIO.PWM(buzzer, 1)
    p_b.ChangeDutyCycle(0)
    p_l=GPIO.PWM(LED_accuracy, 1)
    p_l.ChangeDutyCycle(0)
    # Setup debouncing and callbacks
    GPIO.setup(btn_submit,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(btn_increase,GPIO.IN,pull_up_down=GPIO.PUD_UP)
      
    GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=100)
    GPIO.add_event_detect(btn_increase, GPIO.FALLING, callback=btn_increase_pressed, bouncetime=100)
    
    #GPIO.output(volt, 1)
   


# Load high scores
def fetch_scores():
    # get however many scores there are
    #score_count = None
    score_count = eeprom.read_byte(0)
    # Get the scores
    scores_array = []
    scores = []
    # convert the codes back to ascii
    for i in range(1, (score_count+1)):
        scores_array.append(eeprom.read_block(i,4)) 
        x=''
        for q in range(len(scores_array[i-1])):
            if q<3:
                x += chr(scores_array[i-1][q])
        scores.append([x,scores_array[i-1][3]])  
    
    # return back the results
    return score_count, scores


# Save high scores
def save_scores(new):
    score_num,sd = fetch_scores()
    score_num+=1
    #eeprom.clear(2048)
    eeprom.write_block(0, [5])
    
    sd.append(new)
    sd.sort(key=lambda x: x[1])
    data_to_write=[]
    for i, score in enumerate(sd):
        for letter in score[0]:
            data_to_write.append(ord(letter))
        data_to_write.append(score[1])
        eeprom.write_block(i+1, data_to_write)
    #eeprom.write_block(0,[score_num])
    
    # fetch scores
    # include new score
    # sort
    # update total amount of scores
    # write new scores
    


# Generate guess number
def generate_number():
    return random.randint(1, pow(2, 3)-1)

def re(org_str, index, rep):
    new_str = org_str
    if index < len(org_str):
       new_str = org_str[0:index] + rep + org_str[index + 1:]
    return new_str

# Increase button pressed
def btn_increase_pressed(channel):
    global guess_num
    global play
    if (GPIO.input(channel)==0 and play == "Begin"): # Pull up resistors are being used therefore logic one is its normal state
        global guess_num
        if(guess_num>=7):
            guess_num=1
        else:
            guess_num+=1
                     # Increase the value shown on the LEDs
    a=bin(guess_num).replace("0b","") # this converts the number to binary and ommits the "0b" from it
    a=a[::-1]
    l_num = '000'
    print("{}-is your guess".format(guess_num))
    for i in range(3):
        try:
          l_num = re(l_num,i,a[i])
        except IndexError:
          continue
    GPIO.output(LED_value, (int(a[0]),int(a[1]),int(a[2]))) # display the number being guessed through the LEDs
 # j to binary using
# You can choose to have a global variable store the user’s current guess,
# or just pull the value off the LEDs when a user makes a guess
    time.sleep(0.1)
    # Increase the value shown on the LEDs
    # You can choose to have a global variable store the user's current guess, 
    # or just pull the value off the LEDs when a user makes a guess
def start():
    global start_sec
    start_sec = time.time()

def stop():
    global start_sec
    return time.time() - start_sec   
    


# Guess button
def btn_guess_pressed(channel):
    global play
    global value
    global guess_num
    global end_of_game
    global j
    global start_sec
    
    start()
    
    w=0
    while GPIO.input(channel)==0:
        sleep(0.05)
    if (play== "Begin"):    
        t_pass=stop()
    
        s= value
        y =guess_num
        diff=abs(s-y)
        time_compare=2
    
    if (t_pass>=time_compare):
        #menu()
        #GPIO.cleanup()
        play = "Start"
        end_of_game=True
        j = 0
        start_sec =0
        guess_num=0
        p_l.ChangeDutyCycle(0)
        p_b.ChangeDutyCycle(0)   
        GPIO.output(LED_value, False)

    else:
        if (diff>0 and guess!=0):
            j+=1 # if the difference between the guess and the number is greater than zero
            accuracy_leds() # the the LEDs will be flashed and the buzzer will be sounded
            trigger_buzzer() 
            print("{}-is your guess".format(j))
        else:
            print("{}-is your guess".format(guess))
            #GPIO.cleanup()
            p_l.ChangeDutyCycle(0)
            p_b.ChangeDutyCycle(0)  
            GPIO.output(LED_value, False)
            print("Well done champion, you the winnnneerr!! Whooo ")
            print(value)
            name = input("Please enter your name: ")
            if (len(name)>3):
                name=name[0]+name[1]+name[2]             
            saves_scores([name,j])
            
            #menu()
            play="Start"
            j = 0
            start_sec =0
            guess_num=0            
            end_of_game=True
            #GPIO.cleanup()
    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    # Compare the actual value with the user value displayed on the LEDs
    # Change the PWM LED
    # if it's close enough, adjust the buzzer
    # if it's an exact guess:
    # - Disable LEDs and Buzzer
    # - tell the user and prompt them for a name
    # - fetch all the scores
    # - add the new score
    # - sort the scores
    # - Store the scores back to the EEPROM, being sure to update the score count
    


# LED Brightness
def accuracy_leds():
    global guess_num
    global value
    global p_l
    
    p_l.stop()
    a=value
    b=guess_num
    if (b>a):
        dutycycle = ((8-b)/(8-a))*100
    else:
        dutycycle = (b/a)*100
     
    p_l.ChangeDutyCycle(dutycycle)
    p_l.start(dutycycle)
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
   

# Sound Buzzer
def trigger_buzzer():
    global value
    global guess_num
    global p_b
    
    p_b.start(50)
    e=value
    c=guess_num
    difference=abs(e-c)
    if (difference==3):
        frequency=1
        p_b.ChangeFrequency(frequency)
    elif (difference==2):
        frequency=2
        p_b.ChangeFrequency(frequency)
    elif (difference==1):
        frequency=4
        p_b.ChangeFrequency(frequency)
    else:
        p_b.stop()
    # The buzzer operates differently from the LED
    # While we want the brightness of the LED to change(duty cycle), we want the frequency of the buzzer to change
    # The buzzer duty cycle should be left at 50%
    # If the user is off by an absolute value of 3, the buzzer should sound once every second
    # If the user is off by an absolute value of 2, the buzzer should sound twice every second
    # If the user is off by an absolute value of 1, the buzzer should sound 4 times a second


if __name__ == "__main__":
    try:
        # Call setup function
        setup()
        welcome()
        while True:
            menu()
            pass
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
