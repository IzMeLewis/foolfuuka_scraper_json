import json
import glob
from bs4 import BeautifulSoup
import threading

json_filename = "test"
jsonl = False

class Post:
    def __init__(self, id, name,  time, content, replies, link, image, tripcode, type, board, title, isop=False):
        self.id = id
        self.name = name
        self.time = time
        self.content = content
        self.replies = replies
        self.link = link
        self.image = image
        self.tripcode = tripcode
        self.type = type
        self.board = board
        self.title = title
        self.isop = isop

class PostEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj,Post):
            return {"id": obj.id, "link": obj.link, "title": obj.title, "name": obj.name,"tripcode": obj.tripcode,  "time": obj.time, "type": obj.type, "replies": obj.replies, "image": obj.image, "content": obj.content, "board": obj.board, "isop": obj.isop}
        return super().default(obj)
    
def dump_json(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, cls=PostEncoder, indent=4)

def dump_jsonl(data, file_path):
    with open(file_path, 'w') as jsonl_file:
        for item in data:
            json.dump(item, jsonl_file, cls=PostEncoder)
            jsonl_file.write('\n')

dictTypes = {"icon-trash": "deleted", "icon-eye-close": "spoiler"}

dPosts = []

def parse_html(filename):
    global dPosts
    with open(filename, "r", encoding="utf-8") as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, "html.parser")
    board = soup.find("article", class_="thread")["data-board"]
    op = parse_post(soup, True, board)
    with threading.Lock():
        dPosts.append(op)
    htmlposts = soup.find_all("article", class_="post")
    for post in htmlposts:
        post = parse_post(post, False, board)
        with threading.Lock():
            dPosts.append(post)
    print("finished file " + filename)

def get_text(tag):
    text = ''
    for content in tag.contents:
        if isinstance(content, str):
            text += content
        elif content.name == 'br':
            text += '\n'
        elif content.name == 'a':
            text += content.get('href')
        elif content.name == 'span':
            text += content.get_text()
    return text.strip()


def parse_post(htmlpost, isop, pBoard):
    #this is absolutely disgusting but it works
    pContent = get_text(htmlpost.find("div", class_="text"))
    post = None
    pId = htmlpost.find("a", title="Reply to this post")["data-post"]
    pName = htmlpost.find("span", class_="post_author").get_text(strip=True)
    pTripcode = htmlpost.find("span", class_="post_tripcode").get_text(strip=True)
    if pTripcode == "":
        pTripcode = None
    pTime = htmlpost.find("time")["datetime"]
    
    pLink = htmlpost.find("a", title="Reply to this post")["href"]
    pImage = dict()
    if htmlpost.find("a", class_="post_file_filename"):
        imageLink = htmlpost.find("a", class_="post_file_filename")["href"]
        imageName = htmlpost.find("a", class_="post_file_filename").get_text(strip=True)
        pImage = {imageName: imageLink}
    else:
        pImage = None

    #check for type    
    pType = None
    for key in dictTypes:
        if htmlpost.find("i", class_=key):
            pType = dictTypes[key]
    
    #check for replies
    Preplies = list()
    if htmlpost.find("span", class_="post_backlink", attrs={"data-post" : pId}):
        spanreplies = htmlpost.find("span", class_="post_backlink", attrs={"data-post" : pId})
        if spanreplies.find("a"):
            replies = spanreplies.find_all("a")
            for reply in replies:
                Preplies.append(reply.get_text(strip=True))
        else:
            Preplies = None

    #check if op
    if isop:
        pTitle = htmlpost.find("h2", class_="post_title").get_text(strip=True)
        post = Post(pId, pName, pTime, pContent, Preplies, pLink, pImage, pTripcode, pType, pBoard, pTitle, True)
    else:
        post = Post(pId, pName, pTime, pContent, Preplies, pLink, pImage, pTripcode, pType, pBoard, None, False)

    return post
    
def main():
    global dPosts
    global textOnlyKey
    html_files = glob.glob(r"./*.html")
    threads = []

    for file in html_files:
        thread = threading.Thread(target=parse_html, args=(file,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    
    if jsonl:
        dump_jsonl(dPosts, f"{json_filename}.jsonl")
    else:
        dump_json(dPosts, f"{json_filename}.json")
                

main()