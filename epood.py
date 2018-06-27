import telebot
from telebot import types
import companiesdb
from firebase import firebase
import usersdb
import itemsdb
import dictionary
import redis
import os
from flask import jsonify
from flask import Flask
from flask import request
import requests
from random import randint
import re
import json
import datetime
from telebot.types import LabeledPrice
from telebot.types import ShippingOption

dict = dictionary.texts
db = usersdb.users
companies = companiesdb.companies
items = itemsdb.items
token = os.environ['TELEGRAM_TOKEN']
url = os.environ['FIREBASE_URL']
provider_token = os.environ['PROVIDER_TOKEN']
server = Flask(__name__)


global stage
bot = telebot.TeleBot(token)
fb = firebase.FirebaseApplication(url, None)

################################################################################################## Variables
hide = types.ReplyKeyboardRemove()

fb.patch("/items", items)
################################################################################################## Functions

def newBut(*args):
    mrkup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=True)
    buts = []
    for arg in args:
        but = types.KeyboardButton(arg)
        buts.append(but)
    mrkup.add(*buts)
    return mrkup

def newInlineUrl(*args):
    mrkup = types.InlineKeyboardMarkup(row_width=2)
    buts = []
    for arg1, arg2 in args:
        but = types.InlineKeyboardButton(text = arg1, url = arg2)
        buts.append(but)
    mrkup.add(*buts)
    return mrkup

def newInlineCallback(*args):
    mrkup = types.InlineKeyboardMarkup(row_width=2)
    buts = []
    for arg1, arg2 in args:
        but = types.InlineKeyboardButton(text = arg1, callback_data = arg2)
        buts.append(but)
    mrkup.add(*buts)
    return mrkup

def updateLocalDB():
    global db
    fb.patch("users/", {"212312312":"Test"})
    db = fb.get("users/", None)
    print("Database updated")

def sortAllByCategory():
    keys = list(items.keys())
    values = list(items.values())
    cats = []
    for i in range(0, len(items)):
        if values[i]["category"] in cats:
            print("Skipped "+str(keys[i]))
        else:
            cats.append(values[i]['category'])
    itemsdb.cats = cats


def sortCategories():

    itemkeys = list(items.keys())
    itemvalues = list(items.values())
    catlist = itemsdb.cats
    for s in range(0, len(catlist)):
        itemsdb.bycategory[str(catlist[s])] = {}
    for i in range(0, len(catlist)):
        for x in range(0, len(items)):
            if itemvalues[x]['category'] == catlist[i]:
                #itemsdb.bycategory[str(catlist[i])][str(itemkeys[x])] = items[x]
                itemsdb.bycategory[str(catlist[i])][str(itemkeys[x])] = itemvalues[x]

def categoryButtons():
    mrkup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=True)
    buts = []
    for i in range(0, len(itemsdb.cats)):
        but = types.KeyboardButton(itemsdb.cats[i])
        buts.append(but)
    homebut = types.KeyboardButton(dict["home"])
    buts.append(homebut)
    mrkup.add(*buts)
    return mrkup

def countryButtons():
    mrkup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=True)
    buts = []
    for i in range(0, len(companiesdb.countries)):
        but = types.KeyboardButton(companiesdb.countries[i])
        buts.append(but)
    mrkup.add(*buts)
    return mrkup

def itemInline(data, amount):
    print("Made an inline button with data "+data)
    linemarkup = types.InlineKeyboardMarkup(row_width=5)
    minusone = types.InlineKeyboardButton(text="➖", callback_data=str(data+";"+str(amount-1)))
    minusten = types.InlineKeyboardButton(text="➖10", callback_data=str(data+";"+str(amount-10)))
    amount1 = types.InlineKeyboardButton(text=str(amount), callback_data="AMOUNT")
    plusone = types.InlineKeyboardButton(text="➕", callback_data=str(data+";"+str(amount+1)))
    plusten = types.InlineKeyboardButton(text="➕10", callback_data=str(data+";"+str(amount+10)))
    tocart = types.InlineKeyboardButton(text="🛒 Add to cart 🛒", callback_data=data+","+str(amount)+";add")
    linemarkup.add( minusten, minusone, amount1, plusone, plusten)
    linemarkup.add(tocart)
    return linemarkup

