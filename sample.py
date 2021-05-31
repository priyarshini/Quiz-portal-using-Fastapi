from typing import List
from fastapi import FastAPI,Request,Form
from fastapi.staticfiles import StaticFiles 
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse,JSONResponse
from pydantic import BaseModel,Field
import databases
from sqlalchemy import and_
import sqlalchemy

template=Jinja2Templates(directory="Template")

class quiz(BaseModel):
    question: str
    correct_answer: str
    level:str
    category:str
    incorrect_answer1:str
    incorrect_answer2:str
    incorrect_answer3:str

class view(BaseModel):
    name: str
    category: str
    level:str
    score:int
    duration:int

DATABASE_URL = "sqlite:///./myquiz.db"

metadata = sqlalchemy.MetaData()

database = databases.Database(DATABASE_URL)

player = sqlalchemy.Table(
    "player",
    metadata,
    sqlalchemy.Column("id"),
    sqlalchemy.Column("name")

)

admin = sqlalchemy.Table(
    "admin",
    metadata,
    sqlalchemy.Column("id"),
    sqlalchemy.Column("name"),
    sqlalchemy.Column("password")

)


Userscore = sqlalchemy.Table(
    "userscore",
    metadata,
    sqlalchemy.Column("id"),
    sqlalchemy.Column("name"),
    sqlalchemy.Column("level"),
    sqlalchemy.Column("category"),
    sqlalchemy.Column("score"),
    sqlalchemy.Column("duration")
)

category = sqlalchemy.Table(
    "category",
    metadata,
    sqlalchemy.Column("id"),
    sqlalchemy.Column("name"),
    sqlalchemy.Column("status")
)

