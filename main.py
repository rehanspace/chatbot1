from flask import Flask, render_template, request, session, redirect, url_for
from neo4j import GraphDatabase
import openai
from pyaiml21 import Kernel
from glob import glob
import nltk
from nltk.corpus import wordnet
import wikipedia
import pytholog as pl
import requests
from bs4 import BeautifulSoup
import pickle


bot_name = "RehanChatBot"

app = Flask(__name__)
app.secret_key = "Rehan"

openai.api_key = "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"

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "rehan263666:)"))

myBot = Kernel()

aimls = glob("./data/*.aiml")
for aiml_file in aimls:
    myBot.learn(aiml_file)

print("All files learned")

myBot.respond("set name Rehan", "0")
myBot.setPredicate("Rehan", "Rehan", sessionID="0")
myBot.respond("reset questions", "0")
myBot.respond("reset facts", "0")

nltk.download("punkt")
nltk.download("wordnet")

user_credentials = {
    "Rehan": {"password": "rehan263666:)", "name": "Rehan"},
    "Sufyan": {"password": "noone1", "name": "Sufyan"},
    "Aleeza": {"password": "password", "name": "Aleeza"},
}

# Load Prolog data
# prolog = Prolog()
# prolog.consult("prologdata.pl")
prolog = pl.KnowledgeBase("KB")
knowledge = []

with open("prologdata.pl", "r") as prolog_file:  # learning prolog facts and rules
    knowledge = prolog_file.readlines()

knowledge = [item.strip() for item in knowledge]  # remove '\n'
prolog(knowledge)


def save_brain_dump(data):
    try:
        with open("brain_dump.pickle", "wb") as file:
            pickle.dump(data, file)
        return True
    except Exception as e:
        print(f"An error occurred while saving the brain dump: {str(e)}")
        return False


def load_brain_dump():
    try:
        with open("brain_dump.pickle", "rb") as file:
            data = pickle.load(file)
        return data
    except Exception as e:
        print(f"An error occurred while loading the brain dump: {str(e)}")
        return {}


def fetch_information(data):
    try:
        summary = wikipedia.summary(data)
        return f"{data}: {summary[:200]}..."
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Provide more detailed information about {data}."
    except wikipedia.exceptions.PageError as e:
        return f"Sorry, I couldn't find your required information about {data} on Wikipedia."


def scrape_website(word):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    }
    
    word = word.title()
    a = word.split()
    word = "_".join(a)

    url = "https://en.wikipedia.org/wiki/" + word
    # print(url)
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    # print(soup.prettify())
    # real work starts below

    para = soup.select("div.mw-parser-output")
    paras = []
    for element in para:
        paragraphs = element.find_all("p", class_=False)
        paras.extend(paragraphs)

    try:
        data = paras[0].text
    except IndexError:
        return None

    return data


def create_username_node(tx, name):
    query = "CREATE (u:UserName {name: $name})"
    tx.run(query, name=name)


def create_relation(tx, start_node, relation, end_node):
    query = """
    MATCH (a), (b)
    WHERE a.name = $start_node AND b.name = $end_node
    CREATE (a)-[:`{relation}`]->(b)
    """
    tx.run(query, start_node=start_node, end_node=end_node, relation=relation)


def create_user_node(tx, name):
    query = "CREATE (u:User {name: $name})"
    tx.run(query, name=name)


@app.route("/")
def home():
    if "username" in session:
        username = session["username"]
        name = session.get("name", "")
        return render_template("index.html", username=username, name=name)
    else:
        return redirect(url_for("login"))


def login_user(username):
    session["username"] = username
    session["name"] = user_credentials[username]["name"]

    try:
        with driver.session() as neo4j_session:
            neo4j_session.write_transaction(create_user_node, session["name"])

        brain_dump = load_brain_dump()
        if "users" not in brain_dump:
            brain_dump["users"] = {}
        brain_dump["users"][username] = {"name": session["name"]}
        save_brain_dump(brain_dump)

    except Exception as e:
        print(f"An error occurred while creating a user node: {str(e)}")


def set_fact(fact, value, value2=None):
    if value2:
        new_fact = fact + "(" + value.lower() + "," + value2.lower() + ")"
    else:
        new_fact = fact + "(" + value.lower() + ")"

    knowledge.insert(0, new_fact)
    prolog(knowledge)
    myBot.respond("reset facts", "0")


def query_kb(fact, value):
    myBot.respond("reset questions", "0")
    query = fact + "(X, " + value.lower().strip() + ")"
    result = prolog.query(pl.Expr(query))

    response = ""
    for value in result:
        try:
            response += value["X"].title() + ", "
        except:
            return None

    return response[:-2]


