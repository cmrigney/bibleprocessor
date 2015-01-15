import web
from pymongo import MongoClient, ASCENDING
from bson.code import Code
import json

def doGetCrossRefs(book, chapter, verse, limit):
    client = MongoClient()
    collection = client.bible_database.bible_flat
    item = collection.find_one({"Book": book, "Chapter": chapter, "Verse": verse})
    if item == None:
        return None

    result = []

    #only top 5
    for ref in item["Refs"][:limit]:
        r = collection.find_one({"Book": ref["Book"], "Chapter": ref["Chapter"], "Verse": ref["Verse"]})
        result.append({"Book": ref["Book"], "Chapter": ref["Chapter"], "Verse": ref["Verse"], "Text": r["Text"]})

    return result

def doGetBibleBook(book, chapter):
    client = MongoClient()
    collection = client.bible_database.bible_flat
    maxChapter = client.bible_database.bible_book_meta.find_one({"Book": book})["ChapterCount"]
    items = collection.find({"Book": book, "Chapter": chapter}).sort([("Chapter", ASCENDING), ("Verse", ASCENDING)])
    return { "values": [{"Chapter" : itm["Chapter"], "Verse" : itm["Verse"], "Text" : itm["Text"]} for itm in items],
             "meta": { "MaxChapter": maxChapter } }

def doWordFreq(word):
    client = MongoClient()

    collection = client.bible_database.word_count

    item = collection.find_one({"_id": word})
    if item == None:
        return { "count" : 0 }

    return { "count": item["value"] }

def doFrequencyFollowingQuery(words):
    client = MongoClient();

    map = Code("""
function() {
    var phrase = wordList.join(' ').toLowerCase() + ' ';

    for(var chapNum in this.Chapters)
    {
        if(!this.Chapters.hasOwnProperty(chapNum))
            continue;

        var chapter = this.Chapters[chapNum];
        for(var verseNum in chapter)
        {
            if(!chapter.hasOwnProperty(verseNum))
                continue;

            var verseText = chapter[verseNum].toLowerCase();

            var idx = verseText.indexOf(phrase);

            nextWord = '';

            if(idx >= 0)
            {
                nextWordIdx = idx + phrase.length;
                var letterFound = false;
                for(var i = nextWordIdx; i < verseText.length; i++)
                {
                    if(verseText[i].match(/[a-z]/i)) {
                        letterFound = true;
                        nextWord += verseText[i];
                    }
                    else {
                        if(letterFound)
                            break;
                    }
                }

                if(letterFound) {
                    emit(nextWord, 1);
                }

            }
        }
    }
}
""")

    reduce = Code("""
function(key, values) {
    return Array.sum(values);
}
""")

    collection = client.bible_database.bible_books

    results = collection.inline_map_reduce(map, reduce, scope = { "wordList": words })

    results = sorted(results, key=lambda k: k['value'], reverse=True)

    return results;

def doOrderedQuery(words, limit):
    client = MongoClient()

    map = Code("""
function() {
    var bookName = this.Book;
    for(var chapNum in this.Chapters)
    {
        if(!this.Chapters.hasOwnProperty(chapNum))
            continue;

        var chapter = this.Chapters[chapNum];
        for(var verseNum in chapter)
        {
            if(!chapter.hasOwnProperty(verseNum))
                continue;

            var verseText = chapter[verseNum];

            if(verseText.toLowerCase().indexOf(wordList.join(' ')) >= 0)
            {
                emit({"book": bookName, "chapter": chapNum, "verse": verseNum}, {"text": verseText});
            }
        }
    }
}
    """)

    reduce = Code("""
function(key, values) {
    return values[0].text;
}
    """)

    collection = client.bible_database.bible_books

#need this match format of other
    results = collection.inline_map_reduce(map, reduce, scope = { "wordList": words })

    res = [];

    inner = results;
    for i in xrange(0, len(inner)):
        obj = inner[i];
        dat = {"Scripture": obj["_id"]}
        dat["Scripture"]["text"] = obj["value"]["text"];
        res.append(dat)

    return res[:limit]

