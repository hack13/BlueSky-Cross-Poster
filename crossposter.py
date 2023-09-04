from atproto import Client, models
from mastodon import Mastodon
from dateutil import parser as dateparser
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from database import *
import json
import os
import requests
import datetime
import sys
import pickle

# Load the .env file
load_dotenv()

# Set the Fernet key
# We use Fernet to encrypt the tokens
if os.environ.get('FERNET_KEY') == None:
    print('FERNET_KEY not found in .env file.')
else:
    key = os.environ.get('FERNET_KEY')
    cipher_suite = Fernet(key)

# Serialize the data of the raw post
def serialize_object(obj):
    return pickle.dumps(obj)

# Get the current timestamp in ISO format
def getCurrentTimestamp():
    return datetime.datetime.now(datetime.timezone.utc).replace(
        tzinfo=None).isoformat() + 'Z'

# Check user exists in the database
def findUser(atproto_user):
    user = checkUser(atproto_user)
    return user

# Split long posts into chunks
def split_string_into_chunks(long_string, limit=300):
    chunks = []
    start = 0
    chunk_index = 1
    
    while start < len(long_string):
        chunk_size = min(limit - len(f" ({chunk_index}/{len(long_string)//limit + 1})") - 1, len(long_string) - start)
        
        # Adjust chunk_size to avoid cutting off in the middle of a word
        if start + chunk_size < len(long_string):
            while long_string[start+chunk_size] != ' ':
                chunk_size -= 1
        
        chunk = long_string[start:start+chunk_size] + f" ({chunk_index}/{len(long_string)//limit + 1})"
        chunks.append(chunk)
        start += chunk_size
        chunk_index += 1
    
    return chunks

# Post to Mastodon Function
def mastodonPost(mastoToken, mastoUri, post):
    # Create Mastodon instance
    mastodon = Mastodon(access_token=mastoToken, api_base_url=mastoUri)
    # Fix the post data
    postRaw = pickle.loads(post)
    feed_view = models.AppBskyFeedDefs.FeedViewPost(**postRaw)
    # Process post data
    if feed_view.post.embed == None:
        mastodon.status_post(
            f"{feed_view.post.record.text}", visibility="private", spoiler_text="From AT Proto Instance")
    else:
        mediaData = [] # Create empty list for media
        # Loop through the images and add them to the list
        for index, image in enumerate(feed_view.post.embed.images):
            getImage = requests.get(f"{image.fullsize}")
            rawImage = getImage.content
            imageType = 'image/jpeg' # BlueSky uses jpeg for all images
            imageData = mastodon.media_post(
                rawImage, mime_type=imageType, description=f'{image.alt}')
            mediaData.append(imageData['id'])
        # Post the status with the media
        mastodon.status_post(f"{feed_view.post.record.text}", media_ids=mediaData,
                             visibility="private", spoiler_text="From AT Proto Instance")

# Post to AT Proto Function
def atProtoPost(actor, actorPass, post):
    # Create AT Proto instance
    agent = Client()
    agent.login(actor, actorPass)
    postRaw = pickle.loads(post)
    convertPost = json.loads(postRaw)
    # Process post data
    # Check if the post has a CW
    if convertPost["cw"] == '':
        text = convertPost["text"]
    else:
        text = "CW: " + convertPost["cw"] + "\n" + convertPost["text"]
    textCount = len(text) # Count the characters in the post
    # Check if the post is over 300 characters and chunk it if it is
    if textCount > 300:
        chunked = split_string_into_chunks(text)
    else:
        chunked = []
        chunked.append(text)
    lastPost = None
    # Loop through the chunks and post them
    for index, chunk in enumerate(chunked):
        # First chunk needs to go through the embed process
        if index == 0:
            # If post contains no embed, post it
            if convertPost["embed"]["images"] == None:
                rootPost = agent.send_post(chunk)
            else:
                # If post contains embed, if an image we can just post it
                if convertPost["embed"]["images"][0]["type"] == 'image':
                    images = []
                    for index, image in enumerate(convertPost["embed"]["images"]):
                        getImage = requests.get(image['preview_url']) # sadly we have to use lower quality images 900kb limit
                        rawImage = getImage.content
                        upload = agent.com.atproto.repo.upload_blob(rawImage)
                        imageDescription = image['description']
                        if imageDescription == None:
                            imageDescription = ''
                        else:
                            pass
                        imageData = models.AppBskyEmbedImages.Image(alt=imageDescription, image=upload.blob)
                        images.append(imageData)
                    # Create the embed data
                    embedData = models.AppBskyEmbedImages.Main(images=images)
                    try:
                        rootPost = agent.send_post(chunk, embed=embedData) # Post the status with the embed
                    except Exception as e:
                        print(e)
                # If we are video, since Bsky has no support for video we will just post the link using the external embed
                elif convertPost["embed"]["images"][0]["type"] == 'video':
                    origPost = requests.get(convertPost["url"]).text
                    soup = BeautifulSoup(origPost, 'html.parser')
                    title = soup.find("meta", attrs={"property": "og:title"})['content']
                    description = soup.find("meta", attrs={"property": "og:description"})['content']
                    upload = requests.get(convertPost["embed"]["images"][0]["preview_url"])
                    previewImage = agent.com.atproto.repo.upload_blob(upload.content).blob
                    embedData = models.AppBskyEmbedExternal.Main(
                        external=models.AppBskyEmbedExternal.External(
                            title=title,
                            uri=convertPost["embed"]["images"][0]["url"], 
                            description=description,
                            thumb=previewImage
                        )
                    )
                    try:
                        rootPost = agent.com.atproto.repo.create_record(
                            models.ComAtprotoRepoCreateRecord.Data(
                                repo=agent.me.did,
                                collection=models.ids.AppBskyFeedPost,
                                record=models.AppBskyFeedPost.Main(createdAt=getCurrentTimestamp(), embed=embedData, text=chunk)
                            )
                        )
                    except Exception as e:
                        print(e)
                else:
                    return convertPost["embed"]["images"][0]["type"] + ' is not supported.'
        else:
            if lastPost != None:
                lastPost = agent.send_post(chunk, reply_to=models.AppBskyFeedPost.ReplyRef(lastPost, rootPost))
            else:
                try:
                    lastPost = agent.send_post(chunk, reply_to=models.AppBskyFeedPost.ReplyRef(rootPost, rootPost))
                except Exception as e:
                    print(e)


