import spacy
from spacy.lang.en import English
from pymongo import MongoClient
import pandas as pd

client = MongoClient(
    "mongodb+srv://abbu93:itsmeabbu20@cluster0.bafsc.mongodb.net/TestPyMongo?retryWrites=true&w=majority")
client.list_database_names()
db = client["TestPyMongo"]


def appendChunk(original, chunk):
    return original + ' ' + chunk


def isRelationCandidate(token):
    deps = ["ROOT", "adj", "attr", "agent", "amod"]
    return any(subs in token.dep_ for subs in deps)


def isConstructionCandidate(token):
    deps = ["compound", "prep", "conj", "mod"]
    return any(subs in token.dep_ for subs in deps)


def processSubjectObjectPairs(tokens):
    subject = ''
    object = ''
    relation = ''
    subjectConstruction = ''
    objectConstruction = ''
    for token in tokens:
        if "punct" in token.dep_:
            continue
        if isRelationCandidate(token):
            relation = appendChunk(relation, token.lemma_)
        if isConstructionCandidate(token):
            if subjectConstruction:
                subjectConstruction = appendChunk(
                    subjectConstruction, token.text)
            if objectConstruction:
                objectConstruction = appendChunk(
                    objectConstruction, token.text)
        if "subj" in token.dep_:
            subject = appendChunk(subject, token.text)
            subject = appendChunk(subjectConstruction, subject)
            subjectConstruction = ''
        if "obj" in token.dep_:
            object = appendChunk(object, token.text)
            object = appendChunk(objectConstruction, object)
            objectConstruction = ''
    return (subject.strip(), relation.strip(), object.strip())


def processSentence(sentence):
    nlp_model = spacy.load('en_core_web_md')
    tokens = nlp_model(sentence)
    return processSubjectObjectPairs(tokens)


def getPascalCaseText(string):
    return string.title().replace(' ', '')


def upsertMongoDocs(dfdataset, collection):
    url = "https://research-wiki.web.app/data/"
    for index, row in dfdataset.iterrows():
        dict = {}
        subjectDict = {}
        dict["paragraph_content"] = row["paragraph_content"]
        dict["key_points"] = row["key_points"]
        dict["category_label"] = row["category_label"]
        dict["URL_source"] = row["URL_source"]
        dict["source_name"] = row["source_name"]
        dict["source_title"] = row["source_title"]
        dict["published_year"] = row["published_year"]
        dict["read_by"] = row["read_by"]
        subjectDict["label"] = row["entity1"]
        subjectDict["_type"] = "Subject"
        subjectDict["_id"] = url+row["entity1"]
        sub = row["relation"]
        if len(sub.strip()) > 1:
            sub = getPascalCaseText(sub)
        subjectDict[sub] = row["entity2"]
        # info:{data1:{},data2:{}}
        # subjectDict["info"] = {sub: dict}

        query = {"_id": subjectDict["_id"]}
        update = {"$set": subjectDict}
        collection.update_one(query, update, upsert=True)

        temp = collection.find(query)

        tempInfo = {}
        for x in temp:
            if "info" in x.keys():
                tempInfo = x["info"]

        tempInfo[sub] = dict
        collection.update_one(query, {"$set": {"info": tempInfo}}, upsert=True)

        secondOne = url+row["entity2"]
        #  In case entity 2 is not in the db already
        query = {"_id": secondOne}
        update = {"$set": {
            "_id": secondOne, "_type": "Subject", "label": row["entity2"]}}
        collection.update_one(query, update, upsert=True)


def tripletExtractionAndUpdates(dfdataset):
    relationList = []
    for index, row in dfdataset.iterrows():
        rowTriple = processSentence(row["key_points"].lower())
        dfdataset.at[index, "entity1"] = rowTriple[0]
        dfdataset.at[index, "relation"] = rowTriple[1]
        dfdataset.at[index, "entity2"] = rowTriple[2]
        if(rowTriple[0] and rowTriple[1] and rowTriple[2]):
            relationList.append(rowTriple[1])
    return {"dataset": dfdataset, "relations": relationList}


def processor(dfdataset):
    print(dfdataset)
    dfdataset["entity1"] = ""
    dfdataset["relation"] = ""
    dfdataset["entity2"] = ""

    # run triplet extraction and update dfdataset and identify new properties
    info = tripletExtractionAndUpdates(dfdataset)
    dfdataset = info["dataset"]
    relationList = info["relations"]

    # prepare and mongo documents
    collection_name = "test"
    collection = db[collection_name]
    upsertMongoDocs(dfdataset, collection)

    print("Printing#################################")
    print(dfdataset)
    # update ontology and the graphql queries
    val = {'files': [dfdataset], 'names': ["Processed_dataset.csv"]}
    return val
