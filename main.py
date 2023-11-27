from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base

from auth import AuthHandler
from schemas import AuthDetails

engine = create_engine("mssql+pyodbc://sa:changeme@DESKTOP-RIAC343\SQLEXPRESS/stables?driver=ODBC+Driver+17+for+SQL+Server")
metadata = MetaData()
Base = declarative_base()
Session = sessionmaker(bind = engine)
session = Session()
auth_handler = AuthHandler()
app = FastAPI()

origins = [
    'http://localhost',
    'http://localhost:8000',
    'http://localhost:8001',
    'http://localhost:5171',
    'http://localhost:5172',
    'http://localhost:5173',
    'http://localhost:5174',
    'http://localhost:5176'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

@app.post("/createusernameandpassword", status_code = 201)
def register(auth_details: AuthDetails):
     
     users = []
     query_string = "SELECT username from users"
     query = text(query_string)
     results = session.execute(query).fetchall()
     
     for user in results:
          users.append(user[0])

     print('users list: ')
     print(users)

     if any(x == auth_details.username for x in users):
          raise HTTPException(status_code = 400, detail = 'Username is taken')
     
     hashed_password = auth_handler.get_password_hash(auth_details.password)
     query_string = f"INSERT INTO dbo.users VALUES ('{auth_details.username}' , '{hashed_password}')"
     query = text(query_string)
     session.execute(query)
     session.commit()

     return {'username': auth_details.username, 'password': auth_details.password }

@app.post('/login')
def login(auth_details: AuthDetails):

    query_string = "SELECT username, password FROM users"
    query = text(query_string)
    results = session.execute(query).fetchall()
    found_user = None

    for user in results:
         
         if user[0] == auth_details.username:
              found_user = {'username' : user[0], 'hashed_password' : user[1]}
              print('found_user: ')
              print(found_user)
              break
      
    print(auth_handler.verify_password(auth_details.password, found_user['hashed_password']))
   
    if (found_user is None) or (not auth_handler.verify_password(auth_details.password, found_user['hashed_password'])):
          print('debug test')
          raise HTTPException(status_code = 401, detail = 'Invalid username and / or password')
    token = auth_handler.encode_token(found_user['username'])
    print('token')
    print(token)
    return { 'token': token }


@app.get('/istokenvalid')
def protected(username = Depends(auth_handler.auth_wrapper)):
     return { 'name': username }
     
@app.get("/getcharacters")
async def getCharacters():

    query_string = "SELECT charName, charClass, account, password, emuAccount, emuPassword, [server], [location] FROM Characters, characterClasses WHERE characters.classID = characterClasses.classID;"
    query = text(query_string)
    
    results = session.execute(query).fetchall()

    characters = []
    for character in results:
        dictionary = {
            "charName": character[0],
            "charClass": character[1],
            "account": character[2],
            "password": character[3],
            "emuAccount": character[4],
            "emuPassword": character[5],
            "server": character[6],
            "location": character[7]
        }
        characters.append(dictionary)

    return characters
    
@app.post("/itemsearch")
async def itemSearch(item_search_input: dict):
    
    item_search_input_string = item_search_input['itemSearchInput']
    query_string = f"SELECT * FROM inventory WHERE itemName LIKE '%{item_search_input_string}%'"
    query = text(query_string)
   
    results = session.execute(query).fetchall()
    
    items = []
    for item in results:
        dictionary = {
            "charName": item[0],
            "location": item[1],
            "itemName": item[2],
            "itemId": item[3],
            "itemCount": item[4]
        }
        items.append(dictionary)

    return items

@app.post("/eqdirupdate")
async def eqDirUpdate(eqDir: dict):
    eq_dir = eqDir['eqDir'] 
    query_string_update = f"UPDATE eqDir SET eqDir = '{eq_dir}'"
    session.execute(text(query_string_update))
    session.commit()

    return eq_dir

@app.get("/geteqdir")
async def geteqdir():
    query_string = "SELECT * FROM eqDir"
    query = text(query_string)
    results = session.execute(query).fetchall()
    obj = {"eqDir": results[0][0]}
    return obj
    
@app.post("/getcharinventory") 
async def getCharInventory(charName: dict):
    char_name = charName['charName']
    query_string = f"SELECT * FROM inventory WHERE charName = '{char_name}'" 
    query = text(query_string)

    results = session.execute(query).fetchall()

    items = []
    for item in results:
         dictionary = {
            "charName": item[0],
            "location": item[1],
            "itemName": item[2],
            "itemId": item[3],
            "itemCount": item[4]
        }
         items.append(dictionary)
  
    return items
    
@app.post("/getcharspellbook")
async def getCharSpellbook(charName: dict):
        char_name = charName['charName']
        char_name = charName['charName']
        query_string = f"SELECT * FROM SpellBooks WHERE charName = '{char_name}'" 
        query = text(query_string)

        results = session.execute(query).fetchall()

        spells = []

        for spell in results:

            dictionary = {
                "charName": spell[0],
                "spellLevel": spell[1],
                "spellName": spell[2]
            }

            spells.append(dictionary)
  
        return spells

@app.post("/addcharacter") 
async def addCharacter(character: dict):
     query_string = f"INSERT INTO dbo.Characters VALUES ('{character['charName']}', '{character['classID']}', '{character['account']}', '{character['password']}', '{character['emuAccount']}', '{character['emuPassword']}', '{character['server']}', '{character['location']}')"
     query = text(query_string)
     session.execute(query)
     session.commit()

@app.post("/deletecharacter")
async def deleteCharacter(charName: dict):
     char_name = charName['charName']
     query_string = f"DELETE FROM Characters WHERE charName = '{char_name}'"
     query = text(query_string)
     session.execute(query)
     session.commit()
    
@app.post("/editcharacter")
async def editCharacter(body: dict):
     query_string = f"UPDATE dbo.Characters SET charName = '{body['charName']}', classID = {body['classID']}, account = '${body['account']}', password = '{body['password']}', emuAccount = '{body['emuAccount']}', emuPassword = '{body['emuPassword']}', server = '{body['server']}', location = '{body['location']}' WHERE charName = '{body['charNameMaster']}'"
     query = text(query_string)
     session.execute(query)
     session.commit()

@app.post("/getmissingspells")
async def getMissingSpells(body: dict):
     char_name = body['charName']
     char_class = body['charClass']
     query_string = f"SELECT * from classSpells WHERE charClass = '{char_class}' AND spellName NOT IN (SELECT spellName FROM spellBooks WHERE charName = '{char_name}')"
     query = text(query_string)
     results = session.execute(query)
     
     missing_spells = []

     for spell in results:
          dictionary = {
               "charClass": spell[0],
               "spellLevel": spell[1],
               "spellName": spell[2]
          }
          missing_spells.append(dictionary)

     return missing_spells
          
@app.post("/rewritecharinventory")
async def  rewriteCharInventory(body: dict):
     path = body['eqDir']
     char_name = body['charName']
     items = []

     with open(f"{path}{char_name}", "r") as file:
          next(file)
          for line in file:
              row = line.strip().split("\t")
              items.append(row)
    
     # character invetory parsed and converted to 2d list, now lets delete the old db:
     query_string_delete = f"DELETE FROM dbo.Inventory WHERE charName = '{char_name}'"
     query = text(query_string_delete)
     session.execute(query)
     session.commit()

     # Now that the old DB is deleted, we need to insert the new entries into the new DB:
     for item in items:
          item[1] = item[1].replace("'", "''")
          query_string_insert = f"INSERT INTO dbo.Inventory VALUES ('{char_name}', '{item[0]}', '{item[1]}', '{item[2]}', '{item[3]}', '{item[4]}')"     
          query = text(query_string_insert)
          session.execute(query)
          session.commit()
          print('DB line INSERTed!')

     # SELECT the new charItems DB
     query_string_select = f"SELECT * FROM dbo.Inventory WHERE charName = '{char_name}'"
     query = text(query_string_select)
     results = session.execute(query)

     items = []
     for item in results:
         dictionary = {
             "charName": item[0],
             "itemName": item[1],
             "location": item[2],
             "itemId": item[3],
             "itemCount": item[4]
        }
         items.append(dictionary)

     return items

@app.post("/copyui")
async def copyUi(body: dict):
     
     char_name = body['charName']
     char_class = body['charClass']
     eq_dir = body['eqDir']
  
     with open(f'./classUIs/UI_{char_class}_P1999PVP.ini', 'r') as file:
         ini_contents = file.read()
     
     with open(f'{eq_dir}/UI_{char_name}_P1999PVP.ini', 'w') as file:
         file.write(ini_contents)

     with open(f'./classUIs/{char_class}_P1999PVP.ini', 'r') as file:
         ini_contents2 = file.read()
     
     with open(f'{eq_dir}/{char_name}_P1999PVP.ini', 'w') as file:
         file.write(ini_contents2)

@app.post("/createspellsdb")
async def copyUI(body: dict):
     char_names = body['charNames']
     ed_dir = body['eqDir']
     # DELETE entire spells DB
     query_string_delete = f"DELETE FROM Spellbooks"
     query = text(query_string_delete)
     session.execute(query)
     session.commit()
     # Loop through 'char_names' list
     for char in char_names:
           try:
                with open(f'{ed_dir}{char}spells', 'r') as file:
                    for line in file:
                        row = line.strip().split("\t")
                        if len(row) == 2:
                            row[1] = row[1].replace("'", "''")
                            query_string = f"INSERT into dbo.SpellBooks VALUES ('{char}', '{row[0]}', '{row[1]}')"
                            query = text(query_string)
                            try:
                                session.execute(query)
                                session.commit()
                            except SQLAlchemyError as e:
                                print('error!', str(e))
           except FileNotFoundError as e:
                print("File not found!", str(e))
                
@app.post("/createinventorydb")
async def createInventoryDb(body: dict):
     char_names = body['charNames']
     eq_dir = body['eqDir']
     # DELETE old db
     query_string_delete = f"DELETE FROM Inventory"
     query = text(query_string_delete)
     session.execute(query)
     session.commit()
     # Iterate over 'char_names' list
     for char in char_names:
          try:
               with open(f'{eq_dir}{char}', 'r') as file:
                    for line in file:
                         row = line.strip().split("\t")
                         if len(row) >= 5:
                            row[1] = row[1].replace("'", "''")
                            query_string_insert = f"INSERT into dbo.Inventory VALUES ('{char}', '{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}')"
                            query = text(query_string_insert)
                            try:
                                session.execute(query)
                                session.commit()
                            except SQLAlchemyError as e:
                                print('error!', str(e))
                         else:
                              continue
          except FileNotFoundError as e:
               print("File not found!", str(e))

# def create_class_ids_table():
     
#      classes = {
#           'Bard': 1,
#           'Cleric': 2,
#           'Druid': 3,
#           'Enchanter': 4,
#           'Mage': 5,
#           'Monk': 6,
#           'Necromancer': 7,
#           'Paladin': 8,
#           'Ranger': 9,
#           'Rogue': 10,
#           'Shadowknight': 11,
#           'Shaman': 12,
#           'Warrior': 13,
#           'Wizard': 14
#           }
     
#      for char_class, class_id in classes.items():
#           row = row = Character_Classes(class_id=class_id, char_class=char_class)
#           session.add(row)
#      session.commit()
          
# def create_class_spells_table(folder_path):
     
#      try:
#         # Get a list of filenames in the specified folder
#         filenames = os.listdir(folder_path)
#         # Here, we will iterate over the folder, read each file, and INSERT a dict:
#         for filename in filenames:
#              file_path = os.path.join(folder_path, filename)
#              class_name = filename.replace('.txt', '')
#              with open(file_path, 'r') as file:
#                   content = file.readlines()
                  
#                   class_spells = []
#                   for row in content:
#                        row = row.strip().split(',')
#                        # iterate over each line and fill out objects and push them onto list:
#                        class_spell_row = Class_Spells(
#                           char_class = class_name,
#                           spell_level = row[0],
#                           spell_name = row[1]
#                           )
#                        class_spells.append(class_spell_row)

#                   # INSERT here. Iterate over list and QUERY: (could maybe have just done it inside that loop)
#                   for row in class_spells:
#                        session.add(row)
#                        print(row.char_class)
#                   session.commit()
                  
#      except OSError as e:
#         print("Error:", e)
#         return []
      

    



     
     
            


    
   
   


     