def sort(dict, mes, step1):
    #ldb = db[str(mes.chat.id)]['step']
    step = step1
    keys = list(dict.keys())
    values = list(dict.values())

    for i in range(0, 2):
        if step < len(dict):

            bot.send_photo(mes.chat.id, values[step]['image'])
            bot.send_message(mes.chat.id, values[step]['name']+". "+values[step]['description']+". Price: "+values[step]['price']+"$", reply_markup = itemInline(str(keys[step]), 0))
            #db[str(mes.chat.id)]['browsing'][]
            step += 1
        elif step == len(dict) or len(dict) > step or len(dict) < 6 or len(dict) == 0 or len(dict) == 1:
            print("End of list")
            bot.send_message(mes.chat.id, "End of list!")
            setStage("MainMenu", mes)
            db[str(mes.chat.id)]['step'] = 0
            return
        else:
            print("done")
            setStage("MainMenu", mes)
            db[str(mes.chat.id)]['step'] = 0
            return
    if len(dict) - 5 <= step:
        print("should show more")
        db[str(mes.chat.id)]['step'] = step
        bot.send_message(mes.chat.id, "Show more?", reply_markup=newBut("Show more", "🛒 My cart", "🏠 Home"))

def findId(mes):
    whattoreturn = False
    for i in range(0, len(db)):
        if str(mes.chat.id) == list(db.keys())[i]:
            whattoreturn = True
    return whattoreturn

def calcTotal(mes):
    dict = db[str(mes.chat.id)]
    total = 0
    values = list(dict['cart'].values())
    for i in range(0, len(dict['cart'])):
        total += int(values[i]['price']) * int(values[i]['amount'])
    print("New total is "+str(total))
    return total

def patchCategory(mes):
    db[str(mes.chat.id)]['category'] = itemsdb.bycategory[mes.text]

def patchStage(mes, stage):
    db[str(mes.chat.id)]['stage'] = stage
    try:
        fb.patch("users/"+str(mes.chat.id), db[str(mes.chat.id)])
    except Exception as x:
        print(x)

    print("Patched user's stage")

def cartInlines(name, mes, num):
    amount = int(db[str(mes.chat.id)]['cart'][name]['amount'])
    mrkup = types.InlineKeyboardMarkup(row_width=10)
    x = types.InlineKeyboardButton("❌", callback_data=name+";delete"+"|CART")
    minusone = types.InlineKeyboardButton(text="➖", callback_data=str(name + ";" + str(amount - 1)+"|CART"))
    minusten = types.InlineKeyboardButton(text="➖10", callback_data=str(name + ";" + str(amount - 10)+"|CART"))
    amount1 = types.InlineKeyboardButton(text=str(amount), callback_data="AMOUNT")
    plusone = types.InlineKeyboardButton(text="➕", callback_data=str(name + ";" + str(amount + 1)+"|CART"))
    plusten = types.InlineKeyboardButton(text="➕10", callback_data=str(name + ";" + str(amount + 10)+"|CART"))
    mrkup.add(x, minusten, minusone, amount1, plusone, plusten)
    return mrkup

def getKeys(dict):
    keys = list(dict.keys())

    return keys

