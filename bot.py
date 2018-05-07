import telebot
from telebot import types
import companiesdb
from firebase import firebase
import usersdb
import companiesdb
import itemsdb
import dictionary

dict = dictionary.texts
db = usersdb.users
companies = companiesdb.companies
items = itemsdb.items

token = "564926610:AAGreq0Fw3AqkLrTbVRzPUYDh1XdJWkrvD8"
bot = telebot.TeleBot(token)
url = "https://foralstuff.firebaseio.com/"
fb = firebase.FirebaseApplication(url, None)
global stage

################################################################################################## Variables
hide = types.ReplyKeyboardRemove()


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
    print("Database updated:")
    print(db)

def sortCategories():

    itemkeys = list(items.keys())
    itemvalues = list(items.values())
    catlist = itemsdb.categories
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
    for i in range(0, len(itemsdb.categories)):
        but = types.KeyboardButton(itemsdb.categories[i])
        buts.append(but)
    homebut = types.KeyboardButton(dict["home"])
    buts.append(homebut)
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
    print("Starting to sort with step "+str(step))
    for i in range(0, 2):
        if step < len(dict):

            bot.send_photo(mes.chat.id, values[i]['image'])
            print("Doing "+str(i)+" "+str(keys[i]))
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
    fb.patch("users/"+str(mes.chat.id), db[str(mes.chat.id)])
    print("Patched user's stage")

def cartInlines(name, mes, num):
    amount = int(db[str(mes.chat.id)]['cart'][name]['amount'])
    print("Made an inline for "+ str(name)+ " with amount "+str(amount))
    mrkup = types.InlineKeyboardMarkup(row_width=10)
    x = types.InlineKeyboardButton("❌", callback_data=name+";delete"+"|CART")
    minusone = types.InlineKeyboardButton(text="➖", callback_data=str(name + ";" + str(amount - 1)+"|CART"))
    minusten = types.InlineKeyboardButton(text="➖10", callback_data=str(name + ";" + str(amount - 10)+"|CART"))
    amount1 = types.InlineKeyboardButton(text=str(amount), callback_data="AMOUNT")
    plusone = types.InlineKeyboardButton(text="➕", callback_data=str(name + ";" + str(amount + 1)+"|CART"))
    plusten = types.InlineKeyboardButton(text="➕10", callback_data=str(name + ";" + str(amount + 10)+"|CART"))
    mrkup.add(x, minusten, minusone, amount1, plusone, plusten)
    return mrkup

