import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt

# Setzen Sie die verwendeten GPIO-Pins entsprechend Ihren Verbindungen für die Motor A-Seite
IN1 = 17
IN2 = 18
ENABLE_A = 12

# Setzen Sie die verwendeten GPIO-Pins entsprechend Ihren Verbindungen für die Motor B-Seite
IN3 = 23
IN4 = 24
ENABLE_B = 25

# Initialisieren Sie die GPIO-Bibliothek
GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENABLE_A, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)
GPIO.setup(ENABLE_B, GPIO.OUT)

# PWM-Frequenz (Hz) und Anfangsgeschwindigkeit (0% bis 100%)
PWM_FREQ = 1000
INITIAL_SPEED = 100

# Erstellt PWM-Objekte für die GPIO-Pins der A-Seite
pwm_in1 = GPIO.PWM(IN1, PWM_FREQ)
pwm_in2 = GPIO.PWM(IN2, PWM_FREQ)
pwm_enable_a = GPIO.PWM(ENABLE_A, PWM_FREQ)

# Erstellt PWM-Objekte für die GPIO-Pins der B-Seite
pwm_in3 = GPIO.PWM(IN3, PWM_FREQ)
pwm_in4 = GPIO.PWM(IN4, PWM_FREQ)
pwm_enable_b = GPIO.PWM(ENABLE_B, PWM_FREQ)

# Funktion zum Vorwärtsfahren des Motors auf der Motor A-Seite
def motor_a_forward(speed):
    pwm_in1.start(speed)
    pwm_in2.start(0)
    pwm_enable_a.start(speed)

# Funktion zum Rückwärtsfahren des Motors auf der Motor A-Seite
def motor_a_backward(speed):
    pwm_in1.start(0)
    pwm_in2.start(speed)
    pwm_enable_a.start(speed)

# Funktion zum Stoppen des Motors auf der Motor A-Seite
def motor_a_stop():
    pwm_in1.start(0)
    pwm_in2.start(0)
    pwm_enable_a.start(0)

# Funktion zum Vorwärtsfahren des Motors auf der Motor B-Seite
def motor_b_forward(speed):
    pwm_in3.start(speed)
    pwm_in4.start(0)
    pwm_enable_b.start(speed)

# Funktion zum Rückwärtsfahren des Motors auf der Motor B-Seite
def motor_b_backward(speed):
    pwm_in3.start(0)
    pwm_in4.start(speed)
    pwm_enable_b.start(speed)

# Funktion zum Stoppen des Motors auf der Motor B-Seite
def motor_b_stop():
    pwm_in3.start(0)
    pwm_in4.start(0)
    pwm_enable_b.start(0)

# Callback-Funktion, die aufgerufen wird, wenn eine MQTT-Nachricht empfangen wird
def on_message(client, userdata, message):
    command = message.payload.decode("utf-8")
    print("Empfangene Nachricht:", command)

    if command == "start_a":
        print("Motor A starten...")
        motor_a_forward(INITIAL_SPEED)
    elif command == "stop_a":
        print("Motor A stoppen...")
        motor_a_stop()
    elif command == "start_b":
        print("Motor B starten...")
        motor_b_forward(INITIAL_SPEED)
    elif command == "stop_b":
        print("Motor B stoppen...")
        motor_b_stop()
    elif command == "start_both":
        print("both")
        motor_b_forward(INITIAL_SPEED)
        motor_a_forward(INITIAL_SPEED)
    elif command == "stop_both":
        print("stop both")
        motor_a_stop()
        motor_b_stop()

# MQTT-Client erstellen
mqtt_client = mqtt.Client()
mqtt_client.connect("mqtt.eclipseprojects.io", 1883, 60)

# MQTT-Topic abonnieren
mqtt_client.subscribe("motor/control")

# Callback-Funktion für eingehende Nachrichten festlegen
mqtt_client.on_message = on_message

try:
    # MQTT-Client starten und auf eingehende Nachrichten warten
    mqtt_client.loop_start()

    while True:  # Endlosschleife
        time.sleep(0)

except KeyboardInterrupt:
    # Das Skript beenden, wenn Strg+C gedrückt wird
    motor_a_stop()
    motor_b_stop()
    pwm_in1.stop()
    pwm_in2.stop()
    pwm_in3.stop()
    pwm_in4.stop()
    pwm_enable_a.stop()
    pwm_enable_b.stop()
    GPIO.cleanup()
    mqtt_client.disconnect()
    mqtt_client.loop_stop()
