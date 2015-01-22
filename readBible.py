__author__ = 'crigney'

import re
import pymongo
from pymongo import MongoClient
import pprint
from pymongo import ASCENDING, DESCENDING, TEXT
import csv

pp = pprint.PrettyPrinter(indent=4)

client = MongoClient()
db = client.bible_database
bookCollection = db.bible_books
flatBookCollection = db.bible_flat
metaBookCollection = db.bible_book_meta
bibleTopicCollection = db.bible_topics

bible = open("/Users/crigney/Downloads/kjv12.txt", 'r').read()

arr = re.split('Book [0-9][0-9]', bible)

arr = arr[1:len(arr)]

books = [n.rstrip().lstrip() for n in arr]

def importAsTree():
    for i in xrange(0, len(books)):
        lastChapter = str(-1)
        doc = {}
        book = [x for x in books[i].splitlines() if x != '']
        bookName = book[0]
        doc["Book"] = bookName
        doc["Chapters"] = {}
        book = book[1:]
        for line in book:
            if re.match("[0-9][0-9][0-9]:[0-9][0-9][0-9].*", line):
                currentChapter = str(int(line[0:3]))
                currentVerse = str(int(line[4:7]))
                if lastChapter != currentChapter:
                    doc["Chapters"][currentChapter] = {}
                    lastChapter = currentChapter;
                doc["Chapters"][currentChapter][currentVerse] = line[8:].rstrip().lstrip()
            else:
                doc["Chapters"][currentChapter][currentVerse] += " " + line.rstrip().lstrip()

        bookCollection.insert(doc)
        #pp.pprint(doc)
    print "Done Importing as Tree"

def importAsFlat():
    flatBookCollection.create_index([("BookNumber", ASCENDING), ("Chapter", ASCENDING), ("Verse", ASCENDING)])
    flatBookCollection.create_index([("Book", ASCENDING), ("Chapter", ASCENDING), ("Verse", ASCENDING)])
    flatBookCollection.create_index([("Text", TEXT)], default_language='english')
    for i in xrange(0, len(books)):
        lastChapter = -1
        doc = {}
        book = [x for x in books[i].splitlines() if x != '']
        bookName = book[0]
        doc["Book"] = bookName
        doc["Chapters"] = {}
        book = book[1:]
        for line in book:
            if re.match("[0-9][0-9][0-9]:[0-9][0-9][0-9].*", line):
                currentChapter = int(line[0:3])
                currentVerse = int(line[4:7])
                if lastChapter != currentChapter:
                    doc["Chapters"][currentChapter] = {}
                    lastChapter = currentChapter;
                doc["Chapters"][currentChapter][currentVerse] = line[8:].rstrip().lstrip()
            else:
                doc["Chapters"][currentChapter][currentVerse] += " " + line.rstrip().lstrip()
        for chapNum, items in doc["Chapters"].iteritems():
            for verseNum, text in items.iteritems():
                flatBookCollection.insert({"BookNumber": i+1, "Book" : bookName, "Chapter" : chapNum, "Verse" : verseNum, "Text" : text})
        #pp.pprint(doc)
    print "Done Importing as Flat"

def getVerseLookup():
    verseFile = '/Users/crigney/Downloads/MetaV-master/CSV/Verses.csv'

    verseLookup = {}
    inHeader = True
    with open(verseFile, 'rb') as csvfile:
        verseReader = csv.reader(csvfile, delimiter=',')
        for row in verseReader:
            if inHeader:
                inHeader = False
                continue
            verseLookup[row[0]] = {"Book": row[1], "Chapter": row[2], "Verse": row[3] } #row[0] is unique verseID

    return verseLookup

def getBookMapping():
    booksFile = '/Users/crigney/Downloads/MetaV-master/CSV/Books.csv'

    inHeader = True
    bookMapping = {}
    with open(booksFile, 'rb') as bookscsvfile:
        bookReader = csv.reader(bookscsvfile, delimiter=',')
        for row in bookReader:
            if inHeader:
                inHeader = False
                continue
            bookMapping[int(row[0])] = row[1]

    return bookMapping