def setStage(stage, mes):

    if findId(mes) == True:
        patchStage(mes, stage)
    else:
        pass

    if stage == "firststart":
        newUser(mes)
        bot.send_message(mes.chat.id, "Welcome to {my_bot}! I don't know you yet, so let's register you as a new user!")
        bot.send_message(mes.chat.id, "Let's start by choosing your country?", reply_markup=countryButtons())
        setStage("registerCountry", mes)

    elif stage == "start":
        bot.send_message(mes.chat.id, "Welcome back, "+mes.from_user.first_name+"!")
        setStage("MainMenu", mes)

    elif stage == "registerCountry":
        db[str(mes.chat.id)]['stage'] = stage

    elif stage == "registerCompany":
        db[str(mes.chat.id)]['stage'] = stage
        d = db[str(mes.chat.id)]
        d['city'] = ''
        d['address'] = ''
        country = d['country']
        companies1 = []
        for i in range(0, len(companies[country]['companies'])):
            companies1.append(companies[country]['companies'][i])
        bot.send_message(mes.chat.id, "Choose your company. If you do not see your company, type    \"skip\" to enter your delivery address manually", reply_markup=newBut(*companies1))

    elif stage == "isCompany":
        bot.send_message(mes.chat.id, "Enter your city")
        bot.send_message(mes.chat.id, "If you order for your company, please tap \"Skip\". We'll choose your company in the next step", reply_markup=newBut("Skip"))
        db[str(mes.chat.id)]['stage'] = stage

    elif stage == "enterName":
        bot.send_message(mes.chat.id, "Enter your name")
        bot.send_message(mes.chat.id, "You can also enter Company's name if it is neccessary")
        db[str(mes.chat.id)]['stage'] = stage
    elif stage == "enterEmail":
        bot.send_message(mes.chat.id, "Please enter your e-mail address\nYou can be contacted either through it or your telephone number")
        db[str(mes.chat.id)]['stage'] = stage
    elif stage == "enterPhone":
        bot.send_message(mes.chat.id, "Please enter your phone number with your country code")
        db[str(mes.chat.id)]['stage'] = stage

    elif stage == "registerAddress":
        bot.send_message(mes.chat.id, "Enter delivery address. i.e. Pikk 52-1")
        db[str(mes.chat.id)]['stage'] = stage

    elif stage == "finishRegister":
        bot.send_message(mes.chat.id, "Is this information correct?")
        db[str(mes.chat.id)]['stage'] = stage
        if db[str(mes.chat.id)]['company'] == "":
            bot.send_message(mes.chat.id, db[str(mes.chat.id)]['fullname'] +"\n"+
                                    db[str(mes.chat.id)]['phone'] + "\n" +
                                    db[str(mes.chat.id)]['email'] + "\n" +
                                    db[str(mes.chat.id)]['address']+", "+
                                    db[str(mes.chat.id)]['city'] + ", " +
                                    db[str(mes.chat.id)]['country'], reply_markup=newBut("Yes", "No"))
        else:
            bot.send_message(mes.chat.id, db[str(mes.chat.id)]['fullname'] +"\n"+
                             db[str(mes.chat.id)]['company'] + ", " +
                             db[str(mes.chat.id)]['country'], reply_markup=newBut("Yes", "No"))

    elif stage == "payment":
        db[str(mes.chat.id)]['stage'] = stage
        bot.send_message(mes.chat.id, "Proceed to payment?", reply_markup=newBut("Pay", dict['home']))

    elif stage == "MainMenu":
        bot.send_message(mes.chat.id, "This is main menu. Choose what you would like to do:", reply_markup=newBut(dict["browse"], dict["orders"], dict["cart"], dict["settings"], dict["contact"]))
        print("Main menu")
        db[str(mes.chat.id)]['stage'] = stage
        saveUser(mes)

    elif stage == "browse":
        db[str(mes.chat.id)]['stage'] = stage
        bot.send_message(mes.chat.id, "Choose category:", reply_markup=categoryButtons())

    elif stage == "orders":

        db[str(mes.chat.id)]['stage'] = stage
        db[str(mes.chat.id)]['inlinestep'] = 0
        db[str(mes.chat.id)]['ordersmes'] = ""
        ordersid = bot.send_message(mes.chat.id, "Here are your recent orders:")
        db[str(mes.chat.id)]['ordersmes'] = ordersid.message_id
        makeOrderInlines(mes)

        bot.send_message(mes.chat.id, "Click Home to return home", reply_markup=newBut(dict['home']))

    elif stage == "cart":
        db[str(mes.chat.id)]['stage'] = stage
        if checkKey(db[str(mes.chat.id)], "cart") == True:

            if len(db[str(mes.chat.id)]['cart']) == 0 or len(db[str(mes.chat.id)]['cart']) is None:
                bot.send_message(mes.chat.id,
                                 "Your cart is empty! Add something that you would like to order and come back again!")
                setStage("MainMenu", mes)
            else:

                bot.send_message(mes.chat.id, "This is what's in your cart right now:")
                keys = list(db[str(mes.chat.id)]['cart'].keys())
                values = list(db[str(mes.chat.id)]['cart'].values())
                total = 0
                for i in range(0, len(db[str(mes.chat.id)]['cart'])):
                    #total += int(values[i]['price']) * int(values[i]['amount'])

                    total += int(values[i]['price']) * int(values[i]['amount'])
                    photoid = bot.send_photo(mes.chat.id, values[i]['image']).message_id
                    db[str(mes.chat.id)]['cart'][str(keys[i])]['imageid'] = photoid
                    bot.send_message(mes.chat.id, values[i]['name']+", "+values[i]['description']+". Price per piece: "+str(values[i]['price']+"$"), reply_markup=cartInlines(str(keys[i]), mes, values[i]['amount']))

                totalid = bot.send_message(mes.chat.id, "Total price: "+ str(total)+"$")
                if checkKey(db[str(mes.chat.id)], "cartinfo") == False:
                    db[str(mes.chat.id)]['cartinfo'] = {}
                db[str(mes.chat.id)]['cartinfo']["id"] = totalid.message_id
                db[str(mes.chat.id)]['cartinfo']['total'] = calcTotal(mes)

                saveUser(mes)
                bot.send_message(mes.chat.id, "Would you like to proceed to payment?", reply_markup=newBut("Order", "Clear cart",dict['home']))
        else:
            bot.send_message(mes.chat.id,
                             "Your cart is empty! Add something that you would like to order and come back again!")
            setStage("MainMenu", mes)

    elif stage == "settings":
        bot.send_message(mes.chat.id, "Would you like to complete the registration again and choose a new delivery address?")
        bot.send_message(mes.chat.id, "Your current delivery address looks like this:")
        db[str(mes.chat.id)]['stage'] = stage
        if db[str(mes.chat.id)]['company'] == "":
            bot.send_message(mes.chat.id, db[str(mes.chat.id)]['address'] + ", " +
                             db[str(mes.chat.id)]['city'] + ", " +
                             db[str(mes.chat.id)]['country'], reply_markup=newBut("Register again", dict["home"]))
        else:
            bot.send_message(mes.chat.id, db[str(mes.chat.id)]['company'] + ", " +
                             db[str(mes.chat.id)]['country'], reply_markup=newBut("Register again", dict["home"]))

        db[str(mes.chat.id)]['stage'] = stage

    elif stage == "contact":
        db[str(mes.chat.id)]['stage'] = stage
        bot.send_message(mes.chat.id, dict['contact1'], reply_markup=newBut(dict['home']))


