import RPi.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define GPIO pin for the servo
SERVO_PIN = 18

# Setup GPIO pin as output
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Create PWM instance with 50Hz frequency
pwm = GPIO.PWM(SERVO_PIN, 50)

# Start PWM with a duty cycle of 0
pwm.start(0)

def set_angle(angle:int) -> None:
    """
    Set the angle of the servo motor.
    :param angle: Angle in degrees (0 to 180).
    """
    if 0 <= angle <= 180:
        # Convert angle to duty cycle
        duty = angle / 18 + 2
        # Set duty cycle to PWM
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.4)
        # Stop PWM
        pwm.ChangeDutyCycle(0)
    else:
        print("Invalid angle. Angle must be between 0 and 180.")