def getATProtoFeed(actor, actorPass, limit):
    # Create AT Proto instance
    agent = Client()
    agent.login(actor, actorPass)
    # Get AT Proto feed
    params = models.AppBskyFeedGetAuthorFeed.Params(actor=actor, limit=limit)
    feed = agent.bsky.feed.get_author_feed(params)
    return feed


def getMastoFeed(mastoToken, mastoUri, limit):
    # Create Mastodon instance
    mastodon = Mastodon(access_token=mastoToken, api_base_url=mastoUri)
    # Get Mastodon UserID
    mastodonUserInfo = mastodon.me()
    mastodonUserID = mastodonUserInfo.id
    # Get Mastodon feed
    feed = mastodon.account_statuses(
        mastodonUserID, exclude_replies=True, exclude_reblogs=True, limit=limit)
    return feed

# Add user to database
def createUser(atProtoUser, atProtoPass, mastodonToken, mastodonUri):
    # Check if the user already exists
    user = findUser(atProtoUser)
    if user != None:
        return 'User already exists'
    else:
        # Timestamp
        timeNow = getCurrentTimestamp()
        # Encrypt the tokens
        encMastoToken = Fernet(key).encrypt(mastodonToken.encode())
        encProtoPass = Fernet(key).encrypt(atProtoPass.encode())
        # Add the user to the database
        addUser(atProtoUser, encProtoPass, encMastoToken, mastodonUri, timeNow, timeNow)
        # Return a message
        return 'success'

# Collect posts from AT Proto
def getATPosts():
    users = getUsers()
    timestamp = getCurrentTimestamp()
    for user in users:
        atFeed = getATProtoFeed(user[1], user[2], 10)
        for feed_view in atFeed.feed:
            # Making sure that the post is from the user, we don't wanna handle boosts/reshares
            if feed_view.post.author.handle == user[1]:
                # Serialize the data of the raw post
                serialized_data = serialize_object(feed_view.__dict__)
                # Check if the post is new
                createdAtISO = dateparser.parse(
                    feed_view.post.record.createdAt)
                lastRunISO = dateparser.parse(
                    user[5])
                # Make sure the post isn't a reply
                if feed_view.post.record.reply == None:
                    # If the post is new, add it to the database
                    if createdAtISO > lastRunISO:
                        addATPost(
                            user[0], feed_view.post.record.createdAt, serialized_data)
                    else:
                        # If the post is not new, do nothing
                        print('No new posts.')
                else:
                    print('Post is a reply.')
            else:
                print('No new posts.')  # If not from the user, do nothing
        updateLastRun(user[0], timestamp)  # Update the last run time for the user
    return 'success'

# Collect posts from Mastodon
def getMastoPosts():
    users = getUsers()
    timestamp = getCurrentTimestamp()
    for user in users:
        userToken = Fernet(key).decrypt(user[3]).decode()
        mastoFeed = getMastoFeed(userToken, user[4], 10)
        # print(mastoFeed)
        for post in mastoFeed:
            # Check if the post is new
            createdAtISO = post.created_at
            lastRunISO = dateparser.parse(
                user[6])
            # If the post is new, add it to the database
            if createdAtISO > lastRunISO:
                rawMessage = BeautifulSoup(
                    post.content, 'html.parser').get_text()
                rawSpoiler = BeautifulSoup(
                    post.spoiler_text, 'html.parser').get_text()
                if rawSpoiler != 'From AT Proto Instance':
                    neededData = {
                        'text': rawMessage,
                        'cw': rawSpoiler,
                        'url': post.url,
                        'embed': {
                            'images': post.media_attachments or None
                        }
                    }
                    addMastodonPost(user[0], post.created_at, serialize_object(json.dumps(neededData)))
                else:
                    print('Post is from AT Proto Instance.')
            else:
                # If the post is not new, do nothing
                print('No new posts.')
        updateLastRun(user[0], timestamp, 'mastodon')  # Update the last run time for the user
    return 'success'

# Post to Mastodon
def postToMasto():
    users = getUsers()
    for user in users:
        userToken = Fernet(key).decrypt(user[3]).decode()
        listofPosts = getATPosts(user[0])
        for post in listofPosts:
            try:
                mastodonPost(userToken, user[4], post[3])
                deleteATPost(post[0])
                return 'success'
            except:
                return 'Error posting to Mastodon.'

# Post to AT Proto
def postToAtproto():
    users = getUsers()
    for user in users:
        appPass = Fernet(key).decrypt(user[2]).decode()
        listofPosts = getMastodonPosts(user[0])
        for post in listofPosts:
            try:
                atProtoPost(user[1], appPass, post[3])
                deleteMastodonPost(post[0])
                return 'success'
            except:
                return 'Error posting to AT Proto.'