#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import json
import time
import telebot
import threading


cerboserial = "123456789"# Ist auch gleich VRM Portal ID
bottoken = "xxxx:xxxx"
pvgruppenid = "-xxxx"
acpower = 1
dcpower = 1
L1=1
L2=2
L3=3
pvgesamt=0
Fehler=""
akkuladen=1
se=1
ve=1
akku=1
grid=1337
hausverbrauch =1
akkuladen=1
akkuspg=1
zaehler=0
num=0
neuaufbau=1
lintgrid = 2
nintgrid = 0
strintgrid = "0"
bot = telebot.TeleBot(bottoken, parse_mode=None)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("$SYS/#")
    client.subscribe("N/" + cerboserial + "/system/0/Ac/ConsumptionOnOutput/L1/Power")
    client.subscribe("N/" + cerboserial + "/system/0/Ac/ConsumptionOnOutput/L2/Power")
    client.subscribe("N/" + cerboserial + "/system/0/Ac/ConsumptionOnOutput/L3/Power")
    client.subscribe("N/" + cerboserial + "/system/0/Dc/Pv/Power")
    client.subscribe("N/" + cerboserial + "/vebus/276/Soc")
    client.subscribe("N/" + cerboserial + "/vebus/276/Ac/ActiveIn/P")
    client.subscribe("N/" + cerboserial + "/pvinverter/20/Ac/Power")
    client.subscribe("N/" + cerboserial + "/system/0/Dc/Battery/Power")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):

    try:

        global acpower,dcpower,pvgesamt,se,ve,akku, grid, hausverbrauch, akkuladen, akkuspg, zaehler, L1, L2, L3, Fehler
        # print(msg.topic+" "+str(msg.payload))
        if msg.topic == "N/" + cerboserial + "/pvinverter/20/Ac/Power":# AC PV Generation

            acpower = json.loads(msg.payload)
            acpower = int(acpower['value'])

        if msg.topic == "N/" + cerboserial + "/system/0/Dc/Pv/Power":# DC PV Generation

            dcpower = json.loads(msg.payload)
            dcpower=int(dcpower['value'])

        if msg.topic == "N/" + cerboserial + "/vebus/276/Soc":# Akkuprozent

            akku = json.loads(msg.payload)
            akku=float(akku['value'])

        if msg.topic == "N/" + cerboserial + "/system/0/Ac/ConsumptionOnOutput/L1/Power":# L1

            L1 = json.loads(msg.payload)
            L1=int(L1['value'])

        if msg.topic == "N/" + cerboserial + "/system/0/Ac/ConsumptionOnOutput/L2/Power":# L2

            L2 = json.loads(msg.payload)
            L2=int(L2['value'])

        if msg.topic == "N/" + cerboserial + "/system/0/Ac/ConsumptionOnOutput/L3/Power":# L3

            L3 = json.loads(msg.payload)
            L3=int(L3['value'])

        if msg.topic == "N/" + cerboserial + "/vebus/276/Ac/ActiveIn/P":#grid

            grid = json.loads(msg.payload)
            grid = int(grid['value'])
            grid = grid /1000

        if msg.topic == "N/" + cerboserial + "/system/0/Dc/Battery/Power":# Akkuladen

            akkuladen = json.loads(msg.payload)
            akkuladen=int(akkuladen['value'])
            akkuladen = akkuladen /1000

        # print(acpower)
        # print(dcpower)
        zaehler = zaehler+1
        pvgesamt = acpower + dcpower
        hausverbrauch = (L1+L2+L3)/1000
    except:
        print("Irgendwas ist hier ziemlich schief gelaufen")


client = mqtt.Client("TelegrambotPV")
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.1.167", 1883, 60)
client.loop_start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, Wie gehts?")

@bot.message_handler(commands=['help', "befehle"])
def help(message):
    bot.reply_to(message,
        "Befehle sind\n"
        "/pv : Zeigt PV-Generation an\n"
        "/soc : Zeigt den aktuellen Akkustand an\n"
        "/hausverbrauch: Zeigt den aktuellen Hausverbrauch an\n"
        "/netz: Zeigt W aus dem Netz an\n"
        "/alles: Zeigt eine ??bersicht aller Werte\n"
        "/wieviele : Zeigt eine grobe Einsch??tzung wieviele Ger??te bei aktueller Produktion eingeschaltet werden k??nnen")

