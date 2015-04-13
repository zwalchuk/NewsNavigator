import requests
import sys
import os
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, json, jsonify


app = Flask(__name__)


@app.route('/')
def enter_keyword():
    
    return render_template('index.html')



@app.route('/click', methods=['GET', 'POST'])
def click():
   
    
    nodes=request.json['nodes']
    links=request.json['links']
    bigWords=request.json['bigWords']
    index=request.json['current']
    
    x = nodes[index]['x']
    y = nodes[index]['y']
    text = nodes[index]['text']
    length = len(nodes)
    words={}
    headlines={}
    combo="O["
    comboWords=[]
    combos=[]
    for node in nodes:
        words[node['text']] = node['index']
        if node['expand'] == 1:
            comboWords.append(node['text'])
    for word in comboWords:
        combo+=word+"^"
    combo=combo[:-1]
    combo+="]"
    try:
        get_url = "http://ad-news-shard1.alchemyapi.com:9004/client/DoLegacy2JSONQuery?start=now-7d&end=now&maxResults=1000&schema.enriched.url.cleanedTitle="+combo+"&return=enriched.url.cleanedTitle,enriched.url.url"
        results = requests.get(url=get_url) 
        response = results.json()
    
        for article in response['docs']:
            combos[:]=[]
            for word in comboWords:
                if word.upper() in article['source']['enriched']['url']['cleanedTitle'].upper():
                    combos.append(word)
            comboStr = ''.join(sorted(combos))
            comboLen = len(combos)
            if comboLen not in headlines:
                headlines[comboLen]={}
            if comboStr not in headlines[comboLen]:
                headlines[comboLen][comboStr]={}
            headlines[comboLen][comboStr][article['source']['enriched']['url']['cleanedTitle']]=article['source']['enriched']['url']['url']

    except Exception as e:
        print e
    
    output = { 'results': { 'nodes': [], 'links': [], 'headlines': headlines, 'combo': combo } }
 
    try:
        get_url = "http://ad-news-shard1.alchemyapi.com:9004/client/DoLegacy2JSONQuery?start=now-7dd&end=now&maxResults=1000&schema.enriched.url.enrichedTitle.keywords.keyword.text="+text+"&unique=schema.enriched.url.enrichedTitle.keywords.keyword.text&override=alchemist123!"
        results = requests.get(url=get_url) 
        response=results.json()
        
        #add to bigWords
        wordList = []
        for kword in response['aggregations']:
            wordList.append(kword['key'])
        bigWords[text]={'wordList':wordList,'expand':1}  
        output['results']['bigWords']=bigWords    
        count1=0 
        count2=0

        for newWord in bigWords[text]['wordList']:
            if newWord in words:
                    output['results']['links'].append({'source':index,'target':words[newWord]})
                    continue
            if count2 < 5:    
                for bigWord in bigWords:
                    if bigWords[bigWord]['expand']==0:
                        continue
                    if bigWord == text:
                        continue
                    if newWord in bigWords[bigWord]['wordList']:
                        if newWord not in words:
                            output['results']['nodes'].append({'x': x, 'y': y, 'text': newWord, 'size': 1.5, 'color': 'white', 'expand': 0})
                            words[newWord]=length
                            length+=1
                            count2+=1
                        output['results']['links'].append({'source':words[newWord],'target':words[bigWord]})
                        output['results']['links'].append({'source':words[newWord],'target':index})
            if newWord not in words and count1 < 5:
                output['results']['nodes'].append({'x': x, 'y': y, 'text': newWord, 'size': 1.5, 'color': 'white', 'expand': 0})   
                output['results']['links'].append({'source':length,'target':index})
                length+=1
                count1+=1
                    
    except Exception as e:
        print e 
                
    return jsonify(output)
    
@app.route('/<keyword>')
def news_page(keyword):
    index=0
    nodes=[]
    links=[]
    headlines=[]
    bigWords={}
    try:
        get_url = "http://ad-news-shard1.alchemyapi.com:9004/client/DoLegacy2JSONQuery?start=now-7dd&end=now&maxResults=1000&schema.enriched.url.enrichedTitle.keywords.keyword.text="+keyword+"&unique=schema.enriched.url.enrichedTitle.keywords.keyword.text&override=alchemist123!"
        results = requests.get(url=get_url) 
        response=results.json()
        
        #add to bigWords
        wordList = []
        for kword in response['aggregations']:
            wordList.append(kword['key'])
        bigWords[keyword]={'wordList':wordList,'expand':1}   
    except:
        pass
    count=0
    nodes.insert(0, {'x': 300, 'y': 200, 'text': keyword, 'size': 3, 'fixed': 1, 'color': '#0066FF', 'expand': 1})
    for word in bigWords[keyword]['wordList']:
        if count > 9:
            break
        if word == keyword:
            continue
        else:
            nodes.append({'x': 300, 'y': 200, 'text': word, 'size': 1.5, 'color': 'white', 'expand': 0})
            links.append({'source':count + 1,'target':0})
            count+=1
                   
    return render_template('cloud.html', nodes=json.dumps(nodes), links=json.dumps(links), bigWords=json.dumps(bigWords))

port = os.getenv('VCAP_APP_PORT', '8000')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(port), debug=True)