def newUser(mes):
    id = mes.chat.id
    name = mes.from_user.first_name
    db[str(id)] = {}
    db1 = db[str(id)]
    db1['name'] = name
    db1['language'] = "english"
    db1['stage'] = ''
    db1['country'] = ''
    db1['city'] = ''
    db1['company'] = ''
    db1['address'] = ''
    db1['fullname'] = ''
    db1['orders'] = {}
    db1['cart'] = {}
    db1['step'] = 0
    db1['email'] = ""
    db1['phone'] = ""
    db1['inlinestep'] = 0
    db1['category'] = ""
    db1['orders'] = {}
    db1['browsing'] = {}
    db1['cartinfo'] = {}

def saveUser(mes):

    try:
        fb.patch("users/"+str(mes.chat.id), db[str(mes.chat.id)])
    except Exception as x:
        print("SOMETHING FAILED: "+str(x))
    print("Saved "+str(mes.chat.id)+" to database.")


def getStage(mes):
    return db[str(mes.chat.id)]['stage']

def makeOrderInlines(mes):
    udb = db[str(mes.chat.id)]
    step = udb['inlinestep']
    ordermes = udb['ordersmes']
    initstep = step

    mrkup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    keys = list(udb['orders'].keys())
    values = list(udb['orders'].values())
    print("Orders length: "+str(len(udb['orders'])))
    if step < len(udb['orders']):

        for i in range(0, 2):
            if step < len(udb['orders']):
                but = types.InlineKeyboardButton(text=str(keys[step]), callback_data="orders"+str(values[step]['id']))
                print("Added a button | step: "+str(step))
                buttons.append(but)
                step+=1
                if step > len(udb['orders']):
                    print("END")
                    step = len(udb['orders'])
            else:
                print("List ended")
    print("Current step: "+str(step))
    for i in range(0, len(buttons)):
        mrkup.add(buttons[i])
    #if step <

    plusminus = []

    if step > 2:
        plusminus.append(types.InlineKeyboardButton("<", callback_data="<"))

    if step == 2 or step + 2 <= len(udb['orders']) or len(udb['orders']) - step > 0:
        plusminus.append(types.InlineKeyboardButton(">",callback_data=">"))



    if len(plusminus) > 0:
        mrkup.add(*plusminus)


    bot.edit_message_reply_markup(mes.chat.id, udb['ordersmes'], reply_markup=mrkup)



    #return mrkup



def checkKey(dict, key):
    whattoreturn = False
    keys = list(dict.keys())
    for i in range(0, len(dict)):
        if str(key) == str(keys[i]):
            whattoreturn = True
    return whattoreturn
################################################################################################## Setup
updateLocalDB() # Updating local DB to improve performance
sortAllByCategory()
sortCategories()
################################################################################################## Listeners
prices = [LabeledPrice(label='Working Time Machine', amount=5750),
          LabeledPrice('Gift wrapping', 500)]

def makeLabeledPrices():
    things = []
    keys = list(items.keys())
    values = list(items.values())
    for i in range(0, len(items)):
        things.append(LabeledPrice(values[i]['name'], values[i]['price']*100 ))
    prices = things


