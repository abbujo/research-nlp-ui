import spacy
from spacy.lang.en import English
from pymongo import MongoClient
import pandas as pd
from github import Github
from github import InputGitTreeElement
from datetime import datetime

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

def getSnakeCaseText(string):
    return string.title().replace(' ', '_')

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
        subjectDict["label"] = getSnakeCaseText(row["entity1"])
        subjectDict["_type"] = "Subject"
        subjectDict["_id"] = url+getSnakeCaseText(row["entity1"])
        sub = row["relation"]
        # info:{data1:{},data2:{}}
        # subjectDict["info"] = {sub: dict}

        query = {"_id": subjectDict["_id"]}
        update = {"$set": subjectDict}
        collection.update_one(query, update, upsert=True)

        temp = collection.find(query)

        if len(sub.strip()) > 1:
            sub = getPascalCaseText(sub)

        
        relatedEntity = url+row["entity2"]

        tempInfo = {}
        tempList = []
        flagFirstEntityForRelation = True
        for x in temp:
            if "info" in x.keys():
                tempInfo = x["info"]
            if sub in x.keys():
                flagFirstEntityForRelation = False
                tempList= x[sub]

        if (flagFirstEntityForRelation):
            tempList = [relatedEntity]
        else:
            tempList.append(relatedEntity) 

        tempInfo[sub] = dict
        collection.update_one(query, {"$set": {"info": tempInfo, sub:tempList }}, upsert=True)

        secondOne = url+getSnakeCaseText(row["entity2"])
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
            relationList.append(getPascalCaseText(rowTriple[1]))
    return {"dataset": dfdataset, "relations": relationList}


def getGitCodeLines():
    g = Github("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")
    repo = g.get_user().get_repo('research-visualisation')
    file_contentJS = repo.get_contents('docs/static/visualisation-code.js')
    file_contentTTL = repo.get_contents('docs/static/ontology-code.ttl')

    a_fileJS = file_contentJS.decoded_content
    a_fileTTL = file_contentTTL.decoded_content
    list_of_linesJS = a_fileJS.decode().splitlines()
    list_of_linesTTL = a_fileTTL.decode().splitlines()
    united_linesJS = ""
    for index, line in enumerate(list_of_linesJS):
        united_linesJS=united_linesJS+line+"\n"

    united_linesTTL = ""
    for index, line in enumerate(list_of_linesTTL):
        united_linesTTL=united_linesTTL+line+"\n"

    return {"ontology": {"codelines": united_linesTTL, "file": a_fileTTL, "file_content": file_contentTTL},
            "jsFile": {"codelines": united_linesJS, "file": a_fileJS, "file_content": file_contentJS}, "repo": repo}


def jsFixer(data, relations):
    fix_query1_start = "query1 =(parent)=>'{ Subject(filter: { _id:\"' + parent + '\"}){ _id"
    fix_query1_end = " }}'\n"
    var_query1 = " VarQuery { _id _type label }"
    fix_query2_start = "query2 = (topic) => '{ _CONTEXT { _id _type Subject label } Subject(filter:{_id: [\"' + topic.map(function (item) { return '\"' + item + '\"' }) +']}){ _id _type label"
    fix_query2_end = " }}'\n"
    var_query2 = " VarQuery { _id }"
    q1=""
    q2=""
    for index, item in enumerate(relations):
        q1 = q1 + var_query1.replace("VarQuery", relations[index])
        q2 = q2 + var_query2.replace("VarQuery", relations[index])
    q1 = fix_query1_start + q1 + fix_query1_end
    q2 = fix_query2_start + q2 + fix_query2_end
    lines = q1+q2+data["codelines"]
    return lines


def ttlFixer(data, relations):
    x = "\ndbo:ItemVal a rdf:Property ; rdfs:comment \"property ItemVal\" ; schema:domainIncludes dbo:Subject ; schema:rangeIncludes dbo:Subject .\n"
    for index, item in enumerate(relations):
        relations[index] = x.replace("ItemVal", relations[index])
    newLines = ""
    for index, line in enumerate(relations):
        newLines=newLines+line+"\n"
    lines = data["codelines"]+newLines
    return lines

def gitCommit(repo,git_file,all_files, lines):
    if git_file in all_files:
        contents = repo.get_contents(git_file)
        repo.update_file(contents.path, "committing files from heroku server", lines, contents.sha, branch="main")
        print(git_file + ' UPDATED')
    else:
        repo.create_file(git_file, "committing files", lines, branch="main")
        print(git_file + ' CREATED')


def commitCode(repo, jsFile, ttlFile):
    all_files = []
    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            file = file_content
            all_files.append(str(file).replace('ContentFile(path="','').replace('")',''))

    # Upload to github
    git_prefix = 'docs/'
    git_fileJS = git_prefix + 'visualisation.js'
    git_fileTTL = git_prefix + 'ontology.ttl'
    gitCommit(repo,git_fileJS,all_files,jsFile)
    gitCommit(repo,git_fileTTL,all_files,ttlFile)


def codeFixer(data, relations):
    jsFile = jsFixer(data["jsFile"], relations)
    ttlFile = ttlFixer(data["ontology"], relations)
    commitCode(data["repo"], jsFile, ttlFile)


if __name__ == "__main__":
    dfdataset = pd.read_excel("covid_19_dataset.xlsx")
    print(dfdataset)

def processor(dfdataset):
    dfdataset["entity1"] = ""
    dfdataset["relation"] = ""
    dfdataset["entity2"] = ""

    # run triplet extraction and update dfdataset and identify new properties
    info = tripletExtractionAndUpdates(dfdataset)
    print("Triplets have been successfully created")
    dfdataset = info["dataset"]
    relationList = info["relations"]

    # prepare and mongo documents
    collection_name = "test"
    collection = db[collection_name]
    upsertMongoDocs(dfdataset, collection)
    print("Data has been successfully updated to MongoDB")
    
    # update ontology and the graphql queries - How?
    #  Commit to github after fetching from there - Done
    dict = getGitCodeLines()
    print("Fetched Code lines from remote GIT")
    
    #  relationList
    codeFixer(dict, relationList)
    print("Committed Code lines to remote GIT")
    
    # update ontology and the graphql queries
    val = {'files': [dfdataset], 'names': ["Processed_dataset.csv"]}
    return val