@bot.message_handler(commands=['pv'])
def send_pv(message):
    bot.reply_to(message, "Aktuelle PV Leistung: "+str(pvgesamt).replace('.',',')+"W")

@bot.message_handler(commands=['soc'])
def send_soc(message):
    bot.reply_to(message, "Aktueller SOC: "+str(akku).replace('.',',')+"%")

@bot.message_handler(commands=['hausverbrauch'])
def send_hausverbrauch(message):
    bot.reply_to(message, "Aktueller Verbrauch im Haus "+str(hausverbrauch).replace('.',',')+"kWh")

@bot.message_handler(commands=['netz'])
def netz(message):
    if grid >= 0:
        beziehenexport = " beziehen "
    else:
        beziehenexport = " exportieren "

    bot.reply_to(message, "Wir " +beziehenexport + str(grid).replace('.',',').replace("-","") +"kWh aus dem Netz.")

@bot.message_handler(commands=['alles'])
def send_alles(message):
    if strintgrid == "0":
        aa = "Das bedeutet, dass am besten kein Ger??t mehr zugeschaltet werden sollte!\n"
    else:
        aa = "Das bedeutet, dass etwa noch " + strintgrid + " Ger??te eingeschaltet werden k??nnen\n"
    if grid >= 0:
        bb= "Wir beziehen "+str(grid).replace('.',',')+"kWh aus dem Netz.\n\n"
    else:
        bb ="Wir exprotieren "+str(grid).replace('.',',').replace('-','')+"kWh zum Netz.\n\n"
    bot.reply_to(message,
    "Aktuelle PV Leistung: "+str(pvgesamt).replace('.',',')+"W\n"
    "Aktueller SOC: "+str(akku).replace('.',',')+"%\n"
    "Aktueller Verbrauch im Haus "+str(hausverbrauch).replace('.',',')+"kWh\n" + bb + aa

    )

@bot.message_handler(commands=['wieviele'])
def send_wieviel(message):
    if strintgrid == "0":
        bot.reply_to(message, "Bitte kein Ger??t mehr einschalten")
    elif strintgrid == "1":
        bot.reply_to(message, "Es kann noch ein Ger??t eingeschaltet werden")
    else:
        bot.reply_to(message, "Es k??nnen noch " + strintgrid + " Ger??te eingeschaltet werden")


@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, "Nicht unterst??tze Aktion! Petra? :D")

pollingthread = threading.Thread(target=bot.polling)
pollingthread.start()
print(str(grid) + "Grid")
try:
    while (True):
        time.sleep(10)
        try:

            neuaufbau = neuaufbau + 1
            print(neuaufbau)
            print("Telegrambot l??uft")
            intgrid = int(grid)
            print(intgrid, lintgrid, nintgrid)
            if akku > 70 and intgrid < 0:
                if intgrid != lintgrid:
                    lintgrid = intgrid
                    nintgrid = intgrid * -1
                    strintgrid = str(nintgrid)
                    if strintgrid == "0":
                        print("Bitte kein Ger??t mehr einschalten")
                        bot.send_message(pvgruppenid, "Bitte kein Ger??t mehr einschalten, wir exportieren nicht mehr!")
                    elif strintgrid == "1":
                        bot.send_message(pvgruppenid, "Wir speisen ein! Es kann noch ein Ger??t eingeschalten werden")
                    else:
                        bot.send_message(pvgruppenid, "Wir speisen ein! Es k??nnen noch " + strintgrid + " Ger??te eingeschalten werden")
            else:
                if lintgrid != 0:
                    lintgrid = 0
                    print("Bitte kein Ger??t mehr einschalten")
                    bot.send_message(pvgruppenid, "Bitte kein Ger??t mehr einschalten")
            time.sleep(900)

        except KeyboardInterrupt:
            print("STRG+C erkannt - beende")
            break
        except Exception as e:
            print("Irgendwas ist in der whileschleife schief gelaufen ;( ")
            print(e)

    client.loop_stop()

# deal with ^C
except KeyboardInterrupt:
    print("\ninterrupted!")
    client.loop_stop()

except Exception as e:
    print("Hier ist was schief gelaufen")
    print(e)