shipping_options = [
    ShippingOption(id='instant', title='WorldWide Teleporter').add_price(LabeledPrice('Teleporter', 1000)),
    ShippingOption(id='pickup', title='Local pickup').add_price(LabeledPrice('Pickup', 300))]

@bot.message_handler(commands=['terms'])
def command_terms(message):
    bot.send_message(message.chat.id,
                     'Thank you for shopping with our bot!\n'
                     '1. If your order is not being delievered, go to /contacts and contact store owners. Include your order ID from \"My orders\" tab.\n'
                     '2. For any kind of questions, /contacts is the best way to solve a problem.\n')

def makePayment(mes, price):
    bot.send_message(mes.chat.id,
                     "Real cards won't work with me, no money will be debited from your account."
                     " Use this test card number to pay for your demo invoice: `4242 4242 4242 4242`"
                     "\n\nThis is your demo invoice:", parse_mode='Markdown', reply_markup=newBut(dict['home']))
    bot.send_invoice(mes.chat.id, title=mes.from_user.first_name+"'s Order",
                     description="Your order was listed above. You can return to check it or proceed.",
                     provider_token=provider_token,
                     currency='eur',
                     photo_url=None,
                     photo_height=None,  # !=0/None or picture won't be shown
                     photo_width=None,
                     photo_size=None,
                     is_flexible=False,  # True If you need to set up Shipping Fee
                     prices=price,
                     start_parameter='order-invoice',
                     invoice_payload=str(mes.chat.id))

@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):

    bot.answer_shipping_query(shipping_query.id, ok=True, shipping_options=shipping_options,
                              error_message='Oh, seems like our Dog couriers are having a lunch right now. Try again later!')

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")

@bot.message_handler(content_types=['successful_payment'])
def got_payment(mes):
    bot.send_message(mes.chat.id,
                     'Hoooooray! Thanks for payment! We will proceed your order for `{} {}` as fast as possible! '
                     'Stay in touch.\n\nUse /buy again to get a Time Machine for your friend!'.format(
                         mes.successful_payment.total_amount / 100, mes.successful_payment.currency),
                     parse_mode='Markdown')
    orderid = randint(1000000, 9999999)

    bot.send_message(mes.chat.id, "Your order ID is "+str(orderid))
    if "orders" not in db[str(mes.chat.id)]:
        db[str(mes.chat.id)]['orders'] = {}

    db[str(mes.chat.id)]['orders']['order'+str(orderid)] = db[str(mes.chat.id)]['cart'].copy()
    db[str(mes.chat.id)]['orders']['order' + str(orderid)]['date'] = datetime.datetime.now()
    db[str(mes.chat.id)]['orders']['order' + str(orderid)]['id'] = orderid
    db[str(mes.chat.id)].pop('cart')

    this = db[str(mes.chat.id)]['orders'].copy()
    fb.patch("users/"+str(mes.chat.id)+"/cart", None)
    fb.patch("users/"+str(mes.chat.id)+"/orders/order"+str(orderid), this["order"+str(orderid)])
    bot.send_message(mes.chat.id, "Your cart is now empty!", reply_markup=newBut(dict['home']))

@bot.message_handler(commands=["help"])
def handle_help(mes):
    help_commands = {"start":" Start / Restart bot",
                     "help":"Help page",
                     "settings":"Change address",}
    help_text = "The following commands are available: \n"
    for key in help_commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += help_commands[key] + "\n"
    bot.send_message(mes.chat.id, help_text)

@bot.message_handler(commands=['settings'])
def handle_settings(mes):
    setStage("settings", mes)

@bot.message_handler(commands=['go'])
def go(mes):
    userDB = db[str(mes.chat.id)]
    makePayment(mes,
                [LabeledPrice(label=mes.from_user.first_name + "'s order", amount=int(userDB['cartinfo']['total']))])

