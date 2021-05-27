#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 26 19:30:48 2021

@author: deepasha
"""
import sqlite3
from sqlite3 import Error
from flask import Flask, jsonify, request


conn = sqlite3.connect('database.db')

conn.execute('DROP TABLE IF EXISTS models')
conn.execute('CREATE TABLE models (name TEXT, tokenizer TEXT, model TEXT)')

cur = conn.cursor()

cur.execute("INSERT INTO models (name, tokenizer, model) VALUES (?, ?, ?)",
            ("distilled-bert", "distilbert-base-uncased-distilled-squad", "distilbert-base-uncased-distilled-squad")
            )
cur.execute("INSERT INTO models (name, tokenizer, model) VALUES (?, ?, ?)",
            ("deepset-roberta", "deepset/roberta-base-squad2", "deepset/roberta-base-squad2")
            )

conn.commit()
cur.execute("CREATE TABLE IF NOT EXISTS qa_log(question TEXT, context TEXT, answer TEXT, model TEXT,timestamp REAL)")



print ("Table created successfully")

conn.close()

app = Flask(__name__)
@app.route('/models', methods=['GET','PUT','DELETE'])
def mod():
    conn  =  sqlite3.connect('database.db')
    cursor  =  conn.cursor()
       
    if  request.method =='GET':
        cursor.execute('''SELECT * FROM models''')
        myresult = cursor.fetchall()
        model=[]
        for i in range(0,len(myresult)):
            record = {"name": myresult[i][0] ,"tokenizer":myresult[i][1]  ,"model": myresult[i][2]}
            model.append(record)
        return jsonify(model)
    
    elif request.method == 'PUT':
        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        insert_put = request.json
        name = insert_put['name']
        tokenizer = insert_put['tokenizer']
        model = insert_put['model']

        c.execute("INSERT INTO models VALUES (?, ?, ?)", (name, tokenizer, model))
        conn.commit()
        c.execute("SELECT * FROM models")
        myresult = c.fetchall()
        model = []
        for i in range(0,len(myresult)):
            record = {"name": myresult[i][0] ,"tokenizer":myresult[i][1]  ,"model": myresult[i][2]}
            model.append(record)
        return jsonify(model)

    elif request.method == 'DELETE':
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        modelname = request.args.get('model')
        c.execute("DELETE FROM models WHERE name = ?", (modelname,))
        conn.commit()
        c.execute("SELECT * FROM models")
        myresult = c.fetchall()
        
        model = []
        for i in range(0,len(myresult)):
            record = {"name": myresult[i][0] ,"tokenizer":myresult[i][1]  ,"model": myresult[i][2]}
            model.append(record)
        return jsonify(model)

app.run()
#conn.close()

@app.route("/answer", methods = ['GET','POST'])
def methods_for_answers():
   
    if  request.method =='POST':
        model_name = request.args.get('model', None)
        data = request.json
        #Default model
        if not model_name:
            model_name='distilled-bert'    
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        #Query to retireve information
        c.execute("SELECT DISTINCT name,tokenizer,model FROM models WHERE name=?",(model_name,))
        myresult = c.fetchall()
       
        row= myresult[0]
        name = row[0]
        tokenizer = row[1]
        model = row[2]
   
        #Implementing Model
        hg_comp = pipeline('question-answering', model=model, tokenizer=tokenizer)

        # Answering the Question
        answer = hg_comp({'question': data['question'], 'context': data['context']})['answer']

        #Generating Timestamp
        ts = time.time()

        #Inserting entry into qa_log table
        c.execute("CREATE TABLE IF NOT EXISTS qa_log(question TEXT, context TEXT, answer TEXT, model TEXT,timestamp REAL)")
        c.execute("INSERT INTO qa_log VALUES(?,?,?,?,?)", (data['question'], data['context'],answer, model_name,ts))
        conn.commit()


        c.close()
        conn.close()

        #JSON to return Output
        output = {
        "timestamp": ts,
        "model": model_name,
        "answer": answer,
        "question": data['question'],
        "context": data['context']}  
        return jsonify(output)


    elif  request.method =='GET':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        name= request.args.get('model')
        start= request.args.get('start')
        end= request.args.get('end')
        
        if name:
            c.execute('SELECT * FROM qa_log WHERE model=? AND timestamp >=? AND timestamp <=?',(name,start,end))
            model = c.fetchall()
            output=[]
            for row in model:
              record = {"timestamp": row[4],
                        "model":row[3],
                        "answer": row[2],
                        "question": row[0],
                        "context": row[1]}
              output.append(record)
            return jsonify(output)
        else:
            c.execute('SELECT * FROM qa_log WHERE timestamp >=? AND timestamp <=?',(start,end))
            model = c.fetchall()
            output=[]
            for row in model:
              record = {"timestamp": row[4],
                        "model":row[3],
                        "answer": row[2],
                        "question": row[0],
                        "context": row[1]}
              output.append(record)
            return jsonify(output)
        
if __name__ == '__main__':
    app.run(port='8000', )
conn.close()