def doUnorderedQuery(words, limit):
    wordCount = len(words)

    client = MongoClient()

    map = Code("""
    function() {
        for(var bookName in this.value)
        {
        if(!this.value.hasOwnProperty(bookName))
            continue;
        
        var chapterList = this.value[bookName];
        for(var chapNum in chapterList)
        {
        if(!chapterList.hasOwnProperty(chapNum))
            continue;
        
        var verseList = chapterList[chapNum];
        for(var verseNum in verseList)
        {
        if(!verseList.hasOwnProperty(verseNum))
          continue;
        
        emit({"book": bookName, "chapter": chapNum, "verse": verseNum,  "text": bibleBooks[bookName][chapNum][verseNum]}, {"word": this._id});
        //emit(this._id, {"book": bookName, "chapter": chapNum, "verse": verseNum, "text": bibleBooks[bookName][chapNum][verseNum]});
        }
        }
        }
    }
    """)

    reduce = Code("""
    function(key, values) {
        if(values.length == wordCount)
            return {"Data": key, "Words": values};
    }
    """)

    bibleBooks = {}
    for val in client.bible_database.bible_books.find():
        bibleBooks[val["Book"]] = val["Chapters"];

    collection = client.bible_database.reverse_lookup2

    queryList = []
    for w in words:
        queryList.append({"_id" : w })

    q = {"$or": queryList }
    if wordCount == 1:
        q = queryList[0]

    results = collection.inline_map_reduce(map, reduce, query = q, scope = { "bibleBooks": bibleBooks, "wordCount": wordCount })

    #print results

    res = [];

    inner = results;
    for i in xrange(0, len(inner)):
        obj = inner[i];
        if wordCount == 1:
            res.append({"Scripture": obj["_id"], "Words": obj["value"]})
        elif (obj["value"] != None) and ("Words" in obj["value"]):
            res.append({"Scripture": obj["_id"], "Words": obj["value"]["Words"]})

    return res[:limit]

#########

urls = (
    '/', 'Start',
    '/w/?', 'Query',
    '/freq/?', 'Frequency',
    '/wc/?', 'WordCount',
    '/getbook/?', 'RetreiveBook',
    '/crossrefs/?', 'CrossRefs',
)
app = web.application(urls, globals())

class CrossRefs:
    def GET(self):
        web.header('Content-Type', 'application/json')
        book = web.input(_method='get')["book"]
        chapter = int(web.input(_method='get')["chapter"])
        verse = int(web.input(_method='get')["verse"])
        limit = int(web.input(_method='get')["limit"])
        data = doGetCrossRefs(book, chapter, verse, limit)
        return json.dumps(data)

class RetreiveBook:
    def GET(self):
        web.header('Content-Type', 'application/json')
        book = web.input(_method='get')["book"]
        chapter = web.input(_method='get')["chapter"]
        data = doGetBibleBook(book, int(chapter))
        return json.dumps(data)

class WordCount:
    def GET(self):
        web.header('Content-Type', 'application/json')
        word = web.input(_method='get')["word"]
        data = doWordFreq(word)
        return json.dumps(data)

class Frequency:
    def GET(self):
        #web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        wordList = web.input(_method='get')["words"]
        words = wordList.split(":")
        print words
        data = doFrequencyFollowingQuery(words)
        return json.dumps(data)

class Start:
    def GET(self):
        raise web.seeother('/static/')

class Query:
    def GET(self):
        #web.header('Access-Control-Allow-Origin', '*')
        web.header('Content-Type', 'application/json')
        wordList = web.input(_method='get')["words"]
        ordered = int(web.input(_method='get')["ordered"])
        limit = int(web.input(_method='get')["limit"])
        words = wordList.split(":")
        print words
        if ordered:
            print 'Ordered'
            data = doOrderedQuery(words, limit)
        else:
            print 'Unordered'
            data = doUnorderedQuery(words, limit)
        return json.dumps(data)

if __name__ == "__main__":
    app.run()