@bot.message_handler(commands=["start"])
def init_start(mes):
    findUser = fb.get("users/", str(mes.chat.id))
    if findUser is None:
        setStage("firststart", mes)
    else:
        setStage("start", mes)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    print(call.data)
    mes = call.message
    id = mes.chat.id
    data = str(call.data)
    if data[-5:] == "|CART":


        if str(call.data) != "AMOUNT":
            findName = data[:data.find(";")]
            findAction = data[data.find(";")+1:data.find("|")]
            #print("debug: " + str(int(findAction)))
            print("Name is found: |"+findName+"|")
            print("Action is found: |"+str(findAction)+"|")

            if findAction != "delete" and int(findAction) >= 0:                       ##### ADDING AMOUNT TO CART
                print("Tried to change amount")
                db[str(mes.chat.id)]['cart'][str(findName)]['amount'] = int(findAction)
                newInt = int(db[str(mes.chat.id)]['cart'][findName]['amount'])
                bot.edit_message_reply_markup(chat_id=id, message_id=mes.message_id, reply_markup=cartInlines(findName, mes, newInt))
                db[str(mes.chat.id)]['cartinfo']['total'] = calcTotal(mes)
                try:
                    bot.edit_message_text(chat_id=mes.chat.id, message_id=db[str(mes.chat.id)]['cartinfo']['id'], text="Total price: "+ str(db[str(mes.chat.id)]['cartinfo']['total'])+"$" )
                except Exception as x:
                    print(x)
                    bot.send_message(mes.chat.id, "Something went wrong: "+str(x))
                    bot.send_message(mes.chat.id, "If total price is wrong, try pushing + and then - until you believe it's correct.")
            elif findAction == "delete":
                print("Deleting "+findName)
                imageid = db[str(mes.chat.id)]['cart'][findName]['imageid']
                bot.delete_message(chat_id=mes.chat.id, message_id=imageid)
                db[str(mes.chat.id)]['cart'].pop(findName)
                bot.delete_message(chat_id=mes.chat.id, message_id=mes.message_id)
                saveUser(mes)
                db[str(mes.chat.id)]['cartinfo']['total'] = calcTotal(mes)
                bot.edit_message_text(chat_id=mes.chat.id, message_id=db[str(mes.chat.id)]['cartinfo']['id'],
                                      text="Total price: " + str(db[str(mes.chat.id)]['cartinfo']['total']) + "$")
                if len(db[str(mes.chat.id)]['cart']) == 0 or db[str(mes.chat.id)]['cart'] is None:
                    bot.send_message(mes.chat.id, "Cart is empty! Add something and then come back!")
                    setStage("MainMenu", mes)
                saveUser(mes)
            else:
                print("Something went wrong, returning")
                setStage("MainMenu", mes)
    elif data[data.find(";")+1:] != 'add' and str(call.data) != "AMOUNT" and data != "clear" and data != "skip" and data[:6] != "orders" and data != ">" and data != "<":
        print("Adding "+call.data)
        if int(data[data.find(";")+1:]) >= 0:
            bot.edit_message_reply_markup(chat_id=id, message_id=mes.message_id, reply_markup=itemInline(data[:data.find(";")], int(data[data.find(";")+1:])))

    elif str(data[data.find(";")+1:]) == "add" and int(data[data.find(",") + 1:data.find(";")]) > 0:
        itemName = str(data[:data.find(","):])
        amount = str(data[data.find(",") + 1:data.find(";")])
        if checkKey(db[str(mes.chat.id)], "cart") == False:
            db[str(mes.chat.id)]['cart'] = {}

        print("item name: "+str(itemName))
        db[str(mes.chat.id)]['cart'][itemName] = items[itemName]
        db[str(mes.chat.id)]['cart'][itemName]['amount'] = amount

        bot.send_message(mes.chat.id, items[itemName]['name'] + ", " + db[str(mes.chat.id)]['cart'][itemName]['amount']+" pcs. added to cart")
        print("User's cart: "+str(db[str(mes.chat.id)]['cart']))

    elif data[0:data.find("|")] == "CART":
        print("This is from cart")

            ################################################################ DIFFERENT INLINES #########################

    elif data == "clear":
        db[str(mes.chat.id)]['cart'] = {}
        bot.send_message(mes.chat.id, "Your cart is now empty!")
        setStage("MainMenu", mes)

    elif data == "skip":
        setStage("cart", mes)

    elif data[:6] == "orders" and isinstance(int(data[6:]), int) and data[6:] != "<" and data[6:] != ">":
        print("GOT PAST ordersNUM filter")
        itemsfororder = ""
        keys = list(db[str(mes.chat.id)]['orders']['order'+data[6:]].keys())
        values = list(db[str(mes.chat.id)]['orders']['order'+data[6:]].values())

        for i in range(0, len(db[str(mes.chat.id)]['orders']['order'+data[6:]])):
            if str(keys[i]) != "id" and str(keys[i]) != "date":
                print(db[str(mes.chat.id)]['orders']['order'+data[6:]])

                itemsfororder = \
                    str(itemsfororder) + \
                    str(values[i]['name'])+", "+ \
                    str(str(values[i]['amount']))+ " pcs."+\
                    "\n"
                # str(values[i]['amount'])+\
        itemsfororder = itemsfororder + "\nDate: "+str(db[str(mes.chat.id)]['orders']['order'+data[6:]]['date'])

        bot.send_message(mes.chat.id, "Order #"+str(data[6:])+"\n \nOrdered items: \n \n"+itemsfororder, reply_markup=newBut(dict['home']))
        print("Making more inlines")

    elif data[:6] == "orders" and data[6:] == "<" or data[6:] == ">" and 19 == 23:
        if data[6:] == "<":
            print("Switch step to -5 if possible")
            for i in range(0, 5):
                if db[str(mes.chat.id)]['inlinestep'] >= 0:
                    db[str(mes.chat.id)]['inlinestep'] -= 1
                    print("Step: "+str(db[str(mes.chat.id)]['inlinestep']))
                else:
                    print("Nope")

        elif data[6:] == ">":
            print("Switch step to +5 if possible")
            for i in range(0, 5):
                if db[str(mes.chat.id)]['inlinestep'] < len(db[str(mes.chat.id)]['orders']):
                    db[str(mes.chat.id)]['inlinestep'] += 1
                    print("Step: "+str(db[str(mes.chat.id)]['inlinestep']))
                else:
                    print("Nope")
        else:
            print("Not working right now")
            bot.send_message(mes.chat.id, "This function is being developed", reply_markup=newBut(dict['home']))


        saveUser(mes)

    elif data == ">":
        udb = db[str(id)]
        udb['inlinestep'] += 2
        print("Inlinestep: "+str(udb['inlinestep']))
        makeOrderInlines(mes)

    elif data == "<":
        udb = db[str(id)]
        udb['inlinestep'] = udb['inlinestep'] - 2
        print("Inlinestep: " + str(udb['inlinestep']))
        makeOrderInlines(mes)