# function to check predicates
def check_predicates():
    male = myBot.getPredicate("male", "0")
    female = myBot.getPredicate("female", "0")
    parent = myBot.getPredicate("parent", "0")
    child = myBot.getPredicate("child", "0")
    father_of = myBot.getPredicate("father_of", "0")
    mother_of = myBot.getPredicate("mother_of", "0")
    child_of = myBot.getPredicate("child_of", "0")

    result = None

    if male != "unknown":
        set_fact("male", male)
    elif female != "unknown":
        set_fact("female", female)
    elif parent != "unknown":
        set_fact("parent", parent, child)
    elif father_of != "unknown":
        result = query_kb("father", father_of)
    elif mother_of != "unknown":
        result = query_kb("mother", mother_of)
    elif child_of != "unknown":
        result = query_kb("child", child_of)

    return result


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if (
            username in user_credentials
            and user_credentials[username]["password"] == password
        ):
            login_user(username)
            return redirect(url_for("home"))
        else:
            return render_template("error.html", message="Invalid username or password")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        name = request.form["name"]

        if username and password and name:
            if username not in user_credentials:
                user_credentials[username] = {"password": password, "name": name}

                with driver.session() as neo4j_session:
                    neo4j_session.write_transaction(create_user_node, name)

                return redirect(url_for("login"))
            else:
                return render_template("error.html", message="Username already exists")

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("name", None)
    return redirect(url_for("login"))


@app.route("/fetch_data", methods=["GET"])
def fetch_data():
    if request.method == "GET":
        results = list(prolog.query("my_data(X, Y)"))

        # Process and format the results as per your requirement
        fetched_data = []
        for result in results:
            fetched_data.append(f"{result['X']} - {result['Y']}")

        return "\n".join(fetched_data)

    return "Invalid request"


def get_from_wordnet(url):
    url = url.replace(' ', '')
    synsets = wordnet.synsets(url)
    if len(synsets) > 0:
        result = synsets[0].definition()
    else:
        result = None
    return result


@app.route("/get_response", methods=["GET", "POST"])
def get_response():
    fetch_data()
    if request.method == "POST":
        user_input = request.json["user_input"]

        if user_input.lower() in ["bye", "goodbye", "see you", "see you next time"]:
            return "Goodbye!"

        # Check if the user wants to log out
        if user_input.lower() in ["logout", "sign out"]:
            return redirect(url_for("logout"))

        # Handle "who are you" question
        if user_input.lower() in ["who are you?", "what is your name?"]:
            return f"I am {bot_name}, your chatbot assistant!"
        if user_input.lower() in [
            "who created you?",
            "who made you?",
            "who is your botmaster?",
        ]:
            return "Minal created me. She is my Botmaster!"

        if user_input.lower() == "tell me a joke":
            return "Why don't scientists trust atoms? Because they make up everything!"

        if user_input.lower() == "what is the capital of France?":
            return "The capital of France is Paris."

        # Process user input with NLTK WordNet
        tokens = nltk.word_tokenize(user_input)
        synonyms = []
        for token in tokens:
            synsets = wordnet.synsets(token)
            for synset in synsets:
                synonyms.extend(synset.lemmas())

        response = myBot.respond(user_input, "0")
        result = check_predicates()
        if result:
            response = result

        if "FETCH GPT3 RESPONSE" in response:
            myBot.respond("remove FETCH GPT3 RESPONSE", "0")
            response = (
                openai.Completion.create(
                    engine="davinci", prompt=user_input, max_tokens=50
                )
                .choices[0]
                .text.strip()
            )

            # Create nodes and relations in Neo4j
            with driver.session() as session:
                asked_about = user_input
                session.write_transaction(
                    create_username_node, "User", {"name": "Rehan"}
                )
                session.write_transaction(
                    create_username_node, "Topic", {"name": asked_about}
                )
                session.write_transaction(
                    create_relation, "Rehan", "ASKED_ABOUT", asked_about
                )
                session.commit()

        # Web scraping example
        if user_input.startswith("scrape"):
            split_result = user_input.split(" ")
            user_input1 = " ".join(split_result[1:])
            scraped_data = scrape_website(user_input1)
            if scraped_data:
                return scraped_data

        if user_input.startswith("what is"):
            print("inside wordnet")
            split_result = user_input.split(" ")
            user_input1 = " ".join(split_result[2:])
            result = get_from_wordnet(user_input1)
            if result:
                return result

        return response

    return "Invalid request"


if __name__ == "__main__":
    app.run(port=5001)