quests = sqlalchemy.Table(
    "questions",
    metadata,
    sqlalchemy.Column("id"),
    sqlalchemy.Column("category"),
    sqlalchemy.Column("level"),
    sqlalchemy.Column("question"),
    sqlalchemy.Column("correct_answer"),
    sqlalchemy.Column("incorrect_answer1"),
    sqlalchemy.Column("incorrect_answer2"),
    sqlalchemy.Column("incorrect_answer3"),
    sqlalchemy.Column("status")
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

metadata.create_all(engine)

app = FastAPI()

app.mount("/static",StaticFiles(directory="static"),name="static")

@app.on_event("startup")
async def connect():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/",response_class=HTMLResponse)
async def start(request:Request):
   show="Welcome quizess !"
   query = Userscore.delete()
   rol= await database.execute(query) 
   query = player.delete()
   rol2= await database.execute(query)
   return template.TemplateResponse("index.html",{"request":request,"text":show})

@app.get("/login",response_class=HTMLResponse)
async def createget(request:Request):
    rows = await category_query()
    query1 = player.select()
    playername = await database.fetch_one(query1)
    return template.TemplateResponse("test.html",{"request":request,"rows":rows[0],"playername":playername})

@app.post("/login",response_class=HTMLResponse)
async def create(request:Request,username:str=Form(...)):
    query = player.insert().values(name=username)
    record_id = await database.execute(query)
    query1 = player.select().where(player.c.name == username)
    playername = await database.fetch_one(query1)
    rows = await category_query()
    return template.TemplateResponse("test.html",{"request":request,"rows":rows[0],"playername":playername})

@app.post("/set",response_class=HTMLResponse)
async def quest(request:Request,category:str=Form(...),difficulty:str=Form(...)):
   catinfo=category
   diffinfo=difficulty
   query = player.select()
   playern = await database.fetch_one(query)
   return template.TemplateResponse("quizpage.html",{"request":request,"catinfo":catinfo,"diffinfo":diffinfo,"playern":playern})
  

@app.get("/set/{category}&{difficulty}/",response_model=List[quiz])
async def sendquestions(request:Request,category:str,difficulty:str):
    query=quests.select().where(and_(quests.c.level == difficulty , quests.c.category == category, quests.c.status== 1) )
    qs=await database.fetch_all(query)
    return qs

@app.get("/adminpage.html",response_class=HTMLResponse)
async def adminlogin(request:Request):
    show="Welcome Admin !"
    return template.TemplateResponse("adminpage.html",{"request":request,"text":show})

@app.post("/dashboard",response_class=HTMLResponse)
async def admincheck(request:Request,adminName:str=Form(...),password:str=Form(...)):
    query=admin.select()
    qs=await database.fetch_one(query)
    if (adminName == qs.name and password== qs.password ):
        var="Welcome Admin !"
        return template.TemplateResponse("dashboard.html",{"request":request,"var":var})
    else : 
        show="Incorrect Name or Password !"
        return template.TemplateResponse("adminpage.html",{"request":request,"text":show})  

@app.post("/changed",response_class=HTMLResponse)
async def changepsw(request:Request,psw:str=Form(...),psw1:str=Form(...)):
    if ( psw == psw1 ):
        query=admin.update().where(admin.c.id == 1).values(password=psw1)
        record = await database.execute(query)
        msg="password changed"
        return template.TemplateResponse("dashboard.html",{"request":request,"msg":msg}) 
    else :
        var="password doesn't match"
        return template.TemplateResponse("dashboard.html",{"request":request,"var":var})   

@app.post("/addcat",response_class=HTMLResponse)
async def addcat(request:Request,catname:str=Form(...)):
    query=category.insert().values(name=catname,status=1)
    row=await database.execute(query)
    rows,rows1 = await category_query()
    return template.TemplateResponse("category.html",{"request":request,"rows":rows,"rows1":rows1})

@app.post("/addques",response_class=HTMLResponse)
async def addquestion(request:Request,questio:str=Form(...),inop1:str=Form(...),inop2:str=Form(...),inop3:str=Form(...),inop4:str=Form(...),cname:str=Form(...),lev:str=Form(...)):
    query=quests.insert().values(question=questio,incorrect_answer1=inop1,incorrect_answer2=inop2,incorrect_answer3=inop3,correct_answer=inop4,level=lev,category=cname,status=1)
    rows=await database.execute(query)
    rows2,rows3= await quiz_query()
    cat= await category_query()
    return template.TemplateResponse("qa.html",{"request":request,"rows2":rows2,"rows3":rows3,"cat":cat[0]})
    

@app.get("/category.html",response_class=HTMLResponse)
async def catpage(request:Request):
    rows,rows1 = await category_query()
    return template.TemplateResponse("category.html",{"request":request,"rows":rows,"rows1":rows1})

@app.get("/qa.html",response_class=HTMLResponse)
async def quepage(request:Request):
    rows2,rows3= await quiz_query()
    cat= await category_query()
    return template.TemplateResponse("qa.html",{"request":request,"rows2":rows2,"rows3":rows3,"cat":cat[0]})

@app.post("/category.html",response_class=HTMLResponse)
async def upcat(request:Request,catget:str=Form(...),id:int=Form(...)):
    query = category.select().where(category.c.id == id)
    check = await database.fetch_one(query)
    if (check.status == 0):
        que=category.update().where(category.c.id == id).values(status=1)
        rec = await database.execute(que)
    else :    
        query=category.update().where(category.c.id == id).values(name=catget)
        record = await database.execute(query)
    rows,rows1 = await category_query()
    return template.TemplateResponse("category.html",{"request":request,"rows":rows,"rows1":rows1})

@app.post("/qa.html",response_class=HTMLResponse)
async def upqa(request:Request,levelget:str=Form(...),cat:str=Form(...),id:int=Form(...),qget:str=Form(...),ans1:str=Form(...),ans2:str=Form(...),ans3:str=Form(...),ans:str=Form(...)):
    query = quests.select().where(quests.c.id == id)
    check = await database.fetch_one(query)
    if (check.status == 0):
        que=quests.update().where(quests.c.id == id).values(status=1)
        rec = await database.execute(que)
    else :    
        query=quests.update().where(quests.c.id == id).values(category=cat,level=levelget,question=qget,incorrect_answer1=ans1,incorrect_answer2=ans2,incorrect_answer3=ans3,correct_answer=ans)
        record = await database.execute(query)
    rows2,rows3= await quiz_query()
    cat= await category_query()
    return template.TemplateResponse("qa.html",{"request":request,"rows2":rows2,"rows3":rows3,"cat":cat[0]})        
 
@app.get("/updatecat.html/{id}",response_class=HTMLResponse)
async def upcatget(request:Request,id:int):
    qa = category.select().where(category.c.id == id)
    rowsget = await database.fetch_one(qa)
    return template.TemplateResponse("updatecat.html",{"request":request,"rowsget":rowsget})


@app.get("/updateqa.html/{id}",response_class=HTMLResponse)
async def upqaget(request:Request,id:int):
    qa = quests.select().where(quests.c.id == id)
    rowsget = await database.fetch_one(qa)
    return template.TemplateResponse("updateqa.html",{"request":request,"rowsget":rowsget})    

@app.get("/deletecat.html/{id}",response_class=HTMLResponse)
async def delcatget(request:Request,id:int):
    qa = category.select().where(category.c.id == id)
    rowsget = await database.fetch_one(qa)
    return template.TemplateResponse("deletecat.html",{"request":request,"rowsget":rowsget})

@app.get("/deleteqa.html/{id}",response_class=HTMLResponse)
async def delqaget(request:Request,id:int):
    qa = quests.select().where(quests.c.id == id)
    rowsget = await database.fetch_one(qa)
    return template.TemplateResponse("deleteqa.html",{"request":request,"rowsget":rowsget})

@app.post("/delete",response_class=HTMLResponse)
async def deletingcat(request:Request,catget:str=Form(...),id:int=Form(...)):
    que=category.update().where(category.c.id == id).values(status=0)
    rec = await database.execute(que)
    rows,rows1 = await category_query()
    return template.TemplateResponse("category.html",{"request":request,"rows":rows,"rows1":rows1})

@app.post("/deleteqa",response_class=HTMLResponse)
async def deletingqa(request:Request,id:int=Form(...)):
    que=quests.update().where(quests.c.id == id).values(status=0)
    rec = await database.execute(que)
    rows2,rows3= await quiz_query()
    cat= await category_query()
    return template.TemplateResponse("qa.html",{"request":request,"rows2":rows2,"rows3":rows3,"cat":cat[0]})


@app.get("/deletecat/{id}",response_class=HTMLResponse)
async def deletecat(request:Request,id: int):
    query = category.delete().where(category.c.id == id)
    rol= await database.execute(query)
    rows,rows1 = await category_query()
    return template.TemplateResponse("category.html",{"request":request,"rows":rows,"rows1":rows1})

@app.get("/deleteqa/{id}",response_class=HTMLResponse)
async def deleteqa(request:Request,id: int):
    query = quests.delete().where(quests.c.id == id)
    rol= await database.execute(query)
    rows2,rows3= await quiz_query()
    cat= await category_query()
    return template.TemplateResponse("qa.html",{"request":request,"rows2":rows2,"rows3":rows3,"cat":cat[0]}) 

@app.post("/score",response_class=HTMLResponse)
async def scoreout(request:Request,points:int=Form(...),sec:int=Form(...),levels:str=Form(...),cat:str=Form(...),name:str=Form(...)):
   query = Userscore.insert().values(name=name,category=cat,level=levels,score=points,duration=sec)
   record = await database.execute(query)
   query1=Userscore.select()
   rows=await database.fetch_all(query1)
   return template.TemplateResponse("Scorecard.html",{"request":request,"rows":rows})

async def quiz_query():
    query = quests.select().where(quests.c.status == 1)
    rows2 = await database.fetch_all(query)
    query1 = quests.select().where(quests.c.status == 0)
    rows3 = await database.fetch_all(query1)
    return rows2,rows3

async def category_query():
    query2 = category.select().where(category.c.status == 1)
    rows = await database.fetch_all(query2)
    query1 = category.select().where(category.c.status == 0)
    rows1 = await database.fetch_all(query1)
    return rows,rows1 
   