@bot.message_handler(content_types=['text'])
def handle_Text(mes):


    findUser = mes.chat.id

    if str(findUser) in db:
        print("Found user..")
        userDB = db[str(mes.chat.id)]
        print("[" + mes.from_user.first_name+" | "+userDB['stage']+"]: " + mes.text)


        if getStage(mes) == 'registerCountry' or userDB['country'] == "":
            userDB['country'] = mes.text
            print("User "+mes.from_user.first_name+"'s country is set to "+mes.text)
            setStage("enterName", mes)

        elif getStage(mes) == "enterName" or userDB['fullname'] == "":
            userDB['fullname'] = mes.text
            print("User's new name: "+str(mes.text))
            setStage("enterPhone", mes)
        elif getStage(mes) == "enterPhone" or userDB['phone'] == "":
            userDB['phone'] = mes.text
            print("User's phone: "+str(mes.text))
            setStage("enterEmail", mes)
        elif getStage(mes) == "enterEmail" or userDB['email'] == "":
            userDB['email'] = mes.text
            print("User's email: "+str(mes.text))
            setStage("isCompany", mes)

        elif getStage(mes) == "isCompany" and mes.text == "Skip": ## CHOOSING A COMPANY
            setStage("registerCompany", mes)
            userDB['company'] = mes.text
            print("User " + mes.from_user.first_name + "'s company is set to " + mes.text)

        elif getStage(mes) == "isCompany" and mes.text != "Skip": ## ENTERING CITY NAME
            userDB['city'] = mes.text
            print("User " + mes.from_user.first_name + "'s city is set to " + mes.text)
            setStage('registerAddress', mes)

        elif getStage(mes) == "registerAddress":
            userDB['address'] = mes.text
            print("User " + mes.from_user.first_name + "'s address is set to " + mes.text)
            setStage("finishRegister", mes)

        elif getStage(mes) == "registerCompany" and mes.text != "skip":
            userDB['company'] = mes.text
            setStage("finishRegister", mes)

        elif getStage(mes) == "registerCompany" and mes.text == "skip":
            userDB['company'] = ""
            setStage("isCompany", mes)

        elif getStage(mes) == "finishRegister" and mes.text == "Yes":
            if str(mes.chat.id) in usersdb.backups:
                db[str(mes.chat.id)]['cart'] = usersdb.backups[str(mes.chat.id)]['cart']
            saveUser(mes)
            setStage("MainMenu", mes)

        elif getStage(mes) == "finishRegister" and mes.text == "No":
            print("Restart")
            setStage("firststart", mes)

        elif getStage(mes) == "settings" and mes.text == "Register again":
            print("Restart")
            usersdb.backups[str(mes.chat.id)] = db[str(mes.chat.id)]
            setStage("firststart", mes)

        elif getStage(mes) == "settings" and mes.text == dict["home"]:
            print("Settings cancelled by " + str(userDB))
            saveUser(mes)
            setStage("MainMenu", mes)

        elif mes.text == "Show more":
            sort(db[str(mes.chat.id)]['category'], mes, db[str(mes.chat.id)]['step'])

        elif mes.text == dict["settings"]:
            setStage("settings", mes)

        elif mes.text == dict["cart"]:
            setStage("cart", mes)

        elif mes.text == dict["home"] or mes.text == "Home" or mes.text == "home" or mes.text == "back":
            setStage("MainMenu", mes)

        elif mes.text == dict["browse"]:
            setStage("browse", mes)

        elif mes.text == dict['contact']:
            setStage("contact", mes)

        elif getStage(mes) == "browse" and mes.text in list(itemsdb.cats):
            sort(itemsdb.bycategory[mes.text], mes, 0)
            patchCategory(mes)

        elif getStage(mes) == "payment" and mes.text == "Pay":
            print("Trying to pay now!")

        elif mes.text == "Order" and getStage(mes) == "cart":
            print("This is what is in user's cart:")
            cart = db[str(mes.chat.id)]['cart']
            keys = list(cart.keys())
            values = list(cart.values())
            total = 0
            bot.send_message(mes.chat.id, "This is your order: ")
            text = ""
            for i in range(0, len(cart)):
                print(values[i]['name']+", "+str(values[i]['amount'])+" pcs, "+str(int(values[i]['price'])*int(values[i]['amount']))+"$")
                text = text + str(values[i]['name']+", "+str(values[i]['amount'])+" pcs, "+str(int(values[i]['price'])*int(values[i]['amount']))+"$"+"\n")
                total += int(values[i]['price'])*int(values[i]['amount'])
            bot.send_message(mes.chat.id, text)
            bot.send_message(mes.chat.id, "Price: "+str(total)+"$. Would you like to pick up the order yourself, or get it by delivery?", reply_markup=newBut("I'll pick up myself", "Delivery", dict['home']))

        elif mes.text == "I'll pick up myself" and getStage(mes) == "cart":
            bot.send_message(mes.chat.id, "Great! Address for pickup is "+ usersdb.owner_Info['Store_Name'] + ", " + usersdb.owner_Info['Storage_Address'])
            setStage("payment", mes)

        elif mes.text == "Delivery" and getStage(mes) == "cart":
            setStage("delivery", mes)
            if userDB['city'] == "":
                bot.send_message(mes.chat.id, "Is this a correct delivery address: "+userDB['company']+", "+userDB['country']+"?", reply_markup=newBut("Yes", "No", dict['home']))
            else:
                bot.send_message(mes.chat.id,
                                 "Is this a correct delivery address: " + userDB['address'] +", "+userDB['city'] + ", " + userDB[
                                     'country'] + "?", reply_markup=newBut("Yes", "No"))

        elif mes.text == "Yes" and getStage(mes) == "delivery":
            try:
                makePayment(mes, [LabeledPrice(label=mes.from_user.first_name+"'s order", amount=int(userDB['cartinfo']['total'])*100)]) ## Ask to pay it all :p
            except Exception as x:
                print(x)
                bot.send_message(mes.chat.id, "Some thing is wrong")
                if str(x).find("CURRENCY_TOTAL_AMOUNT_INVALID"):
                    bot.send_message(mes.chat.id, "Our payment provider or Telegram rules restrict you from paying this much amount of money. Please go to contact to visit our website")


        elif mes.text == "No" and getStage(mes) == "delivery":
            bot.send_message(mes.chat.id, "I'll redirect you to settings. Complete it and come to \"Cart\" again!")
            setStage("settings", mes)

        elif mes.text == "Clear cart" and getStage(mes) == "cart":
            bot.send_message(mes.chat.id, "Would you really like to clear your cart?", reply_markup=newInlineCallback(("Yes", "clear"), ("No", "skip")))

        elif mes.text == dict['orders']:
            if "orders" in userDB and len(userDB['orders']) > 0:
                setStage("orders", mes)
            else:
                bot.send_message(mes.chat.id, "Your order list is empty. Order something first!")
                setStage("MainMenu", mes)
        else:
            bot.send_message(mes.chat.id, "Unknown command. Use /help to see available commands")



    elif findId(mes) == False:
        setStage("firststart", mes)
################################################################################################## END



@server.route('/' + token, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://ehitusepood.herokuapp.com/' + token)
    return "!", 200


if __name__ == "__main__":
    try:
        server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
    except Exception as x:
        print(x)
