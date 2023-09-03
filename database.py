import sqlite3

conn = sqlite3.connect('crossposter.db')

cursor = conn.cursor()

# Create the database if it doesn't exist
def createDatabase():
    # Table of users for crossposting
    cursor.execute('''CREATE TABLE IF NOT EXISTS crosspost_users
                    (id INTEGER PRIMARY KEY, atproto_user TEXT, atproto_app_pass TEXT, 
                    mastodon_access_token TEXT, mastodon_uri TEXT, at_last_run TEXT, mastodon_last_run TEXT)''')
    # Table of posts for mastodon crossposting
    cursor.execute('''CREATE TABLE IF NOT EXISTS at_posts
                    (id INTEGER PRIMARY KEY, userID INTEGER, createdAt TEXT, at_post BLOB)''')
    # Table of posts for at crossposting
    cursor.execute('''CREATE TABLE IF NOT EXISTS mastodon_posts
                    (id INTEGER PRIMARY KEY, userID INTEGER, createdAt TEXT, mastodon_post BLOB)''')
    conn.commit()  # Submit changes to database

# Add a user to the database
def addUser(atproto_user, atproto_app_pass, mastodon_access_token, mastodon_uri, timeNow, timeNow2):
    cursor.execute('''INSERT INTO crosspost_users (atproto_user, atproto_app_pass, mastodon_access_token, mastodon_uri, at_last_run, mastodon_last_run)
                    VALUES (?, ?, ?, ?, ?, ?)''', (atproto_user, atproto_app_pass, mastodon_access_token, mastodon_uri, timeNow, timeNow2))
    conn.commit()  # Submit changes to database

# Get users from the database
def getUsers():
    cursor.execute('''SELECT * FROM crosspost_users''')
    users = cursor.fetchall()
    return users

# Add a at post to the database
def addATPost(userID, createdAt, at_post):
    cursor.execute('''INSERT INTO at_posts (userID, createdAt, at_post)
                    VALUES (?, ?, ?)''', (userID, createdAt, at_post))
    conn.commit()  # Submit changes to database

# Add a mastodon post to the database
def addMastodonPost(userID, createdAt, mastodon_post):
    cursor.execute('''INSERT INTO mastodon_posts (userID, createdAt, mastodon_post)
                    VALUES (?, ?, ?)''', (userID, createdAt, mastodon_post))
    conn.commit()  # Submit changes to database

# Delete a at post from the database
def deleteATPost(postID):
    postID = str(postID)
    cursor.execute('''DELETE FROM at_posts WHERE id = ?''', (postID))
    conn.commit()  # Submit changes to database

# Update the last run time for a user
def updateLastRun(userID, timeNow, platform):
    userID = str(userID)
    timeNow = str(timeNow)
    if platform == 'at':
        query = '''UPDATE crosspost_users SET at_last_run = ? WHERE id = ?'''
    elif platform == 'mastodon':
        print('mastodon')
        query = '''UPDATE crosspost_users SET mastodon_last_run = ? WHERE id = ?'''
    cursor.execute(query, (timeNow, userID))
    conn.commit()  # Submit changes to database

# Get list of at posts for a user
def getATPosts(userID):
    userID = str(userID)
    cursor.execute(
        '''SELECT * FROM at_posts WHERE userID = ?''', (userID))
    posts = cursor.fetchall()
    return posts

# Get list of mastodon posts for a user
def getMastodonPosts(userID):
    userID = str(userID)
    cursor.execute(
        '''SELECT * FROM mastodon_posts WHERE userID = ?''', (userID))
    posts = cursor.fetchall()
    return posts

# Delete a mastodon post from the database
def deleteMastodonPost(postID):
    postID = str(postID)
    cursor.execute('''DELETE FROM mastodon_posts WHERE id = ?''', (postID))
    conn.commit()  # Submit changes to database