def setStage(stage, mes):

    if findId(mes) == True:
        patchStage(mes, stage)
    else:
        pass

    if stage == "firststart":
        newUser(mes)
        bot.send_message(mes.chat.id, "Welcome to {my_bot}! I don't know you yet, so let's register you as a new user!")
        bot.send_message(mes.chat.id, "Let's start by choosing your country?", reply_markup=newBut("Estonia", "Finland"))
        #todo: Add to Firebase when testing is done
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
    elif stage == "registerAddress":
        bot.send_message(mes.chat.id, "Enter delivery address. i.e. Pikk 52-1")
        db[str(mes.chat.id)]['stage'] = stage
    elif stage == "finishRegister":
        bot.send_message(mes.chat.id, "Is this information correct?")
        db[str(mes.chat.id)]['stage'] = stage
        if db[str(mes.chat.id)]['company'] == "":
            bot.send_message(mes.chat.id, db[str(mes.chat.id)]['address']+", "+
                                      db[str(mes.chat.id)]['city'] + ", " +
                                      db[str(mes.chat.id)]['country'], reply_markup=newBut("Yes", "No"))
        else:
            bot.send_message(mes.chat.id, db[str(mes.chat.id)]['company'] + ", " +
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
        print("GOT TO BROWSE")
        db[str(mes.chat.id)]['stage'] = stage
        bot.send_message(mes.chat.id, "Choose category:", reply_markup=categoryButtons())

    elif stage == "orders":
        print()
        db[str(mes.chat.id)]['stage'] = stage

    elif stage == "cart":
        db[str(mes.chat.id)]['stage'] = stage
        if checkKey(db[str(mes.chat.id)], "cart") == True:
            if len(db[str(mes.chat.id)]['cart']) == 0 or len(db[str(mes.chat.id)]['cart']) is None:
                bot.send_message(mes.chat.id,
                                 "Your cart is empty! Add something that you would like to order and come back again!")
                setStage("MainMenu", mes)
            else:
                print("This is user's cart: " + str(db[str(mes.chat.id)]['cart']))
                bot.send_message(mes.chat.id, "This is what's in your cart right now:")
                keys = list(db[str(mes.chat.id)]['cart'].keys())
                values = list(db[str(mes.chat.id)]['cart'].values())
                total = 0
                for i in range(0, len(db[str(mes.chat.id)]['cart'])):
                    total += int(values[i]['price']) * int(values[i]['amount'])
                    bot.send_photo(mes.chat.id, values[i]['image'])
                    bot.send_message(mes.chat.id, values[i]['name']+", "+values[i]['description']+". Price per piece: "+str(values[i]['price']+"$"), reply_markup=cartInlines(str(keys[i]), mes, values[i]['amount']))

                totalid = bot.send_message(mes.chat.id, "Total price: "+ str(total)+"$")
                if checkKey(db[str(mes.chat.id)], "cartinfo") == False:
                    db[str(mes.chat.id)]['cartinfo'] = {}
                db[str(mes.chat.id)]['cartinfo']["id"] = totalid.message_id
                db[str(mes.chat.id)]['cartinfo']['total'] = calcTotal(mes)
                print("MSG ID: "+str(totalid.message_id)+" | TOTAL: "+str(total))
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
        print()

def newUser(mes):
    id = mes.chat.id
    name = mes.from_user.first_name
    db[str(id)] = {}
    db1 = db[str(id)]
    db1['name'] = name
    db1['stage'] = ''
    db1['country'] = ''
    db1['city'] = ''
    db1['company'] = ''
    db1['address'] = ''
    db1['orders'] = {}
    db1['cart'] = {}
    db1['step'] = 0
    db1['category'] = ""
    db1['browsing'] = {}
    db1['cartinfo'] = {}

def saveUser(mes):
    fb.patch("users/"+str(mes.chat.id), db[str(mes.chat.id)])
    print("Saved "+str(mes.chat.id)+" to database. DEBUG:")
    print(db[str(mes.chat.id)])

def getStage(mes):
    return db[str(mes.chat.id)]['stage']

def checkKey(dict, key):
    whattoreturn = False
    keys = list(dict.keys())
    for i in range(0, len(dict)):
        if str(key) == str(keys[i]):
            whattoreturn = True
    return whattoreturn
################################################################################################## Setup

updateLocalDB() # Updating local DB to improve performance
sortCategories()

################################################################################################## Listeners

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
        print("This is a cart inline: "+data)

        if str(call.data) != "AMOUNT":
            findName = data[:data.find(";")]
            findAction = data[data.find(";")+1:data.find("|")]
            #print("debug: " + str(int(findAction)))
            print("Name is found: |"+findName+"|")
            print("Action is found: |"+str(findAction)+"|")

            if findAction != "delete" and int(findAction) >= 0:                       ##### ADDING AMOUNT TO CART
                print("Tried to do smth")
                db[str(mes.chat.id)]['cart'][str(findName)]['amount'] = int(findAction)
                newInt = int(db[str(mes.chat.id)]['cart'][findName]['amount'])
                bot.edit_message_reply_markup(chat_id=id, message_id=mes.message_id, reply_markup=cartInlines(findName, mes, newInt))
                db[str(mes.chat.id)]['cartinfo']['total'] = calcTotal(mes)
                bot.edit_message_text(chat_id=mes.chat.id, message_id=db[str(mes.chat.id)]['cartinfo']['id'], text="Total price: "+ str(db[str(mes.chat.id)]['cartinfo']['total'])+"$" )

            elif findAction == "delete":
                print("Deleting "+findName)
                db[str(mes.chat.id)]['cart'].pop(findName)
                bot.delete_message(chat_id=mes.chat.id, message_id=mes.message_id)
                saveUser(mes)

                if len(db[str(mes.chat.id)]['cart']) == 0 or db[str(mes.chat.id)]['cart'] is None:
                    bot.send_message(mes.chat.id, "Cart is empty! Add something and then come back!")
                    setStage("MainMenu", mes)
            else:
                print("Something went wrong, returning")
                setStage("MainMenu", mes)
    elif data[data.find(";")+1:] != 'add' and str(call.data) != "AMOUNT" and data != "clear":
        print("Adding "+call.data)
        #print("DOING THIS: "+str(int(data[data.find(" ")+1:])))
        if int(data[data.find(";")+1:]) >= 0:
            bot.edit_message_reply_markup(chat_id=id, message_id=mes.message_id, reply_markup=itemInline(data[:data.find(";")], int(data[data.find(";")+1:]))) ## todo: fix this shit please
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
    saveUser(mes)

@bot.message_handler(content_types=['text'])
def handle_Text(mes):
    print(db)
    userDB = db[str(mes.chat.id)]
    print("[" + mes.from_user.first_name+" | "+userDB['stage']+": " + mes.text)
    if getStage(mes) == 'registerCountry':
        userDB['country'] = mes.text
        print("User "+mes.from_user.first_name+"'s country is set to "+mes.text)
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
        saveUser(mes)
        setStage("MainMenu", mes)

    elif getStage(mes) == "finishRegister" and mes.text == "No":
        print("Restart")
        setStage("firststart", mes)

    elif getStage(mes) == "settings" and mes.text == "Register again":
        print("Restart")
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

    elif getStage(mes) == "browse" and mes.text in list(itemsdb.categories):
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
        for i in range(0, len(cart)):
            print(values[i]['name']+", "+str(values[i]['amount'])+" pcs, "+str(int(values[i]['price'])*int(values[i]['amount']))+"$")
            bot.send_message(mes.chat.id, values[i]['name']+", "+str(values[i]['amount'])+" pcs, "+str(int(values[i]['price'])*int(values[i]['amount']))+"$")
            total += int(values[i]['price'])*int(values[i]['amount'])

        bot.send_message(mes.chat.id, "Price: "+str(total)+"$. Would you like to pick up the order yourself, or get it by delivery?", reply_markup=newBut("I'll pick up myself", "Delivery"))

    elif mes.text == "I'll pick up myself" and getStage(mes) == "cart":
        bot.send_message(mes.chat.id, "Great! Address for pickup is "+ usersdb.owner_Info['Store_Name'] + ", " + usersdb.owner_Info['Storage_Address'])
        setStage("payment", mes)


    elif mes.text == "Clear cart" and getStage(mes) == "cart":
        bot.send_message(mes.chat.id, "Would you really like to clear your cart?", reply_markup=newInlineCallback(("Yes", "clear"), ("No", "skip")))
    else:
        bot.send_message(mes.chat.id, "Unknown command. Use /help to see available commands")


################################################################################################## END


bot.polling()