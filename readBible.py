__author__ = 'crigney'

import re
import pymongo
from pymongo import MongoClient
import pprint

pp = pprint.PrettyPrinter(indent=4)

client = MongoClient()
db = client.bible_database
bookCollection = db.bible_books

bible = open("/Users/crigney/Downloads/kjv12.txt", 'r').read()

arr = re.split('Book [0-9][0-9]', bible)

arr = arr[1:len(arr)]

books = [n.rstrip().lstrip() for n in arr]

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

print "Done"

"""
genesis = [x for x in books[0].splitlines() if x != '']



for line in genesis:
    if re.match("[0-9][0-9][0-9]:[0-9][0-9][0-9].*", line):
        currentChapter = int(line[0:3])
        currentVerse = int(line[4:7])

    print line
"""