def importMetaVCrossRef():
    booksFile = '/Users/crigney/Downloads/MetaV-master/CSV/Books.csv'
    crossRefFile = '/Users/crigney/Downloads/MetaV-master/CSV/CrossRefIndex.csv'

    inHeader = True

    bookMapping = {}
    metaBookCollection.create_index([("Book", ASCENDING)])
    metaBookCollection.create_index([("BookNum", ASCENDING)])
    with open(booksFile, 'rb') as bookscsvfile:
        bookReader = csv.reader(bookscsvfile, delimiter=',')
        for row in bookReader:
            if inHeader:
                inHeader = False
                continue
            bookMapping[int(row[0])] = row[1]
            metaBookCollection.insert({"BookNum": int(row[0]), "Book": row[1], "ChapterCount": int(row[2])})

    verseLookup = getVerseLookup()

    verseSet = {}

    inHeader = True
    with open(crossRefFile, 'rb') as refcsvfile:
        refReader = csv.reader(refcsvfile, delimiter=',')
        for row in refReader:
            if inHeader:
                inHeader = False
                continue
            fromVerseUID = row[0]
            toVerseUID = row[1]
            if fromVerseUID not in verseSet:
                verseSet[fromVerseUID] = []
            verseSet[fromVerseUID].append(toVerseUID)

    for v in verseSet:
        lst = verseSet[v]
        frombk = verseLookup[v]["Book"]
        frombkname = bookMapping[int(frombk)]
        fromchp = verseLookup[v]["Chapter"]
        fromverseNum = verseLookup[v]["Verse"]
        dbLst = []
        for c in lst:
            tobk = verseLookup[c]["Book"]
            tochp = verseLookup[c]["Chapter"]
            toverseNum = verseLookup[c]["Verse"]
            dbLst.append({"Book": bookMapping[int(tobk)], "Chapter": int(tochp), "Verse": int(toverseNum)})

        existing = flatBookCollection.find_one({"Book": frombkname, "Chapter": int(fromchp), "Verse": int(fromverseNum)})
        existing["Refs"] = dbLst
        flatBookCollection.update({"Book": frombkname, "Chapter": int(fromchp), "Verse": int(fromverseNum)}, {"$set": existing}, upsert=False)

    print "Done importing references"

def importMetaVTopics():
    #topics has no header
    topicsFile = '/Users/crigney/Downloads/MetaV-master/CSV/Topics.csv'
    topicIndexesFile = '/Users/crigney/Downloads/MetaV-master/CSV/TopicIndex.csv'

    verseLookup = getVerseLookup()
    bookMapping = getBookMapping()

    #load topic index
    inHeader = True
    topicToVerseSet = {}
    with open(topicIndexesFile, 'rb') as indexcsv:
        treader = csv.reader(indexcsv, delimiter=',')
        for row in treader:
            if inHeader:
                inHeader = False
                continue
            topicId = int(row[0])
            verseId = int(row[1])
            if topicId not in topicToVerseSet:
                topicToVerseSet[topicId] = []
            topicToVerseSet[topicId].append(verseId)

    #print topicToVerseSet
    #print verseLookup

    topicDict = {}
    emptyTopicCount = 0
    with open(topicsFile, 'rb') as topiccsv:
        treader = csv.reader(topiccsv, delimiter=',')
        for row in treader:
            #print row
            topicId = int(row[0])
            topic = row[1].strip()
            subTopic = row[2].strip()
            if topicId not in topicToVerseSet:
                emptyTopicCount += 1
                continue
            if topic not in topicDict:
                topicDict[topic] = []
            innerDoc = {"id": topicId, "SubTopic": subTopic, "Verses":
                [
                    {
                        "Book": bookMapping[int(verseLookup[str(v)]["Book"])],
                        "Chapter": verseLookup[str(v)]["Chapter"],
                        "Verse": verseLookup[str(v)]["Verse"]
                    }
                    for v
                    in topicToVerseSet[topicId]
                ]
            }

            topicDict[topic].append(innerDoc)

    bibleTopicCollection.create_index([("Topic", ASCENDING)])

    for k in topicDict:
        bibleTopicCollection.insert({"Topic": k, "SubTopics": topicDict[k]})

    print "Done inserting topics"
    print "Empty topic count: " + str(emptyTopicCount)

importMetaVTopics()